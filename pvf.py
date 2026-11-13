from __future__ import annotations
import json, struct, zlib, subprocess, shutil, tempfile, os
from pathlib import Path

MAGIC=b'PVF\0'
HEADER=struct.Struct('<4sHHIIQQIII20s')
DIRENT=struct.Struct('<4sIQQQQIBB2s')
VERSION=(1,0)
COMP_NONE=0
COMP_ZSTD=1
FLAG_REQUIRED=1

# Defensive defaults for files supplied by third parties. These limits do not
# change the PVF 1.0 on-disk format or the writer output.
MAX_FILE_SIZE = 512 * 1024 * 1024
MAX_BLOCKS = 256
MAX_BLOCK_SIZE = 128 * 1024 * 1024
MAX_TOTAL_UNCOMPRESSED = 512 * 1024 * 1024

class PVFError(Exception): pass

def _zstd_compress(data: bytes, level: int=9) -> bytes:
    try:
        import zstandard as zstd
        return zstd.ZstdCompressor(level=level).compress(data)
    except ImportError:
        exe=shutil.which('zstd')
        if not exe: raise PVFError('Zstandard unavailable: install package zstandard or zstd CLI')
        p=subprocess.run([exe,'-q',f'-{level}','-c'],input=data,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        if p.returncode: raise PVFError(p.stderr.decode(errors='replace'))
        return p.stdout

def _zstd_decompress(data: bytes, expected: int) -> bytes:
    try:
        import zstandard as zstd
        return zstd.ZstdDecompressor().decompress(data, max_output_size=expected)
    except ImportError:
        exe=shutil.which('zstd')
        if not exe: raise PVFError('Zstandard unavailable: install package zstandard or zstd CLI')
        # Do not use subprocess.run(capture_output=True) for untrusted input:
        # its stdout can grow without bound. Feeding via a temporary file also
        # avoids a full input/output pipe deadlock while consuming stdout.
        with tempfile.TemporaryDirectory(prefix='pvf_zstd_') as directory:
            source = Path(directory) / 'block.zst'
            source.write_bytes(data)
            process = subprocess.Popen([exe, '-q', '-d', '-c', str(source)],
                                       stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            chunks = []
            total = 0
            try:
                while True:
                    part = process.stdout.read(min(1024 * 1024, expected + 1 - total))
                    if not part:
                        break
                    total += len(part)
                    if total > expected:
                        raise PVFError('Zstandard output exceeds declared block size')
                    chunks.append(part)
                if process.wait() != 0:
                    raise PVFError('Zstandard CLI decompression failed')
                return b''.join(chunks)
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait()
                process.stdout.close()

def write_pvf(path, blocks: list[dict], version=VERSION):
    """Write PVF container. Each payload is canonical UTF-8 JSON compressed with Zstandard."""
    prepared=[]
    seen_ids=set()
    for b in blocks:
        bid=b['id'].encode('ascii')
        if len(bid)!=4: raise PVFError(f'Block ID must be 4 ASCII chars: {b["id"]}')
        if bid in seen_ids: raise PVFError(f'Duplicate block ID: {b["id"]}')
        seen_ids.add(bid)
        raw=json.dumps(b['data'],ensure_ascii=False,separators=(',',':'),allow_nan=False).encode('utf-8')
        comp=_zstd_compress(raw)
        prepared.append((bid,b.get('flags',0),comp,len(raw),int(b.get('record_count',0)),zlib.crc32(raw)&0xffffffff,b.get('schema_version',1),COMP_ZSTD))
    dir_offset=HEADER.size
    data_offset=HEADER.size + len(prepared)*DIRENT.size
    directory=[]; cursor=data_offset
    for bid,flags,comp,rawlen,count,crc,schema,compression in prepared:
        directory.append(DIRENT.pack(bid,flags,cursor,len(comp),rawlen,count,crc,compression,schema,b'\0\0'))
        cursor+=len(comp)
    file_size=cursor
    header0=HEADER.pack(MAGIC,version[0],version[1],HEADER.size,0,file_size,dir_offset,len(prepared),DIRENT.size,0,b'\0'*20)
    hcrc=zlib.crc32(header0)&0xffffffff
    header=HEADER.pack(MAGIC,version[0],version[1],HEADER.size,0,file_size,dir_offset,len(prepared),DIRENT.size,hcrc,b'\0'*20)
    # Write beside the destination and atomically replace it only after the
    # complete container has reached disk. A failed write leaves the old file intact.
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=destination.name + '.', suffix='.tmp',
                                     dir=str(destination.parent))
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(header)
            for d in directory: f.write(d)
            for item in prepared: f.write(item[2])
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_name, destination)
    except Exception:
        try: os.unlink(temp_name)
        except OSError: pass
        raise
    return {'file_size':file_size,'block_count':len(prepared),'header_crc32':hcrc}

def read_pvf(path, verify_source=True):
    """Read PVF with defensive resource limits and verify block CRCs.

    ``verify_source`` is a historical, reserved compatibility argument. It
    does NOT verify the original CAD SHA-256; that comparison is performed by
    geometry_report() when the embedded SRCE block is available.
    """
    p=Path(path)
    actual_size = p.stat().st_size
    if actual_size > MAX_FILE_SIZE:
        raise PVFError('PVF file exceeds configured size limit')
    with p.open('rb') as f:
        h=f.read(HEADER.size)
        if len(h)!=HEADER.size: raise PVFError('Truncated PVF header')
        magic,major,minor,hsize,flags,filesize,diroff,nblocks,entrysize,hcrc,res=HEADER.unpack(h)
        if magic!=MAGIC: raise PVFError('Invalid PVF magic')
        if major!=1: raise PVFError(f'Unsupported PVF major version {major}')
        if hsize!=HEADER.size or entrysize!=DIRENT.size: raise PVFError('Unsupported header/directory layout')
        if filesize!=actual_size: raise PVFError('File size does not match header')
        if nblocks > MAX_BLOCKS: raise PVFError('PVF block count exceeds configured limit')
        hzero=HEADER.pack(magic,major,minor,hsize,flags,filesize,diroff,nblocks,entrysize,0,res)
        if zlib.crc32(hzero)&0xffffffff != hcrc: raise PVFError('Header CRC mismatch')
        if diroff < HEADER.size or diroff + nblocks*entrysize > filesize:
            raise PVFError('Invalid directory offset/count')
        f.seek(diroff)
        entries=[]
        total_uncompressed = 0
        for _ in range(nblocks):
            d=f.read(DIRENT.size)
            if len(d)!=DIRENT.size: raise PVFError('Truncated directory')
            bid,bflags,off,csize,usize,count,crc,compression,schema,reserved=DIRENT.unpack(d)
            if off+csize>filesize or off<diroff+nblocks*entrysize: raise PVFError('Invalid block offset/size')
            if csize > MAX_BLOCK_SIZE or usize > MAX_BLOCK_SIZE:
                raise PVFError('PVF block exceeds configured size limit')
            total_uncompressed += usize
            if total_uncompressed > MAX_TOTAL_UNCOMPRESSED:
                raise PVFError('PVF total uncompressed size exceeds configured limit')
            try: block_name=bid.decode('ascii')
            except UnicodeDecodeError: raise PVFError('Non-ASCII block identifier')
            entries.append((block_name,bflags,off,csize,usize,count,crc,compression,schema))
        ids=[e[0] for e in entries]
        if len(ids)!=len(set(ids)): raise PVFError('Duplicate block identifier in directory')
        ranges=sorted((e[2],e[2]+e[3],e[0]) for e in entries)
        for prev,cur in zip(ranges,ranges[1:]):
            if prev[1] > cur[0]: raise PVFError(f'Overlapping blocks: {prev[2]} and {cur[2]}')
        blocks={}
        for bid,bflags,off,csize,usize,count,crc,compression,schema in entries:
            f.seek(off); packed=f.read(csize)
            if compression==COMP_ZSTD: raw=_zstd_decompress(packed,usize)
            elif compression==COMP_NONE: raw=packed
            else: raise PVFError(f'Unknown compression code {compression} in {bid}')
            if len(raw)!=usize: raise PVFError(f'Uncompressed size mismatch in {bid}')
            if zlib.crc32(raw)&0xffffffff != crc: raise PVFError(f'CRC mismatch in {bid}')
            try: data=json.loads(raw.decode('utf-8'))
            except Exception as e: raise PVFError(f'Invalid JSON payload in {bid}: {e}')
            blocks[bid]={'data':data,'record_count':count,'flags':bflags,'schema_version':schema}
    return {'version':(major,minor),'blocks':blocks,'directory':entries,'file_size':filesize}

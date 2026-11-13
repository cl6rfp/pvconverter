"""Regression tests for resource limits when opening untrusted PVF containers."""
from __future__ import annotations
import struct
import tempfile
import unittest
import zlib
from pathlib import Path
from unittest.mock import patch

import pvf


class PVFDefensiveReadTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'sample.pv'
        pvf.write_pvf(self.path, [{'id': 'TEST', 'data': {'hello': 'board'}}])

    def patch_entry(self, **fields):
        data = bytearray(self.path.read_bytes())
        header = pvf.HEADER.unpack_from(data)
        offset = header[6]
        entry = list(pvf.DIRENT.unpack_from(data, offset))
        indexes = {'offset': 2, 'compressed_size': 3, 'raw_size': 4}
        for key, value in fields.items():
            entry[indexes[key]] = value
        pvf.DIRENT.pack_into(data, offset, *entry)
        self.path.write_bytes(data)

    def test_valid_file_remains_readable(self):
        self.assertEqual(pvf.read_pvf(self.path)['blocks']['TEST']['data']['hello'], 'board')

    def test_rejects_file_over_configured_limit(self):
        with patch.object(pvf, 'MAX_FILE_SIZE', self.path.stat().st_size - 1):
            with self.assertRaisesRegex(pvf.PVFError, 'file exceeds'):
                pvf.read_pvf(self.path)

    def test_rejects_block_count_before_directory_allocation(self):
        data = bytearray(self.path.read_bytes())
        header = list(pvf.HEADER.unpack_from(data))
        header[7] = pvf.MAX_BLOCKS + 1
        header[9] = 0
        header[9] = zlib.crc32(pvf.HEADER.pack(*header)) & 0xffffffff
        pvf.HEADER.pack_into(data, 0, *header)
        self.path.write_bytes(data)
        with self.assertRaisesRegex(pvf.PVFError, 'block count'):
            pvf.read_pvf(self.path)

    def test_rejects_declared_large_raw_block_before_decompression(self):
        self.patch_entry(raw_size=pvf.MAX_BLOCK_SIZE + 1)
        with self.assertRaisesRegex(pvf.PVFError, 'block exceeds'):
            pvf.read_pvf(self.path)

    def test_rejects_excessive_total_before_decompression(self):
        self.patch_entry(raw_size=500)
        with patch.object(pvf, 'MAX_TOTAL_UNCOMPRESSED', 499):
            with self.assertRaisesRegex(pvf.PVFError, 'total uncompressed'):
                pvf.read_pvf(self.path)

    def test_rejects_zstd_output_longer_than_declared(self):
        self.patch_entry(raw_size=1)
        with self.assertRaises(pvf.PVFError):
            pvf.read_pvf(self.path)

    def test_still_rejects_crc_corruption(self):
        data = bytearray(self.path.read_bytes())
        offset = pvf.HEADER.size
        entry = list(pvf.DIRENT.unpack_from(data, offset))
        entry[6] ^= 1
        pvf.DIRENT.pack_into(data, offset, *entry)
        self.path.write_bytes(data)
        with self.assertRaisesRegex(pvf.PVFError, 'CRC mismatch'):
            pvf.read_pvf(self.path)


if __name__ == '__main__':
    unittest.main()

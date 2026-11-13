import unittest
from unittest.mock import patch

from gencad_roundtrip_audit import audit


class RoundTripAuditTest(unittest.TestCase):
    def test_compares_source_coordinates_and_metadata(self):
        source = {
            'components': [{'reference':'R1','position':[1.0,2.0],'layer':'BOTTOM',
                            'rotation':90.0,'device':'D','shape':'S','shape_extra':['MIRRORY']}],
            'shapes': [{'name':'S','pins':[]}], 'pads':[], 'padstacks':[], 'signals':[],
            'routes':[], 'mechanical_holes':[], 'tracks':[], 'board_artworks':[], 'devices':[]
        }
        import hashlib, base64
        raw = b'$HEADER\n$ENDHEADER\n'
        sha = hashlib.sha256(raw).hexdigest()
        block_data = {
            'META':{'source_sha256':sha},
            'SRCE':{'encoding':'base64-latin-1','data':base64.b64encode(raw).decode()},
            'COMP':[{'reference':'R1','x':1.0,'y':2.0,'source_layer':'BOTTOM','rotation_deg':90.0,
                     'device':'D','shape_id':1,'shape_transform_tokens':['MIRRORY']}],
            'SHAP':[{'id':1,'name':'S'}],
        }
        doc = {'blocks':{k:{'data':v} for k,v in block_data.items()}}
        with patch('gencad_roundtrip_audit.parse_file', return_value=(source,raw)),\
             patch('gencad_roundtrip_audit.read_pvf', return_value=doc):
            result = audit('sample.cad','sample.pv')
        self.assertEqual(result['error_count'], 0)
        self.assertGreater(result['checks'], 15)

    def test_detects_moved_component(self):
        import hashlib, base64
        raw=b'abc'; sha=hashlib.sha256(raw).hexdigest()
        source={'components':[{'reference':'R1','position':[1,2],'shape':'S'}],
                'shapes':[{'name':'S','pins':[]}], 'pads':[], 'padstacks':[], 'signals':[],
                'routes':[], 'mechanical_holes':[], 'tracks':[], 'board_artworks':[], 'devices':[]}
        blocks={'META':{'source_sha256':sha},'SRCE':{'encoding':'base64-latin-1',
                'data':base64.b64encode(raw).decode()},'COMP':[{'reference':'R1','x':9,'y':2,
                'shape_id':1}],'SHAP':[{'id':1,'name':'S'}]}
        with patch('gencad_roundtrip_audit.parse_file',return_value=(source,raw)),\
             patch('gencad_roundtrip_audit.read_pvf',return_value={'blocks':{k:{'data':v} for k,v in blocks.items()}}):
            result=audit('a','b')
        self.assertGreater(result['error_count'], 0)
        self.assertIn('COMP[1].position',str(result['errors']))


if __name__ == '__main__': unittest.main()

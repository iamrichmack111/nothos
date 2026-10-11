import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import nothos
class Core(unittest.TestCase):
    def test_newline(self):
        self.assertEqual(nothos.clean(r'first\nsecond'),'first\nsecond')
    def test_overlap(self):
        original=(nothos.CHUNK,nothos.OVERLAP)
        try:
            nothos.CHUNK=5;nothos.OVERLAP=2
            parts=list(nothos.chunks('a b c d e f g h'))
            self.assertEqual(parts,['a b c d e','d e f g h'])
        finally:nothos.CHUNK,nothos.OVERLAP=original
    def test_records(self):
        items=list(nothos.records())
        self.assertGreater(len(items),150)
        self.assertTrue(any(x['kind']=='entity' for x in items))
    def test_digest_stable(self):
        r=next(nothos.records());self.assertEqual(nothos.digest(r),nothos.digest(r))
if __name__=='__main__':unittest.main()

import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import nothos
class V6(unittest.TestCase):
 def test_palette(self):self.assertEqual(nothos.PALETTE['tier3'],'#FACC15')
 def test_entities(self):self.assertIn('hermes',nothos.query_entities('Explain Hermes and Apollo'))
 def test_morph_no_fabrication(self):self.assertIsNone(nothos.morph('λύρα')['lemma'])
 def test_graph(self):self.assertIn('edges',nothos.graph_data('hermes'))
 def test_evaluate(self):self.assertGreaterEqual(nothos.evaluate(True)['passed'],4)
 def test_medusa(self):self.assertIn('MEDUSA',nothos.BANNER)
if __name__=='__main__':unittest.main()

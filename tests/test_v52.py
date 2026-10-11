import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import nothos
class EvidenceTests(unittest.TestCase):
    def test_tiers(self):
        self.assertLess(nothos.evidence_tier({'verification':'source_locator_provided_text_not_independently_collated'}),nothos.evidence_tier({'verification':'dataset_relationship_unverified'}))
    def test_source_language(self):
        self.assertEqual(nothos.source_language('Ovid, Metamorphoses 1.1'),'Latin / Roman-era')
        self.assertEqual(nothos.source_language('Homeric Hymn to Hermes'),'Greek tradition')
    def test_source_first(self):
        a={'kind':'relation','verification':'dataset_relationship_unverified','score':.9,'family':'a'}
        b={'kind':'passage','verification':'source_locator_provided_text_not_independently_collated','score':.5,'family':'b'}
        self.assertEqual(nothos.source_first([a,b],1)[0]['family'],'b')
    def test_citation_audit(self):
        self.assertTrue(any('Citation [3]' in x for x in nothos.audit_answer('See [3]',[{},{}])))
    def test_caution_wording(self):
        item=next(x for x in nothos.records() if x['id']=='curated:pan_syrinx')
        self.assertIn('does not explicitly deny',item['body'])
if __name__=='__main__':unittest.main()

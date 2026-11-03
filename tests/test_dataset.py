import csv, json, hashlib, pathlib, unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]/'data'
def read(name):
 with (ROOT/name).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
class DatasetTests(unittest.TestCase):
 def test_counts(self):
  self.assertEqual(len(read('nodes.csv')),150)
  self.assertEqual(len(read('relationships.csv')),350)
  self.assertEqual(len(read('assertions.csv')),350)
 def test_references(self):
  nodes={x['id'] for x in read('nodes.csv')};sources={x['id'] for x in read('sources.csv')}
  rels=read('relationships.csv');assertions=read('assertions.csv')
  self.assertEqual(len(nodes),150)
  self.assertEqual(len({(x['source_id'],x['type'],x['target_id']) for x in rels}),350)
  self.assertTrue(all(x['source_id'] in nodes and x['target_id'] in nodes for x in rels))
  self.assertTrue(all(x['subject_id'] in nodes and x['object_id'] in nodes for x in assertions))
  self.assertTrue(all(x['source_id'] in sources for x in read('evidence.csv')))
 def test_manifest(self):
  manifest=json.loads((ROOT/'manifest.json').read_text())
  for name,sha in manifest['sha256'].items():self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),sha)
if __name__=='__main__':unittest.main()

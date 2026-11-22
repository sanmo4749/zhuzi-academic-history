import json,sqlite3,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from kb import validate,EXCHANGE_TABLES

class PublicLibrary(unittest.TestCase):
 def setUp(self):
  self.con=sqlite3.connect(':memory:');self.con.executescript((ROOT/'schema.sql').read_text(encoding='utf-8'))
  self.seed=json.loads((ROOT/'data/public_seed.json').read_text(encoding='utf-8'))
  for table in EXCHANGE_TABLES:
   for record in self.seed[table]:
    keys=list(record);self.con.execute(f"INSERT INTO {table} ({','.join(keys)}) VALUES ({','.join('?' for _ in keys)})",[record[k] for k in keys])
  self.con.commit()
 def tearDown(self):self.con.close()
 def test_public_evidence_is_metadata_only(self):
  self.assertEqual(validate(self.con),[])
  self.assertEqual(len(self.seed['claims']),64)
  self.assertEqual(len(self.seed['pages']),42)
  self.assertTrue(all(not p['text'] for p in self.seed['pages']))
  self.assertTrue(all(c['primary_status']=='not_checked' for c in self.seed['claims']))
  self.assertTrue(all(s['path'].startswith('private_sources/') for s in self.seed['sources']))
 def test_primary_claim_requires_actual_primary_source(self):
  self.con.execute("UPDATE claims SET review_status='primary_checked',primary_status='primary_checked' WHERE id='C001'")
  self.assertIn('missing_primary_source_witness:C001',validate(self.con))
 def test_hypothesis_is_preserved(self):
  rows=self.con.execute("SELECT modality FROM claims WHERE instr(summary,'严复')>0").fetchall()
  self.assertIn(('source_hypothesis',),rows)
 def test_cli_import_rolls_back_without_evidence(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);(root/'data').mkdir();disk=sqlite3.connect(root/'data/research.sqlite3');self.con.backup(disk);disk.close()
   bad=json.loads(json.dumps(self.seed['claims'][0]));bad['id']='BAD001';payload=root/'bad.json';payload.write_text(json.dumps({'claims':[bad]},ensure_ascii=False),encoding='utf-8')
   run=subprocess.run([sys.executable,str(ROOT/'scripts/kb.py'),'--root',str(root),'import-json',str(payload)],capture_output=True)
   self.assertNotEqual(run.returncode,0)
   c=sqlite3.connect(root/'data/research.sqlite3');self.assertEqual(c.execute('SELECT count(*) FROM claims').fetchone()[0],64);c.close()

if __name__=='__main__':unittest.main()

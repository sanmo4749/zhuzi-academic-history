"""Initialize the public metadata example without overwriting an existing library."""
import argparse,json,sqlite3
from pathlib import Path
from kb import EXCHANGE_TABLES,validate

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);a=p.parse_args();root=a.root.resolve()
 target=root/'data/research.sqlite3'
 if target.exists():raise SystemExit('Database already exists; nothing overwritten. Use kb.py validate/status.')
 seed=json.loads((root/'data/public_seed.json').read_text(encoding='utf-8'))
 target.parent.mkdir(parents=True,exist_ok=True)
 con=sqlite3.connect(target)
 try:
  con.executescript((root/'schema.sql').read_text(encoding='utf-8'))
  with con:
   for table in EXCHANGE_TABLES:
    for record in seed[table]:
     keys=list(record);con.execute(f"INSERT INTO {table} ({','.join(keys)}) VALUES ({','.join('?' for _ in keys)})",[record[k] for k in keys])
   errors=validate(con)
   if errors:raise ValueError(str(errors))
  print('Public example initialized; no source PDFs, OCR or scanned images were included.')
 except Exception:
  con.close();target.unlink(missing_ok=True);raise
 finally:con.close()

if __name__=='__main__':main()

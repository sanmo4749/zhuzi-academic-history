"""Regenerate derived research artifacts from SQLite; never rebuild the database."""
import argparse,json,re,sqlite3,sys
from pathlib import Path
from kb import locate,rows,validate,EXCHANGE_TABLES

def write_json(path,value):
 path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')

def main():
 for stream in (sys.stdout,sys.stderr):
  if hasattr(stream,'reconfigure'):stream.reconfigure(encoding='utf-8')
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root');a=p.parse_args();root=locate(a.root)
 con=sqlite3.connect((root/'data/research.sqlite3').as_uri()+'?mode=ro',uri=True);con.row_factory=sqlite3.Row
 errors=validate(con)
 if errors:raise SystemExit('数据库未通过校验：'+str(errors))
 data={t:rows(con,f'SELECT * FROM {t} ORDER BY id') for t in EXCHANGE_TABLES};con.close()
 for s in data['sources']:
  if not re.fullmatch(r'[A-Za-z0-9_-]+',s['id']):raise SystemExit('来源ID不适合目录命名：'+s['id'])
 pages=sorted(data['pages'],key=lambda r:(r['source_id'],r['pdf_page']))
 by_page={p['id']:p for p in pages};claims={c['id']:c for c in data['claims']}
 reviewed={e['page_id'] for e in data['evidence'] if e['review_status'] in ('source_passage_checked','primary_checked')}
 claim_pages={}
 for e in data['evidence']:claim_pages.setdefault(e['page_id'],set()).add(e['claim_id'])
 previous=root/'data/coverage.json'
 old={r['page_id']:r for r in json.loads(previous.read_text(encoding='utf-8'))} if previous.exists() else {}
 coverage=[dict(page_id=p['id'],source_id=p['source_id'],pdf_page=p['pdf_page'],text_chars=len(p['text']),text_origin=p['text_origin'],printed_page=p['printed_page'],page_map_status=p['page_map_status'],passage_reviewed=p['id'] in reviewed,full_page_transcription_checked=old.get(p['id'],{}).get('full_page_transcription_checked',False),curated_claim_count=len(claim_pages.get(p['id'],set()))) for p in pages]
 stats={t:len(data[t]) for t in ['sources','pages','entities','mentions','claims','relations','disputes','methods']}
 stats.update(ocr_nonempty_pages=sum(bool(p['text'].strip()) for p in pages),passage_reviewed_pages=len(reviewed),primary_checked_claims=sum(c['primary_status']=='primary_checked' for c in data['claims']))
 for t in EXCHANGE_TABLES:
  if t in ('sources','pages'):continue
  (root/f'data/{t}.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in data[t]),encoding='utf-8')
 write_json(root/'data/sources.json',data['sources']);write_json(root/'data/statistics.json',stats);write_json(root/'data/coverage.json',coverage)
 for s in data['sources']:
  target=root/'corpus'/s['id']/'pages.jsonl';target.parent.mkdir(parents=True,exist_ok=True)
  target.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in pages if r['source_id']==s['id']),encoding='utf-8')
 data['pages']=pages;data['entities'].sort(key=lambda r:r['resolution_status']=='unresolved_machine')
 for s in data['sources']:
  source=Path(s['path']);source=source if source.is_absolute() else root/source
  s['uri']=source.as_uri() if source.is_file() else ''
 data['stats']=stats;data['images']={}
 for image in sorted((root/'evidence').glob('*')):
  if image.suffix.lower() not in ('.png','.jpg','.jpeg'):continue
  sid,sep,n=image.stem.rpartition('_')
  if sep and f'{sid}:{n}' in by_page:data['images'][f'{sid}:{n}']='evidence/'+image.name
 template=Path(__file__).with_name('navigation.html').read_text(encoding='utf-8')
 (root/'研究导航.html').write_text(template.replace('__DATA__',json.dumps(data,ensure_ascii=False).replace('<','\\u003c')),encoding='utf-8')
 print(json.dumps({'refreshed':str(root),'counts':stats},ensure_ascii=False,indent=2))

if __name__=='__main__':main()

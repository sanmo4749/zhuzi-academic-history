"""Provenance-first research library. Python standard library only."""
import argparse,json,sqlite3,sys
from pathlib import Path

TABLES=['entities','claims','evidence','relations','disputes','methods']
EXCHANGE_TABLES=['sources','pages','entities','mentions','claims','evidence','relations','disputes','methods']
STATUSES={'machine','text_checked','source_passage_checked','primary_checked','rejected'}
def locate(value=None):
 if value:return Path(value).resolve()
 cfg=Path(__file__).resolve().parents[1]/'library.json'
 if cfg.exists():
  target=Path(json.loads(cfg.read_text(encoding='utf-8'))['root']).expanduser()
  return (target if target.is_absolute() else cfg.parent/target).resolve()
 for p in Path(__file__).resolve().parents:
  if (p/'data/research.sqlite3').exists():return p
 raise SystemExit('请先运行 python scripts/init_library.py 初始化示例库；或用 --root 指定自有资料库')
def emit(value):print(json.dumps(value,ensure_ascii=False,indent=2))
def rows(con,sql,args=()):return [dict(r) for r in con.execute(sql,args)]
def validate(con):
 errors=[]
 if con.execute('PRAGMA integrity_check').fetchone()[0]!='ok':errors.append('integrity_check')
 errors.extend(str(tuple(r)) for r in con.execute('PRAGMA foreign_key_check'))
 for r in con.execute('SELECT c.id FROM claims c LEFT JOIN evidence e ON e.claim_id=c.id WHERE e.id IS NULL'):
  errors.append('claim_without_evidence:'+r[0])
 for r in con.execute("SELECT c.id FROM claims c WHERE c.review_status IN ('source_passage_checked','primary_checked') AND NOT EXISTS(SELECT 1 FROM evidence e WHERE e.claim_id=c.id AND e.review_status IN ('source_passage_checked','primary_checked'))"):
  errors.append('unsupported_review_status:'+r[0])
 for table in ['pages','claims','evidence','mentions']:
  for r in con.execute(f'SELECT id,review_status FROM {table}'):
   if r[1] not in STATUSES:errors.append('invalid_status:'+str(tuple(r)))
 for r in con.execute('SELECT p.id FROM pages p JOIN sources s ON s.id=p.source_id WHERE p.pdf_page<1 OR p.pdf_page>s.pages'):
  errors.append('page_out_of_range:'+r[0])
 for r in con.execute("SELECT id FROM claims WHERE primary_status='primary_checked' AND review_status!='primary_checked'"):
  errors.append('invalid_primary_status:'+r[0])
 for r in con.execute("SELECT c.id FROM claims c WHERE (c.primary_status='primary_checked' OR c.review_status='primary_checked') AND NOT EXISTS(SELECT 1 FROM evidence e JOIN pages p ON p.id=e.page_id JOIN sources s ON s.id=p.source_id WHERE e.claim_id=c.id AND e.review_status='primary_checked' AND s.kind='primary_source')"):
  errors.append('missing_primary_source_witness:'+r[0])
 return errors
def main():
 for stream in (sys.stdout,sys.stderr):
  if hasattr(stream,'reconfigure'):stream.reconfigure(encoding='utf-8')
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root')
 sub=p.add_subparsers(dest='cmd',required=True)
 sub.add_parser('status');sub.add_parser('validate');sub.add_parser('disputes')
 q=sub.add_parser('search');q.add_argument('query');q.add_argument('--layer',choices=['claims','pages','entities','methods'],default='claims');q.add_argument('--limit',type=int,default=10);q.add_argument('--checked-only',action='store_true')
 q=sub.add_parser('page');q.add_argument('source');q.add_argument('number',type=int)
 q=sub.add_parser('entity');q.add_argument('name')
 q=sub.add_parser('export-json');q.add_argument('path')
 q=sub.add_parser('import-json');q.add_argument('path')
 a=p.parse_args();root=locate(a.root);db=root/'data/research.sqlite3'
 uri=db.as_uri()+('?mode=rw' if a.cmd=='import-json' else '?mode=ro')
 con=sqlite3.connect(uri,uri=True);con.row_factory=sqlite3.Row;con.execute('PRAGMA foreign_keys=ON')
 if a.cmd=='status':
  emit({'root':str(root),'counts':{t:con.execute(f'SELECT count(*) FROM {t}').fetchone()[0] for t in ['sources','pages','mentions']+TABLES},'text_origins':rows(con,'SELECT text_origin,count(*) count FROM pages GROUP BY text_origin'),'claim_review':rows(con,'SELECT review_status,count(*) count FROM claims GROUP BY review_status')})
 elif a.cmd=='validate':
  errors=validate(con);emit({'ok':not errors,'errors':errors});sys.exit(bool(errors))
 elif a.cmd=='search':
  field={'claims':'summary','pages':'text','entities':'label','methods':'content'}[a.layer]
  conditions=[f'instr({field},?)>0'];args=[a.query]
  if a.layer in ['claims','pages']:conditions.append("review_status!='rejected'")
  if a.checked_only:
   if a.layer in ['claims','pages']:conditions.append("review_status IN ('source_passage_checked','primary_checked')")
   else:raise SystemExit('--checked-only 仅适用于论断或页文；页文未做全文校订，不会因某段核过而升级')
  result=rows(con,f"SELECT * FROM {a.layer} WHERE {' AND '.join(conditions)} ORDER BY id LIMIT ?",(*args,max(1,min(200,a.limit))))
  for r in result:
   if a.layer=='claims':r['evidence']=rows(con,'SELECT e.*,p.source_id,p.pdf_page,p.printed_page,p.page_map_status FROM evidence e JOIN pages p ON p.id=e.page_id WHERE e.claim_id=?',(r['id'],))
  emit(result)
 elif a.cmd=='page':
  result=rows(con,'SELECT p.*,s.path source_path FROM pages p JOIN sources s ON s.id=p.source_id WHERE p.source_id=? AND p.pdf_page=?',(a.source,a.number));emit(result)
 elif a.cmd=='entity':
  result=rows(con,'SELECT * FROM entities WHERE instr(label,?)>0 OR instr(aliases,?)>0',(a.name,a.name))
  for r in result:
   r['relations']=rows(con,"SELECT r.*,c.summary,c.review_status,c.modality FROM relations r JOIN claims c ON c.id=r.claim_id WHERE (r.subject_id=? OR r.object_id=?) AND c.review_status!='rejected'",(r['id'],r['id']))
   r['mentions']=rows(con,'SELECT page_id,matched_text FROM mentions WHERE entity_id=? LIMIT 40',(r['id'],))
  emit(result)
 elif a.cmd=='disputes':emit(rows(con,'SELECT * FROM disputes'))
 elif a.cmd=='export-json':
  data={t:rows(con,f'SELECT * FROM {t}') for t in EXCHANGE_TABLES};data['schema_version']='1.0';Path(a.path).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8');emit({'written':str(Path(a.path).resolve())})
 elif a.cmd=='import-json':
  data=json.loads(Path(a.path).read_text(encoding='utf-8'));counts={}
  try:
   if not isinstance(data,dict):raise ValueError('顶层必须为JSON对象')
   unknown=set(data)-set(EXCHANGE_TABLES)-{'schema_version'}
   if unknown:raise ValueError(f'未知数据表 {unknown}')
   with con:
    for table in EXCHANGE_TABLES:
     if not isinstance(data.get(table,[]),list):raise ValueError(f'{table}:必须为记录数组')
     valid={r[1] for r in con.execute(f'PRAGMA table_info({table})')}
     for record in data.get(table,[]):
      if set(record)-valid:raise ValueError(f'{table}:未知字段 {set(record)-valid}')
      keys=list(record)
      if not keys:raise ValueError('空记录')
      con.execute(f"INSERT INTO {table} ({','.join(keys)}) VALUES ({','.join('?' for _ in keys)})",[record[k] for k in keys])
     counts[table]=len(data.get(table,[]))
    errors=validate(con)
    if errors:raise ValueError(str(errors))
   emit({'imported':counts})
  except (ValueError,TypeError,sqlite3.Error) as exc:raise SystemExit('导入已回滚：'+str(exc))
 con.close()
if __name__=='__main__':main()

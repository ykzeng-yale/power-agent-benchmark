#!/usr/bin/env python3
"""Publish separately identified source-text-redacted derivatives, never rawdata.

Original responses/transports stay in restricted storage. This tool uses an
explicit public schema, not recursive retention of unknown/raw model fields.
Scientific figures require manual review before optional export; numeric CSVs
are exported only when the frozen scorer verified their data.
"""
import argparse,base64,copy,hashlib,json,pathlib,re
VERSION='workflow-capabilities-public-derivative1'
def sha(b):return hashlib.sha256(b).hexdigest()
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def omitted(v):return {'omitted':True,'original_value_sha256':sha(canonical(v))}
def bounded(v,n=128):return v[:n]if isinstance(v,str)else v
def simple(v):
 if type(v)in(int,float,bool)or v is None:return v
 if isinstance(v,str)and len(v)<=128:return v
 if isinstance(v,list)and all(type(x)in(int,float,bool)or x is None for x in v):return v
 return omitted(v)
def result_rows(rows):return [{'metric':bounded(r.get('metric')),'value':r.get('value'),'unit':bounded(r.get('unit'))}for r in rows or[]if isinstance(r,dict)]
def source_fragments(record):
 # Protect both direct repeated content and long source text copied into code.
 tokens=[]
 for s in record.get('sources')or[]:
  text=s.get('content')if isinstance(s,dict)else None
  if not isinstance(text,str):continue
  words=re.findall(r'\w+',text.lower())
  for i in range(0,max(0,len(words)-39),10):tokens.append(' '.join(words[i:i+40]))
 return tokens

def public_code(code,fragments):
 if not isinstance(code,str):return None,False
 text=' '.join(re.findall(r'\w+',code.replace('\\n','\n').lower()))
 if any(fragment in text for fragment in fragments):return {'omitted_source_bulk_in_code':True,'original_code_sha256':sha(code.encode())},True
 return code,False

def public_answer(answer):
 if not isinstance(answer,dict):return None
 out={k:copy.deepcopy(answer[k])for k in ['method','evidence_ids','simulation']if k in answer}
 out['results']=result_rows(answer.get('results'))
 out['citations']=[{'title':bounded(c.get('title'),500),'url':bounded(c.get('url'),3000),'supports':omitted(c.get('supports'))}for c in answer.get('citations')or[]if isinstance(c,dict)]
 for key in ['summary','assumptions','limitations']:
  if key in answer:out[key]=omitted(answer[key])
 out['artifact_claims']=[{k:c[k]for k in ['artifact_id','role','data_artifact_ids']if k in c}for c in answer.get('artifact_claims')or[]if isinstance(c,dict)]
 return out

def public_file(file):
 return {k:copy.deepcopy(file[k])for k in ['artifact_id','name','original_name','size','type','mime_type','sha256','execution_id']if k in file}

def scrub_source_bulk(value,fragments):
 if isinstance(value,str):
  text=' '.join(re.findall(r'\w+',value.replace('\\n','\n').lower()))
  return {'omitted_source_bulk':True,'original_value_sha256':sha(value.encode())}if any(fragment in text for fragment in fragments)else value
 if isinstance(value,dict):return {k:scrub_source_bulk(v,fragments)for k,v in value.items()}
 if isinstance(value,list):return [scrub_source_bulk(v,fragments)for v in value]
 return value

def public_record(record):
 if not isinstance(record,dict):return None
 fragments=source_fragments(record)
 out={k:copy.deepcopy(record[k])for k in ['scientificStatus','status','success','workflowMode','verificationPolicy','verification','model','harnessVersion','runId','usage','budget','iterations','elapsed_ms','design','evidence']if k in record}
 out['answer']=public_answer(record.get('answer'));out['results']=result_rows(record.get('results'))
 out['sources']=[{k:copy.deepcopy(s[k])for k in ['id','title','url','content_sha256','retrieved_content_sha256','provider_content_sha256','retrieved_at','source_type','content_scope','truncation_scope','provider','content_truncated','retrieval_roles']if k in s}for s in record.get('sources')or[]if isinstance(s,dict)]
 out['source_requests']=[{k:copy.deepcopy(s[k])for k in ['tool','phase','url','success','source_ids','provider','provider_usage','additional_provider_usage','billing_scope','cache_hit','usage_unknown']if k in s}for s in record.get('source_requests')or[]if isinstance(s,dict)]
 # No submitted tool inputs/results, provider excerpt, model content or raw
 # message transcript is retained in public event metadata.
 out['trace_metadata']=[{k:copy.deepcopy(t[k])for k in ['timestamp','type','role','phase','round','call','model','response_id','stop_reason','elapsed_ms','usage','input_sha256','source_ids','candidate_round','precheck_evidence_ids']if k in t}for t in record.get('trace')or[]if isinstance(t,dict)]
 out['executions']=[]
 for e in record.get('executions')or[]:
  if not isinstance(e,dict):continue
  v={k:copy.deepcopy(e[k])for k in ['id','role','phase','worker_phase','candidate_round','success','exitCode','elapsed_ms','code_sha256']if k in e}
  v['code'],v['code_redacted_for_source_bulk']=public_code(e.get('code'),fragments)
  v['computed']={'results':result_rows((e.get('computed')or{}).get('results')),'simulation':copy.deepcopy((e.get('computed')or{}).get('simulation'))}if isinstance(e.get('computed'),dict)else None
  v['output_files']=[public_file(f)for f in e.get('output_files')or[]if isinstance(f,dict)]
  for key in ['purpose','output','stderr']:
   if key in e:v[key]=omitted(e[key])
  out['executions'].append(v)
 out['outputFiles']=[public_file(f)for f in record.get('outputFiles')or[]if isinstance(f,dict)]
 plan=record.get('plan')
 if isinstance(plan,dict):
  out['plan']={k:copy.deepcopy(plan[k])for k in ['ready','request_kind','calculation_type','method','alpha','sidedness','target_power','allocation_ratio','sample_size_unit']if k in plan}
  out['plan']['parameters']=[{'name':bounded(p.get('name')),'value':simple(p.get('value')),'unit':bounded(p.get('unit')),'source':p.get('source')}for p in plan.get('parameters')or[]if isinstance(p,dict)]
  for key in ['estimand','hypothesis','assumptions','missing_information','clarification_questions','scientific_notes']:
   if key in plan:out['plan'][key]=omitted(plan[key])
 review=record.get('review')
 if isinstance(review,dict):
  out['review']={k:copy.deepcopy(review[k])for k in ['verdict','checked_evidence_ids','independent_check_evidence_ids']if k in review}
  out['review']['checks']=[{'name':bounded(c.get('name')),'passed':c.get('passed'),'evidence':omitted(c.get('evidence'))}for c in review.get('checks')or[]if isinstance(c,dict)]
  out['review']['issues']=[{'severity':c.get('severity'),'description':omitted(c.get('description')),'correction':omitted(c.get('correction'))}for c in review.get('issues')or[]if isinstance(c,dict)]
  if 'summary'in review:out['review']['summary']=omitted(review['summary'])
 out['candidates']=[{'round':c.get('round'),'answer':public_answer(c.get('answer')),'evidence_ids':c.get('evidence_ids')}for c in record.get('candidates')or[]if isinstance(c,dict)]
 # Reference audit may contain free prose/source-derived strings. The original
 # complete gate output remains accessible only in restricted original records.
 if 'referenceAudit'in record:out['referenceAudit']=omitted(record['referenceAudit'])
 if 'error'in record:out['error']=omitted(record['error'])
 # verification.rounds[].review holds the same unredacted model review; project
 # it separately instead of leaving it in a copied topology ledger.
 if isinstance(out.get('verification'),dict):
  for round_ in out['verification'].get('rounds')or[]:
   if isinstance(round_,dict)and'review'in round_:round_['review']=omitted(round_['review'])
 return scrub_source_bulk(out,fragments)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--scored',type=pathlib.Path,required=True);ap.add_argument('--out',type=pathlib.Path,required=True);ap.add_argument('--figures-reviewed',action='store_true');a=ap.parse_args()
 if a.out.exists():raise RuntimeError('Refuse overwrite of prior publication derivative')
 original=a.scored.read_bytes();data=json.loads(original);public={k:copy.deepcopy(data[k])for k in ['analysis_version','protocol_sha256','planned_attempts','recorded_accounting_rows','summary']if k in data};public['publication_derivative_version']=VERSION;public['restricted_original_scored_results_sha256']=sha(original);public['redaction_scope']='Source content, raw/tool/model trace bodies, prose and repeated source bulk are omitted. Original raw captures remain restricted. This derivative is not byte-identical rawdata and is not independently re-scoreable without original receipt content.'
 public['records']=[];a.out.mkdir(parents=True);files=[]
 for row in data['records']:
  out={k:copy.deepcopy(row[k])for k in ['task_id','mode','profile','repeat','job_id','dispatched','transport_captured','transport_sha256','protocol_sha256','duration_seconds','capture_error','process_error','exit_code','runtime_changed','operational_status','evaluation']if k in row}
  record=row.get('record');out['record']=public_record(record)
  out['restricted_original_provider_record_sha256']=sha(canonical(record))
  original_row=a.scored.parent/f"{row['job_id']}.json"
  if original_row.exists():out['restricted_original_accounting_file_sha256']=sha(original_row.read_bytes())
  out['exported_artifacts']=[]
  for f in (record or{}).get('outputFiles')or[]:
   if not isinstance(f,dict)or f.get('name')not in ['sensitivity.csv','sensitivity.png','sensitivity.pdf']:continue
   if f['name'].endswith('.csv'):
    if not (row.get('evaluation')or{}).get('artifact_details',{}).get('csv_pass'):continue
   elif not a.figures_reviewed:continue
   b=base64.b64decode(f.get('content_base64',''),validate=True)
   if sha(b)!=f.get('sha256')or len(b)!=f.get('size'):raise RuntimeError('Artifact byte identity mismatch')
   # Model metadata is never allowed to escape the public output directory.
   if not re.fullmatch(r'[A-Za-z0-9_.-]+',row['job_id'])or not re.fullmatch(r'[A-Za-z0-9_.-]+',f.get('artifact_id','')):raise RuntimeError('Unsafe export identity')
   dest=a.out/'artifacts'/row['job_id']/f['artifact_id']/f['name'];dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b)
   meta={'path':str(dest.relative_to(a.out)),'sha256':sha(b),'original_artifact_id':f['artifact_id']};files.append(meta);out['exported_artifacts'].append(meta)
  public['records'].append(out)
 for name in ['protocol.json','public-questions.json']:
  p=a.scored.parent/name
  if p.exists():b=p.read_bytes();(a.out/name).write_bytes(b);files.append({'path':name,'sha256':sha(b),'scope':'Unchanged answer-free prospective protocol/question payload'})
 output=a.out/'public-scored-results.json';output.write_text(json.dumps(public,indent=2,allow_nan=False)+'\n');files.append({'path':output.name,'sha256':sha(output.read_bytes())})
 manifest={'version':VERSION,'restricted_original_scored_results_sha256':sha(original),'figure_export_requires_manual_review':True,'figures_reviewed_flag':a.figures_reviewed,'files':files,'qualification':'SHA links identify original/derivative objects separately. Metadata redaction cannot prove absence of every paraphrase or text embedded in image pixels; review delivered scientific figures before publication.'}
 (a.out/'publication-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print(json.dumps({'public_derivative_sha256':sha(output.read_bytes()),'records':len(public['records']),'files':len(files)},indent=2))
if __name__=='__main__':main()

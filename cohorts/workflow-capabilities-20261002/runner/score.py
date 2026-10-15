#!/usr/bin/env python3
"""Versioned judge-free capability scorer. No provider/model calls.

Automatic figure checks certify received parseable files + correct companion data,
not that the visible plot faithfully draws those data. That requires the frozen
blinded visual rubric; it is reported separately and never inferred from headers.
"""
import base64,binascii,csv,datetime,hashlib,io,json,math,pathlib,re,struct,subprocess,tempfile,urllib.parse,zlib
VERSION='workflow-capabilities-score1'
HEX=re.compile(r'^[0-9a-f]{64}$')
def digest(b):return hashlib.sha256(b).hexdigest()
def finite(x):return type(x)in(int,float) and math.isfinite(x)
def canon(x):return str(x).strip().lower().replace('-','_').replace(' ','_')
UNITS={'participants_per_group':'participants_per_arm','subjects_per_group':'participants_per_arm','participants_per_arm':'participants_per_arm','subjects_total':'participants_total','total_participants':'participants_total','events_total':'events','number_of_events':'events','sd_units':'outcome_sd','standard_deviation_units':'outcome_sd','df':'degrees_of_freedom'}
METHODS={'pooled_two_sample_t':'two_sample_t','two_sample_t_test':'two_sample_t','paired_t_test':'paired_t','one_way_anova_omnibus':'one_way_anova','schoenfeld':'logrank_schoenfeld','cox_schoenfeld':'logrank_schoenfeld','hsieh_lavori':'cox_hsieh_lavori','open_cohort_stepped_wedge_gls':'open_cohort_sw_gls'}
def norm(x,field=''):
 c=canon(x)
 return (UNITS if field=='unit' else METHODS if field=='method' else {'omnibus':'not_applicable','one_tailed':'one_sided','two_tailed':'two_sided'} if field=='alternative' else {}).get(c,c)
def obj(x):return x if isinstance(x,dict) else {}
def array(x):return x if isinstance(x,list) else []
def successful_execution(e,require_computed=True):
 return isinstance(e,dict) and e.get('success')is True and e.get('exitCode')in(0,None) and isinstance(e.get('code'),str) and digest(e['code'].encode())==e.get('code_sha256') and (not require_computed or isinstance(e.get('computed'),dict))
def result_rows(record):
 if isinstance(record.get('results'),list):return record['results']
 return array(obj(record.get('answer')).get('results'))
def check_numerical(record,oracle):
 values=result_rows(record);errors=[];found=[]
 for expected in oracle['results']:
  matches=[r for r in values if isinstance(r,dict) and norm(r.get('metric'))==norm(expected['metric'])]
  if len(matches)!=1:errors.append('missing_or_ambiguous_metric:'+expected['metric']);continue
  r=matches[0];v=r.get('value')
  if not finite(v) or expected['integer'] and (v!=int(v) or v<1):errors.append('invalid_numeric:'+expected['metric']);continue
  if abs(v-expected['value'])>expected['absolute_tolerance']+1e-12:errors.append('numeric_mismatch:'+expected['metric'])
  if norm(r.get('unit'),'unit')!=norm(expected['unit'],'unit'):errors.append('unit_mismatch:'+expected['metric'])
  if 'power'in expected['metric'] and not 0<=v<=1:errors.append('invalid_probability:'+expected['metric'])
  found.append(r)
 return not errors,errors,found

def check_design(record,oracle):
 d=obj(record.get('design'));errors=[]
 for k,want in oracle['design'].items():
  if want is None:continue
  got=d.get(k)
  ok=finite(got) and abs(got-want)<=1e-12 if type(want)in(int,float) else norm(got,'unit' if k=='sample_size_unit' else k)==norm(want,'unit' if k=='sample_size_unit' else k)
  if not ok:errors.append('design_mismatch:'+k)
 return not errors,errors

def check_execution(record,rows):
 es=[e for e in array(record.get('executions')) if successful_execution(e,False) and e.get('role')=='coder']
 declared=array(obj(record.get('answer')).get('evidence_ids'));accepted=[e for e in es if e.get('id')in declared]
 round_=obj(record.get('verification')).get('current_candidate_round')
 errors=[]
 if type(round_)is not int or any(e.get('candidate_round')!=round_ for e in accepted) or len(set(declared))!=len(declared) or set(declared)!={e.get('id')for e in accepted}:errors.append('coder_evidence_not_all_current_valid_unique')
 accepted=[e for e in accepted if e.get('candidate_round')==round_]
 if not accepted:errors.append('missing_current_answer_coder_evidence')
 for row in rows:
  if not any(any(isinstance(v,dict) and all(v.get(k)==row.get(k) for k in ['metric','value','unit']) for v in array(obj(e.get('computed')).get('results'))) for e in accepted):errors.append('metric_not_exactly_linked_to_executed_result:'+str(row.get('metric')))
 # Every mode is requested to execute required verification. Current-round
 # review IDs must be actual successful reviewer/self-reviewer R evidence.
 review=obj(record.get('review'));ids=array(review.get('independent_check_evidence_ids'))
 verification=[e for e in array(record.get('executions')) if successful_execution(e) and e.get('role')in ['reviewer','self_reviewer'] and e.get('id')in ids]
 if record.get('verificationPolicy')!='required' or review.get('verdict')!='pass' or not verification:errors.append('missing_required_actual_verification')
 if any(e.get('candidate_round')!=round_ for e in verification) or len(set(ids))!=len(ids) or set(ids)!={e.get('id')for e in verification}:errors.append('verification_not_all_current_valid_unique')
 checked=array(review.get('checked_evidence_ids'))
 # Inspection may cover other current-round coder attempts, including failed
 # code. It cannot promote those attempts to numerical/artifact producers.
 if not set(declared)<=set(checked):errors.append('review_does_not_cover_current_answer_evidence')
 inspection_valid=len(set(checked))==len(checked)
 for id in checked:
  matches=[e for e in array(record.get('executions'))if isinstance(e,dict) and e.get('id')==id]
  if len(matches)!=1 or matches[0].get('role')!='coder' or matches[0].get('candidate_round')!=round_:inspection_valid=False
 if not inspection_valid:errors.append('checked_coder_inspection_not_all_current_valid_unique')
 return not errors,errors,accepted

def safe_source_url(url):
 try:
  u=urllib.parse.urlsplit(url)
  return u.scheme=='https' and not u.username and not u.password and u.port in(None,443)
 except ValueError:return False

def equivalent_source(url,want):
 # Predeclared official R mirror/version aliases. Other references require the
 # named document, so a general domain home page cannot pass acquisition.
 if not safe_source_url(url):return False
 u=urllib.parse.urlsplit(url);w=urllib.parse.urlsplit(want)
 if url.rstrip('/')==want.rstrip('/'):return True
 if w.hostname=='stat.ethz.ch' and '/library/stats/html/'in w.path:
  return (u.hostname in ['stat.ethz.ch','cran.r-project.org','www.r-project.org'] and u.path.endswith('/library/stats/html/'+w.path.split('/')[-1]))
 return u.hostname==w.hostname and u.path==w.path

def check_sources(record,oracle):
 errors=[];cites=array(obj(record.get('answer')).get('citations'));valid=[];annotations=[]
 trace=array(record.get('trace'));sources=array(record.get('sources'))
 searches=[(i,t)for i,t in enumerate(trace)if isinstance(t,dict) and t.get('type')=='search']
 reads=[(i,t)for i,t in enumerate(trace)if isinstance(t,dict) and t.get('type')=='source_read']
 for s in array(record.get('sources')):
  if not isinstance(s,dict) or not equivalent_source(s.get('url',''),oracle['source_url']):continue
  content=s.get('content');stamp=s.get('retrieved_at')
  if not isinstance(content,str) or not content.strip() or not isinstance(stamp,str) or not HEX.fullmatch(str(s.get('content_sha256',''))) or digest(content.encode())!=s['content_sha256']:continue
  try:datetime.datetime.fromisoformat(stamp.replace('Z','+00:00'))
  except ValueError:continue
  search_positions=[i for i,t in searches if any(isinstance(other,dict) and other.get('id')in array(t.get('source_ids')) and equivalent_source(other.get('url',''),oracle['source_url']) and isinstance(other.get('content'),str) and other['content'].strip() and digest(other['content'].encode())==other.get('content_sha256') for other in sources)]
  read_positions=[i for i,t in reads if s.get('id')in array(t.get('source_ids'))]
  if not search_positions or not read_positions or not any(i<j for i in search_positions for j in read_positions):continue
  deduplicated=False
  if s.get('content_scope')!='provider_extracted_document_text':
   # Identical URL/body may reuse an earlier search receipt whose original
   # excerpt scope is correctly retained by the frozen runtime. Accept only
   # the real extraction event's exact URL/source/hash/bytes, not any read label.
   extraction_positions=[]
   for i,t in reads:
    value=obj(t.get('results'))
    if value.get('provider')!='tavily_extract' or t.get('url')!=s.get('url') or value.get('url')!=s.get('url') or s.get('id')not in array(t.get('source_ids')):continue
    if any(isinstance(v,dict) and v.get('id')==s.get('id') and v.get('url')==s.get('url') and v.get('content_sha256')==s['content_sha256'] and isinstance(v.get('content'),str) and digest(v['content'].encode())==s['content_sha256'] for v in array(value.get('results'))):extraction_positions.append(i)
   if s.get('content_scope')!='provider_excerpt' or not any(i<j for i in search_positions for j in extraction_positions):continue
   deduplicated=True
  if not any(isinstance(c,dict) and c.get('url')==s.get('url') and str(c.get('supports','')).strip() for c in cites):continue
  valid.append(s.get('id'))
  annotations.append({'source_id':s.get('id'),'stored_content_scope':s.get('content_scope'),'identical_content_deduplicated_document_read':deduplicated,'qualification':'Actual named-document search/read receipt; provider extraction scope retained, no complete PDF or source-support certification.'})
 if not valid:errors.append('missing_search_and_hashed_document_read_and_linked_citation')
 return bool(valid),errors,valid,annotations

def decode_artifact(file):
 if not isinstance(file,dict):raise ValueError('invalid_artifact_schema')
 for key in ['artifact_id','name','size','type','mime_type','sha256','execution_id','content_base64']:
  if key not in file:raise ValueError('missing_artifact_field:'+key)
 if not isinstance(file['name'],str) or pathlib.PurePath(file['name']).name!=file['name'] or '..'in pathlib.PurePath(file['name']).parts:raise ValueError('unsafe_artifact_name')
 if type(file['size'])is not int or not 0<file['size']<=10*1024*1024:raise ValueError('invalid_artifact_size')
 if not HEX.fullmatch(str(file['sha256'])):raise ValueError('invalid_artifact_digest')
 try:b=base64.b64decode(file['content_base64'],validate=True)
 except (binascii.Error,TypeError):raise ValueError('invalid_artifact_base64')
 if len(b)!=file['size'] or digest(b)!=file['sha256']:raise ValueError('artifact_bytes_size_or_digest_mismatch')
 return b

def check_csv(b,expected):
 try:
  text=b.decode('utf-8-sig');reader=csv.DictReader(io.StringIO(text));fields=reader.fieldnames;rows=list(reader)
 except (ValueError,UnicodeError,csv.Error):return False,['invalid_csv'],None
 errors=[]
 if fields!=expected['columns']:errors.append('csv_column_schema_mismatch')
 if len(rows)!=len(expected['rows']):errors.append('csv_row_count_mismatch')
 wanted={tuple(float(r[k]) for k in expected['key_columns']):r for r in expected['rows']};seen=set();canonical=[]
 for row in rows:
  try:
   if set(row)!=set(expected['columns']) or any(row[c]is None for c in expected['columns']):raise ValueError()
   numeric={c:float(row[c]) for c in expected['columns']}
   if not all(math.isfinite(v) for v in numeric.values()):raise ValueError()
   key=tuple(numeric[c] for c in expected['key_columns'])
   if key in seen:errors.append('csv_duplicate_grid_row');continue
   seen.add(key)
   # Grid inputs have declared finite decimal values; allow machine roundoff.
   match=[k for k in wanted if all(abs(a-b)<=1e-12 for a,b in zip(k,key))]
   if len(match)!=1:errors.append('csv_unexpected_grid_row');continue
   expected_row=wanted[match[0]]
   for c,v in numeric.items():
    if c in expected['integer_columns'] and v!=int(v):errors.append('csv_noninteger:'+c)
    if abs(v-expected_row[c])>expected['absolute_tolerances'][c]+1e-12:errors.append('csv_numeric_mismatch:'+c)
   canonical.append(numeric)
  except (ValueError,TypeError,KeyError,OverflowError):errors.append('csv_invalid_numeric_row')
 if len(seen)!=len(wanted):errors.append('csv_missing_grid_rows')
 canonical.sort(key=lambda r:tuple(r[k] for k in expected['key_columns']))
 return not errors,sorted(set(errors)),digest(json.dumps(canonical,sort_keys=True,separators=(',',':'),allow_nan=False).encode())

def check_png(b):
 if not b.startswith(b'\x89PNG\r\n\x1a\n'):return False,'invalid_png_signature'
 pos=8;chunks=[];compressed=[];dimensions=None;ended=False
 try:
  while pos<len(b):
   length=struct.unpack('>I',b[pos:pos+4])[0];kind=b[pos+4:pos+8];data=b[pos+8:pos+8+length];crc=struct.unpack('>I',b[pos+8+length:pos+12+length])[0]
   if len(data)!=length or length>10*1024*1024 or zlib.crc32(kind+data)&0xffffffff!=crc:raise ValueError()
   chunks.append(kind);pos+=12+length
   if kind==b'IHDR':
    if dimensions is not None or length!=13:raise ValueError()
    width,height,depth,color,compression,filter_,interlace=struct.unpack('>IIBBBBB',data)
    dimensions=(width,height,depth,color,compression,filter_,interlace)
   if kind==b'IDAT':compressed.append(data)
   if kind==b'IEND':ended=True;break
  if not ended or pos!=len(b) or not dimensions or not compressed or chunks[0]!=b'IHDR':raise ValueError()
  w,h,depth,color,compression,filter_,interlace=dimensions
  if w<640 or h<400 or w>4096 or h>4096 or color not in [0,2,3,4,6] or compression!=0 or filter_!=0 or interlace not in [0,1]:raise ValueError()
  if depth not in {0:[1,2,4,8,16],2:[8,16],3:[1,2,4,8],4:[8,16],6:[8,16]}[color] or color==3 and b'PLTE'not in chunks:raise ValueError()
  obj_=zlib.decompressobj();decoded=obj_.decompress(b''.join(compressed),64*1024*1024+1)
  if not obj_.eof or obj_.unused_data or len(decoded)>64*1024*1024:raise ValueError()
  # Noninterlaced row lengths/filters are validated; Adam7 structurally decoded
  # PNG remains valid but no semantic pixel claim is made for either case.
  if interlace==0:
   channels={0:1,2:3,3:1,4:2,6:4}[color];rowlen=(w*depth*channels+7)//8+1
   if len(decoded)!=rowlen*h or any(decoded[i*rowlen]>4 for i in range(h)):raise ValueError()
  return True,dict(format='png',width=w,height=h,decoded_bytes=len(decoded),scope='Parseable image delivery only; blinded visual rubric checks scientific plot content.')
 except (ValueError,struct.error,zlib.error,IndexError):return False,'invalid_png_structure_or_dimensions'

def check_pdf(b):
 if not b.startswith(b'%PDF-') or b'%%EOF'not in b[-2048:]:return False,'invalid_pdf_structure'
 with tempfile.TemporaryDirectory(prefix='pa-figure-verify-')as td:
  path=pathlib.Path(td)/'figure.pdf';path.write_bytes(b)
  try:r=subprocess.run(['pdfinfo',str(path)],text=True,capture_output=True,timeout=15)
  except (OSError,subprocess.SubprocessError):return False,'pdf_parser_unavailable_or_failed'
  pages=re.search(r'^Pages:\s+(\d+)',r.stdout,re.M)
  if r.returncode or not pages or int(pages.group(1))<1:return False,'invalid_pdf_parse'
  return True,dict(format='pdf',pages=int(pages.group(1)),scope='Parseable figure delivery only; scientific plot content not automatically certified.')

def check_artifacts(record,oracle,accepted):
 es={e.get('id'):e for e in accepted};actual={};errors=[];delivered=array(record.get('outputFiles'))
 for e in accepted:
  for f in array(e.get('output_files')):
   if isinstance(f,dict) and f.get('execution_id')==e.get('id'):
    key=f.get('artifact_id')
    if key in actual:errors.append('duplicate_artifact_id')
    actual[key]=f
 final=[]
 for f in delivered:
  if not isinstance(f,dict) or f.get('artifact_id')not in actual or f!=actual[f['artifact_id']]:errors.append('delivered_artifact_not_exact_execution_snapshot');continue
  try:b=decode_artifact(f)
  except ValueError as e:errors.append(str(e));continue
  final.append((f,b))
 csvs=[(f,b)for f,b in final if f['name']==oracle['csv']['name'] and f['type']=='csv' and f['mime_type']=='text/csv']
 figures=[(f,b)for f,b in final if f['name']in ['sensitivity.png','sensitivity.pdf'] and f['type']in ['png','pdf'] and f['mime_type']==('image/png'if f['type']=='png'else'application/pdf')]
 csv_pass=False;dataset_sha=None
 if len(csvs)!=1:errors.append('missing_or_ambiguous_sensitivity_csv')
 else:
  csv_pass,csv_err,dataset_sha=check_csv(csvs[0][1],oracle['csv']);errors.extend(csv_err)
 figure_pass=False;figure_info=[]
 if not figures:errors.append('missing_sensitivity_figure')
 else:
  for f,b in figures:
   ok,info=(check_png if f['type']=='png' else check_pdf)(b);figure_info.append({'artifact_id':f['artifact_id'],'passed':ok,'inspection':info});figure_pass|=ok
  if not figure_pass:errors.append('unparseable_sensitivity_figure')
 return not errors and csv_pass and figure_pass,errors,dict(csv_pass=csv_pass,figure_delivery_pass=figure_pass,canonical_numeric_dataset_sha256=dataset_sha,figure_info=figure_info,visual_scientific_content='pending_separate_blinded_rubric')

def check_clarification(record,oracle):
 errors=[];plan=obj(record.get('plan'));status=record.get('scientificStatus',record.get('status'))
 text=' '.join(str(s)for k in ['missing_information','clarification_questions']for s in array(plan.get(k)))
 if status!='needs_clarification' or plan.get('ready')is not False:errors.append('missing_explicit_needs_clarification')
 if not array(plan.get('clarification_questions')):errors.append('missing_focused_questions')
 for i,patterns in enumerate(oracle['topics']):
  if not any(re.search(p,text,re.I) for p in patterns):errors.append('missing_material_input_topic:'+str(i+1))
 for r in result_rows(record):
  if not isinstance(r,dict):errors.append('invalid_result_schema');continue
  unit=norm(r.get('unit'),'unit');metric=norm(r.get('metric'))
  conditional_event=oracle['conditional_events_allowed'] and unit=='events' and 'event'in metric
  count_label=bool(re.search(r'(?:sample.?size|(?:^|_)n(?:$|_)|participants?|subjects?|patients?|clusters?|recruit)',metric,re.I))
  count_unit=unit in [norm(u,'unit')for u in oracle['forbidden_count_units']]or bool(re.search(r'participants?|subjects?|patients?|clusters?',unit,re.I))
  if not conditional_event and (count_label or count_unit):errors.append('unwarranted_definitive_count')
 # Event calculations may be conditional and correctly labelled; unlabelled
 # numerical participant recommendations do not satisfy this task instruction.
 return not errors,errors

def score(record,oracle):
 try:
  if not isinstance(record,dict):raise ValueError('provider_record_is_not_object')
  errors=[]
  if record.get('evaluation_version_changed'):errors.append('frozen_dependency_changed')
  if oracle['kind']=='clarification':
   ok,why=check_clarification(record,oracle);errors.extend(why)
   return dict(scoring_version=VERSION,passed=ok and not errors,outcome_kind='clarification',clarification_pass=ok,numeric_pass=None,source_pass=None,artifact_pass=None,reasons=errors)
  numerical,why,rows=check_numerical(record,oracle);errors.extend(why)
  design,why=check_design(record,oracle);errors.extend(why)
  evidence,why,accepted=check_execution(record,rows);errors.extend(why)
  sources,why,sourceids,annotations=check_sources(record,oracle);errors.extend(why)
  artifacts,why,details=check_artifacts(record,oracle,accepted);errors.extend(why)
  completed=record.get('success')is True and record.get('scientificStatus',record.get('status'))=='completed'
  if not completed:errors.append('not_completed')
  return dict(scoring_version=VERSION,passed=not errors,outcome_kind='calculation',completed=completed,numeric_pass=numerical,completed_numeric_pass=completed and numerical,design_pass=design,evidence_pass=evidence,source_pass=sources,source_ids=sourceids,source_receipt_annotations=annotations,artifact_pass=artifacts,artifact_details=details,reasons=sorted(set(errors)))
 except Exception as e:
  return dict(scoring_version=VERSION,passed=False,outcome_kind=oracle.get('kind','unknown'),numeric_pass=False,evidence_pass=False,source_pass=False,artifact_pass=False,reasons=['invalid_provider_schema'],scorer_error_type=type(e).__name__)

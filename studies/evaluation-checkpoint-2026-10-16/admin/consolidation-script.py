from pathlib import Path
import io,json,gzip,hashlib,tarfile,subprocess,tempfile,shutil,datetime,collections,csv,statistics,os
R=Path('/users/jxia3/atlas/incr'); O=R.parent/'observe'; D=R/'studies/evaluation-checkpoint-2026-10-16'
D.mkdir(exist_ok=True); (D/'admin').mkdir(exist_ok=True)
STOP={'time':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reason':'User requested cancellation and consolidation; no further evaluation is queued.','historical_state':'cancelled-partial','supplemental_state':'not-started','service_active':False,'timer_disabled':True}
(D/'admin/cancellation.json').write_text(json.dumps(STOP,indent=2)+'\n')
SUFFIX={'.json','.jsonl','.csv','.tsv','.log','.md','.txt','.time','.patch','.out','.err','.stdout','.stderr'}
EXCLUDE={'node_modules','__pycache__','.git','target','inputs','min_inputs','outputs','fixture','cache','unused-cache','fork-cache','pread-cache','mmap-cache','read-cache','dup-cache'}
seen={}; records=[]; excluded=collections.Counter(); archives=[]
T=tarfile.open(D/'detailed-statistics.tar.gz','w:gz',compresslevel=6)
def keep(name,size):
 p=Path(name)
 if any(x in EXCLUDE for x in p.parts):return False
 return (p.suffix in SUFFIX or str(p).endswith(('.json.gz','.jsonl.gz','.csv.gz'))) and (p.suffix not in {'.txt','.out','.err','.stdout','.stderr'} or size<=2*1024**2)
def add(name,data):
 h=hashlib.sha256(data).hexdigest()
 if h not in seen:
  info=tarfile.TarInfo('sha256/'+h);info.size=len(data);info.mtime=0;T.addfile(info,io.BytesIO(data));seen[h]=len(data)
 records.append({'source':name,'sha256':h,'bytes':len(data)})
def read(p):
 try:return p.read_bytes()
 except PermissionError:return subprocess.check_output(['sudo','-n','cat','--',str(p)])
def walk(root,label):
 if not root.exists():return
 for directory,dirs,files in os.walk(root,followlinks=False):
  dirs[:]=sorted(d for d in dirs if d not in EXCLUDE and not (Path(directory)/d).is_symlink())
  for n in sorted(files):
   p=Path(directory)/n;rel=label+'/'+str(p.relative_to(root))
   if p.is_symlink():continue
   if n.endswith(('.tar.gz','.tgz')):archives.append((p,rel));continue
   if n.endswith('.tar.gz.part-000'):archives.append((p,rel));continue
   if keep(p.relative_to(root),p.stat().st_size):add(rel,read(p))
   else:excluded[p.suffix or '(no suffix)']+=1
roots=[]
for p in sorted((R/'studies').iterdir()):
 if p==D or not p.is_dir():continue
 for sub in ['results','evidence','checkpoint-evidence']:
  if (p/sub).exists():roots.append((p/sub,'incr/studies/'+p.name+'/'+sub))
 # Top-level summaries, methodology and historical interpretation.
 for f in p.iterdir():
  if f.is_file() and not f.is_symlink() and keep(f.name,f.stat().st_size):add('incr/studies/'+p.name+'/'+f.name,read(f))
roots.append((R/'qualification/results','incr/qualification/results'))
for repo,label in [(R,'incr'),(O,'observe')]:
 for p in (repo/'evaluation').iterdir():
  if p.is_dir() and ('results' in p.name or p.name=='analysis'):roots.append((p,label+'/evaluation/'+p.name))
 for n in ['QUALIFICATION_LOG.md','CONTEXT.md','DESIGN.md']:
  p=repo/n
  if p.exists():add(label+'/'+n,read(p))
for root,label in roots:walk(root,label)
# Archived copies may contain measurement records no longer present loose.
for p,label in archives:
 try:
  if p.name.endswith('.part-000'):
   with tempfile.TemporaryFile() as stream:
    for part in sorted(p.parent.glob(p.name[:-3]+'*')):
     with part.open('rb') as f:shutil.copyfileobj(f,stream)
    stream.seek(0)
    with tarfile.open(fileobj=stream,mode='r:gz') as a:
     for m in a:
      if m.isfile() and keep(m.name,m.size):add(label+'::'+m.name,a.extractfile(m).read())
  else:
   with tarfile.open(p,'r:gz') as a:
    for m in a:
     if m.isfile() and keep(m.name,m.size):add(label+'::'+m.name,a.extractfile(m).read())
 except (tarfile.TarError,EOFError) as e:raise RuntimeError(str(p)) from e
T.close()
with gzip.open(D/'files.jsonl.gz','wt') as f:
 for row in records:f.write(json.dumps(row,separators=(',',':'))+'\n')
# Verify every content-addressed member and the entire original-path index.
restored={}
with tarfile.open(D/'detailed-statistics.tar.gz','r:gz') as t:
 for m in t:
  h=hashlib.sha256(t.extractfile(m).read()).hexdigest();assert m.name=='sha256/'+h and h not in restored;restored[h]=m.size
assert restored==seen and all(restored[x['sha256']]==x['bytes'] for x in records)
index={'created':STOP['time'],'scope':'All available measurement/statistics, correctness summaries, resources, logs, provenance and historical reports, including archived-only records; no cross-cohort pooling. No downloaded inputs, runtime caches, executable artifacts, output datasets or binary profiles.','source_roots':[{'path':str(a),'label':b} for a,b in roots],'original_path_records':len(records),'unique_content_files':len(seen),'archive_sources_read':len(archives),'excluded_file_counts':dict(excluded),'payload_layout':'files.jsonl.gz maps original source paths (archive::member for archived records) to detailed-statistics.tar.gz members sha256/<hash>. Duplicate bytes are stored once.','files':{n:{'bytes':(D/n).stat().st_size,'sha256':hashlib.sha256((D/n).read_bytes()).hexdigest()} for n in ['detailed-statistics.tar.gz','files.jsonl.gz']},'verified_roundtrip':True,'repositories':{}}
for repo,label in [(R,'incr'),(O,'observe')]:
 index['repositories'][label]={'head':subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()}
(D/'catalog.json').write_text(json.dumps(index,indent=2)+'\n')
# Flat per-invocation timing/resource records for convenient analysis.
rows=[];families=[]
for cohort,path in [('new-full',R/'studies/observe-reproduction/results/historical-01'),('final-targeted',R/'studies/paper-size-benchmarks/results/memory-queue-targeted-paper-01'),('old-full',R/'studies/paper-size-benchmarks/results/replay-final-paper-01')]:
 vs=[json.loads(p.read_text()) for p in (path/'sequences').glob('*/[0-9][0-9].*.json')]
 for v in vs:
  resource=v.get('resources',{}) or {}
  if not isinstance(resource,dict):resource={}
  row={k:v.get(k) for k in ['benchmark','mode','repetition','script','index','elapsed_sec','valid','returncode','peak_cache_bytes','peak_work_bytes','cache_bytes','cache_entries_before','cache_entries_after','stdout_bytes','stderr_bytes']};row['cohort']=cohort;row['resources_json']=json.dumps(resource,sort_keys=True);row['problems_json']=json.dumps(v.get('problems',[]));rows.append(row)
 manifest=json.loads((R/'studies/paper-size-benchmarks/manifest.json').read_text())
 for b in manifest['benchmarks']:
  n=b['name'];k=len(b['scripts']);entry={'cohort':cohort,'benchmark':n,'expected_versions':k,'modes':{}}
  for m in ['bash','original','observe']:
   samples=[]
   for rep in range(3):
    seq=[v for v in vs if (v['benchmark'],v['mode'],v['repetition'])==(n,m,rep)]
    if len(seq)==k and all(v['valid'] for v in seq):samples.append({'repetition':rep,'seconds':sum(v['elapsed_sec'] for v in seq),'edited_seconds':sum(v['elapsed_sec'] for v in seq if v['index']>0)})
   entry['modes'][m]={'complete_repetitions':len(samples),'samples':samples,'median_seconds':statistics.median(x['seconds'] for x in samples) if len(samples)==3 else None,'median_edited_seconds':statistics.median(x['edited_seconds'] for x in samples) if len(samples)==3 else None}
  if any(v['complete_repetitions'] for v in entry['modes'].values()):families.append(entry)
with (D/'invocations.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(sorted(rows,key=lambda x:(x['cohort'],x['benchmark'],x['repetition'],x['mode'],x['index'])))
(D/'family-statistics.json').write_text(json.dumps(families,indent=2)+'\n')
print(json.dumps({'source_records':len(records),'unique_files':len(seen),'invocations':len(rows),'archive_bytes':(D/'detailed-statistics.tar.gz').stat().st_size,'new_full_count':sum(v['cohort']=='new-full' for v in rows),'new_full_valid':sum(v['cohort']=='new-full' and v['valid'] for v in rows)},indent=2))

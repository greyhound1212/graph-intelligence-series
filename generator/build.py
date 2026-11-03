import csv, json, random, hashlib, pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'data'; OUT.mkdir(exist_ok=True)
SEED=202701
rng=random.Random(SEED)
SPEC=[('Person','PER',40),('Organization','ORG',20),('Location','LOC',25),('Vehicle','VEH',15),('Event','EVT',20),('Shipment','SHP',15),('Transaction','TX',10),('Account','ACC',5)]
NODES=[]
for label,prefix,count in SPEC:
 for i in range(1,count+1):
  id=f'{prefix}-{i:03d}'
  name=({'Person':'Person','Organization':'Meridian Enterprise','Location':'Port Meridian Site','Vehicle':'Vehicle','Event':'Port Activity','Shipment':'Shipment','Transaction':'Transfer','Account':'Account'}[label])+f' {i:03d}'
  NODES.append(dict(id=id,label=label,name=name,synthetic='true'))
# Override selected illustrative entities
names={'PER-001':'Mara Voss','PER-002':'Elias Renner','PER-003':'Sofia Kade','PER-004':'Jonas Vale','PER-005':'Nina Solberg','ORG-001':'Meridian Freight Ltd','ORG-002':'North Quay Storage','ORG-003':'Bluewater Trade Services','ORG-004':'Harborline Transport','LOC-001':'East Dock Warehouse','LOC-002':'North Terminal','LOC-003':'Meridian Business Center','LOC-004':'West Logistics Yard'}
for n in NODES:
 n['name']=names.get(n['id'],n['name'])
BY={l:[n['id'] for n in NODES if n['label']==l] for l,_,_ in SPEC}
RULES=[('WORKS_FOR','Person','Organization'),('MANAGES','Person','Organization'),('REGISTERED_AT','Organization','Location'),('OPERATES','Organization','Vehicle'),('PARTICIPATED_IN','Person','Event'),('OCCURRED_AT','Event','Location'),('INVOLVES_VEHICLE','Event','Vehicle'),('SENT','Organization','Shipment'),('RECEIVED','Organization','Shipment'),('ORIGINATED_AT','Shipment','Location'),('DESTINED_FOR','Shipment','Location'),('HOLDS_ACCOUNT','Organization','Account'),('DEBITED_FROM','Transaction','Account'),('CREDITED_TO','Transaction','Account')]
mandatory=[('PER-001','MANAGES','ORG-001'),('PER-002','WORKS_FOR','ORG-001'),('PER-003','WORKS_FOR','ORG-002'),('PER-004','WORKS_FOR','ORG-004'),('ORG-001','REGISTERED_AT','LOC-003'),('ORG-002','REGISTERED_AT','LOC-001'),('ORG-004','REGISTERED_AT','LOC-004'),('ORG-003','REGISTERED_AT','LOC-003'),('ORG-001','REGISTERED_AT','LOC-003')]
rels=[]; seen=set()
def add(s,t,o):
 k=(s,t,o)
 if k in seen:return False
 seen.add(k);rels.append(dict(id=f'REL-{len(rels)+1:04d}',source_id=s,type=t,target_id=o,valid_from='2027-01-01',valid_to='',synthetic='true'));return True
for r in mandatory:add(*r)
while len(rels)<350:
 t,a,b=rng.choice(RULES)
 add(rng.choice(BY[a]),t,rng.choice(BY[b]))
SOURCES=[dict(id=f'SRC-{i:04d}',type=['SyntheticRegistry','SyntheticManifest','SyntheticObservation','SyntheticLedger'][i%4],title=f'Harborlight synthetic source {i:03d}',origin_source_id='',collected_at='2027-12-31T12:00:00',reliability=['A','B','C'][i%3],information_credibility=['1','2','3'][i%3],access_class='SYNTHETIC') for i in range(1,51)]
ASSERTIONS=[]; EVIDENCE=[]
for i,r in enumerate(rels):
 aid=f'AST-{i+1:04d}'
 ASSERTIONS.append(dict(id=aid,subject_id=r['source_id'],predicate=r['type'],object_id=r['target_id'],assessment='Supported' if i%7 else 'Unverified',valid_from='2027-01-01',valid_to=''))
 EVIDENCE.append(dict(assertion_id=aid,source_id=SOURCES[i%len(SOURCES)]['id']))
def write(filename,rows,fields):
 with (OUT/filename).open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
write('nodes.csv',NODES,['id','label','name','synthetic'])
write('relationships.csv',rels,['id','source_id','type','target_id','valid_from','valid_to','synthetic'])
write('sources.csv',SOURCES,list(SOURCES[0]))
write('assertions.csv',ASSERTIONS,list(ASSERTIONS[0]))
write('evidence.csv',EVIDENCE,['assertion_id','source_id'])
manifest={'dataset':'HBL-01','version':'1.0.0','seed':SEED,'domain_nodes':len(NODES),'domain_relationships':len(rels),'sources':len(SOURCES),'assertions':len(ASSERTIONS),'sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(OUT.glob('*.csv'))}}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
print('Generated:',manifest['domain_nodes'],'nodes,',manifest['domain_relationships'],'relationships')

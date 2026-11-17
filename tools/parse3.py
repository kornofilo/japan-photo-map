import json,re,sys,collections
txt=json.load(open(sys.argv[1]))[0]['text']
body=txt.split('BEGIN ',1)[1]; n=int(body.split('\n',1)[0]); lines=body.split('\n')[1:]; lines=lines[:lines.index('END')]
print('declared',n,'got',len(lines))
open(sys.argv[2],'w').write('\n'.join(lines))
# per-day DSC ranges from the date column
byday=collections.defaultdict(list)
for l in lines:
    name,i,m=l.split('|')
    mm=re.match(r'DSC_(\d{4})\.(\w+)$',name)
    if mm:
        d=re.match(r'(\d+)/(\d+)/(\d+)',m)
        byday[(int(d.group(3)),int(d.group(2)),int(d.group(1))) if d else m].append(int(mm.group(1)))
for k in sorted(byday,key=str):
    v=sorted(byday[k]); print(k,len(v),v[0],v[-1])

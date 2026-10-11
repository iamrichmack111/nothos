#!/usr/bin/env python3
"""NOTHOS V5: Ollama embeddings, hybrid retrieval, evidence-aware answers."""
import argparse, hashlib, json, math, os, re, sqlite3, sys, time, unicodedata, html, http.server, urllib.parse, collections, shutil, subprocess, mimetypes
from pathlib import Path
import requests
import numpy as np
ROOT=Path(__file__).resolve().parent
DB=Path(os.environ.get('NOTHOS_DB',str(ROOT/'nothos.sqlite3')))
URL=os.environ.get('OLLAMA_URL',os.environ.get('OLLAMA_HOST','http://localhost:11434')).rstrip('/')
EMBED=os.environ.get('NOTHOS_EMBED_MODEL','embeddinggemma-2')
CHAT=os.environ.get('NOTHOS_CHAT_MODEL','gemma3:4b')
DEFAULT_TOP_K=int(os.environ.get('NOTHOS_TOP_K','12'))
CHUNK=int(os.environ.get('NOTHOS_CHUNK_WORDS','220'))
OVERLAP=int(os.environ.get('NOTHOS_OVERLAP_WORDS','45'))
BATCH=int(os.environ.get('NOTHOS_BATCH_SIZE','8'))
TRANSLATE_MODEL=os.environ.get('NOTHOS_TRANSLATE_MODEL','translategemma:4b')
SHOW_PROGRESS=os.environ.get('NOTHOS_PROGRESS','auto')

def clean(s):
    """Decode literal escaped newlines and normalize whitespace for terminal output."""
    if not isinstance(s,str): s=json.dumps(s,ensure_ascii=False) if s is not None else ''
    s=s.replace('\\r\\n','\n').replace('\\n','\n').replace('\\t',' ')
    return re.sub(r'[ \t]+',' ',s).strip()

def flat(s): return re.sub(r'\s+',' ',clean(s)).strip()

def db():
    c=sqlite3.connect(DB)
    c.row_factory=sqlite3.Row
    c.execute('PRAGMA journal_mode=WAL')
    c.executescript('''CREATE TABLE IF NOT EXISTS docs(
        id TEXT PRIMARY KEY, kind TEXT NOT NULL, entity_id TEXT, title TEXT, body TEXT,
        source TEXT, verification TEXT, content_hash TEXT, model TEXT, vector BLOB,
        family TEXT, meta TEXT);
        CREATE INDEX IF NOT EXISTS idx_docs_model ON docs(model);
        CREATE INDEX IF NOT EXISTS idx_docs_family ON docs(family);
        CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT NOT NULL);
        CREATE VIRTUAL TABLE IF NOT EXISTS docs_fts USING fts5(title,body,source,content='docs',content_rowid='rowid',tokenize='unicode61 remove_diacritics 2');
        CREATE TRIGGER IF NOT EXISTS docs_ai AFTER INSERT ON docs BEGIN
          INSERT INTO docs_fts(rowid,title,body,source) VALUES(new.rowid,new.title,new.body,new.source);
        END;
        CREATE TRIGGER IF NOT EXISTS docs_ad AFTER DELETE ON docs BEGIN
          INSERT INTO docs_fts(docs_fts,rowid,title,body,source) VALUES('delete',old.rowid,old.title,old.body,old.source);
        END;
        CREATE TRIGGER IF NOT EXISTS docs_au AFTER UPDATE ON docs BEGIN
          INSERT INTO docs_fts(docs_fts,rowid,title,body,source) VALUES('delete',old.rowid,old.title,old.body,old.source);
          INSERT INTO docs_fts(rowid,title,body,source) VALUES(new.rowid,new.title,new.body,new.source);
        END;''')
    return c

def chunks(s):
    if not 0<=OVERLAP<CHUNK: raise ValueError('Overlap must be smaller than chunk size')
    # Preserve paragraph/line boundaries as much as possible, no broken Unicode.
    words=clean(s).split()
    for i in range(0,len(words),CHUNK-OVERLAP):
        if not words[i:i+CHUNK]:break
        yield ' '.join(words[i:i+CHUNK])
        if i+CHUNK>=len(words):break

def as_text(v):
    if isinstance(v,list):return '; '.join(as_text(x) for x in v)
    if isinstance(v,dict):return '; '.join(f'{k}: {as_text(x)}' for k,x in v.items())
    return clean(v)

def records():
    graph=json.loads((ROOT/'data/greek_myth_knowledge_graph_v3.json').read_text(encoding='utf-8'))
    entities=graph.get('entities',[])
    if isinstance(entities,dict):entities=list(entities.values())
    for e in entities:
        eid=str(e.get('id') or e.get('name'))
        name=e.get('name',eid)
        fields=['name','transliteration','name_interpretation','domain','powers','strengths','weaknesses_or_limits','symbols','associated_entities','primary_references','signature_story','power_in_action','social_status_context','interpretation_status']
        body='\n'.join(f'{k.replace("_"," ")}: {as_text(e[k])}' for k in fields if e.get(k))
        source=as_text(e.get('primary_references',''))
        for n,part in enumerate(chunks(body)):
            yield dict(id=f'entity:{eid}:{n}',kind='entity',entity_id=eid,title=f'{name} | {e.get("type","entity")}',body=part,source=source,verification=e.get('source_verification','legacy_unverified'),family=f'entity:{eid}',meta={'source_type':'secondary_dataset'})
    for i,r in enumerate(graph.get('relationships',[])):
        subject=r.get('subject',r.get('source',r.get('from','')))
        obj=r.get('object',r.get('target',r.get('to','')))
        predicate=r.get('predicate',r.get('relation','related_to'))
        # A broad association is not evidence that a figure uses a particular instrument.
        if {str(subject).lower(),str(obj).lower()}=={'pan','lyre'}: continue
        ref=as_text(r.get('source_reference',''))
        body=f'{subject} — {predicate.replace("_"," ")} — {obj}. '+as_text(r.get('note',''))
        family='rel:'+'|'.join(sorted([str(subject),str(obj)]))+'|'+str(predicate)
        yield dict(id=f'relation:{i}',kind='relation',entity_id=str(subject),title=f'{subject} → {obj}',body=body,source=ref,verification='reference_locator_unverified' if ref else 'dataset_relationship_unverified',family=family,meta={'source_type':'secondary_dataset','raw':r})
    # Curated source-located narrative summaries: NOT verbatim ancient quotations.
    corrections_path=ROOT/'data/curated_evidence.json'
    if corrections_path.exists():
        for item in json.loads(corrections_path.read_text(encoding='utf-8')):
            yield dict(id='curated:'+item['id'],kind='passage',entity_id=item['entity_id'],
                title=item['title'],body=item['summary'],source=item['source'],
                verification='source_locator_provided_text_not_independently_collated',
                family='curated:'+item['id'],meta={'source_type':'curated_source_summary',
                'not_verbatim':True,'tags':item['tags']})
    for i,r in enumerate(graph.get('allegorical_mappings',[])):
        yield dict(id=f'allegory:{i}',kind='interpretation',entity_id=str(r.get('entity','')),title='Proposed modern allegory (not ancient evidence)',body=as_text(r),source='User-defined interpretation',verification='interpretive_only',family=f'allegory:{i}',meta={'source_type':'interpretation'})
    for path in sorted((ROOT/'passages').rglob('*.txt')):
        if not path.is_file():continue
        sidecar=path.with_suffix('.json')
        meta=json.loads(sidecar.read_text(encoding='utf-8')) if sidecar.exists() else {}
        rel=path.relative_to(ROOT/'passages').as_posix()
        for n,part in enumerate(chunks(path.read_text(encoding='utf-8'))):
            yield dict(id=f'passage:{rel}:{n}',kind='passage',entity_id=str(meta.get('entity_id','')),title=meta.get('title',path.stem),body=part,source=as_text(meta.get('citation','Local passage: citation not supplied')),verification=meta.get('verification','user_supplied_unverified'),family=f'passage:{rel}',meta={'source_type':'primary_passage' if meta.get('citation') else 'unattributed_text','part':n,'file':rel,'author':meta.get('author',''),'language':meta.get('language',''),'license_note':meta.get('license_note','')})
    manifest=ROOT/'data/image_manifest.json'
    if manifest.exists():
        for i,item in enumerate(json.loads(manifest.read_text(encoding='utf-8')).get('images',[])):
            if not item.get('license_verified'):continue
            p=(ROOT/item.get('local_path','')).resolve()
            if not p.is_relative_to(ROOT.resolve()) or not p.is_file():continue
            if item.get('image_sha256') and hashlib.sha256(p.read_bytes()).hexdigest()!=item['image_sha256']:continue
            yield dict(id=f'image:{item.get("image_id",i)}',kind='image',entity_id=as_text(item.get('depicted_entities')),title=item.get('description','Artwork'),body=as_text(item),source=as_text(item.get('source_url')),verification='image_metadata_only',family=f'image:{i}',meta={'source_type':'image_metadata','path':str(p)})

def ollama_embed(texts):
    try:
        r=requests.post(URL+'/api/embed',json={'model':EMBED,'input':texts},timeout=600);r.raise_for_status()
        vecs=r.json()['embeddings']
    except (requests.RequestException,KeyError) as exc:raise RuntimeError(f'Ollama embedding failed ({URL}, {EMBED}): {exc}') from exc
    if len(vecs)!=len(texts):raise ValueError('Embedding count mismatch')
    out=[]
    for v in vecs:
        a=np.asarray(v,dtype=np.float32);norm=np.linalg.norm(a)
        if a.ndim!=1 or not np.isfinite(a).all() or norm<=0:raise ValueError('Invalid vector')
        out.append(a/norm)
    return out

def digest(r):
    return hashlib.sha256(json.dumps({k:r[k] for k in ('kind','title','body','source','verification','meta')},sort_keys=True,ensure_ascii=False).encode()).hexdigest()

def ingest():
    c=db();count=0;unchanged=0;seen=set();pending=[]
    print(tint('INDEXING • preparing documents and embeddings','gold'),file=sys.stderr,flush=True)
    def flush():
        nonlocal count
        if not pending:return
        progress('Embedding '+str(count+len(pending))+' records')
        vectors=ollama_embed([f'{r["title"]}\n{r["body"]}' for r,h in pending])
        for (r,h),v in zip(pending,vectors):
            c.execute('''INSERT INTO docs(id,kind,entity_id,title,body,source,verification,content_hash,model,vector,family,meta)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET
            kind=excluded.kind,entity_id=excluded.entity_id,title=excluded.title,body=excluded.body,
            source=excluded.source,verification=excluded.verification,content_hash=excluded.content_hash,
            model=excluded.model,vector=excluded.vector,family=excluded.family,meta=excluded.meta''',
            (r['id'],r['kind'],r['entity_id'],r['title'],r['body'],r['source'],r['verification'],h,EMBED,v.tobytes(),r['family'],json.dumps(r['meta'],ensure_ascii=False)))
            count+=1
        c.commit();pending.clear();print(f'Embedded {count} records...',flush=True)
    for r in records():
        seen.add(r['id']);h=digest(r)
        old=c.execute('SELECT content_hash,model FROM docs WHERE id=?',(r['id'],)).fetchone()
        if old and (old['content_hash'],old['model'])==(h,EMBED):unchanged+=1;continue
        pending.append((r,h))
        if len(pending)>=BATCH:flush()
    flush()
    stale=[r['id'] for r in c.execute('SELECT id FROM docs') if r['id'] not in seen]
    for rid in stale:c.execute('DELETE FROM docs WHERE id=?',(rid,))
    c.commit()
    print(f'Index ready: {count} embedded, {unchanged} unchanged, {len(stale)} stale removed. {DB}')

def lexical(c,query,limit=80,kind=None):
    terms=re.findall(r'[^\W_]+',unicodedata.normalize('NFKC',query),flags=re.UNICODE)
    terms=[t for t in terms if len(t)>1]
    if not terms:return {}
    expr=' OR '.join('"'+t.replace('"','')+'"' for t in terms[:16])
    try:
        sql='SELECT d.id,bm25(docs_fts,3.0,1.0,0.7) AS bm FROM docs_fts JOIN docs d ON d.rowid=docs_fts.rowid WHERE docs_fts MATCH ? AND d.model=?'
        args=[expr,EMBED]
        if kind:sql+=' AND d.kind=?';args.append(kind)
        sql+=' ORDER BY bm LIMIT ?';args.append(limit)
        return {r['id']:rank for rank,r in enumerate(c.execute(sql,args),1)}
    except sqlite3.OperationalError:return {}

# Source quality measures provenance, not truth. No legacy record is marked verified.
SOURCE_TIERS={
    'verified_primary_text':1,
    'verified_primary_passage':1,
    'verified_passage_locator':2,
    'source_locator_provided_text_not_independently_collated':3,
    'reference_locator_unverified':4,
    'user_supplied_unverified':4,
    'legacy_unverified':4,
    'dataset_relationship_unverified':5,
    'image_metadata_only':5,
    'interpretive_only':6,
}

def evidence_tier(hit):
    return SOURCE_TIERS.get(hit.get('verification',''),5)

def source_language(source):
    """Coarse source tradition label, not a full language detector."""
    x=(source or '').casefold()
    latin=('ovid','virgil','vergil','propertius','statius','seneca','hyginus','latin')
    greek=('homer','hesiod','apollonius','pausanias','apollodorus','pindar','euripides','aristophanes','greek')
    if any(w in x for w in latin) and any(w in x for w in greek):return 'mixed Greek / Latin'
    if any(w in x for w in latin):return 'Latin / Roman-era'
    if any(w in x for w in greek):return 'Greek tradition'
    return 'unspecified'

def source_first(hits,k,include_legacy=False):
    """Select diverse passage evidence first, then use legacy records as fallback."""
    if not hits:return []
    def rank(h):
        tier=evidence_tier(h)
        # Preserve relevance among equal-tier hits; prioritize citations over generic edges.
        return (tier, 0 if h['kind']=='passage' else 1, -h['score'])
    ordered=sorted(hits,key=rank)
    selected=[]; families=set(); signatures=set()
    for h in ordered:
        signature=(re.sub(r'[^a-z0-9]+','',h.get('source','').casefold()),re.sub(r'[^a-z0-9]+','',h.get('title','').casefold()))
        if h['family'] in families or signature in signatures:continue
        if not include_legacy and evidence_tier(h)>=5 and len([x for x in selected if evidence_tier(x)<=4])>=k:
            continue
        families.add(h['family']);signatures.add(signature);selected.append(h)
        if len(selected)>=k:break
    return selected

def audit_answer(answer_text,hits):
    """Deterministic citation and known-conflation checks, not semantic fact verification."""
    issues=[]
    valid={str(i) for i in range(1,len(hits)+1)}
    for n in re.findall(r'\[(\d+)\]',answer_text):
        if n not in valid:issues.append(f'Citation [{n}] is not among retrieved sources')
    if re.search(r'\bPan\b.{0,70}\b(play(?:s|ed|ing)?|uses?|perform(?:s|ed)?)\b.{0,35}\blyre\b',answer_text,re.I|re.S):
        issues.append('Potential unsupported Pan–lyre performance claim; review source')
    if re.search(r'\b(?:Homeric Hymn to Pan|Greek hymn)\b.{0,90}\b(?:explicitly says|states|proves)\b.{0,40}\bnot the lyre\b',answer_text,re.I|re.S):
        issues.append('Do not attribute an explicit lyre exclusion to the hymn')
    if re.search(r'\bOvid\b',answer_text,re.I) and not re.search(r'\b(?:Roman|Latin|Ovid.s|later)\b',answer_text,re.I):
        issues.append('Label Ovid as a Latin/Roman-era source')
    if not re.search(r'\[\d+\]',answer_text):issues.append('No numbered source citations in answer')
    return sorted(set(issues))

def retrieve(query,k=DEFAULT_TOP_K,kind=None,diversify=True):
    progress('Searching • encoding query')
    c=db();q=ollama_embed([query])[0]
    sql='SELECT * FROM docs WHERE model=?';args=[EMBED]
    if kind:sql+=' AND kind=?';args.append(kind)
    rows=c.execute(sql,args).fetchall()
    if not rows:return []
    scored=[]
    for row in rows:
        v=np.frombuffer(row['vector'],dtype=np.float32)
        if len(v)==len(q):scored.append((float(np.dot(q,v)),row))
    progress('Searching • ranking '+str(len(scored))+' documents')
    scored.sort(key=lambda x:x[0],reverse=True)
    dense={r['id']:i for i,(_,r) in enumerate(scored[:max(80,k*10)],1)}
    sparse=lexical(c,query,max(80,k*10),kind)
    byid={r['id']:(s,r) for s,r in scored}
    candidates=set(dense)|set(sparse)
    output=[]
    for rid in candidates:
        if rid not in byid:continue
        sim,row=byid[rid]
        # Reciprocal rank fusion; primary passages get a small evidence-oriented tie-break.
        score=(1/(60+dense[rid]) if rid in dense else 0)+(1/(60+sparse[rid]) if rid in sparse else 0)
        meta=json.loads(row['meta'] or '{}')
        if row['kind']=='passage' and row['source'] and row['verification'] not in ('user_supplied_unverified','unverified'):score+=0.006
        if rid.startswith('curated:') and any(t.lower() in query.lower() for t in meta.get('tags',[])):score+=0.008
        output.append(dict(id=rid,kind=row['kind'],title=row['title'],text=clean(row['body']),source=clean(row['source']),verification=row['verification'],similarity=round(sim,4),score=score,family=row['family'],meta=meta))
    output.sort(key=lambda x:x['score'],reverse=True)
    if diversify:
        chosen=[];counts={}
        for r in output:
            fam=r['family'];limit=2 if r['kind']=='passage' else 1
            if counts.get(fam,0)>=limit:continue
            counts[fam]=counts.get(fam,0)+1;chosen.append(r)
            if len(chosen)>=k:break
        output=chosen
    else:output=output[:k]
    for r in output:
        r['score']=round(r['score'],5)
        r['evidence_tier']=evidence_tier(r)
        r['source_language']=source_language(r['source'])
    return output

def display(results,json_mode=False):
    if json_mode:
        for r in results:print(json.dumps(r,ensure_ascii=False))
        return
    if not results:print('No indexed results. Run: python nothos.py ingest');return
    for i,r in enumerate(results,1):
        print('\n'+tint(f'[{i}] {r["title"]}','gold')+f' | {r["kind"]} | hybrid={r["score"]:.5f} cosine={r["similarity"]:.3f}')
        print(tint('    Source: ','blue')+f'{r["source"] or "No source provided"} | '+tint(f'Tier: {r.get("evidence_tier",evidence_tier(r))}',tier_tint(r.get('evidence_tier',evidence_tier(r))))+f' | {r.get("source_language",source_language(r["source"]))}')
        print(f'    Verification: {r["verification"]}')
        print('    '+flat(r['text'])[:900])

def show_evidence(query,k=DEFAULT_TOP_K,json_mode=False):
    """Display exactly the source records used by `ask`, without an LLM call."""
    hits=focused_evidence(query,k)
    if json_mode:
        for i,h in enumerate(hits,1):
            print(json.dumps({'citation':i,**h},ensure_ascii=False))
        return
    if not hits:
        print('No indexed evidence. Run: python nothos.py ingest')
        return
    for i,h in enumerate(hits,1):
        print('\n'+tint(f'[{i}] Tier {evidence_tier(h)}',tier_tint(evidence_tier(h)))+' | '+tint(h['title'],'gold'))
        print(tint('    Source: ','blue')+(h['source'] or 'not supplied'))
        print(tint('    Status: ','muted')+h['verification'])
        if h.get('meta',{}).get('language'):print(tint('    Language: ','blue')+h['meta']['language'])
        print(tint('    Content: ','muted')+flat(h['text'])[:1300])


def answer(query,k=DEFAULT_TOP_K,model=CHAT,mode='strict'):
    # Overfetch to avoid a top-k context dominated by generic relationship edges.
    hits=focused_evidence(query,k)
    if not hits:print('No indexed evidence. Run ingest first.');return
    progress('Research • composing cited answer')
    context=[]
    for i,r in enumerate(hits,1):
        context.append(f'[{i}] {r["title"]}\nTYPE: {r["kind"]}\nSOURCE: {r["source"] or "not supplied"}\nSOURCE LANGUAGE: {source_language(r["source"])}\nEVIDENCE TIER: {evidence_tier(r)} (1 best, 6 interpretation)\nVERIFICATION: {r["verification"]}\nTEXT: {r["text"][:1300]}')
    system='''You are NOTHOS, a cautious research assistant for Greek mythology, Greek philology and social history. Answer using ONLY supplied retrieved records. Cite records as [1], [2] etc. Distinguish ancient textual evidence, dataset summaries, and modern/user-proposed allegories. Dataset verification flags like legacy_unverified or reference_locator_unverified mean the source has NOT been independently checked. Do not claim a named Siren was a companion of Persephone unless a retrieved source names that individual. The lyre is a stringed instrument, whereas Pan's syrinx (panpipes) is a reed wind instrument; never equate them. Hermes INVENTS the lyre and gives it TO Apollo in an exchange involving cattle. Apollo does NOT give the lyre to Hermes. Pan is associated with the syrinx. In Ovid, Syrinx becomes reeds from which Pan makes his pipes; this transformation is directly connected to his musical practice. Do not infer instrument use from an 'associated_with' graph edge. NEVER say an ancient author explicitly denies a claim unless the passage contains that denial. State instead that the supplied evidence does not establish it. Greek and Latin/Roman sources must be clearly distinguished. Prefer cited passages over generic graph associations. Answer only the entities and relationships asked about; do not introduce Orpheus or Sirens in an answer about Hermes, Apollo, Pan and instruments unless necessary. Never invert the giver and recipient of a transfer. Treat citations as record references, not proof of verified primary texts. Never turn a title or editorial caution into an ancient quotation. Distinguish a source-located summary from a verbatim verified quotation. If the evidence does not establish an answer, say so. Never invent primary-source quotations or passages. Reply in readable paragraphs with real newlines, not JSON or escaped \\n. End with a short 'Evidence limitations' note when needed.'''
    if mode=='exploratory':
        system+=' Exploratory mode: you may propose new symbolic readings, but prefix each with HYPOTHESIS and explicitly separate it from ancient testimony.'
    payload={'model':model,'stream':False,'messages':[{'role':'system','content':system},{'role':'user','content':f'QUESTION: {query}\n\nRETRIEVED RECORDS:\n'+ '\n\n'.join(context)}], 'options':{'temperature':0.15}}
    try:
        r=requests.post(URL+'/api/chat',json=payload,timeout=600);r.raise_for_status()
        response=r.json()['message']['content']
    except (requests.RequestException,KeyError) as exc:
        print(f'Answer model unavailable ({model}): {exc}\nShowing evidence instead:',file=sys.stderr);display(hits);return
    progress('Research • complete',done=True)
    print(clean(response))
    warnings=audit_answer(response,hits)
    if warnings:
        print('\n--- Automated answer checks (review required) ---')
        for warning in warnings:print('! '+warning)
    print('\n'+tint('--- Sources retrieved ---','gold'))
    for i,h in enumerate(hits,1):print(tint(f'[{i}] Tier {evidence_tier(h)}',tier_tint(evidence_tier(h)))+f' | {source_language(h["source"])} | {h["source"] or h["title"]} ({h["verification"]})')

def doctor():
    print('NOTHOS V6 diagnostics')
    print('Database:',DB,'exists:',DB.exists())
    print('Ollama:',URL,'embed model:',EMBED,'chat model:',CHAT,'default top-k:',DEFAULT_TOP_K)
    try:
        r=requests.get(URL+'/api/tags',timeout=10);r.raise_for_status()
        names=[m['name'] for m in r.json().get('models',[])]
        print('Models:',', '.join(names) or '(none)')
        print('Embedding model installed:',any(x.split(':')[0]==EMBED.split(':')[0] for x in names))
    except Exception as exc:print('Ollama connection failed:',exc)
    if DB.exists():
        c=db();print('Indexed documents:',c.execute('SELECT count(*) FROM docs').fetchone()[0]);print('Kinds:',dict(c.execute('SELECT kind,count(*) FROM docs GROUP BY kind').fetchall()))


# NOTHOS V6: user-visible provenance colors; never promote uncollated text to verified.
PALETTE={'background':'#090B10','panel':'#151922','gold':'#D4AF37','text':'#F2EEE5',
 'muted':'#A6ADBB','tier1':'#22C55E','tier2':'#38BDF8','tier3':'#FACC15',
 'tier4':'#F97316','tier5':'#EF4444','tier6':'#A855F7'}
BANNER=r'''
             _..---.._
         .-''  .---.  ``-.
       .'   .-`  |  `-.   `.
      /   _/  /\ | /\  \_   \
     / .-'  _/  \|/  \_  `-. \
    | /  .-'  .-~~~~-.  `-.  \ |
    | | /    /  .--.  \    \ | |
    | |/    |  (o  o)  |    \| |
    |  \    |    /\    |    /  |
     \  `-._\  \__/  /_.-'  /
      `._    `-.__.-'    _.'
         `--..____..--'
       /\ /\ /\ || /\ /\ /\
      /  V  V  \||/  V  V  \
     [  N O T H O S  ]
      ══ MEDUSA ══ SOURCE FIRST
'''
# ANSI coloring is terminal-only; NO_COLOR and non-TTY output remain plain text.
ANSI={'gold':'\x1b[38;2;212;175;55m','green':'\x1b[38;2;34;197;94m',
      'blue':'\x1b[38;2;56;189;248m','yellow':'\x1b[38;2;250;204;21m',
      'orange':'\x1b[38;2;249;115;22m','red':'\x1b[38;2;239;68;68m',
      'purple':'\x1b[38;2;168;85;247m','muted':'\x1b[38;2;166;173;187m',
      'reset':'\x1b[0m','bold':'\x1b[1m'}
def color_enabled():
    return os.environ.get('NOTHOS_COLOR','auto').lower() in ('1','always','yes','true') or (
        os.environ.get('NOTHOS_COLOR','auto').lower() not in ('0','never','no','false')
        and 'NO_COLOR' not in os.environ and sys.stdout.isatty() and os.environ.get('TERM','')!='dumb')
def tint(value,shade):
    value=str(value)
    return ANSI.get(shade,'')+value+ANSI['reset'] if color_enabled() else value
def tier_tint(tier):
    return ('green','blue','yellow','orange','red','purple')[max(1,min(6,int(tier)))-1]
def progress(message,done=False):
    """Stderr spinner/progress activity; never claim a numeric percentage of Ollama completion."""
    if SHOW_PROGRESS=='never' or (SHOW_PROGRESS=='auto' and not sys.stderr.isatty()):return
    bar='━'*18 if done else '━'*9+'╸'+'·'*8
    print('\r'+tint('▰ '+bar+' '+message,'green' if done else 'gold')+' '*8,file=sys.stderr,flush=True)

def show_banner():
    """Display local Medusa PNG with Chafa and FIGlet; gracefully degrade if absent."""
    art=ROOT/'assets'/'medusa.png'
    if art.exists() and shutil.which('chafa') and sys.stdout.isatty():
        subprocess.run(['chafa','--size','45x25',str(art)],check=False)
    elif not art.exists():
        print(tint('MEDUSA IMAGE MISSING — copy medusa.png into assets/','orange'))
    elif not shutil.which('chafa'):
        print(tint('Install chafa for the 45x25 Medusa portrait: brew install chafa','orange'))
    if shutil.which('figlet'):
        result=subprocess.run(['figlet','-w','120','NOTHOS'],capture_output=True,text=True,check=False)
        print(tint(result.stdout,'gold'))
    else:
        print(tint('━'*14+'  N O T H O S  '+'━'*14,'gold'))
    print(tint('  GREEK RESEARCH  •  SOURCE FIRST  •  OBSIDIAN & GOLD','blue'))

# Decorative terminal Medusa, original ASCII design, not borrowed from neofetch.
ALIASES={'syrinx_nymph':{'syrinx','nymph_syrinx'},'syrinx_instrument':{'panpipes','reed pipes','pipes'},
         'hermes':{'hermes'},'apollo':{'apollo'},'pan':{'pan'},'lyre':{'lyre'}}
STOPWORDS={'explain','the','and','of','in','a','an','to','is','are','what','relationship','between','with','how','does','did','their','from','which','about'}
def query_entities(query):
    words=set(re.findall(r'[^\W_]+',query.casefold()))
    found=[]
    for name,aliases in ALIASES.items():
        if any(alias in query.casefold() for alias in aliases):found.append(name)
    return found

def focused_evidence(query,k=DEFAULT_TOP_K):
    # Retrieve a broad pool, rank by cited provenance, then relevance to query entities.
    candidates=retrieve(query,max(60,k*6))
    names=query_entities(query)
    tokens=set(re.findall(r'[^\W_]+',query.casefold()))-STOPWORDS
    def focus(h):
        title=h.get('title','').casefold();body=h['text'].casefold();tags=' '.join(h.get('meta',{}).get('tags',[])).casefold()
        matches=sum(bool(re.search(r'\b'+re.escape(n.split('_')[0])+r'\b',title+' '+tags+' '+body[:550])) for n in names)
        title_matches=sum(bool(re.search(r'\b'+re.escape(n.split('_')[0])+r'\b',title+' '+tags)) for n in names)
        irrelevant=sum(w in (title+' '+tags) for w in ('sirens','orpheus','muses') if w not in tokens)
        return (matches*2+title_matches*2-irrelevant*5,h['score'])
    relevant=sorted(candidates,key=lambda h:(-evidence_tier(h),*focus(h)),reverse=True)
    # Preserve tier ordering as primary constraint; select best matching source-located evidence.
    relevant=sorted(relevant,key=lambda h:(evidence_tier(h),-focus(h)[0],-focus(h)[1]))
    selected=[];seen_families=set();seen_signatures=set()
    for h in relevant:
        signature=(h['source'].casefold().strip(),h['title'].casefold().strip())
        if h['family'] in seen_families or signature in seen_signatures:continue
        # Avoid unrelated contextual spillover while sufficient focused evidence exists.
        if focus(h)[0]<0 and len(selected)>=min(k,4):continue
        selected.append(h);seen_families.add(h['family']);seen_signatures.add(signature)
        if len(selected)>=k:break
    return selected

def coverage(query,hits):
    names=query_entities(query)
    return {name:[i for i,h in enumerate(hits,1) if name.split('_')[0] in (h['title']+' '+h['text']).casefold()] for name in names}

def morph(word):
    # Lexical lookup placeholder, not a morphological parser or etymology authority.
    normalized=unicodedata.normalize('NFC',word)
    return {'input':word,'normalized':normalized,'characters':len(normalized),
            'script':'Greek' if any('GREEK' in unicodedata.name(c,'') for c in normalized) else 'other',
            'lemma':None,'morphology':None,'etymology':None,
            'warning':'No morphological lexicon is installed. No lemma, root or etymology inferred.'}
TIMELINE=[{'period':'Archaic Greek','approximate':'8th–6th c. BCE','examples':['Hesiod','Homeric Hymns'],'dating':'approximate; individual hymns vary'},
 {'period':'Classical Greek','approximate':'5th–4th c. BCE','examples':['Aristophanes','Euripides'],'dating':'approximate'},
 {'period':'Hellenistic Greek','approximate':'3rd–1st c. BCE','examples':['Apollonius Rhodius'],'dating':'approximate'},
 {'period':'Roman-era Latin','approximate':'1st c. BCE onward','examples':['Ovid'],'dating':'approximate'}]

def graph_data(entity=''):
    graph=json.loads((ROOT/'data/greek_myth_knowledge_graph_v3.json').read_text(encoding='utf-8'))
    relationships=graph.get('relationships',[])
    nodes={};edges=[]
    for r in relationships:
        src=str(r.get('subject',r.get('source',r.get('from',''))));dst=str(r.get('object',r.get('target',r.get('to',''))))
        if not src or not dst:continue
        if entity and entity.casefold() not in (src.casefold(),dst.casefold()):continue
        for v in (src,dst):nodes[v]={'id':v,'label':v}
        edges.append({'source':src,'target':dst,'label':r.get('predicate',r.get('relation','associated_with')),
                      'status':'dataset_relationship_unverified'})
        if len(edges)>=300:break
    return {'nodes':list(nodes.values()),'edges':edges,'note':'Dataset edges are unverified associations, not verified primary-source assertions.'}
def graph_text(entity=''):
    g=graph_data(entity)
    return '\n'.join(f"{e['source']} --{e['label']}--> {e['target']} [unverified]" for e in g['edges']) or 'No matching relationships.'

def evaluate(json_mode=False):
    # Offline deterministic regression checks, not a claim of full semantic verification.
    curated=[r for r in records() if r['id'].startswith('curated:')]
    text=' '.join(x['body'].casefold() for x in curated)
    checks={'hermes_lyre_invention':'tortoise' in text and 'lyre' in text,
            'hermes_to_apollo':'hermes transfers' in text,
            'pan_syrinx':'reed pipes' in text,
            'syrinx_to_reeds':'becomes reeds' in text,
            'variant_parentage':'other ancient traditions' in text,
            'no_primary_text_promoted':all(x['verification']=='source_locator_provided_text_not_independently_collated' for x in curated)}
    report={'checks':checks,'passed':sum(checks.values()),'total':len(checks),'limitations':'Fixture checks only; no Ollama calls, primary-source collation or generated-claim entailment.'}
    if json_mode:print(json.dumps(report,indent=2))
    else:
        for name,ok in checks.items():print(('PASS' if ok else 'FAIL'),name)
        print(f"{report['passed']}/{report['total']} checks. {report['limitations']}")
    return report

class WebHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def do_GET(self):
        parsed=urllib.parse.urlsplit(self.path);path=parsed.path
        params=urllib.parse.parse_qs(parsed.query)
        if path=='/api/evidence':
            query=params.get('q',[''])[0][:500]
            if not query:return self.respond({'error':'Missing q'},400)
            try:
                hits=focused_evidence(query,min(20,max(1,int(params.get('k',['12'])[0]))))
                return self.respond({'query':query,'entities':query_entities(query),'coverage':coverage(query,hits),'results':[{'citation':i,**h} for i,h in enumerate(hits,1)]})
            except Exception as exc:return self.respond({'error':str(exc)},503)
        if path=='/api/graph':return self.respond(graph_data(params.get('entity',[''])[0]))
        if path=='/api/timeline':return self.respond(TIMELINE)
        if path=='/api/morph':return self.respond(morph(params.get('word',[''])[0]))
        if path=='/api/evaluate':return self.respond({'checks':'Use CLI python nothos.py evaluate for regression results'})
        if path=='/' or path=='/index.html':
            page=(ROOT/'web/index.html').read_bytes()
            self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(page)));self.end_headers();self.wfile.write(page);return
        self.respond({'error':'Not found'},404)
    def respond(self,obj,status=200):
        body=json.dumps(obj,ensure_ascii=False).encode()
        self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)

def serve(host,port):
    show_banner()
    print(f'NOTHOS V6 dashboard: http://{host}:{port} (local only by default)')
    http.server.ThreadingHTTPServer((host,port),WebHandler).serve_forever()


def import_text(paths,author='',title='',language='Greek',citation='',license_note='',recursive=True):
    """Copy user-supplied UTF-8 texts into the passage corpus with transparent provenance.
    This is a local importer, not a downloader; users are responsible for rights/attribution.
    """
    dest=ROOT/'passages'/'imported';dest.mkdir(parents=True,exist_ok=True)
    files=[]
    for raw in paths:
        src=Path(raw).expanduser().resolve()
        if src.is_file():files.append(src)
        elif src.is_dir():files.extend(sorted(src.rglob('*.txt') if recursive else src.glob('*.txt')))
        else:raise FileNotFoundError(src)
    imported=[]
    for src in files:
        if src.suffix.lower() not in ('.txt','.text','.md'):continue
        data=src.read_text(encoding='utf-8-sig')
        if not data.strip():continue
        # Stable per-file ID prevents same-name collisions across different directories.
        suffix=hashlib.sha256(str(src).encode()).hexdigest()[:10]
        stem=re.sub(r'[^a-zA-Z0-9_-]+','_',src.stem)[:65] or 'text'
        dst=dest/f'{stem}_{suffix}.txt'
        dst.write_text(data,encoding='utf-8')
        meta={'title':title or src.stem,'author':author,'language':language,
              'citation':citation,'license_note':license_note,
              'verification':'user_supplied_unverified',
              'original_path':str(src),'imported_at':time.strftime('%Y-%m-%d')}
        dst.with_suffix('.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
        imported.append(str(dst.relative_to(ROOT)))
    print(tint(f'Imported {len(imported)} text files. Run: python nothos.py ingest','green'))
    for item in imported:print('  '+item)

def translate_text(text='',file=None,model=TRANSLATE_MODEL,source='Ancient Greek',target='English',output=None):
    """Call a user-installed Ollama translation model; preserve text and provenance."""
    if file:text=Path(file).expanduser().read_text(encoding='utf-8-sig')
    if not text.strip():raise ValueError('Provide text or --file')
    system=(f'Translate from {source} to {target}. Preserve names, line breaks, '
            'uncertain readings, and bracketed lacunae. Do not invent missing text. '
            'Output the translation only; do not add an unsupported scholarly citation.')
    progress('Translation • requesting '+model)
    r=requests.post(URL+'/api/chat',json={'model':model,'stream':False,
        'messages':[{'role':'system','content':system},{'role':'user','content':text}],
        'options':{'temperature':0.1}},timeout=900)
    r.raise_for_status()
    translated=r.json()['message']['content']
    if output:
        Path(output).expanduser().write_text(translated,encoding='utf-8')
        print(tint('Saved translation to '+output,'green'))
    else:print(translated)
    progress('Translation • complete',done=True)

def genealogy(entity='pan',json_mode=False):
    """Source-located, explicitly unverified competing traditions; no false Tier 1 claims."""
    path=ROOT/'data'/'genealogy_variants.json'
    data=json.loads(path.read_text(encoding='utf-8')) if path.exists() else []
    matches=[r for r in data if r['child'].casefold()==entity.casefold()]
    if json_mode:print(json.dumps(matches,ensure_ascii=False,indent=2));return
    if not matches:print('No indexed genealogy variants for '+entity);return
    for i,r in enumerate(matches,1):
        print(tint(f'[{i}] {r["child"]}: {r.get("father","?")} + {r.get("mother","not specified")}', 'gold'))
        print(tint('    Source: ','blue')+r['source'])
        print(tint('    Verification: ','orange')+r['verification'])
        if r.get('note'):print('    '+r['note'])

def main():
    p=argparse.ArgumentParser(description='NOTHOS V6 source-first Greek research suite')
    s=p.add_subparsers(dest='cmd',required=True)
    s.add_parser('ingest');s.add_parser('doctor');s.add_parser('banner')
    im=s.add_parser('import-text',help='Import UTF-8 Greek/Latin/English .txt or .md files')
    im.add_argument('paths',nargs='+');im.add_argument('--author',default='');im.add_argument('--title',default='')
    im.add_argument('--language',default='Greek');im.add_argument('--citation',default='')
    im.add_argument('--license-note',default='');im.add_argument('--no-recursive',action='store_true')
    tr=s.add_parser('translate',help='Translate via installed Ollama TranslateGemma model')
    tr.add_argument('text',nargs='?',default='');tr.add_argument('--file');tr.add_argument('--model',default=TRANSLATE_MODEL)
    tr.add_argument('--source',default='Ancient Greek');tr.add_argument('--target',default='English');tr.add_argument('--output')
    gn=s.add_parser('genealogy');gn.add_argument('entity',nargs='?',default='pan');gn.add_argument('--json',action='store_true')
    web=s.add_parser('web');web.add_argument('--host',default='127.0.0.1');web.add_argument('--port',type=int,default=8789)
    ev=s.add_parser('evaluate');ev.add_argument('--json',action='store_true')
    mo=s.add_parser('morph');mo.add_argument('word')
    tl=s.add_parser('timeline')
    graph=s.add_parser('graph');graph.add_argument('--entity',default='');graph.add_argument('--json',action='store_true')
    for cmd in ('search','ask','evidence'):
        q=s.add_parser(cmd);q.add_argument('query');q.add_argument('--top-k',type=int,default=DEFAULT_TOP_K)
        if cmd=='evidence':q.add_argument('--json',action='store_true')
        if cmd=='search':q.add_argument('--kind',choices=['entity','relation','passage','interpretation','image']);q.add_argument('--json',action='store_true');q.add_argument('--no-diversity',action='store_true')
        elif cmd=='ask':q.add_argument('--model',default=CHAT);q.add_argument('--mode',choices=['strict','exploratory'],default='strict')
    p.add_argument('--color',choices=['auto','always','never'],default=None,help='Terminal ANSI colors (or NOTHOS_COLOR environment variable)')
    a=p.parse_args()
    if a.color:os.environ['NOTHOS_COLOR']=a.color
    if a.cmd=='ingest':ingest()
    elif a.cmd=='doctor':doctor()
    elif a.cmd=='banner':show_banner()
    elif a.cmd=='import-text':import_text(a.paths,a.author,a.title,a.language,a.citation,a.license_note,not a.no_recursive)
    elif a.cmd=='translate':translate_text(a.text,a.file,a.model,a.source,a.target,a.output)
    elif a.cmd=='genealogy':genealogy(a.entity,a.json)
    elif a.cmd=='web':serve(a.host,a.port)
    elif a.cmd=='evaluate':evaluate(a.json)
    elif a.cmd=='morph':print(json.dumps(morph(a.word),ensure_ascii=False,indent=2))
    elif a.cmd=='timeline':print(json.dumps(TIMELINE,ensure_ascii=False,indent=2))
    elif a.cmd=='graph':print(json.dumps(graph_data(a.entity),ensure_ascii=False,indent=2) if a.json else graph_text(a.entity))
    elif a.cmd=='search':display(retrieve(a.query,a.top_k,a.kind,not a.no_diversity),a.json)
    elif a.cmd=='evidence':show_evidence(a.query,a.top_k,a.json)
    else:answer(a.query,a.top_k,a.model,a.mode)
if __name__=='__main__':main()

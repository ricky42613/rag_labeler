from fastapi import FastAPI
from pydantic import BaseModel
import json
from typing import List
import os
import redis
import lancedb
import pandas as pd 
import pyarrow as pa
from mlx_utils import build_model, mlx_encode
import torch.nn.functional as F
from torch import Tensor
from jieba import Tokenizer

jiebaTokenizer = Tokenizer()

jiebaTokenizer.set_dictionary("./dict/merge.4jieba.default.dict")
jiebaTokenizer.load_userdict("./dict/merge.4jieba.extra.dict")
def average_pool(last_hidden_states: Tensor,
                 attention_mask: Tensor) -> Tensor:
    last_hidden = last_hidden_states.masked_fill(~attention_mask[..., None].bool(), 0.0)
    return last_hidden.sum(dim=1) / attention_mask.sum(dim=1)[..., None]

max_length = 512
model, tokenizer = build_model('model_cfg.json', 'mlx_bert.npz')
CHANNEL_NAME = 'extension'
redis_connection = redis.Redis(host='localhost', port='6379')
lancedb_connection = lancedb.connect("../pipeline/knowledge-base")
dimension = 384
fields = ['rec_id', 'content', 'context', 'question', 'answer', 'url', 'user', 'tags', 'embedding']
schema = pa.schema([
            pa.field("rec_id", pa.string()),
            pa.field("content", pa.string()),
            pa.field("context", pa.string()),
            pa.field("question", pa.string()),
            pa.field("answer", pa.string()),
            pa.field("url", pa.string()),
            pa.field("user", pa.string()),
            pa.field("tags", pa.list_(pa.string())),
            pa.field("embedding", pa.list_(pa.float64(), dimension)),
        ])
browser_table = lancedb_connection.create_table("browser", schema=schema, exist_ok=True)
browser_table.create_fts_index("context", writer_heap_size=1024 * 1024 * 512, replace=True)
def v_search(q:str):
    q = q[:max_length]
    embeddings = mlx_encode(q, tokenizer, model)
    browser_table = lancedb_connection.create_table("browser", schema=schema, exist_ok=True)
    df = browser_table.search(embeddings[0], vector_column_name="embedding").to_pandas()
    return df

def f_search(q:str):
    q = q.lower()
    toks = [word for word in jiebaTokenizer.cut(q.strip(), HMM=False) if not word.isspace()]
    browser_table = lancedb_connection.create_table("browser", schema=schema, exist_ok=True)
    df = browser_table.search(" ".join(toks)).to_pandas()
    return df

def hybrid_rerank(df_vs, df_fts):
    vs_rst = json.loads(df_vs.to_json(orient="records"))
    fts_rst = json.loads(df_fts.to_json(orient="records"))
    last_id = 0
    tab = {}
    ret = []
    alpha = 0.5
    for item in vs_rst:
        item['fts_score'] = 0
        tab[item['rec_id']] = last_id
        last_id += 1
        item['score'] = alpha * (1-item['_distance'])
        ret.append(item)
    for item in fts_rst:
        item['fts_score'] = item['score']
        if item['rec_id'] not in tab:
            item['score'] = (1-alpha) * item['score']
            ret.append(item)
        else:
            rec_idx = tab[item['rec_id']]
            ret[rec_idx]['score'] += (1-alpha) * item['score']
    return pd.DataFrame.from_records(ret)
class Tags(BaseModel):
    tags: List[str]

class RAGdata(BaseModel):
    rec_id: str = None
    content: str
    context: str
    question: str
    answer: str
    url: str
    user: str
    tags: List[str]

configFile = './config.json'
app = FastAPI()
@app.post("/api/data")
def save_data(data: RAGdata):
    rec = data.__dict__
    del rec['rec_id']
    toks = [word for word in jiebaTokenizer.cut(rec['context'].strip(), HMM=False) if not word.isspace()]
    rec['context'] = ' '.join(toks)
    redis_connection.publish(CHANNEL_NAME, json.dumps(rec))
    return {'status': 200}

@app.put("/api/data")
def update_data(data: RAGdata):
    updateData = {}
    for field in fields:
        if field not in ['context', 'question', 'answer']:
            continue
        updateData[field] = getattr(data, field)
    print(updateData)
    browser_table = lancedb_connection.create_table("browser", schema=schema, exist_ok=True)
    browser_table.update(where=f'rec_id = "{data.rec_id}"', values=updateData)
    return {'status': 200}

@app.get("/api/data")
def get_data(page: int, pageSize: int):
    browser_table = lancedb_connection.create_table("browser", schema=schema, exist_ok=True)
    begIdx = pageSize * (page-1)
    total = len(browser_table)
    endIdx = min(begIdx + pageSize, total)
    recs = []
    if begIdx < total:
        data = browser_table.to_arrow().take([i for i in range(begIdx, endIdx)])
        for i in range(len(data)):
            rec = {}
            for field in fields:
                if field == 'embedding':
                    continue
                if field != 'tags':
                    rec[field] = str(data[field][i])
                else:
                    rec[field] = list(data[field][i])
                    rec[field] = [str(item) for item in rec[field]]
            recs.append(rec)
    return {'status': 200, 'data': json.dumps(recs)}

@app.delete("/api/data")
def delete_data(rec_ids: str):
    browser_table = lancedb_connection.create_table("browser", schema=schema, exist_ok=True)
    id_list = [f'"{rec_id}"' for rec_id in rec_ids.split(',')]
    browser_table.delete(f'rec_id IN ({",".join(id_list)})')
    return {'status':200}

@app.get("/api/num_of_data")
def num_of_data():
    browser_table = lancedb_connection.create_table("browser", schema=schema, exist_ok=True)
    return {'status': 200, 'data': len(browser_table)}

@app.get("/api/search")
def get_data(q: str=None, tags: str='', mode: str='vector'):
    browser_table = lancedb_connection.create_table("browser", schema=schema, exist_ok=True)
    if q == None:
        df = browser_table.search(None, vector_column_name="embedding").to_pandas()
    elif mode == 'vector':
        df = v_search(q)
    elif mode == 'fts':
        df = f_search(q)
    elif mode == 'hybrid':
        df_vs = v_search(q)
        df_fts = f_search(q)
        df = hybrid_rerank(df_vs, df_fts)
    df = df.drop(columns=['embedding'])
    if len(tags) > 0:
        taglist = tags.split(',')
        df = df[df['tags'].apply(lambda item: bool(set(item) & set(taglist)))]    
    df = json.loads(df.to_json(orient="records"))[:10]
    return {'status': 200, 'data': json.dumps(df)}

@app.post('/api/tags')
def save_tags(data: Tags):
    cfg = {}
    if os.path.exists(configFile):
        with open(configFile, 'r') as f:
            cfg = json.load(f)
    cfg['tags'] = data.tags
    with open(configFile, 'w') as f:
        json.dump(cfg, f, indent=4, ensure_ascii=False)
    return {"status": 200}

@app.get('/api/tags')
def save_tags():
    cfg = {'tags': []}
    if os.path.exists(configFile):
        with open(configFile, 'r') as f:
            cfg = json.load(f)
    return {"status": 200, 'tags': cfg['tags']}
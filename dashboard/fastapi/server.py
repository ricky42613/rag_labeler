from fastapi import FastAPI
from pydantic import BaseModel
import json
from typing import List
import os
import redis
import lancedb
import pyarrow as pa
from transformers import AutoModel, AutoTokenizer
import torch.nn.functional as F
from torch import Tensor


def average_pool(last_hidden_states: Tensor,
                 attention_mask: Tensor) -> Tensor:
    last_hidden = last_hidden_states.masked_fill(~attention_mask[..., None].bool(), 0.0)
    return last_hidden.sum(dim=1) / attention_mask.sum(dim=1)[..., None]

# Configuration
# REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
# REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
# CHANNEL_NAME = os.getenv('REDIS_CHANNEL_NAME', 'extension')
# print('connect redis')
model_name = 'intfloat/multilingual-e5-small'
max_length = 512
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name).to('cpu')
model.eval()
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
    redis_connection.publish(CHANNEL_NAME, json.dumps(rec))
    return {'status': 200}

@app.put("/api/data")
def update_data(data: RAGdata):
    browser_table = lancedb_connection.create_table("browser", schema=schema, exist_ok=True)
    updateData = {}
    for field in fields:
        if field not in ['context', 'question', 'answer']:
            continue
        updateData[field] = getattr(data, field)
    print(updateData)
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
    id_list = [f'"{rec_id}"' for rec_id in rec_ids.split(',')]
    browser_table = lancedb_connection.create_table("browser", schema=schema, exist_ok=True)
    browser_table.delete(f'rec_id IN ({",".join(id_list)})')
    return {'status':200}

@app.get("/api/num_of_data")
def num_of_data():
    browser_table = lancedb_connection.create_table("browser", schema=schema, exist_ok=True)
    return {'status': 200, 'data': len(browser_table)}

@app.get("/api/search")
def get_data(q: str=None, tags: str=''):
    browser_table = lancedb_connection.create_table("browser", schema=schema, exist_ok=True)
    global model
    global tokenizer
    embeddings = [None]
    if q != None:
        batch_dict = tokenizer([q], max_length=512, padding=True, truncation=True, return_tensors='pt')
        outputs = model(**batch_dict)
        embeddings = average_pool(outputs.last_hidden_state, batch_dict['attention_mask'])
        embeddings = F.normalize(embeddings, p=2, dim=1).tolist()
    # df = browser_table.search(embeddings[0], vector_column_name="embedding").limit(10).to_list()
    df = browser_table.search(embeddings[0], vector_column_name="embedding").to_pandas()
    if len(tags) > 0:
        taglist = tags.split(',')
        print(taglist)
        df = df[df['tags'].apply(lambda item: bool(set(item) & set(taglist)))]    
    df = df.drop(columns=['embedding'])
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
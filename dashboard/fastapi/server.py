from fastapi import FastAPI
from pydantic import BaseModel
import json
from typing import List
import os
import redis
import lancedb
import pyarrow as pa

# Configuration
# REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
# REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
# CHANNEL_NAME = os.getenv('REDIS_CHANNEL_NAME', 'extension')
# print('connect redis')
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
def get_data(q: str, tags: str):
    # tagList = tags.split(',')
    # if len(q) > 0:
    #     searchSQL = f'''
    #     SELECT *, score
    #     FROM (
    #         SELECT *, fts_main_knowledge.match_bm25(
    #             rec_id,
    #             '{q}'
    #         ) AS score
    #         FROM knowledge
    #     ) sq
    #     WHERE score IS NOT NULL
    #     '''
    #     if len(tagList) > 0:
    #         searchSQL +=  f' AND list_has_any(tags, $selectedTags)'
    # else:
    #     searchSQL = f'''
    #         SELECT * FROM knowledge
    #     '''
    #     if len(tagList) > 0:
    #         searchSQL +=  f'WHERE list_has_any(knowledge.tags, $selectedTags)'
    # if len(q) > 0:
    #     searchSQL += ' ORDER BY score;'
    # print(searchSQL)
    # if len(tagList) > 0:
    #     con.execute(searchSQL, {'selectedTags': tagList})
    # else:
    #     con.execute(searchSQL)
    # data = con.fetchall()
    recs = []
    # for item in data:
    #     rec = {}
    #     for idx, field in enumerate(Fields):
    #         rec[field[0]] = item[idx]
    #         if len(q) > 0:
    #             rec['score'] = item[-1]
    #     recs.append(rec)
    return {'status': 200, 'data': json.dumps(recs)}

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
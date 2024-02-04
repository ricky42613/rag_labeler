from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import json
from trafilatura import extract
from lxml import html
import duckdb
from typing import List, Optional
import os
import redis
import lancedb
import pyarrow as pa

# Configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
CHANNEL_NAME = os.getenv('REDIS_CHANNEL_NAME', 'extension')
redis_connection = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
lancedb_connection = lancedb.connect("../pipeline/knowledge-base")
dimension = 384
fields = ['recId', 'content', 'context', 'question', 'answer', 'url', 'user', 'tags', 'embedding']
schema = pa.schema([
            pa.field("recId", pa.string()),
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
class Tags(BaseModel):
    tags: List[str]

class RAGdata(BaseModel):
    recId: str = None
    content: str
    context: str
    question: str
    answer: str
    url: str
    user: str
    tags: List[str]

configFile = './config.json'
app = FastAPI()
# con = duckdb.connect(database='my-knowledge-center.duckdb', read_only=False)
# Fields = [('recId', 'VARCHAR', "PRIMARY KEY"), ('content', 'VARCHAR'), ('context', 'VARCHAR'),('question', 'VARCHAR'),('answer', 'VARCHAR'),('url', 'VARCHAR'),('user', 'VARCHAR'), ('tags', 'VARCHAR[]')]
# con.execute('SHOW TABLES')
# tables = con.fetchall()
# tables = [item[0] for item in tables]
# if 'knowledge' in tables:
#     con.execute('DROP TABLE knowledge')
# con.execute('CREATE SEQUENCE IF NOT EXISTS seq_rec_id START 1;')
# con.execute(f"CREATE TABLE IF NOT EXISTS knowledge({', '.join([' '.join(list(field)) for field in Fields])})")
# Test for duckDB query
# con.execute("SELECT * FROM knowledge")
# print(con.fetchall())
@app.post("/api/data")
def save_data(data: RAGdata):
    rec = data.__dict__
    del rec['recId']
    redis_connection.publish(CHANNEL_NAME, json.dumps(rec))
    # contentTree = html.fromstring(data.content)
    # mainText = extract(contentTree)
    # data.content = mainText
    # rec = []
    # for field in Fields:
    #     if field[0] == 'recId':
    #         continue
    #     rec.append(getattr(data, field[0]))
    # insertCmd = f"INSERT INTO knowledge ({','.join(field[0] for field in Fields if field[0]!='recId')}) VALUES (?, ?, ?, ?, ?, ?, ?)"
    
    # con.execute(insertCmd, rec)
    # con.execute("PRAGMA create_fts_index('knowledge', 'recId', 'context', 'question', overwrite=1)")
    return {'status': 200}

@app.put("/api/data")
def update_data(data: RAGdata):
    updateField = []
    updateData = {}
    # for field in Fields:
    #     if field[0] not in ['context', 'question', 'answer']:
    #         continue
    #     updateField.append(f"{field[0]}=${field[0]}")
    #     updateData[field[0]] = getattr(data, field[0])
      
    # updateCmd = f"UPDATE knowledge SET {','.join(updateField)} WHERE recId={data.recId}"
    
    # con.execute(updateCmd, updateData)
    # con.execute("PRAGMA create_fts_index('knowledge', 'recId', 'context', 'question', overwrite=1)")
    return {'status': 200}

@app.get("/api/data")
def get_data(page: int, pageSize: int):
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
            
    # con.execute(f"SELECT * FROM knowledge LIMIT {pageSize} OFFSET {offset}")
    # data = con.fetchall()
    # for item in data:
    #     rec = {}
    #     for idx, field in enumerate(Fields):
    #         rec[field[0]] = item[idx]
    #     recs.append(rec)
    return {'status': 200, 'data': json.dumps(recs)}

@app.delete("/api/data")
def delete_data(recIds: str):
    browser_table.delete(f"recId IN ({recIds})")
    # delIds = recIds.split(',')
    # con.execute(f"DELETE FROM knowledge WHERE recId IN ({','.join(['?' for _ in range(len(delIds))])})", delIds)
    return {'status':200}

@app.get("/api/num_of_data")
def num_of_data():
    return {'status': 200, 'data': len(browser_table)}

@app.get("/api/search")
def get_data(q: str, tags: str):
    # tagList = tags.split(',')
    # if len(q) > 0:
    #     searchSQL = f'''
    #     SELECT *, score
    #     FROM (
    #         SELECT *, fts_main_knowledge.match_bm25(
    #             recId,
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
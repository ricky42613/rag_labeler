from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import json
from trafilatura import extract
from lxml import html
import duckdb
from typing import List
import os
class Tags(BaseModel):
    tags: List[str]

class RAGdata(BaseModel):
    recId: int | None = None
    content: str
    context: str
    question: str
    answer: str
    url: str
    user: str
    tags: List[str]

configFile = './config.json'
app = FastAPI()
con = duckdb.connect(database='my-knowledge-center.duckdb', read_only=False)
Fields = [('recId', 'INT', "DEFAULT nextval('seq_rec_id')", "PRIMARY KEY"), ('content', 'VARCHAR'), ('context', 'VARCHAR'),('question', 'VARCHAR'),('answer', 'VARCHAR'),('url', 'VARCHAR'),('user', 'VARCHAR'), ('tags', 'VARCHAR[]')]
con.execute('SHOW TABLES')
tables = con.fetchall()
tables = [item[0] for item in tables]
# if 'knowledge' in tables:
#     con.execute('DROP TABLE knowledge')
con.execute('CREATE SEQUENCE IF NOT EXISTS seq_rec_id START 1;')
con.execute(f"CREATE TABLE IF NOT EXISTS knowledge({', '.join([' '.join(list(field)) for field in Fields])})")
# Test for duckDB query
# con.execute("SELECT * FROM knowledge")
# print(con.fetchall())
@app.post("/api/data")
def save_data(data: RAGdata):
    """Get segmentation maps from image file"""
    contentTree = html.fromstring(data.content)
    mainText = extract(contentTree)
    data.content = mainText
    rec = []
    for field in Fields:
        if field[0] == 'recId':
            continue
        rec.append(getattr(data, field[0]))
    insertCmd = f"INSERT INTO knowledge ({','.join(field[0] for field in Fields if field[0]!='recId')}) VALUES (?, ?, ?, ?, ?, ?, ?)"
    
    con.execute(insertCmd, rec)
    con.execute("PRAGMA create_fts_index('knowledge', 'recId', 'context', 'question', overwrite=1)")
    return {'status': 200}

@app.put("/api/data")
def update_data(data: RAGdata):
    updateField = []
    updateData = {}
    for field in Fields:
        if field[0] not in ['context', 'question', 'answer']:
            continue
        updateField.append(f"{field[0]}=${field[0]}")
        updateData[field[0]] = getattr(data, field[0])
      
    updateCmd = f"UPDATE knowledge SET {','.join(updateField)} WHERE recId={data.recId}"
    
    con.execute(updateCmd, updateData)
    con.execute("PRAGMA create_fts_index('knowledge', 'recId', 'context', 'question', overwrite=1)")
    return {'status': 200}

@app.get("/api/num_of_data")
def num_of_data():
    """Get segmentation maps from image file"""
    con.execute("SELECT COUNT(*) FROM knowledge")
    numOfData = con.fetchall()[0][0]
    return {'status': 200, 'data': numOfData}

@app.get("/api/data")
def get_data(page: int, pageSize: int):
    """Get segmentation maps from image file"""
    offset = pageSize * (page-1)
    con.execute(f"SELECT * FROM knowledge LIMIT {pageSize} OFFSET {offset}")
    data = con.fetchall()
    recs = []
    for item in data:
        rec = {}
        for idx, field in enumerate(Fields):
            rec[field[0]] = item[idx]
        recs.append(rec)
    return {'status': 200, 'data': json.dumps(recs)}

@app.delete("/api/data")
def delete_data(recIds: str):
    delIds = recIds.split(',')
    con.execute(f"DELETE FROM knowledge WHERE recId IN ({','.join(['?' for _ in range(len(delIds))])})", delIds)
    return {'status':200}
@app.get("/api/search")
def get_data(q: str):
    """Get segmentation maps from image file"""
    searchSQL = f'''
    SELECT *, score
    FROM (
        SELECT *, fts_main_knowledge.match_bm25(
            recId,
            '{q}'
        ) AS score
        FROM knowledge
    ) sq
    WHERE score IS NOT NULL
    ORDER BY score DESC LIMIT 10;'''
    con.execute(searchSQL)
    data = con.fetchall()
    recs = []
    for item in data:
        rec = {}
        for idx, field in enumerate(Fields):
            rec[field[0]] = item[idx]
            rec['score'] = item[-1]
        recs.append(rec)
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
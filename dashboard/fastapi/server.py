from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import json
from datetime import datetime
from trafilatura import extract
from lxml import html
import duckdb

class RAGdata(BaseModel):
    content: str
    context: str
    question: str
    answer: str
    url: str
    user: str

app = FastAPI()
con = duckdb.connect(database='my-knowledge-center.duckdb', read_only=False)
Fields = [('recId', 'INT', "DEFAULT nextval('seq_rec_id')"), ('content', 'VARCHAR'), ('context', 'VARCHAR'),('question', 'VARCHAR'),('answer', 'VARCHAR'),('url', 'VARCHAR'),('user', 'VARCHAR')]
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
    rec = [getattr(data, field[0]) for field in Fields if field[0] != 'recId']
    insertCmd = f"INSERT INTO knowledge ({','.join(field[0] for field in Fields if field[0]!='recId')}) VALUES (?, ?, ?, ?, ?, ?)"
    con.execute(insertCmd, rec)
    con.execute("PRAGMA create_fts_index('knowledge', 'recId', 'context', 'question')")
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
from bytewax import operators as op
from bytewax.dataflow import Dataflow
from redis_input import *
from model import EmbeddingModelSingleton
from db_output import DBOutput
from data import RAGdata
import json
def parse_rec(msg):
    rec = json.loads(msg, object_hook=lambda d: RAGdata(**d))
    if type(rec) != list:
        rec = [rec]
    return rec


flow = Dataflow("rag-pipeline")
model_name = 'intfloat/multilingual-e5-small'
max_length = 512
encoder = EmbeddingModelSingleton(model_path=model_name, max_input_length=max_length, device="cpu")
print('Waiting input!')
stream = op.input("input", flow, RedisInput())
stream = op.flat_map("parse", stream, lambda msg: parse_rec(msg))
stream = op.map("maintext", stream,lambda record: record.extract_maintext())
stream = op.map("embedding", stream ,lambda record: record.encode(encoder))
op.output("output", stream, DBOutput("knowledge-base", table_name='browser', dimension=384))
from bytewax import operators as op
from bytewax.dataflow import Dataflow
from redis_input import *

flow = Dataflow("rag-pipeline")
stream = op.input("input", flow, RedisInput())
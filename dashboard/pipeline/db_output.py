from typing import List
from bytewax.outputs import DynamicSink, StatelessSinkPartition
import lancedb
import pyarrow as pa
import uuid

class DBSink(StatelessSinkPartition):
    def __init__(self, table, fields) -> None:
        self.table = table
        self.fields = fields
    def write_batch(self, recs):
        batch_data = []
        for rec in recs:
            data = {}
            data['recId'] = str(uuid.uuid4())
            for f in self.fields:
                if f == 'recId':
                    continue
                data[f] = getattr(rec, f)
            batch_data.append(data)
        self.table.add(batch_data)
        print(len(self.table))


class DBOutput(DynamicSink):
    def __init__(self, uri, table_name, dimension) -> None:
        self.db = lancedb.connect(uri)
        self.fields = ['recId', 'content', 'context', 'question', 'answer', 'url', 'user', 'tags', 'embedding']
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
        self.table = self.db.create_table(table_name, schema=schema, exist_ok=True)
        if len(self.table) > 256:
            self.table.create_index(metric="cosine", vector_column_name="embedding", replace=True, num_partitions=self.partition_num)
    def build(self, worker_index, worker_count):
        return DBSink(self.table, self.fields)
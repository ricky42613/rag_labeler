from bytewax.outputs import DynamicSink, StatelessSinkPartition
import lancedb
import pyarrow as pa

class LanceDBSink(StatelessSinkPartition):
    def __init__(self) -> None:
        pass

class LanceDBOutput(DynamicSink):
    def __init__(self, uri, table_name, dimension) -> None:
        self.db = lancedb.connect(uri)
        schema = pa.schema([
            pa.field("vector", pa.list_(pa.float32(), dimension)),
            pa.field("rec_id", pa.int32),
        ])
        self.table = self.db.create_table(table_name, schema=schema, exist_ok=True)
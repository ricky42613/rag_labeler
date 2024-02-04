from bytewax.inputs import FixedPartitionedSource, StatefulSourcePartition
import redis
import os

class RedisSource(StatefulSourcePartition):
    def __init__(self, host, port, channel):
        r = redis.Redis(host=host, port=port)
        self.pubSubscribe = r.pubsub(ignore_subscribe_messages=True)
        self.channel = channel
        self.pubSubscribe.subscribe(self.channel)
    
    def next_batch(self, sched):
        message = self.pubSubscribe.get_message()
        if message is None:
            return []
        data = message['data']
        if isinstance(data, bytes):
            data = data.decode('utf-8')
        return [data]
    def snapshot(self):
        return None
    
    def close(self):
        self.pubSubscribe.close()
    
    def next_awake(self):
        return None # called next_batch immediately

class RedisInput(FixedPartitionedSource):
    def __init__(self) -> None:
        self.redis_host = os.getenv('REDIS_HOST', 'localhost')
        self.redis_port = os.getenv('REDIS_PORT', '6379')
        self.channel_name = os.getenv('REDIS_CHANNEL_NAME', 'extension')

    def list_parts(self):
        return ['single-part']
    
    def build_part(self, now, for_part, resume_state):
        return RedisSource(self.redis_host, self.redis_port, self.channel_name)


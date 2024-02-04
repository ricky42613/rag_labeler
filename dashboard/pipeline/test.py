import json
import logging
import os

import redis



# Configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
CHANNEL_NAME = os.getenv('REDIS_CHANNEL_NAME', 'extension')

# Connect to Redis
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
with open('test.json', 'r') as f:
    data = json.load(f)
r.publish(CHANNEL_NAME, json.dumps(data))

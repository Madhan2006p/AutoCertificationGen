from redis import Redis
from rq import Worker, Queue, Connection
import os

# Get Redis URL from environment or default to localhost
msg = "Connecting to Redis..."
print(msg)
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
conn = Redis.from_url(redis_url)

if __name__ == "__main__":
    with Connection(conn):
        print("Worker started")
        worker = Worker(["default"])
        worker.work()

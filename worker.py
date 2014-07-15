from redis import Redis
import os

redis = Redis(os.environ['REDIS_HOST'])

def process_queue_items():
    while 1:
        msg = redis.blpop('titles_queue')
        try:
            print msg
            # do some real work
        except Exception, e:
            print e

if __name__ == '__main__':
    process_queue_items()
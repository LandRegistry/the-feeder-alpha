from redis import Redis
import os, sys,  time, urlparse, json, logging
import requests

#TODO move config out. This is a mess make this into proper package with config and test config
url = urlparse.urlparse(os.environ.get('REDIS_HOST'))
queue_key = os.environ.get('REDIS_QUEUE_KEY')

#public_api = os.environ.get('PUBLIC_TITLES_API') I think this is on the way out

public_search_api = os.environ.get('PUBLIC_SEARCH_API')
authenticated_search_api = os.environ.get('AUTHENTICATED_SEARCH_API')
# Assumption is that Elastic search for these two are on different domains

#TODO when config cleaned and package created can move this to init?
queue = Redis(host=url.hostname, port=url.port, password=url.password)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()
logger.addHandler(logging.StreamHandler())

def  authenticated_filter(message):
        payload = message[1].replace('\'', '\"')
        json_data = json.loads(payload)
        return json_data

#TODO change this to excluded explicitly rather
# than include
def public_filter(message):
    payload = message[1].replace('\'', '\"')
    json_data = json.loads(payload)
    title_number = json_data.get('title_number')
    property_details = json_data.get('property')
    address = property_details.get('address')
    payment = json_data.get('payment')

    public_title = {"title_number": title_number,
          "house_number" : address.get('house_number'),
          "road" : address.get('road'),
          "town" : address.get('town'),
          "postcode" : address.get('postcode'),
          "price_paid": payment.get('price_paid')
    }
    return public_title

class Worker(object):

    def __init__(self, feed_url, filter):
        self.feed_url = feed_url
        self.filter = filter

    def do_work(self, message):
        try:
            data = self.filter(message)
            logger.info("Filtered data %s from message %s" % (data, message))
            self.send(data)
        except:
            e = sys.exc_info()[0]
            logger.error("Error extracting data from %s : Error %s" % (message, e))

    def send(self, data):
        headers = {"Content-Type": "application/json"}
        try:
            payload = json.dumps(data)
            response = requests.put(self.feed_url,  data=payload, headers=headers)
            logger.info("PUT data %s to URL %s : status code %s'" %  (data, self.feed_url, response.status_code))
        except requests.exceptions.RequestException as e:
            logger.error("Error sending %s to %s: Error %s" % (data, self.feed_url, e))
        except:
            e = sys.exc_info()[0]
            logger.error("Error extracting data from %s : Error %s" % (data, e))


class Consumer(object):

    def __init__(self, queue, queue_key, workers):
        self.queue = queue
        self.queue_key = queue_key
        self.workers = workers

    def run(self):
        while True:
            logger.info("Public titles worker awaiting data from  %s'" %  self.queue)
            message = self.get_next_message()
            logger.info("Public titles worker received data %s from  %s'" %  (message, self.queue))
            for worker in workers:
                worker.do_work(message)
                time.sleep(2)

    def get_next_message(self):
        return self.queue.blpop(self.queue_key)


if __name__ == '__main__':

    workers = []
    workers.append(Worker(public_search_api, public_filter))
    workers.append(Worker(authenticated_search_api, authenticated_filter))

    consumer = Consumer(queue, queue_key, workers)
    consumer.run()


import sys
import json
import requests
import cPickle as pickle

from thefeeder import logger


class FeedWorker(object):
    def __init__(self, feed_url, filter):
        self.feed_url = feed_url
        self.filter = filter

    def do_work(self, message):
        try:
            data = self.filter(message)
            logger.info("Filtered data %s from message" % (data))
            self.send(data)
        except pickle.UnpicklingError as e:
            logger.error("Error extracting data from message", exc_info=e)

    def send(self, data):
        if not data:
            return
        headers = {"Content-Type": "application/json"}
        try:
            payload = json.dumps(data)

            # todo: all apis should accept put at /titles
            if '<title_number>' in self.feed_url:
                self.feed_url = self.feed_url.replace('<title_number>', data['title_number'])

            response = requests.put(self.feed_url, data=payload, headers=headers)
            logger.info("PUT to URL %s, status code %s, payload %s" % (self.feed_url, response.status_code, payload))
        except requests.exceptions.RequestException as e:
            logger.error("Error sending %s to %s: Error %s" % (data, self.feed_url, e))
        except:
            e = sys.exc_info()[0]
            logger.error("Error extracting data from %s : Error %s" % (data, e))

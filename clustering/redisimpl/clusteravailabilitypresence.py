
import redis
import logging
import time
import json

from threading import Timer


logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s', level=logging.DEBUG)

class ClusterAvailability(object):


    def __init__(self, redis, server_id, url, presence_interval):

        self.redis = redis
        self.server_id = server_id
        self.channel_name = "cluster_management_channel"
        self.presence_interval = presence_interval

        self.server_status = dict()
        self.server_status['id'] = server_id
        self.server_status['ordinal'] = -1
        self.server_status['timestamp_epoch'] = time.time()
        self.server_status['url'] = url
        # logging.info("Server %s status = %s.", self.server_id, json.dumps(self.server_status))
        self.first = True


    def status(self):
        self.server_status['timestamp_epoch'] = time.time()
        return json.dumps(self.server_status)

    def set_ordinal(self, ordinal):
        self.server_status['ordinal'] = ordinal

    def publishClusterPresence(self):

        if self.first :
            logging.info("%s starts claiming presence in cluster with ordinal %d", \
                            self.server_id, self.server_status['ordinal'])
            self.first = False

        if -1 != self.server_status['ordinal'] :
            self.redis.publish(self.channel_name, self.status())

        self.timer = Timer(self.presence_interval, self.publishClusterPresence )
        self.timer.start()

#!/usr/bin/python

from flask import Flask, request, redirect
from flask_restful import Resource, Api
from json import dumps
# from flask.ext.jsonpify import jsonify
from flask_jsonpify import jsonify
from sqlalchemy import create_engine

import sys

import redis
import logging

from Queue import Queue

from uribasedid import URIBasedIDBuilder
from clustering.redisimpl import ClusterAvailabilityCheck, ClusterAvailability


default_port                = 30500
must_redirect               = False
redirection_url             = "http://series-manager-demo-lab-env.wziem3322e.eu-west-2.elasticbeanstalk.com/"
flask_default_port          = 5000
server_id                   = ''
service_path                = '/series'
server_url                  = ''
cluster_availability_check  = None


class SeriesManagerServer(Resource):

    def __init__(self):
        self.__name__ = "application"

    def get(self):

        if cluster_availability_check :
            if cluster_availability_check.is_master() :
                logging.info("MASTER: replying ...")
                conn = db_connect.connect()
                query = conn.execute("select * from series")
                return {'series': [i[0] for i in query.cursor.fetchall()]}

            else :
                logging.info("master url to redirect = %s", cluster_availability_check.get_master_url() )
                return redirect(cluster_availability_check.get_master_url(), code=302)
        else :
            logging.info("Redirection to %s", redirection_url )
            return redirect(redirection_url + service_path, code=302)


#    def set_cluster_availability_check(self, _cluster_availability_check_ ):
#        self.cluster_availability_check = _cluster_availability_check_
#        logging.info("Setting %s", self.cluster_availability_check )




# Local : ./series-manager-server.py 30501
# Local or remote : ./series-manager-server.py
# Tests with :  curl -vL http://localhost:30501/series
#               wget http://localhost:30501/series
#               curl http://series-manager-demo-lab-env.wziem3322e.eu-west-2.elasticbeanstalk.com/series

application = Flask(__name__)
flask_rest_api = Api(application)
db_connect = create_engine('sqlite:///./series.db')

series_manager_server = SeriesManagerServer()
flask_rest_api.add_resource(series_manager_server, "/series")


# ID instance 1 :   30501 05298d9d-7efb-432e-9aa0-30cfdf97e939
#                   ./series-manager-server-ft.py 30501 05298d9d-7efb-432e-9aa0-30cfdf97e939
# ID instance 2 :   30502 a34e172a-c11c-4252-b5ac-9f1e48825ac1
#                   ./series-manager-server-ft.py 30502 a34e172a-c11c-4252-b5ac-9f1e48825ac1

_redis_ = redis.StrictRedis(host='127.0.0.1', port=6379)
queue_check = Queue()


if __name__ == '__main__':

    logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s', level=logging.DEBUG)
    if 1 < len(sys.argv) :
        # Local deployment, redirect.
        must_redirect = True
        server_id = URIBasedIDBuilder.build(sys.argv[2], "127.0.0.1", sys.argv[1], service_path )
        server_url = URIBasedIDBuilder.url("127.0.0.1", sys.argv[1], service_path )
        logging.info("server id = %s", server_id)

        try :
            # Starts the cluster management check routine; Should rely queue between threads.
            cluster_availability_check = ClusterAvailabilityCheck(_redis_, server_id, server_url, queue_check, 10)
            cluster_availability_check.daemon = True
            cluster_availability_check.start()

            cluster_availability = ClusterAvailability(_redis_, server_id, server_url, 10)
            cluster_availability_check.set_cluster_availability( cluster_availability )

            # series_manager_server.set_cluster_availability_check( cluster_availability_check )

            application.run(port=sys.argv[1])

        except KeyboardInterrupt :
            logging.info("That's all folks.")

    else :
        # Remote deployment: do not redirect.
        application.run()

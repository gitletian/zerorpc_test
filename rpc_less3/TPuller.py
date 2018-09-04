# coding: utf-8
# __author__: ""

import zerorpc
import gevent
from gevent import event


endpoint = "tcp://0.0.0.0:4243"
trigger = event.Event()


class Puller(zerorpc.Puller):
    def lolita(self, a, b):
        print('lolita', a, b)
        print(a + b)
        trigger.set()


puller = Puller()
puller.connect(endpoint)
puller.run()

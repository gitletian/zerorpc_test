# coding: utf-8
# __author__: ""

import zerorpc
from gevent import event

endpoint = "tcp://0.0.0.0:4243"
pusher = zerorpc.Pusher()
pusher.bind(endpoint)

trigger = event.Event()

trigger.clear()
pusher.lolita(1, 4)
trigger.wait()
print('done')





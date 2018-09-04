# coding: utf-8
# __author__: ""


import gevent
import gevent.event
import zerorpc


def test_pushpull_inheritance():
    endpoint = "tcp://0.0.0.0:4243"

    pusher = zerorpc.Pusher()
    pusher.bind(endpoint)
    trigger = gevent.event.Event()

    class Puller(zerorpc.Puller):
        def lolita(self, a, b):
            print('lolita', a, b)
            assert a + b == 3
            trigger.set()

    puller = Puller()
    puller.connect(endpoint)
    gevent.spawn(puller.run)

    trigger.clear()
    pusher.lolita(1, 2)
    trigger.wait()
    print('done')

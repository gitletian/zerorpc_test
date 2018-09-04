# coding: utf-8
# __author__: ""

import zerorpc

endpoint = "tcp://0.0.0.0:4243"
from gevent import event
import gevent


def test_pubsub_inheritance():

    publisher = zerorpc.Publisher()
    publisher.bind(endpoint)
    trigger = gevent.event.Event()

    class Subscriber(zerorpc.Subscriber):
        def lolita(self, a, b):
            print('lolita', a, b)
            trigger.set()

    subscriber = Subscriber()
    subscriber.connect(endpoint)
    gevent.spawn(subscriber.run)

    trigger.clear()
    # We need this retry logic to wait that the subscriber.run coroutine starts
    # reading (the published messages will go to /dev/null until then).
    for attempt in range(0, 10):
        print("====", attempt)
        publisher.lolita(1, 2)
        if trigger.wait(0.2):
            print('done')
            return

    raise RuntimeError("The subscriber didn't receive any published message")

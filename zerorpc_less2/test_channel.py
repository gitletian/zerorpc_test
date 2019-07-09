# -*- coding: utf-8 -*-
# Open Source Initiative OSI - The MIT License (MIT):Licensing
#
# The MIT License (MIT)
# Copyright (c) 2015 François-Xavier Bourlet (bombela+zerorpc@gmail.com)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
'''
    zmq.ROUTER   socket 的类型

    REQ-REP模式: 请求回复模式，REQ请求然后等待响应。REQ监听然后回复:  REQ: REP 是 N:1 的关系(顺序处理)
        REQ方先发后收，send-recv。REP方先收后发，recv-send。REQ和REP不停的重复它们的操作循环。
        REP类似于一个http服务器，REQ类似于客户端。一个REP可以连接多个REQ端，REP顺序处理REQ的请求。
        如果你看zeromq代码会发现REQ是 DEALER 的子类，REP是 OUTER 的子类

    PUSH-PULL模式: 推拉模式，PUSH发送，send。PULL方接收，recv. PUSH: PULL 是 1:N 的关系(顺序处理)
        PUSH可以和多个PULL建立连接，PUSH发送的数据被顺序发送给PULL方。比如你PUSH和三个PULL建立连接，分别是A,B,C。
        PUSH发送的第一数据会给A,第二数据会给B，第三个数据给C，第四个数据给A。一直这么循环。
        这个类似现实中的发牌，PUSH是发牌方，PUSH顺序给每个PULL发牌。顺序代表发完一个发另一个，不能同时进行。
        push会负载均衡的将消息分发到pull端。push端无法recv，pull无法send。

    PUB-SUB模式: 发布订阅模式。PUB发送,send。SUB接收，recv。PUB: SUB 是 1: N 的关系(非顺序)
        和PUSH-PULL模式不同，PUB将消息同时发给和他建立的链接，类似于广播。另外发布订阅模式也可以使用订阅过滤来实现只接收特定的消息。
        订阅过滤是在服务器上进行过滤的，如果一个订阅者设定了过滤，那么发布者将只发布满足他订阅条件的消息。
        这个就是广播和收听的关系。PUB-SUB模式虽然没有使用网络的广播功能，但是它内部是异步的。也就是一次发送没有结束立刻开始下一次发送。
        如果存在某个pub没有被任何sub连接，则该pub会丢弃所有的消息

    DEALER-ROUTER模式: 代理模式，这种模式主要用于扩容 REQ-REP 模式的。如果你需要扩容多个 REP 服务器。那么就可以用代理模式。
        REQ: REP 是 N:N 的关系(顺序处理)

        ROUTER 对应于REQ，它相当于一个REP服务器，执行先收后发，recv-send循环。
        但是内部它将前端REQ的请求收进来，然后将请求发给 DEALER，DEALER接收 ROUTER 的消息，将消息发送给REP，只不过 DEALER 面对的是N个REP。
        通过代理模式的改造，REQ-REP将具有自动扩容能力。
        DEALER-ROUTER 模式都是异步的，如果将这个机制整合在一起运作。类似于一个异步的接线员，是一个 N对接线员 对M的链接 拓扑关系。
        它将N个REQ请求链接到M个REQ上。并且保证它们是负载均衡的。

    PAIR-PAIR模式: 配对模式，主要用于inproc进行进程内的通信
        你可以在一个线程中调用recv等在哪里，另一个进程使用send来让接收线程继续。这种模式类型与信号灯。

    总结:
        某些zeromq模式中的收发顺序模式，既不能打乱也不能省略。比如你不能用SUB进行发送将引发错误。
        REP模式也不能省略recv-send中的任何一个，不能跳过recv直接进行send，这都将引发错误。
        另外zeromq不能为你实现其他的协议，比如你不能用zeromq实现一个HTTP服务器，zeromq有自己的传输协议，
        或者说zeromq有自己的协议用来使上面的模式运作。
'''


from __future__ import print_function
from __future__ import absolute_import
from builtins import range

from zerorpc import zmq
import zerorpc

endpoint = "tcp://0.0.0.0:4243"
TIME_FACTOR = 0.2


def test_events_channel_client_side():
    '''
    测试 channel
    :return:
    '''

    # 创建 server events
    server_events = zerorpc.Events(zmq.ROUTER)
    server_events.bind(endpoint)
    server = zerorpc.ChannelMultiplexer(server_events)

    # 穿件 client events
    client_events = zerorpc.Events(zmq.DEALER)
    client_events.connect(endpoint)
    client = zerorpc.ChannelMultiplexer(client_events)

    # 向 chanel 提交 信息
    client_channel = client.channel()
    client_channel.emit('someevent', (42,))

    # server 接受 信息
    event = server.recv()
    print(event)
    assert list(event.args) == [42]
    assert event.identity is not None

    # 创建 新的 event, 并回复
    reply_event = server.new_event('someanswer', (21,), xheader={'response_to': event.header['message_id']})
    reply_event.identity = event.identity
    server.emit_event(reply_event)
    event = client_channel.recv()
    assert list(event.args) == [21]


def test_events_channel_client_side_server_send_many():
    server_events = zerorpc.Events(zmq.ROUTER)
    server_events.bind(endpoint)
    server = zerorpc.ChannelMultiplexer(server_events)

    client_events = zerorpc.Events(zmq.DEALER)
    client_events.connect(endpoint)
    client = zerorpc.ChannelMultiplexer(client_events)

    client_channel = client.channel()
    client_channel.emit('giveme', (10,))

    event = server.recv()
    print(event)
    assert list(event.args) == [10]
    assert event.identity is not None

    for x in range(10):
        reply_event = server.new_event('someanswer', (x,), xheader={'response_to': event.header['message_id']})
        reply_event.identity = event.identity
        server.emit_event(reply_event)
    for x in range(10):
        event = client_channel.recv()
        assert list(event.args) == [x]


def test_events_channel_both_side():
    server_events = zerorpc.Events(zmq.ROUTER)
    server_events.bind(endpoint)
    server = zerorpc.ChannelMultiplexer(server_events)

    client_events = zerorpc.Events(zmq.DEALER)
    client_events.connect(endpoint)
    client = zerorpc.ChannelMultiplexer(client_events)

    client_channel = client.channel()
    client_channel.emit('openthat', (42,))

    event = server.recv()
    print(event)
    assert list(event.args) == [42]
    assert event.name == 'openthat'

    server_channel = server.channel(event)
    server_channel.emit('test', (21,))

    event = client_channel.recv()
    assert list(event.args) == [21]
    assert event.name == 'test'

    server_channel.emit('test', (22,))

    event = client_channel.recv()
    assert list(event.args) == [22]
    assert event.name == 'test'

    server_events.close()
    server_channel.close()
    client_channel.close()
    client_events.close()

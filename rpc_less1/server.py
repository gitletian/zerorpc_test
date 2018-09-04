# coding: utf-8
# __author__: ""
import pdb
import zerorpc
import time

###################################################### 单 RPC ##################################################################
class HelloRPC(object):
    def hello(self, name):
        return "Hello, %s" %name

    def hello2(self, name):
        return "哇塞, %s" % name


def reserve1(qq):
    return "呵呵, %s " % qq


def reserve2(qq):
    return "嘿嘿, %s " % qq


###########################################################  RPC streaming #####################################################
class StreamingRPC(object):
    @zerorpc.stream
    def streaming_range(self, fr, to, step):
        print("------call--------%s" % type(list(range(fr, to, step))))
        # 以 generator 形式返回
        time.sleep(5)
        return list(range(fr, to, step))


class ExceptionRPC(object):
    def bad(self):
        raise Exception(":p")


# s = zerorpc.Server(dict(reserve1=reserve1, reserve2=reserve2))
s = zerorpc.Server(StreamingRPC())

s.bind("tcp://0.0.0.0:4242")
s.run()





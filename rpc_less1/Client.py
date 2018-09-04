# coding: utf-8
# __author__: ""
import zerorpc


c = zerorpc.Client("tcp://127.0.0.1:4242")

# print(c.reserve2("郭元培"))

t = c('streaming_range', 10, 20, 2, async=True)
print(type(t))
print("=============== midd ===============")


for item in c.streaming_range(10, 20, 2):
    print(item)

print("============end===========")

print("=============== midd2 ===============")
tt = t.get()
print(type(tt))



# try:
#     c.bad()
# except Exception as e:
#     print(" An error occurred : %s" % e.msg)

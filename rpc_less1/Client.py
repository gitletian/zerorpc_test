# coding: utf-8
# __author__: ""
import zerorpc

'''
注意:
    1、如果 请求是异步的 则需要 设置方法调用为 async=True
    2、如果是同步的 则 async=False, 如果 等待时间比较长,则需要 设置 Client 为 None 或 0, timeout 为等待的预估时间

shell 运行(目前不支持 异步):
    zerorpc "tcp://172.16.1.20:4245" predict_kcc "${hdfs_data_dir}/${daterange}" "${columns}" --timeout 3600 --heartbeat 0
'''
c = zerorpc.Client("tcp://127.0.0.1:4242", timeout=60 * 60, heartbeat=None)

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

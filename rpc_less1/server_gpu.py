# coding: utf-8
from hdfs.client import Client
import os
from os.path import sep
import pynvml
import zerorpc
import shutil
from multiprocessing import Process
import functools

client = Client("http://172.16.1.13:50070;http://172.16.1.14:50070")
local_base_path = "/mnt/disk1/predict_data/predict_kcc_data"


def clear_gpc(index=3):
    '''
    清理 第 index 个 gpu 上的 应用程序
    :param index: gpu 的下标
    :return:
    '''
    pynvml.nvmlInit()
    handle = pynvml.nvmlDeviceGetHandleByIndex(index)
    progresses = pynvml.nvmlDeviceGetComputeRunningProcesses(handle)

    for progress in progresses:
        print("[@@@]    old progress pid is = " + str(progress.pid))
        os.popen('kill -9 %s' % progress.pid)

    pynvml.nvmlShutdown()


def gpu_process(async, device):
    '''
    进程装饰器, 新启一个进程进行 gpu 相关计算
    :param async: 子进程为同步还是异步
    :param device: 需要的 gpu 设备编号
    :return:
    '''
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            print('[@@@]    clear gpu device.')
            clear_gpc(device)

            print('[@@@]    Child process will start.')
            p = Process(target=func, args=args, kwargs=kwargs)
            p.start()
            if not async:
                p.join()

            print('[@@@]    Child process end.')
        return wrapper
    return decorator


def hdfs_to_local(hdfs_path, columns):
    '''
    下载 hdfs 文件夹 到 本地
    :param hdfs_path:  hdfs 文件路径
    :param columns:  列信息
    :return: 本地文件路径
    '''
    file_name = os.path.basename(hdfs_path)
    file_path = sep.join([local_base_path, file_name])
    local_file = "{}.csv".format(file_path)

    if not os.path.exists(local_base_path):
        os.makedirs(local_base_path)

    if os.path.exists(file_path):
        shutil.rmtree(file_path)

    if os.path.exists(local_file):
        os.remove(local_file)

    client.download(hdfs_path, file_path)
    # 合并文件
    os.system("cat {0}/* >> {1}".format(file_path, local_file))

    # 添加列信息
    if columns:
        os.system("sed -i '1 i {0}' {1}".format(columns, local_file))

    return local_file


def local_to_hdfs(hdfs_path, local_file):
    '''
    上传 预测结果到 hdsf
    :param local_path:
    :param hdfs_path:
    :return:
    '''
    # 会覆盖旧文件 temp_dir
    print('[@@@]    upload to hdfs  {0}.pre     {1}'.format(hdfs_path, local_file))
    client.upload(hdfs_path + ".pre", local_file, temp_dir='/tmp/data', overwrite=True)


@gpu_process(False, 3)
def gpu_predict(local_file):
    '''
    调用预测脚本开始预测
    :param local_file: 需要预测的路径
    :return:
    '''
    print("[@@@]    predict begin ..........")

    import tensorflow as tf
    from model import Model, sess_holder
    hparam = tf.contrib.training.HParams(
        # model
        batch_size=1000,
        n_epoch=15,
        n_classes=3,
        learning_rate=0.001,
        l2_reg=0.001,
        dropout_keep=0.5,
        max_len=280,
        embedding_size=300,
        lstm_hiddeen_size=300,

        evalute_every=200,
        decay_schema=None,
        mode='trai',
        encoder='matdmn',
        restore=False,
        train_file='/mnt/disk2/data/xly/data/myownsenti/kcc_train0627.csv',
        valid_file='/mnt/disk2/data/xly/data/myownsenti/kcc_test0627.csv',
        test_file=local_file,
        # save_dir='../checkpoints',
        save_dir='../checkpoints/matdmn1561617804/1561618348',

        embedding_file='/mnt/disk2/data/xly/data/myownsenti/vector/general-300-kcc-0624.txt'
    )
    model = Model(hparam)
    model.inference()

    print("[@@@]    predict end ")


def predict_kcc(hdfs_path, columns=None):
    '''
    预测 kcc
    :param hdfs_path:
    :param columns:
    :return:
    '''
    if not isinstance(hdfs_path, str):
        hdfs_path = hdfs_path.decode(encoding="utf-8")
        columns = columns.decode(encoding="utf-8")

    local_file = hdfs_to_local(hdfs_path, columns)
    gpu_predict(local_file)
    local_to_hdfs(hdfs_path, local_file)

    print("[@@@]    predict result hdfs path is: {0}.pre".format(hdfs_path))


if __name__ == '__main__':
    s = zerorpc.Server(dict(predict_kcc=predict_kcc))
    s.bind("tcp://0.0.0.0:4245")
    s.run()




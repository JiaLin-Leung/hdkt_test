# encoding: utf-8
import time


# 思路：
# 1，循环中查询tbkt_base.mobile_subject_detail_hn这个表里面已开通的用户，每次500个，每天循环100次，共5万人；
# 2，将第一步查出来的数据，逐一拿到对应参数参数，请求接口：http://mapiboss.m.tbkt.cn/open_status/
# 3，将第二步的请求结果进行处理（具体处理方式）
# 4，将处理完毕的数据进行对比，拿到数据不一致的用户写到一个表里面（建表关键字段：循环次数，查询日期）
def loop():
    a = 1
    while a <= 10:
        print "这是第%s次循环" % a
        a += 1
    return


if __name__ == '__main__':
    time1 = int(time.time())
    loop()
    time2 = int(time.time())
    print ("数据耗时:%s" % (time2 - time1))


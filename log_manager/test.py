# -*- coding: utf-8 -*-

import json
from elasticsearch import Elasticsearch
import datetime
import time
import requests
import urllib

def scroll_test():
    hosts = [{'host': '10.130.44.108', 'port': 9200}]
    es = Elasticsearch(hosts=hosts)

    start_time = datetime.datetime.strptime('2018-07-28 00:00:00', '%Y-%m-%d %H:%M:%S')
    end_time = datetime.datetime.strptime('2019-09-01 00:00:00', '%Y-%m-%d %H:%M:%S')
    indices = ['cmslog']

    # body = {"sort": [{"@timestamp": {"order": "asc"}}], "query": {"bool": {
    #     "must": [{"match": {
    #         "event_type": "OrigLocal sgBlindMakeCallEx SgEvtRemoteAlerting SgEvtConnected SgEvtDisconnected"}},
    #         {"range": {
    #             "@timestamp": {"gte": start_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
    #                            "lte": end_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')}}}]}}}
    # print(body)
    body = {'sort': [{'@timestamp': {'order': 'asc'}}], 'query': {'bool': {'must': [
        {'match': {'event_type': 'OrigLocal sgBlindMakeCallEx SgEvtRemoteAlerting SgEvtConnected SgEvtDisconnected'}},
        {'range': {'@timestamp': {'gte': '2018-07-28T17:47:09.180000Z', 'lte': '2020-08-01T17:47:22.554000Z'}}}]}},
            'size': 1000}

    # Initialize the scroll
    page = es.search(
        index=','.join(indices),
        body=body,
        scroll='2m',  # 保持游标查询窗口2分钟
        size=1000
    )
    sid = page['_scroll_id']
    scroll_size = page['hits']['total']
    print ('total scroll_size: ', scroll_size)

    l = []
    # Start scrolling
    all_count = 0
    start_time = datetime.datetime.now()
    while scroll_size > 0:
        print ("Scrolling...")
        page = es.scroll(scroll_id=sid, scroll='2m')
        # Update the scroll ID
        sid = page['_scroll_id']
        # Get the number of results that we returned in the last scroll
        scroll_size = len(page['hits']['hits'])
        print ("scroll size: " + str(scroll_size))
        all_count = all_count + scroll_size
        print('all_count=%s' % all_count)
        # Do something with the obtained page
        docs = page['hits']['hits']
        l += [x['_source'] for x in docs]
    now = datetime.datetime.now()
    print(u'一共检索到%s满足要求的记录,用时%s(秒)' % (all_count, (now - start_time).seconds))


def time_test():
    timestamp = (int(time.time()/60)) * 60
    print(timestamp)
    begin_time = datetime.datetime.fromtimestamp(timestamp-300)
    end_time = datetime.datetime.fromtimestamp(timestamp)
    print(begin_time)
    print(end_time)
    start_time = '2019-07-12T20:16:07.904Z'
    start_time = datetime.datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%S.%fZ')
    print(start_time)
    timestamp = time.mktime(datetime.datetime.timetuple(start_time))
    print(timestamp)


def timestamp_test():
    t = time.time()
    print (t)  # 原始时间数据
    print (int(t))  # 秒级时间戳
    print (int(round(t * 1000)))  # 毫秒级时间戳

    now_time = lambda: int(round(t * 1000))
    print (now_time())


def datetime_test():
    now = datetime.datetime.now().replace(microsecond=0)
    print(now)
    delta = datetime.timedelta(minutes=10, seconds=now.second)
    begin = now - delta
    print(begin)
    delta = datetime.timedelta(minutes=5, seconds=now.second)
    end = now - delta
    print(end)


def http_test():
    body = dict()
    body['startTime'] = '2018-08-01 00:00:00'
    body['endTime'] = '2019-09-01 00:00:00'
    headers = {'content-type': "application/json"}
    url = 'http://192.168.33.10:8001/cms/sgBlindMakeCallEx/'
    response = requests.post(url, data=json.dumps(body, ensure_ascii=False), headers=headers)
    print(response.text)
    return response.text


def rest_http_test():
    start_time = '2019-08-13 14:00:00'
    end_time = '2019-08-13 14:30:00'
    # headers = {'content-type': "application/json"}
    params = 'startTime=%s&endTime=%s' % (start_time, end_time)
    # params = urllib.quote(params)
    # url = 'http://10.130.44.108:8001/apps/cms/sgBlindMakeCallEx/?%s' % params
    # url = 'http://127.0.0.1:8001/apps/cms/sgBlindMakeCallEx/?%s' % params
    url = 'http://127.0.0.1:8001/apps/cms/callDetail/?%s' % params
    # url = urllib.quote(url)
    print(url)
    response = requests.get(url)
    print(response.text)
    return response.text


def request_datetime_test():
    start_time = '2019-08-13 14:00:00'
    end_time = '2019-08-13 14:30:00'
    begin = int(time.mktime(datetime.datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S').timetuple()))
    end = int(time.mktime(datetime.datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S').timetuple()))
    print('begin=%s, end=%s' % (begin, end))


if __name__ == '__main__':
    # time_test()
    # http_test()
    # timestamp_test()
    rest_http_test()
    # datetime_test()
    # request_datetime_test()



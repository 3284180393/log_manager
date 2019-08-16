# -*- coding: utf-8 -*-

import json
from elasticsearch import Elasticsearch
import datetime
import time
import requests


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
    print 'total scroll_size: ', scroll_size

    l = []
    # Start scrolling
    all_count = 0
    start_time = datetime.datetime.now()
    while scroll_size > 0:
        print "Scrolling..."
        page = es.scroll(scroll_id=sid, scroll='2m')
        # Update the scroll ID
        sid = page['_scroll_id']
        # Get the number of results that we returned in the last scroll
        scroll_size = len(page['hits']['hits'])
        print "scroll size: " + str(scroll_size)
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


def http_test():
    body = dict()
    body['startTime'] = '2019-08-01 00:00:00'
    body['endTime'] = '2019-09-01 00:00:00'
    headers = {'content-type': "application/json"}
    url = 'http://10.130.76.106:8001/cms/sgBlindMakeCallEx/'
    response = requests.post(url, data=json.dumps(body, ensure_ascii=False), headers=headers)
    print(response.text)
    return response.text


if __name__ == '__main__':
    # time_test()
    http_test()

# -*- coding: utf-8 -*-


import datetime
from elasticsearch import Elasticsearch
import json
import logging
from models import CallingNumber
from models import DNIS
import requests
from elasticsearch.helpers import bulk
import time

LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
logging.basicConfig(filename='my.log', level=logging.DEBUG, format=LOG_FORMAT)


class BlindMakeCall:
    """
    定义cms的sgBlindMakeCallEx相关信息
    """
    def __init__(self, session_id, calling_number, dnis, start_time, platform_id, platform_name, platform_code):
        """
        初始化sgBlindMakeCallEx相关信息
        :param session_id: 通呼的session_id
        :param calling_number:sgBlindMakeCallEx的外显号
        :param dnis: sgBlindMakeCallEx的被叫
        :param start_time: 发起sgBlindMakeCallEx的时间
        resID:关联的resID
        connID:关联的connID
        callID:关联的callID
        call_result:呼叫结果
        end_time:sgBlindMakeCallEx结束时间
        """
        self.session_id = session_id
        self.start_time = start_time
        self.calling_number = calling_number
        self.dnis = dnis
        self.platform_id = platform_id
        self.platform_name = platform_name
        self.platform_code = platform_code
        self.target = None
        self.res_id = None
        self.call_id = None
        self.conn_id = None
        self.call_result = None
        self.end_time = None

    def get_call_detail(self):
        info = dict()
        info['session_id'] = self.session_id
        info['start_time'] = self.start_time
        info['end_time'] = self.end_time
        info['calling_number'] = self.calling_number.calling_number
        info['calling_number_belong_to'] = self.calling_number.belong_to
        info['calling_number_province'] = self.calling_number.province
        info['calling_number_city'] = self.calling_number.city
        info['calling_number_city_code'] = self.calling_number.city_code
        info['dnis'] = self.dnis.dnis
        info['dnis_prefix'] = self.dnis.prefix
        info['target'] = self.target
        info['dnis_isp'] = self.dnis.isp
        info['dnis_province'] = self.dnis.province
        info['dnis_city'] = self.dnis.city
        info['dnis_city_code'] = self.dnis.city_code
        info['call_result'] = self.call_result
        info['platform_id'] = self.platform_id
        info['platform_name'] = self.platform_name
        info['platform_code'] = self.platform_code
        return info


class CMSLog:
    """
    用来定义同cms的日志相关操作的类
    """
    def __init__(self, es_cluster=[{'host': '10.130.44.108', 'port': 9200}], cms_log_index='cmslog', blink_call_detail_index='cms_blink_make_call', dnis_query_url='http://paas.ccod.com/t/qn-api/phone_area/queryisp/', voip_query_url='http://paas.ccod.com/t/qn-api/phone_area/queryvoip/', platform_id='tx_cloud', platform_name=u'腾讯云平台', platform_code='010'):
        """
        初始化cms操作相关的参数
        :param es_cluster: elasticsearch集群定义
        :param cms_log_index: cms日志索引
        :param blink_call_detail_index: cms的sgBlinkMakeCallEx事件索引
        :param dnis_query_url: 查询被叫归属地信息的接口地址
        :param voip_query_url: 查询话批公司相关信息的接口地址
        """
        self.es = Elasticsearch(es_cluster)
        self.cms_log_index = cms_log_index
        self.blink_call_detail_index = blink_call_detail_index
        self.dnis_query_url = dnis_query_url
        self.voip_query_url = voip_query_url
        self.platform_id = platform_id
        self.platform_name = platform_name
        self.platform_code = platform_code

    def __get_blink_make_call(self, session_id, event_list):
        """
        从某通通话事件中恢复所有sgBlindMakeCallEx信息
        :param session_id:某通通话的session_id
        :param event_list:某通通话的所有event列表
        :return:恢复出的所有sgBlindMakeCallEx信息
        """
        conn_call_dict = dict()
        dnis_dict = dict()
        call_list = list()
        for event in event_list:
            if event['event_type'] == 'orig:CCODServices::OrigLocal':
                dnis = event['dnis']
                dnis_dict[dnis] = dict()
                dnis_dict[dnis]['calling_number'] = event['calling_number']
                dnis_dict[dnis]['dnis_type'] = event['dnis_type']
                dnis_dict[dnis]['conn_id'] = event['conn_id']
            elif event['event_type'] == '@@sgBlindMakeCallEx':
                calling_number = CallingNumber(event['calling_number'])
                dnis = DNIS(event['dnis'])
                dnis.prefix = dnis_dict[event['dnis']]['dnis_type']
                make_call = BlindMakeCall(session_id, calling_number, dnis, event['@timestamp'], self.platform_id, self.platform_name, self.platform_code)
                make_call.call_result = event['result']
                make_call.end_time = make_call.start_time
                if len(conn_call_dict) == 0:
                    make_call.target = 'AGENT'
                elif len(conn_call_dict) == 1:
                    make_call.target = 'CUSTOMER'
                else:
                    make_call.target = 'THIRD_PART'
                if event['result'] != 'GATEWAY_SUCCESS':
                    call_list.append(make_call)
                else:
                    make_call.call_id = '%s' % hex(int(event['call_id']))
                    make_call.res_id = '%s' % hex(int(event['res_id']))
                    conn_call_dict[dnis_dict[event['dnis']]['conn_id']] = make_call
            elif event['event_type'] == 'Conn':
                conn_call_dict[event['conn_id']] = conn_call_dict['%s-%s' % (event['call_id'], event['res_id'])]
                del conn_call_dict['%s-%s' % (event['call_id'], event['res_id'])]
                conn_call_dict[event['conn_id']].end_time = event['@timestamp']
            elif event['event_type'] == 'SgEvtRemoteAlerting':
                conn_call_dict[event['conn_id']].call_result = 'ALERTING'
                conn_call_dict[event['conn_id']].end_time = event['@timestamp']
            elif event['event_type'] == 'SgEvtConnected':
                conn_call_dict[event['conn_id']].call_result = 'CONNECT'
                conn_call_dict[event['conn_id']].end_time = event['@timestamp']
            elif event['event_type'] == 'SgEvtDisconnected':
                if event['conn_id'] not in conn_call_dict.keys():
                    continue
                conn_call_dict[event['conn_id']].end_time = event['@timestamp']
                if conn_call_dict[event['conn_id']].call_result == 'GATEWAY_SUCCESS':
                    conn_call_dict[event['conn_id']].call_result == 'NOT_ALERTING'
                elif conn_call_dict[event['conn_id']].call_result == 'ALERTING':
                    conn_call_dict[event['conn_id']].call_result == 'NOT_CONNECT'
                elif conn_call_dict[event['conn_id']].call_result == 'CONNECT':
                    conn_call_dict[event['conn_id']].call_result == 'CALL_SUCCESS'
            else:
                pass
        for conn_id in conn_call_dict.keys():
            call = conn_call_dict[conn_id]
            if call.call_result == 'GATEWAY_SUCCESS':
                logging.error(u'%s makecall只有网管返回GATEWAY_SUCCESS,无振铃事件' % conn_id)
                call.call_result = 'NOT_ALERTING'
            elif call.call_result == 'ALERTING':
                logging.error(u'%s makecall只有振铃事件,无接通也无挂断事件' % conn_id)
                call.call_result = 'NOT_CONNECT'
            elif call.call_result == 'CONNECT':
                logging.error(u'%s makecall只有接通事件无挂断事件' % conn_id)
                call.call_result = 'CALL_SUCCESS'
        call_list.extend(conn_call_dict.values())
        logging.info(u'%s通话一共分析出%s通@@sgBlindMakeCallEx事件' % (session_id, len(call_list)))
        return call_list

    def check_blink_call(self, start_time, end_time):
        """
        检查某个时间段里面cms发生的所有sgBlindMakeCallEx相关信息
        :param start_time:开始时间
        :param end_time:结束时间
        :param es_host:es的host ip地址
        :param es_port:es的port端口
        :return:该时间段发生的sgBlindMakeCallEx
        """
        all_call_dict = dict()
        body = {"sort": [{"@timestamp": {"order": "asc"}}], "query": {"bool": {
            "must": [{"match": {
                "event_type": "OrigLocal sgBlindMakeCallEx SgEvtRemoteAlerting SgEvtConnected SgEvtDisconnected"}},
                     {"range": {
                         "@timestamp": {"gte": start_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                                        "lte": end_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')}}}]}}, "from": 0,
                "size": 10000}
        print(body)
        call_res = self.__scan_es_by_scroll(self.cms_log_index, body=body)
        for src in call_res:
            if src['session_id'] not in all_call_dict.keys():
                all_call_dict[src['session_id']] = list()
            all_call_dict[src['session_id']].append(src)
        all_call_list = list()
        for session_id in all_call_dict.keys():
            try:
                call_list = self.__get_blink_make_call(session_id, all_call_dict[session_id])
                all_call_list.extend(call_list)
            except Exception, e:
                logging.error(u'%s解析异常:%s' % (session_id, e), exc_info=True)
            else:
                pass
        logging.info(u'总共匹配到%s通呼叫' % len(all_call_list))
        dnis_call_dict = dict()
        calling_number_call_dict = dict()
        for call in all_call_list:
            if call.dnis.prefix == 'SIP':
                continue
            if call.dnis.dnis not in dnis_call_dict.keys():
                dnis_call_dict[call.dnis.dnis] = list()
            dnis_call_dict[call.dnis.dnis].append(call)
            if call.calling_number.calling_number not in calling_number_call_dict.keys():
                calling_number_call_dict[call.calling_number.calling_number] = list()
            calling_number_call_dict[call.calling_number.calling_number].append(call)
        print(u'总共匹配到%s通呼叫' % len(all_call_list))
        try:
            query_ret = json.loads(self.__get_dnis_info_from_remote(dnis_call_dict.keys()))
        except Exception, e:
            logging.error(u'查询被叫号码信息异常:%s' % e, exc_info=True)
        else:
            if query_ret['result']:
                dnis_dict = dict()
                for dnis_info in query_ret['data']:
                    dnis_dict[dnis_info['phone']] = dnis_info
            for dnis_number in dnis_call_dict.keys():
                if dnis_number not in dnis_dict.keys():
                    logging.error(u'服务器没有返回被叫号码%s的相关信息' % dnis_number)
                else:
                    info = dnis_dict[dnis_number]
                    for call in dnis_call_dict[dnis_number]:
                        call.dnis.set_relative_info(info['flag'], info['serv_provider'], info['city_code'],
                                                    info['province_name'], info['city_name'])
            try:
                query_ret = json.loads(self.__get_voip_info_from_remote(calling_number_call_dict.keys()))
            except Exception, e:
                logging.error(u'查询被叫号码信息异常:%s' % e, exc_info=True)
            else:
                if query_ret['result']:
                    number_dict = dict()
                    for number_info in query_ret['data']:
                        number_dict[number_info['phone']] = number_info
                for calling_number in calling_number_call_dict.keys():
                    if calling_number not in number_dict.keys():
                        logging.error(u'服务器没有返回外显号%s的相关信息' % calling_number)
                    else:
                        info = number_dict[calling_number]
                        for call in calling_number_call_dict[calling_number]:
                            call.calling_number.set_relative_info(info['voip_Name'], '010', info['province_name'],
                                                                  info['city_name'])
            logging.info(
                u'一共检查到%s条sgBlindMakeCallEx,现在准备添加到%s/doc中去' % (len(all_call_list), self.blink_call_detail_index))
            self.__bulk_blink_call_data(all_call_list)
        return all_call_list

    def __get_dnis_info_from_remote(self, dnis_list):
        body = dict()
        body['numbers'] = dnis_list
        headers = {'content-type': "application/json"}
        response = requests.post(self.dnis_query_url, data=json.dumps(body, ensure_ascii=False), headers=headers)
        logging.info(response.text)
        return response.text

    def __get_voip_info_from_remote(self, calling_number_list):
        body = dict()
        body['numbers'] = calling_number_list
        headers = {'content-type': "application/json"}
        response = requests.post(self.voip_query_url, data=json.dumps(body, ensure_ascii=False), headers=headers)
        logging.info(response.text)
        return response.text

    def __create_make_call_detail_index(self):
        '''
        创建索引,创建索引名称为ott，类型为ott_type的索引
        :return:
        '''
        # 创建映射
        _index_mappings = {
            "mappings": {
                'doc': {
                    "properties": {
                        "session_id": {
                            "type": "keyword"
                        },
                        "start_time": {
                            "type": "date",
                            "format": "yyyy-MM-dd HH:mm:ss||yyyy-MM-dd HH:mm:ss.SSS||yyyy-MM-dd||epoch_millis"
                        },
                        "end_time": {
                            "type": "date",
                            "format": "yyyy-MM-dd HH:mm:ss||yyyy-MM-dd HH:mm:ss.SSS||yyyy-MM-dd||epoch_millis"
                        },
                        "calling_number": {
                            "type": "keyword"
                        },
                        "calling_number_belong_to": {
                            "type": "keyword"
                        },
                        "calling_number_province": {
                            "type": "keyword"
                        },
                        "calling_number_city": {
                            "type": "keyword"
                        },
                        "calling_number_city_code": {
                            "type": "keyword"
                        },
                        "dnis": {
                            "type": "keyword"
                        },
                        "dnis_prefix": {
                            "type": "keyword"
                        },
                        "target": {
                            "type": "keyword"
                        },
                        "dnis_isp": {
                            "type": "keyword"
                        },
                        "dnis_province": {
                            "type": "keyword"
                        },
                        "dnis_city": {
                            "type": "keyword"
                        },
                        "dnis_city_code": {
                            "type": "keyword"
                        }
                    }
                }

            }
        }
        if self.es.indices.exists(index=self.blink_call_detail_index) is not True:
            res = self.es.indices.create(index=self.blink_call_detail_index, body=_index_mappings)
            print res

    def __bulk_blink_call_data(self, call_list):
        actions = list()
        for call in call_list:
            action = {
                "_index": self.blink_call_detail_index,
                "_type": 'doc',
                "_source": {
                    "session_id": call.session_id,
                    "start_time": int(time.mktime(time.strptime(call.start_time, '%Y-%m-%dT%H:%M:%S.%fZ'))) * 1000,
                    "end_time": int(time.mktime(time.strptime(call.end_time, '%Y-%m-%dT%H:%M:%S.%fZ'))) * 1000,
                    "calling_number": call.calling_number.calling_number,
                    "dnis_prefix": call.dnis.prefix,
                    "calling_number_province": call.calling_number.province,
                    "calling_number_city": call.calling_number.city,
                    "calling_number_city_code": call.calling_number.city_code,
                    "dnis": call.dnis.dnis,
                    "calling_number_belong_to": call.calling_number.belong_to,
                    "target": call.target,
                    "dnis_isp": call.dnis.isp,
                    "dnis_province": call.dnis.province,
                    "dnis_city": call.dnis.city,
                    "dnis_city_code": call.dnis.city_code,
                    "call_result": call.call_result,
                    "platform_id": call.platform_id,
                    "platform_name": call.platform_name,
                    "platform_code": call.platform_code
                }
            }
            actions.append(action)
        bulk(client=self.es, actions=actions)
        logging.info(u'数据添加完毕')

    def query_blink_call(self, start_time, end_time):
        call_list = list()
        body = {"query": {"bool": {
            "must": [{"range": {
                "start_time": {"gte": int(time.mktime(start_time.timetuple())) * 1000,
                               "lte": int(time.mktime(end_time.timetuple())) * 1000}}}]}}, "from": 0, "size": 10000}
        # print(json.dumps(body, ensure_ascii=False))
        #         # call_res = self.es.search(self.blink_call_detail_index, body=body)
        #         # for hit in call_res['hits']['hits']:
        #         #     call_list.append(hit['_source'])
        call_list = self.__scan_es_by_scroll(self.blink_call_detail_index, body)
        logging.info(u'一共发现%s条满足条件的sgBlindMakeCallEx事件' % len(call_list))
        return call_list

    def __scan_es_by_scroll(self, index_name, body, scroll='2m', size=1000):
        page = self.es.search(
            index=index_name,
            body=body,
            scroll=scroll,  # 保持游标查询窗口2分钟
            size=size
        )
        sid = page['_scroll_id']
        scroll_size = page['hits']['total']
        search_list = list()
        # Start scrolling
        start_time = datetime.datetime.now()
        while scroll_size > 0:
            print "Scrolling..."
            page = self.es.scroll(scroll_id=sid, scroll='2m')
            # Update the scroll ID
            sid = page['_scroll_id']
            # Get the number of results that we returned in the last scroll
            scroll_size = len(page['hits']['hits'])
            print "scroll size: " + str(scroll_size)
            # Do something with the obtained page
            for hit in page['hits']['hits']:
                search_list.append(hit['_source'])
        now = datetime.datetime.now()
        logging.info(u'一共检索到%s满足要求的记录,用时%s(秒)' % (len(search_list), (now - start_time).seconds))
        return search_list

    def cms_log_check_task(self):
        timestamp = (int(time.time()) % 60) * 60
        begin_time = datetime.datetime.fromtimestamp(timestamp - 600)
        end_time = datetime.datetime.fromtimestamp(timestamp - 300)
        call_list = self.check_blink_call(begin_time, end_time)
        return call_list


if __name__ == '__main__':
    test_start_time = datetime.datetime.strptime('2018-07-28 00:00:00', '%Y-%m-%d %H:%M:%S')
    test_end_time = datetime.datetime.strptime('2019-09-01 00:00:00', '%Y-%m-%d %H:%M:%S')
    # test_start_time = datetime.datetime.now()
    # test_end_time = datetime.datetime.now()
    cms = CMSLog()
    # test_call_list = cms.query_blink_call(test_start_time, test_end_time)
    test_call_list = cms.query_blink_call(test_start_time, test_end_time)
    # test_call_list = cms.check_blink_call(test_start_time, test_end_time)
    # test_call_list = cms.query_blink_call(datetime.datetime.now(), datetime.datetime.now())
    # test_call_list = query_blink_call(test_start_time, test_end_time)
    print(u'一共发现%s条呼叫' % len(test_call_list))
    # ret = dict()
    # ret['result'] = True
    # ret['data'] = call_list
    # print(u'查询返回结果:%s' % json.dumps(ret, ensure_ascii=False))
    # create_make_call_detail_index()
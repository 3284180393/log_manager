# -*- coding: utf-8 -*-

from django.http import HttpResponse
import json
import logging
import datetime
import cms
import urllib


LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
logging.basicConfig(filename='my.log', level=logging.DEBUG, format=LOG_FORMAT)


def url_test(request, app_name, event_name):
    print('app_name=%s, event_name=%s' % (app_name, event_name))
    dc = dict()
    dc['a'] = '1'
    return HttpResponse(json.dumps(dc, ensure_ascii=False), content_type="application/json,charset=utf-8")


def get_app_event_detail(request, app_name, event_name, params):
    """
    获取应用相关事件详情
    :param request: http请求消息
    :param app_name: 应用名
    :param event_name: 事件名
    :param params: 检查参数
    :return:检查结果
    """
    print('in haha')
    ret = dict()
    ret['result'] = False
    if app_name != 'cms':
        logging.error(u'目前还不支持%s应用' % app_name)
        ret['data'] = u'目前还不支持%s应用' % app_name
    elif event_name != 'sgBlindMakeCallEx':
        logging.error(u'目前%s还不支持%s事件检查' % (app_name, event_name))
        ret['data'] = u'目前%s还不支持%s事件检查' % (app_name, event_name)
    else:
        try:
            print(params)
            param_dict = json.loads(params)
            print(param_dict)
        except Exception, e:
            logging.error(u'%s不是一个合法的json串' % params)
            ret['data'] = u'%s不是一个合法的json串' % params
        else:
            if app_name == 'cms' and event_name == 'sgBlindMakeCallEx':
                if 'startTime' not in param_dict.keys() or 'endTime' not in param_dict.keys():
                    logging.error(u'%s的%s事件检查必须包含startTime和endTime' % (app_name, event_name))
                else:
                    try:
                        start_time = datetime.datetime.strptime(param_dict['startTime'], '%Y-%m-%d %H:%M:%S')
                        end_time = datetime.datetime.strptime(param_dict['endTime'], '%Y-%m-%d %H:%M:%S')
                    except Exception, e:
                        logging.error(u'时间格式错误,开始时间和结束时间的格式必须为yyyy-MM-dd HH:mm:ss')
                        ret['data'] = u'时间格式错误,开始时间和结束时间的格式必须为yyyy-MM-dd HH:mm:ss'
                    else:
                        try:
                            print('nice')
                            call_list = cms.CMSLog().query_blink_call(start_time, end_time)
                            ret['data'] = call_list
                            ret['result'] = True
                            logging.info(u'查询%s的%s的信息成功' % (app_name, event_name))
                        except Exception, e:
                            logging.error(u'查询%s的%s的信息异常:%s' % (app_name, event_name, e), exc_info=True)
                            ret['data'] = u'查询%s的%s的信息异常:%s' % (app_name, event_name, e)
    logging.info(json.dumps(ret, ensure_ascii=False))
    return HttpResponse(json.dumps(ret, ensure_ascii=False), content_type="application/json,charset=utf-8")

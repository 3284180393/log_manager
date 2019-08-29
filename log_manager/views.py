# -*- coding: utf-8 -*-

from django.http import HttpResponse
import json
import datetime
import time
from log_manager import cms
from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore, register_events, register_job
from log_manager.conf import log_conf
import logging as logger

logging = logger.getLogger(__name__)

# LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
# logging.basicConfig(filename='my.log', level=logging.DEBUG, format=LOG_FORMAT)


# 开启定时工作
try:
    # 实例化调度器
    scheduler = BackgroundScheduler()
    # 调度器使用DjangoJobStore()
    scheduler.add_jobstore(DjangoJobStore(), "default")
    # 设置定时任务，选择方式为interval，时间间隔为10s
    # 另一种方式为每天固定时间执行任务，对应代码为：
    # @register_job(scheduler, 'cron', day_of_week='mon-fri', hour='9', minute='30', second='10',id='task_time')
    @register_job(scheduler, "interval", minutes=log_conf.cms_check_span)
    def my_job():
        # 这里写你要执行的任务
        now = datetime.datetime.now().replace(microsecond=0)
        begin = now - datetime.timedelta(minutes=log_conf.cms_check_span+log_conf.cms_check_delay, seconds=now.second)
        end = now - datetime.timedelta(minutes=log_conf.cms_check_delay, seconds=now.second)
        cms_log = cms.CMSLog(es_cluster=log_conf.es_cluster, cms_log_index=log_conf.cms_log_index, blink_call_index=log_conf.cms_blink_make_call, dnis_query_url=log_conf.dnis_query_url, voip_query_url=log_conf.voip_query_url, platform_id=log_conf.platform_id, platform_name=log_conf.platform_name, platform_code=log_conf.platform_code)
        print(u'准备开始检查%s到%s期间的呼叫' % (begin, end))
        call_list = cms_log.check_blink_call(begin, end)
        msg = u'%s到%s一共检查到%s通sgBlinkCallEx事件' % (begin, end, len(call_list))
        logging.info(msg)
        print(msg)
    register_events(scheduler)
    scheduler.start()
except Exception as e:
    print(e)
    # 有错误就停止定时器
    scheduler.shutdown()


def url_test(request, app_name, event_name):
    print('app_name=%s, event_name=%s' % (app_name, event_name))
    dc = dict()
    dc['a'] = '1'
    return HttpResponse(json.dumps(dc, ensure_ascii=False), content_type="application/json,charset=utf-8")


def get_app_event_detail(request, app_name, event_name):
    """
    获取应用相关事件详情
    :param request: http请求消息
    :param app_name: 应用名
    :param event_name: 事件名
    :param params: 检查参数
    :return:检查结果
    """
    ret = dict()
    ret['result'] = False
    if app_name != 'cms':
        logging.error(u'目前还不支持%s应用' % app_name)
        ret['data'] = u'目前还不支持%s应用' % app_name
    elif event_name != 'sgBlindMakeCallEx' and event_name != 'callDetail':
        logging.error(u'目前%s还不支持%s事件检查' % (app_name, event_name))
        ret['data'] = u'目前%s还不支持%s事件检查' % (app_name, event_name)
    else:
        if app_name == 'cms':
            try:
                start_time = int(time.mktime(datetime.datetime.strptime(request.GET.get('startTime'), '%Y-%m-%d %H:%M:%S').timetuple()))
                end_time = int(time.mktime(datetime.datetime.strptime(request.GET.get('endTime'), '%Y-%m-%d %H:%M:%S').timetuple()))
            except Exception as e:
                logging.error(u'获取开始或是结束时间异常,开始时间和结束时间的格式必须为yyyy-MM-dd HH:mm:ss:%s' % e, exc_info=True)
                ret['data'] = u'获取开始或是结束时间异常,开始时间和结束时间的格式必须为yyyy-MM-dd HH:mm:ss:%s' % e
            else:
                try:
                    if event_name == 'sgBlindMakeCallEx':
                        call_list = cms.CMSLog(es_cluster=log_conf.es_cluster, cms_log_index=log_conf.cms_log_index, blink_call_index=log_conf.cms_blink_make_call, dnis_query_url=log_conf.dnis_query_url, voip_query_url=log_conf.voip_query_url, platform_id=log_conf.platform_id, platform_name=log_conf.platform_name, platform_code=log_conf.platform_code).query_blink_call(start_time, end_time)
                    else:
                        call_list = cms.CMSLog(es_cluster=log_conf.es_cluster, cms_log_index=log_conf.cms_log_index, blink_call_index=log_conf.cms_blink_make_call, dnis_query_url=log_conf.dnis_query_url, voip_query_url=log_conf.voip_query_url, platform_id=log_conf.platform_id, platform_name=log_conf.platform_name, platform_code=log_conf.platform_code).query_call_detail(start_time, end_time)
                    ret['data'] = call_list
                    ret['result'] = True
                    logging.info(u'查询%s的%s的信息成功' % (app_name, event_name))
                except Exception as e:
                    logging.error(u'查询%s的%s的信息异常:%s' % (app_name, event_name, e), exc_info=True)
                    ret['data'] = u'查询%s的%s的信息异常:%s' % (app_name, event_name, e)
    logging.info(json.dumps(ret, ensure_ascii=False))
    return HttpResponse(json.dumps(ret, ensure_ascii=False), content_type="application/json,charset=utf-8")


def start_app_event_check(request, app_name, event_name):
    """
    开始应用相关事件检查
    :param request: http请求消息
    :param app_name: 应用名
    :param event_name: 事件名
    :param params: 检查参数
    :return:检查结果
    """
    ret = dict()
    ret['result'] = False
    if app_name != 'cms':
        logging.error(u'目前还不支持%s应用' % app_name)
        ret['data'] = u'目前还不支持%s应用' % app_name
    elif event_name != 'sgBlindMakeCallEx' or event_name != 'callDetail':
        logging.error(u'目前%s还不支持%s事件检查' % (app_name, event_name))
        ret['data'] = u'目前%s还不支持%s事件检查' % (app_name, event_name)
    else:
        if app_name == 'cms' and event_name == 'sgBlindMakeCallEx':
            try:
                body = json.loads(request.body)
                logging.info('GET=%s' % request.GET)
                logging.info('startTime=%s, endTime=%s' % (body['startTime'], body['endTime']))
                start_time = int(time.mktime(datetime.datetime.strptime(body['startTime'], '%Y-%m-%d %H:%M:%S').timetuple()))
                end_time = int(time.mktime(datetime.datetime.strptime(body['endTime'], '%Y-%m-%d %H:%M:%S').timetuple()))
                logging.info('begin=%s, end=%s' % (start_time, end_time))
            except Exception as e:
                logging.error(u'获取开始或是结束时间异常,开始时间和结束时间的格式必须为yyyy-MM-dd HH:mm:ss:%s' % e, exc_info=True)
                ret['data'] = u'获取开始或是结束时间异常,开始时间和结束时间的格式必须为yyyy-MM-dd HH:mm:ss:%s' % e
            else:
                try:
                    if event_name == 'sgBlindMakeCallEx':
                        call_list = cms.CMSLog(es_cluster=log_conf.es_cluster, cms_log_index=log_conf.cms_log_index, blink_call_index=log_conf.cms_blink_make_call, dnis_query_url=log_conf.dnis_query_url, voip_query_url=log_conf.voip_query_url, platform_id=log_conf.platform_id, platform_name=log_conf.platform_name, platform_code=log_conf.platform_code).check_blink_call(start_time, end_time)
                    else:
                        call_list = cms.CMSLog(es_cluster=log_conf.es_cluster, cms_log_index=log_conf.cms_log_index, blink_call_index=log_conf.cms_blink_make_call, dnis_query_url=log_conf.dnis_query_url, voip_query_url=log_conf.voip_query_url, platform_id=log_conf.platform_id, platform_name=log_conf.platform_name, platform_code=log_conf.platform_code).check_call_detail(start_time, end_time)
                    ret['data'] = call_list
                    ret['result'] = True
                    logging.info(u'查询%s的%s的信息成功' % (app_name, event_name))
                except Exception as e:
                    logging.error(u'查询%s的%s的信息异常:%s' % (app_name, event_name, e), exc_info=True)
                    ret['data'] = u'查询%s的%s的信息异常:%s' % (app_name, event_name, e)
    logging.info(json.dumps(ret, ensure_ascii=False))
    return HttpResponse(json.dumps(ret, ensure_ascii=False), content_type="application/json,charset=utf-8")

# -*- coding: utf-8 -*-

from django.http import HttpResponse
import json
import datetime
import time
import cms
from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore, register_events, register_job
from conf import log_conf
import logging as logger

logging = logger.getLogger(__name__)

# LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
# logging.basicConfig(filename='my.log', level=logging.DEBUG, format=LOG_FORMAT)


#开启定时工作
try:
    # 实例化调度器
    scheduler = BackgroundScheduler()
    # 调度器使用DjangoJobStore()
    scheduler.add_jobstore(DjangoJobStore(), "default")
    # 设置定时任务，选择方式为interval，时间间隔为10s
    # 另一种方式为每天固定时间执行任务，对应代码为：
    # @register_job(scheduler, 'cron', day_of_week='mon-fri', hour='9', minute='30', second='10',id='task_time')
    @register_job(scheduler,"interval", minutes=1)
    def my_job():
        # 这里写你要执行的任务
        print('hello, boy')
        timestamp = (int(time.time()/60)) * 60
        begin_time = datetime.datetime.fromtimestamp(timestamp - log_conf.cms_check_delay * 60 - log_conf.cms_check_span * 60)
        end_time = datetime.datetime.fromtimestamp(timestamp - log_conf.cms_check_delay * 60)
        cms_log = cms.CMSLog(es_cluster=log_conf.es_cluster, cms_log_index=log_conf.cms_log_index, blink_call_index=log_conf.cms_blink_make_call, dnis_query_url=log_conf.dnis_query_url, voip_query_url=log_conf.voip_query_url, platform_id=log_conf.platform_id, platform_name=log_conf.platform_name, platform_code=log_conf.platform_code)
        call_list = cms_log.check_blink_call(begin_time, end_time)
        msg = u'%s到%s一共检查到%s通sgBlinkCallEx事件' % (begin_time, end_time, len(call_list))
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
    print(request.method)
    print(request.body)
    ret = dict()
    ret['result'] = False
    if app_name != 'cms':
        logging.error(u'目前还不支持%s应用' % app_name)
        ret['data'] = u'目前还不支持%s应用' % app_name
    elif event_name != 'sgBlindMakeCallEx':
        logging.error(u'目前%s还不支持%s事件检查' % (app_name, event_name))
        ret['data'] = u'目前%s还不支持%s事件检查' % (app_name, event_name)
    else:
        if app_name == 'cms' and event_name == 'sgBlindMakeCallEx':
            try:
                body = json.loads(request.body)
                print(body['startTime'])
                print(body['endTime'])
                print('body=%s' % body)
                start_time = int(time.mktime(datetime.datetime.strptime(body['startTime'], '%Y-%m-%d %H:%M:%S').timetuple()))
                end_time = int(time.mktime(datetime.datetime.strptime(body['endTime'], '%Y-%m-%d %H:%M:%S').timetuple()))
            except Exception, e:
                logging.error(u'获取开始或是结束时间异常,开始时间和结束时间的格式必须为yyyy-MM-dd HH:mm:ss:%s' % e, exc_info=True)
                ret['data'] = u'获取开始或是结束时间异常,开始时间和结束时间的格式必须为yyyy-MM-dd HH:mm:ss:%s' % e
            else:
                try:
                    call_list = cms.CMSLog().query_blink_call(start_time, end_time)
                    ret['data'] = call_list
                    ret['result'] = True
                    logging.info(u'查询%s的%s的信息成功' % (app_name, event_name))
                except Exception, e:
                    logging.error(u'查询%s的%s的信息异常:%s' % (app_name, event_name, e), exc_info=True)
                    ret['data'] = u'查询%s的%s的信息异常:%s' % (app_name, event_name, e)
    logging.info(json.dumps(ret, ensure_ascii=False))
    return HttpResponse(json.dumps(ret, ensure_ascii=False), content_type="application/json,charset=utf-8")

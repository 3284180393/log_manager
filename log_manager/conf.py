# -*- coding: utf-8 -*-

import configparser
import sys


class LogConf:
    def __init__(self):
        cf = configparser.ConfigParser()
        cf.read('./log_manager/log.conf', encoding='utf-8')
        secs = cf.sections()
        print('current_path=%s' % sys.path[0])
        print(secs)
        # hosts = cf.get('elasticsearch', 'hosts')
        # es_cluster = list()
        # for host in hosts.split('|'):
        #     es = {}
        #     es['host'] = host.split(':')[0]
        #     es['port'] = int(host.split(':')[1])
        #     es_cluster.append(es)
        # self.es_cluster = es_cluster
        # self.cms_log_index = cf.get('elasticsearch', 'cms_log_index')
        # self.cms_blink_make_call = cf.get('elasticsearch', 'cms_blink_make_call')
        # self.cms_call_detail_index = cf.get('elasticsearch', 'cms_call_detail_index')
        # self.dnis_query_url = cf.get('ccod', 'dnis_query_url')
        # self.voip_query_url = cf.get('ccod', 'voip_query_url')
        # self.platform_id = cf.get('ccod', 'platform_id')
        # self.platform_name = cf.get('ccod', 'platform_name')
        # self.platform_code = cf.get('ccod', 'platform_code')
        # self.cms_check_delay = int(cf.get('task', 'cms_check_delay'))
        # self.cms_check_span = int(cf.get('task', 'cms_check_span'))


log_conf = LogConf()


if __name__ == '__main__':
    print(log_conf)




# -*- coding: utf-8 -*-


class CallingNumber:
    """
    用来定义外显号相关信息的类
    """
    def __init__(self, calling_number):
        """
        初始化外显号相关信息
        :param calling_number:外显号码
        belong_to:属于哪家话批公司
        province:外显号归属哪个省
        city:外显号归属哪个市
        city_code:外显号所在城市的区号
        """
        self.calling_number = calling_number
        self.belong_to = None
        self.province = None
        self.city = None
        self.city_code = None

    def set_relative_info(self, belong_to, city_code, prince, city):
        """
        设定外显相关信息
        :param belong_to:归属哪家话批公司
        :param city_code: 所在城市区号
        :param prince: 所在省
        :param city: 所在市
        :return:
        """
        self.belong_to = belong_to
        self.city_code = city_code
        self.province = prince
        self.city = city

class DNIS:
    """
    用来定义被叫号码相关信息的类
    """
    def __init__(self, dnis):
        """
        初始化外显号相关信息
        :param dnis:被叫号码
        prefix:被叫号码前缀
        phone_type:被叫终端类型
        isp:属于哪家运营商
        province:外显号归属哪个省
        city:外显号归属哪个市
        city_code:外显号所在城市的区号
        """
        self.dnis = dnis
        self.prefix = None
        self.phone_type = None
        self.isp = None
        self.province = None
        self.city = None
        self.city_code = None

    def set_relative_info(self, phone_type, isp, city_code, province, city):
        """
        设置被叫号码相关信息
        :param phone_type:被叫终端类型
        :param isp: 被叫号码所属运营商
        :param province: 被叫号码归属省
        :param city: 被叫号码归属城市
        :param city_code: 被叫号码区号
        :return:
        """
        self.phone_type = phone_type
        self.isp = isp
        self.province = province
        self.city = city
        self.city_code = city_code
# coding: utf-8
from enum import Enum, unique


# 用户类型
@unique
class UserType(Enum):
    Stu = 1  # 学生
    Prt = 2  # 家长
    Tea = 3  # 教师
    All = [1, 3]


# 登录类型
@unique
class LoginType(Enum):
    App = 1
    Web = 2


# 登录平台类型
@unique
class PlatformType(Enum):
    Android = 1
    IOS = 2
    Web = 3
    All = [1, 2, 3]


# 用户状态
@unique
class UserStatus(Enum):
    Forbid = 2  # 禁用


# 科目
@unique
class SubjectID(Enum):
    Math = 2  # 数学
    Phy = 3  # 物理
    Chem = 4  # 化学
    Eng = 9  # 英语
    Chn = 5  # 语文
    All = [2, 3, 4, 9, 5]


# 开通类型
@unique
class StateType(Enum):
    Not = 0  # 未开通
    Try = 1  # 体验
    Open = 2  # 已开通


# 班级变更类型
@unique
class UnitActionType(Enum):
    Add = 1  # 添加
    Change = 2  # 变更


# 部门类型
@unique
class DpmType(Enum):
    Pri = 1  # 小学
    Jun = 2  # 初中
    All = [1, 2]


# 短信验证码类型
@unique
class SmsCodeType(Enum):
    Reg = 1  # 注册
    Back = 2  # 找回
    All = [1, 2]


# 错误提示
@unique
class ErrorMsg(Enum):
    CnMobile = "请输入河南移动手机号"
    Param = "参数错误, 请联系客服"
    Unknown = "未知错误, 请联系客服"
    PhoneLen = "手机号长度为11个数字"
    PwdLen = "密码6~16个字符"
    NameLen = "姓名2~5个汉字"

import datetime
import os
import time
import json
import logging
import re
import hashlib
from typing import Optional
from mutagen.mp3 import MPEGInfo
import math
import pypinyin
from . import ajax
import urllib
from django.template import loader
from django.http import HttpResponse
from django.conf import settings
try:
    import cBytesIO as BytesIO
except ImportError:
    from io import BytesIO
log = logging.getLogger(__name__)
RE_CHINAMOBILE = re.compile(r"^1(([3][456789])|([5][012789])|([8][23478])|([4][7])|([7][8])|([9][8]))[0-9]{8}$")


class Struct(dict):
    """
    - 为字典加上点语法. 例如:
    >>> o = Struct({'a':1})
    >>> o.a
    >>> 1
    >>> o.b
    >>> None
    """

    def __init__(self, *e, **f):
        if e:
            self.update(e[0])
        if f:
            self.update(f)

    def __getattr__(self, name):
        # Pickle is trying to get state from your object, and dict doesn't implement it.
        # Your __getattr__ is being called with "__getstate__" to find that magic method,
        # and returning None instead of raising AttributeError as it should.
        if name.startswith('__'):
            raise AttributeError
        return self.get(name)

    def __setattr__(self, name, val):
        self[name] = val

    def __delattr__(self, name):
        self.pop(name, None)

    def __hash__(self):
        return id(self)


def render_template_data(request, template_path, context):
    t = loader.get_template(template_path)
    if hasattr(request, 'auth'):
        user = request.user
        context['auth'] = user
    context['settings'] = settings
    s = t.render(context, request)
    return s


def render_template(request, template_path, context={}):
    print(os.path.abspath(template_path), 22222222222222222222222222222222222)
    s = render_template_data(request, template_path, context)
    return HttpResponse(s)


def is_chinamobile(phone):
    """
    功能说明：       判断是否为移动手机号
    ----------------------------------------------------------------------------
    修改人                修改时间                修改原因
    ----------------------------------------------------------------------------
    王晨光                2016-10-10
    """
    if not isinstance(phone, str):
        return False
    return RE_CHINAMOBILE.match(phone)


def from_unixtime(stamp, str_format="%Y-%m-%d %H:%M:%S"):
    """
    时间戳转Datetime
    :param stamp: 时间
    :param str_format: 格式化字符串
    :return: str
    """
    if not isinstance(stamp, int):
        return stamp
    st = time.localtime(stamp)
    return datetime.datetime(*st[:6]).strftime(str_format)


def num_to_ch(num):
    """
    功能说明：讲阿拉伯数字转换成中文数字（转换[0, 10000)之间的阿拉伯数字 ）
    ----------------------------------------------------------------------------
    修改人                修改时间                修改原因
    ----------------------------------------------------------------------------
    陈龙                2012.2.9
    """
    num = int(num)
    _MAPPING = ('零', '一', '二', '三', '四', '五', '六', '七', '八', '九',)
    _P0 = ('', '十', '百', '千',)
    _S4 = 10 ** 4

    if _S4 <= num < 0:
        return None
    if num < 10:
        return _MAPPING[num]
    else:
        lst = []
        while num >= 10:
            lst.append(num % 10)
            num = num / 10
        lst.append(num)
        c = len(lst)  # 位数
        result = u''
        for idx, val in enumerate(lst):
            if val != 0:
                result += _P0[idx] + _MAPPING[int(val)]
            if idx < c - 1 and lst[idx + 1] == 0:
                result += '零'
        return result[::-1].replace('一十', '十')


def ajax_try(data):
    """
    接口异常修饰器
    ---------------------
    王晨光     2017-2-17
    ---------------------
    :param data: 默认data
    """

    def foo(f):
        def wrap(request, *args, **kw):
            try:
                return f(request, *args, **kw)
            except Exception as e:
                log.error(e)
                return ajax.jsonp_fail(request, error="500", data=data, message="抱歉，服务器开小差了，请联系客服12556185")

        return wrap

    return foo


def get_ip(request):
    """
    获取用户IP

    王晨光     2016-09-19

    :returns: ip address
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return x_forwarded_for or ''


def join(o):
    """
    把数组用逗号连接成字符串

    例如:
    >>> join([1, 2])
    >>> '1,2'
    """
    if isinstance(o, (list, tuple, set)):
        return ','.join(str(i) for i in o)
    return str(o)


def casts(self, **kw):
    """
    功能说明：       批量转换url参数类型
    用法:
    >>> request.GET.__class__ = casts
    >>> args = request.GET.casts(keyword=str, page=int, a="(\d+)")
    >>> print args
    >>> {'keyword': '', 'page':0, 'a':''}
    ----------------------------------------------------------------------------
    修改人                修改时间                修改原因
    ----------------------------------------------------------------------------
    王晨光                2016-6-26
    """
    args = Struct()
    for k, typ in kw.items():
        v = self.get(k)
        if isinstance(typ, str):
            if typ == 'json':
                try:
                    v = json.loads(v) if v else {}
                except Exception as e:
                    print(e)
                    pass
            elif typ == 'datetime':
                if v:
                    if v.endswith('24:00:00'):
                        v = v.split()[0] + ' 23:59:59'
                        v = time.strptime(v, "%Y-%m-%d %H:%M:%S")
                        v = time.localtime(time.mktime(v) + 1)
                        v = datetime.datetime(*v[:6])
                    else:
                        t = time.strptime(v, "%Y-%m-%d %H:%M:%S")
                        v = datetime.datetime(*t[:6])
                else:
                    v = None
            elif typ == 'timestamp':
                if v:
                    if v.endswith('24:00:00'):
                        v = v.split()[0] + ' 23:59:59'
                        v = time.strptime(v, "%Y-%m-%d %H:%M:%S")
                        v = int(time.mktime(v) + 1)
                    else:
                        t = time.strptime(v, "%Y-%m-%d %H:%M:%S")
                        v = int(time.mktime(t))
            else:
                m = re.match(typ, v or '')
                groups = m.groups() if m else ()
                groups = [g for g in groups if g is not None]
                v = groups[0] if groups else ''
        else:
            defv = type_default_value(typ)
            try:
                v = typ(v) if v is not None else defv
            except:
                v = defv
        args[k] = v
    return args


def strxor(s, key):
    """
    功能:异或加密
    返回:一个bytearray类型
    """
    try:
        key = key & 0xff
        a = bytearray(s)
        b = bytearray(len(a))
        for i, c in enumerate(a):
            b[i] = c ^ key
        return b
    except Exception as e:
        print(e)


def type_default_value(type):
    """返回基本类型默认值, 没有识别的类型返回None"""
    tab = {str: "", list: [], int: 0}
    return tab.get(type)


def loads(self):
    """
    功能说明：      解析json格式参数
    用法:
    >>> request.__class__ = loads
    >>> args = request.loads()
    >>> print args
    >>> {}
    """
    try:
        o = json.loads(self.body)
    except Exception as e:
        print(e)
        o = {}
    return Struct(o)


def check_response(data_dict):
    """
    功能:检测返回数据结果
    :param data_dict:
    :return: 成功返回data_dict的data和True,失败或者错误返回message和False
    """
    # 返回结果的response可能为ok, fail, error
    if data_dict.response == "error" or data_dict.response == "fail":
        return data_dict.data, data_dict.message, False
    else:
        if isinstance(data_dict.data, dict):
            data = Struct(data_dict.data)
        else:
            data = data_dict.data
        return data, data_dict.message, True


def upload_key():
    """
    功能: 上传资源密匙
    --------------------
    编辑: 吕建威
    --------------------
    日期: 2018-11-30
    --------------------
    """
    now = datetime.datetime.now()
    date_now = now.strftime(u"%Y%m%d")

    m = hashlib.md5()
    m.update(u'{}{}'.format(settings.UPLOAD_FILE_KEY_VALUE, date_now).encode('utf-8'))

    key = m.hexdigest()

    return key


def pinyin_abb(name):
    """
    功能:将姓名转换为拼音首字母缩写
    ----------------------------
    添加人:宋国洋
    ----------------------------
    添加时间:2018-06-29
    ----------------------------
    举例: 张三 >> zs
    """
    if not isinstance(name, str):
        name = name.decode()
    rows = pypinyin.pinyin(name, style=pypinyin.NORMAL)
    return ''.join(row[0][0] for row in rows if len(row) > 0)


def get_portrait(portrait, user_type):
    """
    功能:根据角色类型返回默认头像
    :param portrait: 头像url
    :param user_type: 角色类型
    :return: 头像绝对路径
    -----------------------------
    添加人:宋国洋
    -----------------------------
    添加时间:2018-06-27
    """
    portrait = strip_pollution(portrait)
    if portrait:
        # 获取文件的绝对路径
        return get_abs_url(portrait)
    else:
        if user_type == 1:
            # 学生
            return '%s/stu_default.png' % settings.FILE_VIEW_URL
        elif user_type == 2:
            # 家长
            return '%s/stu_default.png' % settings.FILE_VIEW_URL
        elif user_type == 3:
            # 教师
            return '%s/tea_default.png' % settings.FILE_VIEW_URL


def get_abs_url(path):
    """
    功能:获取文件的绝对路径
    :param path: 相对路径
    :return: 绝对路径
    -----------------------------
    添加人:宋国洋
    -----------------------------
    添加时间:2018-06-27
    """
    if not path:
        return ''
    if path.startswith("http"):
        return path
    zi_yuan_source = settings.FILE_VIEW_URL
    if path.endswith("mp3") and "outside" not in path:
        return "%s/upload_media/tts/%s" % (zi_yuan_source, path)
    return "%s/upload_media/%s" % (zi_yuan_source, path)


def filter_word_flag(message):
    """判断是否含有敏感词汇"""
    r = u""">|<|习近平|彭丽媛|李克强|普渡众生|救渡世人|杀戮|李洪志|假新闻|方励之|学生运动|六.四六四|
    中共高层|北京当局|血洗|强奸|两会|新一届|国家领导人|人大代表|政协委员|党专制|贪恋权力|倒行逆施|
    军权膨胀|公投|谪系人马|江泽民|胡锦涛|温家宝|曾庆红|军委主席|流氓政权|禽流感|吾尔开希|血吸虫|
    保钓活动|自焚|民主自由|性伴侣|东海天然气|公开信|爆炸|紫陽|祸国殃民|专制政权|讲真相|追悼会|001工程|
    扩大台湾农产品|包机|福建戒毒所|康晓光|康小光|权威主义|保钓|希望之声|九&评|退党|抵制日货|游行|滕兴善|
    陆建华|陈晖|张戎|不为人知的故事|The Unknown Story|芙蓉姐姐|焦国标|讨伐中宣部|窝囊的中国|哈工大女博士|
    平可夫|总统号|瓦良格|萨拉托加|明斯克号|福莱斯特|航空母舰|太石村|银行卡诈骗|三峡移民|移民|杜湘成|滕兴善|
    癌症村|拉法叶舰|拉案|陈光诚|维权|绝食抗议|反垄断法|天药|系统神学|许万平|郑茂清|新股发行|中天行公司|国统会|
    十七大前后的中国|中国丈夫毛泽东的情事|胡温面临的地雷阵|内部日记|十二个春秋|邓力群|未来自由中国在民间|颐和园|
    刘志华生活腐败|保钓行动|上海合作组织|朝令夕改|高考移民|高考舞弊|取款风波|出国考察|高考泄题|姬鹏飞|西藏边防|
    武装冲突|戴松林疑案|高莺莺死亡案件|湘阴群体事件|法＆轮|湘潭韶山|杨长军天安门广场自残事件|无线针孔摄象机|
    无线针孔摄象机看字专用针孔摄像机|隐形无线耳机|暗访摄像包|台湾进口纽扣式超清晰针孔摄像机|汽车反测速雷达|迷魂药|迷奸药|
    瘙痒药吃了后就全身痒想脱光衣服的|三唑伦|仿五四枪/狙击枪|军用炸药|六合彩/买码|完全自杀手册|陈良宇|裸之秀|核电站|力霸|
    宏观调控|人大主任|国家药监局|尼日利亚|绑架|双规|境外并购|美国副国务卿|陈水扁过境美国|招待费耗资3700亿|高家伟|
    安徽农民工子弟学校|刘胡兰|乡亲铡刀|缅甸问题|杭州湾跨海大桥|摧毁旧卫星|医生状告医院|开单提成|大连建厂|中国反卫星武器|
    辽宁两会|衡阳中院工作报告|衡阳中院|中院工作报告|衡阳中院|衡阳中级人民法院|查禁八本图书|长株潭‘申特’不受重庆成都影响|
    三峡旅游资源被垄断|浏阳河水出现异味|威海政府掀"全民募捐"浪潮|山西黑砖窑|北大一教授被辞退致信教育部部长陈情|取消利息税|
    郑筱萸案件|体协原副主席宋万年|汉唐证券|辽宁海城二台子社区|中国石化集团公司高层人事变动|安徽高考文科统分|2008奥运性感泳装|
    加强网上群体性事件信息管理|物价上涨|高校罢课|高校罢餐|超级&信使|人权圣火|同样的世界，同样的人权|人权圣火之歌|事纪神|呼喊派|
    门徒会|统一教|观音法门|中功|菩提功|民运|藏独|示威|西藏&独立|集会|游行|喇嘛&抗议|拉萨&抗议|哲蚌寺|甘丹寺|藏族&独立|拉萨&戒严|
    西藏&暴乱|五一&游行|高校&游行|抵制家乐福|交行|账 号|招行|超?级短信|超级?短信|超?级信使|抵制家乐福|抵制法货|游行|西藏&起义|
    达赖&抗议|色拉寺|法国&游行|51&游行|超级信使|超 级 信使|超级 信使|裸体|法轮功|法&轮|轮&工&力|明&慧&网|法&輪|超科学|共匪|
    功德圆满|九评讲播|邪灵|上天在警告世人|同化宇宙|萬&古&事&為&法&來|万&古&事&為&法&來|讲&真&相&民&谣|讲&真&相&诗&歌|
    突&破&网&络&封&锁|滴&滴&血&泪&唤&君&醒|坦&荡&正&法&路|江氏一只黑手|康妮·契普卡|法&轮&转&动|天安门自焚|正念|
    用&真&像&打&破&禁&锢|法&囵|漠&视&人&权&施&独&裁|洗&脑&酷&刑|溶心法理|freenet-china.org|www.dajiyuan.com.cn|
    briefcase.yahoo.com|breakit.batcave.net|bbs.ievista.com|lookatme0.tripod.ca|www.geocities.com|baishishi|
    twfgm.no-ip.com|noblock.no-ip.com|www.dajiyuan.com|xiaopin.zapto.org|donghua.zapto.org|nolie.redirectme.net|
    mzc.zapto.org|gui.hopto.org|spr.hopto.org|freenet-china.org|www.minghui|www.minghui.org|24.83.220.95|www.xys2.org|
    101.redirectme.net|belong.zapto.org|elite.zapto.org|fresh.hopto.org|spring.bounceme.net|twfgm.no-ip.com|zapto.org|
    X泽民|x泽民|江core|江xx|江核心|江氏|反攻大陆|反共|天安门事件|射精|性交|阴道|阴茎|野鸡|口交|鸡巴|勃起|一夜情|鸡奸|江卖国|江贼民|
    sy01.nhua.org|www.downdown.net|www.111shop.com|zhina444.allhere.com|zhina444.xrs.net|gau12.amxy.com|dd21.kaxb.com|
    qxbbs.homeftp.net|uw.slyip.com|207.44.142.89|Web3.km120.com|h119.ath.cx|转&法&轮|法轮佛法|国家恐怖主义|24.87.30.178|
    江氏集团|江家班|江黑心|党魁|dadaobao.myetang.com|sy01.nhua.org|祝春林|马英泽|大纪元|卖淫|生化袭击|婊子|新闻封锁|大面积爆发|
    屠城|反宇宙的力量|庸医|台湾特工|一手操控|生化武器|政府黑暗|隐瞒疫情|安全投毒|封城|隐瞒数据|生物武器|骚货|江系人马|重疫区|消息封锁|
    瘟疫|nu18.com|万&古&事&为&法&来|精液|阴唇|阴蒂|淫邪|龟头|xxboy.net|www.hellocd.com|www6.kinghost.com|www.boybbs.net|
    pointsmoney.com|中国农民调查|韩桂芝|刘杰告状信|逊克农场26队|红顶商人|杀人奶粉|慰问信|瀑布沟|经租房|丁子霖|生者与死者|清水君|
    杨建利|王炳章|movie.yygov.com|交媾|刘晓竹|中宣部是中国社会的艾滋病|民运分子|新闻管制|舆论钳制|乱伦|轮奸|做爱|loveroot|suck|
    dick|shit|fuck|妓女|退脏帐号|退脏不咎|嘉禾事件|绿色台商|张玉凤&毛泽东|张万钧|www.in-wa.com|www.500movies.com|www.hhslut.com|
    www.hkgirlz.com|www.taiwanmovie.com|www.pussyasians.com|证券&巨资|蒋彦永|中国铁路&签名|爱国者同盟|love21cn|正邪大决战|
    救度世人|迷昏药|迷魂药|河南&艾滋病|黑龙江&干部|新唐人电视|权贵私有化|炮轰中国教育部|废除劳教签名活动|跨世纪的良心犯|汉风|克劳塞维茨|
    赵&紫&阳|大紀元|趙&紫&陽|www.12488.com|www.90550.com|29t.com|两性视频|情色电影|尤甘斯克|六四屠城|ftp.xinhone.com|
    u1.tengotech.com|w8.sullyhome.net|ming.got-game.org|王斌余|市长自杀|木塔里甫|玉素甫|库尔勒市长|超级信使|二手汽车|
    超级信使|性幻想|偷拍|婚外恋|情色|艳照|露点|一夜情|婚外情|两性|隐私|腐败中国|三个呆婊|社会主义灭亡|打倒中国|打倒共产党|
    打倒共产主义|打倒胡锦涛|打倒江泽民|打倒江主席|打倒李鹏|打倒罗干|打倒温家宝|打倒中共|打倒朱镕|抵制共产党|抵制共产主义|
    抵制胡锦涛|抵制江泽民|抵制江主席|抵制李鹏|抵制罗干|抵制温家宝|抵制中共|抵制朱镕基|灭亡中国|亡党亡国|粉碎四人帮|激流中国|
    特供|特贡|特共|zf大楼|殃视|贪污腐败|强制拆除|形式主义|政治风波|太子党|上海帮|北京帮|清华帮|红色贵族|权贵集团|河蟹社会|
    喝血社会|九风|9风|十七大|十7大|十九大|17da|九学|9学|四风|4风|双规|南街村|最淫官员|警匪|官匪|独夫民贼|官商勾结|城管暴力执法|
    强制捐款|毒豺|一党执政|一党专制|一党专政|专制政权|宪法法院|胡平|苏晓康|贺卫方|谭作人|焦国标|万润南|张志新|辛灝年|高勤荣|王炳章|
    高智晟|司马璐|刘晓竹|刘宾雁|魏京生|寻找林昭的灵魂|别梦成灰|谁是新中国|讨伐中宣部|异议人士|民运人士|启蒙派|选国家主席|民一主|
    min主|民竹|民珠|民猪|chinesedemocracy|大赦国际|国际特赦|da选|投公|公头|宪政|平反|党章|维权|昝爱宗|宪章|08宪|08xz|抿主|
    敏主|人拳|人木又|人quan|renquan|中国人权|中国新民党|群体事件|群体性事件|上中央|去中央|讨说法|请愿|请命|公开信|联名上书|
    万人大签名|万人骚动|截访|上访|shangfang|信访|访民|集合|集会|组织集体|静坐|静zuo|jing坐|示威|示wei|游行|you行|油行|
    游xing|youxing|官逼民反|反party|反共|抗议|亢议|抵制|低制|底制|di制|抵zhi|dizhi|boycott|血书|焚烧中国国旗|baoluan|
    流血冲突|出现暴动|发生暴动|引起暴动|baodong|灭共|杀毙|罢工|霸工|罢考|罢餐|霸餐|罢参|罢饭|罢吃|罢食|罢课|罢ke|霸课|ba课|
    罢教|罢学|罢运|网特|网评员|网络评论员|五毛党|五毛们|5毛党|戒严|jieyan|jie严|戒yan|8的平方事件|知道64|八九年|贰拾年|2o年|
    20和谐年|贰拾周年|六四|六河蟹四|六百度四|六和谐四|陆四|陆肆|198964|5月35|89年春夏之交|64惨案|64时期|64运动|4事件|四事件|
    北京风波|学潮|学chao|xuechao|学百度潮|门安天|天按门|坦克压大学生|民主女神|历史的伤口|高自联|北高联|血洗京城|四二六社论|王丹|
    柴玲|沈彤|封从德|王超华|王维林|吾尔开希|吾尔开西|侯德健|阎明复|方励之|蒋捷连|丁子霖|辛灏年|蒋彦永|严家其|陈一咨|中华局域网|党的喉舌|
    互联网审查|当局严密封锁|新闻封锁|封锁消息|爱国者同盟|关闭所有论坛|网络封锁|金盾工程|无界浏览|无界网络|自由门|何清涟|中国的陷阱|汪兆钧|
    记者无疆界|境外媒体|维基百科|纽约时报|bbc中文网|华盛顿邮报|世界日报|东森新闻网|东森电视|星岛日报|wikipedia|美国广播公司|英国金融时报|
    自由亚洲|自由时报|中国时报|反分裂|威胁论|左翼联盟|钓鱼岛|保钓组织|主权|弓单|火乍|木仓|石肖|核蛋|步qiang|bao炸|爆zha|baozha|zha药|
    zha弹|炸dan|炸yao|zhadan|zhayao|hmtd|三硝基甲苯|六氟化铀|炸药配方|弹药配方|炸弹配方|皮箱炸弹|火药配方|人体炸弹|人肉炸弹|解放军|
    兵力部署|军转|军事社|8341部队|第21集团军|七大军区|7大军区|北京军区|沈阳军区|济南军区|成都军区|广州军区|南京军区|兰州军区|颜色革命|
    规模冲突|塔利班|基地组织|恐怖分子|恐怖份子|三股势力|印尼屠华|印尼事件|蒋公纪念歌|马英九|mayingjiu|李天羽|苏贞昌|林文漪|陈水扁|陈s扁|
    陈随便|阿扁|a扁|告全国同胞书|台百度湾|台完|台wan|taiwan|台弯|湾台|台湾国|台湾共和国|台军|台独|台毒|台du|taidu|twdl|一中一台|打台湾|
    两岸战争|攻占台湾|支持台湾|进攻台湾|占领台湾|统一台湾|收复台湾|登陆台湾|解放台湾|解放tw|解决台湾|光复民国|台湾独立|台湾问题|台海问题|
    台海危机|台海统一|台海大战|台海战争|台海局势|入联|入耳关|中华联邦|国民党|x民党|民进党|青天白日|闹独立|duli|fenlie|日本万岁|小泽一郎|
    劣等民族|汉人|汉维|维汉|维吾|吾尔|热比娅|伊力哈木|疆独|东突厥斯坦解放组织|东突解放组织|蒙古分裂分子|列确|阿旺晋美|藏人|臧人|zang人|藏民|
    藏m|达赖|赖达|dalai|哒赖|dl喇嘛|丹增嘉措|打砸抢|西独|藏独|葬独|臧独|藏毒|藏du|zangdu|支持zd|藏暴乱|藏青会|雪山狮子旗|拉萨|啦萨|啦沙|
    啦撒|拉sa|lasa|la萨|西藏|藏西|藏春阁|藏獨|藏独|藏独立|藏妇会|藏青会|藏字石|xizang|xi藏|x藏|西z|tibet|希葬|希藏|硒藏|稀藏|西脏|西奘|
    西葬|西臧|援藏|bjork|王千源|安拉|回教|回族|回回|回民|穆斯林|穆罕穆德|穆罕默德|默罕默德|伊斯兰|圣战组织|清真|清zhen|qingzhen|真主|阿拉伯|
    高丽棒子|韩国狗|满洲第三帝国|满狗|鞑子|江丑闻|江嫡系|江毒|江独裁|江蛤蟆|江核心|江黑心|江胡内斗|江祸心|江家帮|江绵恒|江派和胡派|江派人马|
    江泉集团|江人马|江三条腿|江氏集团|江氏家族|江氏政治局|江氏政治委员|江梳头|江太上|江戏子|江系人|江系人马|江宰民|江贼|江贼民|江主席|麻果丸|
    麻将透|麻醉弹|麻醉狗|麻醉枪|麻醉槍|麻醉药|麻醉藥|台独|台湾版假币|台湾独立|台湾国|台湾应该独立|台湾有权独立|天灭中共|中共帮凶|中共保命|
    中共裁|中共党文化|中共腐败|中共的血旗|中共的罪恶|中共帝国|中共独裁|中共封锁|中共封网|中共腐败|中共黑|中共黑帮|中共解体|中共近期权力斗争|
    中共恐惧|中共权力斗争|中共任用|中共退党|中共洗脑|中共邪教|中共邪毒素|中共政治游戏|爱女人|爱液|按摩棒|拔出来|爆草|包二奶|暴干|暴奸|暴乳|
    爆乳|暴淫|屄|被操|被插|被干|逼奸|仓井空|插暴|操逼|操黑|操烂|肏你|肏死|操死|操我|厕奴|插比|插b|插逼|插进|插你|插我|插阴|潮吹|潮喷|成人dv|
    成人电影|成人论坛|成人小说|成人电|成人电影|成人卡通|成人聊|成人片|成人视|成人图|成人文|成人小|成人电影|成人论坛|成人色情|成人网站|成人文学|
    成人小说|艳情小说|成人游戏|吃精|赤裸|抽插|扌由插|抽一插|春药|大波|大力抽送|大乳|荡妇|荡女|盗撮|多人轮|发浪|放尿|肥逼|粉穴|封面女郎|
    风月大陆|干死你|干穴|肛交|肛门|龟头|裹本|国产av|好嫩|豪乳|黑逼|后庭|后穴|虎骑|花花公子|换妻俱乐部|黄片|几吧|鸡吧|鸡巴|鸡奸|寂寞男|
    寂寞女|妓女|激情|集体淫|奸情|叫床|脚交|金鳞岂是池中物|金麟岂是池中物|精液|就去日|巨屌|菊花洞|菊门|巨奶|巨乳|菊穴|开苞|口爆|口活|口交|
    口射|口淫|裤袜|狂操|狂插|浪逼|浪妇|浪叫|浪女|狼友|聊性|流淫|铃木麻|凌辱|漏乳|露b|乱交|乱伦|轮暴|轮操|轮奸|裸陪|买春|美逼|美少妇|美乳|
    美腿|美穴|美幼|秘唇|迷奸|密穴|蜜穴|蜜液|摸奶|摸胸|母奸|奈美|奶子|男奴|内射|嫩逼|嫩女|嫩穴|捏弄|女优|炮友|砲友|喷精|屁眼|品香堂|前凸后翘|
    强jian|强暴|强奸处女|情趣用品|情色|拳交|全裸|群交|惹火身材|人妻|人兽|日逼|日烂|肉棒|肉逼|肉唇|肉洞|肉缝|肉棍|肉茎|肉具|揉乳|肉穴|肉欲|
    乳爆|乳房|乳沟|乳交|乳头|三级片|骚逼|骚比|骚女|骚水|骚穴|色逼|色界|色猫|色盟|色情网站|色区|色色|色诱|色欲|色b|少年阿宾|少修正|射爽|射颜|
    食精|释欲|兽奸|兽交|手淫|兽欲|熟妇|熟母|熟女|爽片|爽死我了|双臀|死逼|丝袜|丝诱|松岛枫|酥痒|汤加丽|套弄|体奸|体位|舔脚|舔阴|调教|偷欢|
    偷拍|推油|脱内裤|文做|我就色|无码|舞女|无修正|吸精|夏川纯|相奸|小逼|校鸡|小穴|小xue|写真|性感妖娆|性感诱惑|性虎|性饥渴|性技巧|性交|
    性奴|性虐|性息|性欲|胸推|穴口|学生妹|穴图|亚情|颜射|阳具|杨思敏|要射了|夜勤病栋|一本道|一夜欢|一夜情|一ye情|阴部|淫虫|阴唇|淫荡|
    阴道|淫电影|阴阜|淫妇|淫河|阴核|阴户|淫贱|淫叫|淫教师|阴茎|阴精|淫浪|淫媚|淫糜|淫魔|淫母|淫女|淫虐|淫妻|淫情|淫色|淫声浪语|淫兽学园|
    淫书|淫术炼金士|淫水|淫娃|淫威|淫亵|淫样|淫液|淫照|阴b|应召|幼交|幼男|幼女|欲火|欲女|玉女心经|玉蒲团|玉乳|欲仙欲死|玉穴|援交|原味内衣|
    援助交际|张筱雨|招鸡|招妓|中年美妇|抓胸|自拍|自慰|作爱|18禁|99bb|a4u|a4y|adult|amateur|anal|a片|fuck|gay片|g点|g片|hardcore|
    h动画|h动漫|incest|porn|secom|sexinsex|sm女王|xiao77|xing伴侣|tokyohot|yin荡|贱人|装b|大sb|傻逼|傻b|煞逼|煞笔|刹笔|傻比|
    沙比|欠干|婊子养的|我日你|我操|我草|卧艹|卧槽|爆你菊|艹你|cao你|你他妈|真他妈|别他吗|草你吗|草你丫|操你妈|擦你妈|操你娘|操他妈|
    日你妈|干你妈|干你娘|娘西皮|狗操|狗草|狗杂种|狗日的|操你祖宗|操你全家|操你大爷|妈逼|你麻痹|麻痹的|妈了个逼|马勒|狗娘养|贱比|贱b|
    下贱|死全家|全家死光|全家不得好死|全家死绝|白痴|无耻|sb|杀b|你吗b|你妈的|婊子|贱货|人渣|混蛋|媚外|和弦|兼职|限量|铃声|性伴侣|
    男公关|火辣|精子|射精|诱奸|强奸|做爱|性爱|发生关系|按摩|快感|处男|猛男|少妇|屌|屁股|下体|a片|内裤|浑圆|咪咪|发情|刺激|白嫩|
    粉嫩|兽性|风骚|呻吟|sm|阉割|高潮|裸露|不穿|一丝不挂|脱光|干你|干死|我干|裙中性运动|乱奸|乱伦|乱伦类|乱伦小|伦理大|伦理电影|
    伦理毛|伦理片|裸聊|裸聊网|裸体写真|裸舞视|裸照|美女裸体|美女写真|美女上门|美艳少妇|妹按摩|妹上门|迷幻药|迷幻藥|迷昏口|迷昏药|
    迷昏藥|迷魂香|迷魂药|迷魂藥|迷奸粉|迷奸药|迷情粉|迷情水|迷情药|迷药|迷藥|谜奸药|骚妇|骚货|骚浪|骚女|骚嘴|色电影|色妹妹|色情表演|
    色情电影|色情服务|色情图片|色情小说|色情影片|色情表演|色情电影|色情服务|色情片|色视频|色小说|性伴侣|性服务|性福情|性感少|性伙伴|
    性交|性交视频|性交图片|性奴|性奴集中营|性虐|阴唇|阴道|阴蒂|阴户|阴间来电|阴茎|阴茎增大|阴茎助勃|阴毛|陰唇|陰道|陰戶|淫荡|淫荡美女|
    淫荡视频|淫荡照片|淫乱|淫靡|淫魔|淫魔舞|淫女|淫情女|淫肉|淫騷妹|淫兽|淫兽学|淫水|淫穴|morphine|摇头丸|迷药|乖乖粉|narcotic|
    麻醉药|精神药品|爱女人|爱液|按摩棒|拔出来|爆草|包二奶|暴干|暴奸|暴乳|爆乳|暴淫|屄|被操|被插|被干|逼奸|仓井空|插暴|操逼|操黑|操烂|
    肏你|肏死|操死|操我|厕奴|插比|插b|插逼|插进|插你|插我|插阴|潮吹|潮喷|成人电影|成人论坛|成人色情|成人网站|成人文学|成人小说|艳情小说|
    成人游戏|吃精|赤裸|抽插|扌由插|抽一插|春药|大波|大力抽送|大乳|荡妇|荡女|盗撮|多人轮|发浪|放尿|肥逼|粉穴|封面女郎|风月大陆|干死你|干穴|
    肛交|肛门|龟头|裹本|国产av|好嫩|豪乳|黑逼|后庭|后穴|虎骑|花花公子|换妻俱乐部|黄片|几吧|鸡吧|鸡巴|鸡奸|寂寞男|寂寞女|妓女|激情|
    集体淫|奸情|叫床|脚交|金鳞岂是池中物|金麟岂是池中物|精液|就去日|巨屌|菊花洞|菊门|巨奶|巨乳|菊穴|开苞|口爆|口活|口交|口射|口淫|
    裤袜|狂操|狂插|浪逼|浪妇|浪叫|浪女|狼友|聊性|流淫|铃木麻|凌辱|漏乳|露b|乱交|乱伦|轮暴|轮操|轮奸|裸陪|买春|美逼|美少妇|美乳|美腿|
    美穴|美幼|秘唇|迷奸|密穴|蜜穴|蜜液|摸奶|摸胸|母奸|奈美|奶子|男奴|内射|嫩逼|嫩女|嫩穴|捏弄|女优|炮友|砲友|喷精|屁眼|品香堂|前凸后翘|
    强jian|强暴|强奸处女|情趣用品|情色|拳交|全裸|群交|惹火身材|人妻|人兽|日逼|日烂|肉棒|肉逼|肉唇|肉洞|肉缝|肉棍|肉茎|肉具|揉乳|肉穴|
    肉欲|乳爆|乳房|乳沟|乳交|乳头|三级片|骚逼|骚比|骚女|骚水|骚穴|色逼|色界|色猫|色盟|色情网站|色区|色色|色诱|色欲|色b|少年阿宾|少修正|
    射爽|射颜|食精|释欲|兽奸|兽交|手淫|兽欲|熟妇|熟母|熟女|爽片|爽死我了|双臀|死逼|丝袜|丝诱|松岛枫|酥痒|汤加丽|套弄|体奸|体位|舔脚|
    舔阴|调教|偷欢|偷拍|推油|脱内裤|文做|我就色|无码|舞女|无修正|吸精|夏川纯|相奸|小逼|校鸡|小穴|小xue|写真|性感妖娆|性感诱惑|性虎|
    性饥渴|性技巧|性交|性奴|性虐|性息|性欲|胸推|穴口|学生妹|穴图|亚情|颜射|阳具|杨思敏|要射了|夜勤病栋|一本道|一夜欢|一夜情|一ye情|
    阴部|淫虫|阴唇|淫荡|阴道|淫电影|阴阜|淫妇|淫河|阴核|阴户|淫贱|淫叫|淫教师|阴茎|阴精|淫浪|淫媚|淫糜|淫魔|淫母|淫女|淫虐|淫妻|淫情|
    淫色|淫声浪语|淫兽学园|淫书|淫术炼金士|淫水|淫娃|淫威|淫亵|淫样|淫液|淫照|阴b|应召|幼交|幼男|幼女|欲火|欲女|玉女心经|玉蒲团|玉乳|
    欲仙欲死|玉穴|援交|原味内衣|援助交际|张筱雨|招鸡|招妓|中年美妇|抓胸|自拍|自慰|作爱|18禁|99bb|a4u|a4y|adult|amateur|anal|a片|
    fuck|gay片|g点|g片|hardcore|h动画|h动漫|incest|porn|secom|sexinsex|sm女王| xiao77|xing伴侣|tokyohot|yin荡"""
    r = r.replace('\n', '').replace(' ', '') + u'|The Unknown Story'
    if isinstance(message, str):
        return re.sub(r, u'**', message)


def check_hans(val):
    """判断是否是汉字"""
    if u'\u4e00' <= val <= u'\u9fa5':
        return True
    else:
        return False


def all_hans(words):
    """检查字符串是否为汉字"""
    belong = True
    for w in words:
        belong = belong and check_hans(w)
    return belong


def list_to_str(data_list):
    """
    功能:将列表元素转换成字符串返回
    """
    ret_str = ""
    for obj in data_list:
        if ret_str:
            ret_str += ",%s" % obj
        else:
            ret_str = "%s" % obj
    return ret_str


def strip_pollution(
        raw: str,
        match: Optional[str] = r'[\s]+',
) -> str:
    """
    清除字符串中的非法字符
    :param raw: 可能包含空格等非法字符串的数据
    :param match: 正则匹配式
    :return: 筛除脏数据后字符串
    """
    parts = re.split(match, raw)
    clear = ''.join(parts)
    return clear


def upload_static_sever():
    """
    功能: 返回上传文件地址
    --------------------
    编辑: 吕建威
    --------------------
    日期: 2018-08-06
    --------------------
    """
    # 拼装上传服务器地址
    upload_domain = settings.FILE_WEB_URLROOT
    upload_folder = u'hdkt'
    key = upload_key()
    upload_url = u'{upload_domain}/swf_upload/?upcheck={key}&upType={upload_folder}'.format(
        upload_domain=upload_domain,
        key=key,
        upload_folder=upload_folder,
    )

    return upload_url


def get_absurl(url):
    """
    将相对路径转换为绝对路径
    :param url:
    :return:
    """
    if not url:
        return ""
    if "http" in url:
        return url
    return "http://flv.m.xueceping.cn/upload_media/%s" % url


def get_duration(url):
    """
    返回音频时长
    :param url: 绝对路径
    :return:
    """
    try:
        if url:
            with urllib.request.urlopen(url) as response:
                data = response.read()
                f = BytesIO(data)
                info = MPEGInfo(f)
                duration = math.ceil(info.length)
                f.close()
        else:
            duration = 0
        return duration
    except Exception as e:
        logging.error(e)
    return 0


def date_to_unix(obj_value, add=0):
    """
    功能: 把时间字符串转换为时间戳并返回
    ---------------------------------
    编辑: 王建彬
    ---------------------------------
    接收参数类型: '20180326', '2018-03-26', '2018-03-26 18:00:00', datetime.datetime格式
    ---------------------------------------------------------------------------------
    修改:宋国洋   添加多参数类型的转换,且非datetime格式的数据只精确到天,datetime格式精确到秒
    """

    if isinstance(obj_value, datetime.datetime) or isinstance(obj_value, str):
        if isinstance(obj_value, datetime.datetime):
            if add > 0:
                obj_value += datetime.timedelta(days=add)
            time_stamp = int(time.mktime(obj_value.timetuple()))
        else:
            obj_value = obj_value.strip()
            # 只获取字符串中的数字
            string_obj = ""
            for st in re.findall(r'\d', obj_value):
                string_obj += st
            if len(string_obj) < 8:
                raise ValueError("illegal param")
            y, m, d, h = string_obj[:4], string_obj[4:6], string_obj[6:8], string_obj[8:10]
            t_date = datetime.datetime(int(y), int(m), int(d), int(h))
            if add > 0:
                t_date += datetime.timedelta(days=add)
            time_stamp = int(time.mktime(t_date.timetuple()))
        return time_stamp
    else:
        raise ValueError("param type must be str or datetime.datetime")
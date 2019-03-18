# encoding: utf-8
import json

from libs.utils import db, from_unixtime, render_template, filter_word_flag, ajax, time
from libs.utils.ajax import ajax_ok, ajax_fail

"""
功能：获取教师所带班级id  判断老师是否有所带班级
"""


def jxhd_class_list(request):
    context = {}
    teacher_data = db.default.mobile_order_region.filter(user_id=274, user_type=3, del_state=0)[:]
    class_id = []
    for teacher in teacher_data:
        class_id.append(teacher.unit_class_id)
    context["class_id"] = class_id
    if len(class_id) > 0:
        return render_template(request, '/index.html', context)
    else:
        return render_template(request, '/not_content.html', context)




"""
获取班级名字  老师名字
"""


def get_unit_name(request):
    context = {}
    if request.method == 'GET':
        user_id = request.user.id
        real_name = 'dbj'
        sql = '''
             SELECT
                B.unit_name,
                B.id as unit_id
             FROM
                 mobile_order_region A
             INNER JOIN school_unit_class B ON A.unit_class_id = B.id 
             WHERE
                    a.user_id = %s 
                  AND a.del_state = 0 
                  AND a.is_pend = 0 
                  AND a.user_type = 3;
                    ''' % user_id
        unit_names = db.default.fetchall_dict(sql)
        context["real_name"] = real_name
        context["unit_names"] = unit_names
    return ajax_ok(data=context)
    # return render_template(request, '/interaction/index.html', context)


"""
发送
"""


def send_message(request):
    if request.method == "POST":
        args = request.QUERY.casts(
            send_type=str,
            content=str,
            addusername=str,
            classlist=str,
            send_time=str
        )
        user_id = request.user.id
        send_type = args.send_type  # 发送type ' 0-定时发送 1-立即发送'
        content = args.content  # 发送的内容
        content = filter_word_flag(content)
        addusername = args.addusername  # 署名
        send_time = args.send_time  # 发送时间
        classlist = args.classlist  # 发送的班级列表 # 将传过来的字符串转换成对象   [1,2,3,5,6]
        if not send_type or not content or not addusername or not classlist or not send_time:
            return ajax.jsonp_fail(request, message="参数不完整！")
        if send_type == "1":
            # 立即发送
            timeStamp = int(time.time())
        else:
            timeArray = time.strptime(send_time, "%Y-%m-%d %H:%M:%S")
            timeStamp = int(time.mktime(timeArray))  # 将格式化时间转换为时间戳
        if send_type == "0" and timeStamp < int(time.time()):
            return ajax.jsonp_fail(request, message="定时时间不能小于当前时间！")
        # 以json格式输出选中的班级id
        classlist = json.loads(classlist)
        print("classlist",classlist)
        classesids = []
        phone = []
        # 输出班级id 数组格式
        for i in classlist:
            classesids.append(i['unit_id'])
        print("classesids", classesids)
        if len(classlist) == 0:
            return ajax.jsonp_fail(request, message="参数不完整！")
        # 遍历选中的班级下面每个用户的手机号
        for i in classesids:
            phone_sql = '''
                SELECT
                    a.phone_number
                FROM
                    mobile_order_region mor
                INNER JOIN auth_user a ON a.id = mor.user_id
                WHERE
                    mor.unit_class_id = %s
                AND MOR.user_type = 1
                AND MOR.is_update = 0
                AND MOR.del_state = 0
                AND MOR.is_pend = 0;
            ''' % i
            print("phone_sql", phone_sql)
            phone_data = db.default.fetchall_dict(phone_sql)
            print("phone_data", phone_data)
            for a in phone_data:
                phone.append(a['phone_number'])
        if len(phone) > 0:
            phone = list(set(phone))
            print("phone", phone)
            phonesre = ','.join(phone)
            print("phonesre", phonesre)
            message_info = []
        # 先在hdkt_jxhd写一条主记录    然后在hdkt_jxhd_class创建多条班级记录
        id = db.default.hdkt_jxhd.create(
            add_user=user_id,
            type=1,
            context_type=2,
            content=content,
            status=send_type,  # '-1-取消发送 0-未发送 1-已发送'
            add_time=int(time.time()),
            addusername=addusername,
            send_time=timeStamp
        )
        if id:  # 创建完主记录再在详情表添加记录
            for i in classlist:  # 遍历班级列表
                i['message_id'] = id
                i['status'] = send_type
                sql_num = '''
                    select count(id) as num from `mobile_order_region` WHERE unit_class_id = %s and del_state = 0 and user_type = 1 AND is_pend = 0
                ''' % i['unit_id']
                print("sql_num", sql_num)
                data_num = db.default.fetchone_dict(sql_num)
                if data_num['num'] < 1:
                    sql_class = '''
                        SELECT unit_name from `school_unit_class` where id = %s
                    ''' % i['unit_id']
                    data_class = db.default.fetchone_dict(sql_class)
                    return ajax.jsonp_fail(request, message=data_class['unit_name'] + "内不存在学生")
                message_info.append(i)
            db.default.hdkt_jxhd_class.bulk_create(message_info)
    return ajax_ok(data="发送成功")




"""
功能: 已发送页面
"""


def send_message_list(request):

    context = {}
    user_id = request.user.id
    sql = '''
       select a.content,c.unit_name,d.name as school_name,a.send_time,
        CASE
            b.status 
            WHEN -1 THEN
            '取消发送' 
            WHEN 0 THEN
            '未发送'  
             WHEN 1 THEN
            '已发送'  
            END 'status_name'
       from hdkt_jxhd a 
       INNER join hdkt_jxhd_class b 
        on a.id = b.message_id
        INNER join `school_unit_class` c 
        on c.id = b.unit_id
        INNER join `school` d
        on c.school_id = d.id
        where a.add_user = %s and a.status != -1 and a.type = 1
        ORDER BY a.add_time desc
    ''' % user_id
    print(sql)
    messages = db.default.fetchall_dict(sql)
    for i in messages:
        i['send_time'] = from_unixtime(i['send_time'], str_format='%Y{y}%m{m}%d{d}' + ' %H:%M:%S').format(y='年', m='月', d='日')
    context["data"] = messages
    return ajax_ok(data=context)



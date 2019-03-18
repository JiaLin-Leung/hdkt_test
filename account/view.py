# # encoding: utf-8
# '''
# @author: dbj
# @file: view.py
# @time: 2019/3/12 11:45
# @desc:
# '''
# import time
# from linecache import cache
#
# from django.contrib import auth
#
# from libs.utils import ajax, db, render_template, auth_token, datetime
#
#
# def login(request):
#     """
#     功能: 登录 /login/
#     --------------------------------------------------
#     修改人                修改日期              修改原因
#     ----------------------------------------------------
#     梁佳霖               2018年12月11日
#     """
#     if request.method == "POST":
#         args = request.QUERY.casts(
#             user_name=str,
#             pass_word=str,
#             role_type=int
#         )
#         # 获取参数
#         username = args.user_name or ''
#         password = args.pass_word or ''
#         role_type = args.role_type
#         cache_name = f"login_key_{username}"
#         # 判断缓存
#         valid_data = cache.get(cache_name)
#         if valid_data:
#             if int(valid_data["valid_num"]) >= 3:
#                 return ajax.jsonp_fail(request, message='错误次数超过3次，请2分钟后重试！')
#         # 参数判断
#         # 验证用户是否存在
#         user_exists = db.default.auth_user.filter(phone_number=username, is_active=1, role_type=role_type)
#         if not user_exists.exists():
#             return ajax.jsonp_fail(request, message='账号不存在')
#         username = user_exists.first().get('username')
#         # 验证用户密码是否正确
#         user = auth.authenticate(username=username, password=password)
#         # 验证通过
#         if user:
#             context = {}
#             auth.login(request, user)
#             user_temp = user_exists.first()
#             context['user_id'] = user_temp.id
#             context['real_name'] = user_temp.real_name
#             # context['phone'] = user_temp.phone_number
#             context['tbkt_token'] = auth_token.create_token(user_temp.id)
#             # 信息记录模块
#             # 1、更新最后登录时间
#             user_exists.update(last_login=datetime.datetime.now())
#             # 2、更新登录次数
#             login_num = user_temp.logins + 1
#             user_exists.update(logins=login_num)
#             # 3、验证成功后写入登录记录表
#             db.default.hdkt_logins.create(
#                 user_id=user_temp.id,
#                 login_time=int(time.time()),
#                 login_type='1',
#                 ip="127.0.0.1",
#                 user_type='1'
#             )
#
#             return ajax.jsonp_ok(request, context, message='登录成功')
#         # 验证未通过 密码错误
#         else:
#             valid_num = 1
#             if valid_data:
#                 valid_num = int(valid_data["valid_num"])
#                 valid_num += 1
#             # 删除原来的缓存
#             cache.delete(cache_name)
#             # 写入新缓存
#             cache.set(cache_name, {"valid_num": valid_num}, 60 * 2)
#             return ajax.jsonp_fail(request, message='密码错误')
#     sql = """SELECT version, download, DATE_FORMAT(FROM_UNIXTIME(release_date),"%Y-%m-%d")
#                AS date FROM hdkt.system_version WHERE file_type = 1 ORDER BY -api, -release_date;"""
#     print(sql)
#     app_obj = db.default.fetchone_dict(sql)
#     print("app_obj", app_obj)
#     return render_template(request, 'login.html', {"data": app_obj})
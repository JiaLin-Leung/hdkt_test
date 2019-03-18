# coding: utf-8
"""同步课堂登录模块"""
import time
import hashlib
import base64
import random
from .common import strxor
from django.conf import settings


def get_random_string(length=12,
                      allowed_chars='abcdefghijklmnopqrstuvwxyz'
                                    'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'):
    """
    Returns a securely generated random string.

    The default length of 12 with the a-z, A-Z, 0-9 character set returns
    a 71-bit value. log_2((26+26+10)^12) =~ 71 bits
    """
    return ''.join(random.choice(allowed_chars) for i in range(length))


def sha1_encode_password(password, salt=''):
    if not salt:
        salt = get_random_string()
    hash = hashlib.sha1((salt + password).encode()).hexdigest()
    return "sha1$%s$%s" % (salt, hash)


def pbkdf2(password, salt, iterations, dklen=0, digest=None):
    """
    Implements PBKDF2 with the same API as Django's existing
    implementation, using the stdlib.

    This is used in Python 2.7.8+ and 3.4+.
    """
    if digest is None:
        digest = hashlib.sha256
    if not dklen:
        dklen = None
    return hashlib.pbkdf2_hmac(
        digest().name, password, salt, iterations, dklen)


def pbkdf2_encode_password(password, salt=''):
    iterations = 20000
    if not salt:
        salt = get_random_string()
    hash = pbkdf2(password, salt, iterations, digest=hashlib.sha256)
    hash = base64.b64encode(hash).decode('ascii').strip()
    return "pbkdf2_sha256$%d$%s$%s" % (iterations, salt, hash)


def encode_password(password, salt=''):
    algorithm = settings.PASSWORD_ALGORITHM
    if algorithm == 'sha1':
        hash = sha1_encode_password(password)
    elif algorithm == 'pbkdf2':
        hash = pbkdf2_encode_password(password)
    else:
        assert 0, 'Unsupport PASSWORD_ALGORITHM: %s' % algorithm
    return hash


def verify_password(password, encoded):
    """验证密码是否正确, 返回True/False"""
    if encoded.startswith('sha1$'):
        algorithm, salt, hash = encoded.split('$', 2)
        encoded_2 = sha1_encode_password(password, salt)
    elif encoded.startswith('pbkdf2_sha256$'):
        algorithm, iterations, salt, hash = encoded.split('$', 3)
        encoded_2 = pbkdf2_encode_password(password, salt)
    else:
        return False
    return encoded == encoded_2


def encode_plain_password(password):
    """编码明文密码"""
    if isinstance(password, str):
        return base64.b64encode(password.encode())
    else:
        return base64.b64encode(password)


def decode_plain_password(data):
    """解码明文密码"""
    return base64.b64decode(data)


def create_checkcode(user_id, expire_time):
    """
    快速计算session校验码
    """
    return user_id ^ expire_time ^ int(settings.SECRET_KEY)


def create_token(user_id):
    """
    生成session值
    1. 校验码 = 用户ID ^角色ID ^ 过期时间戳 ^ 服务器SECRET_KEY
    2. token = 用户ID|角色ID|过期时间戳|校验码
    3. token = 异或加密(token, 服务器SECRET_KEY)
    4. token = Base64编码(token)
    -------------------------
    添加python3的兼容
    """
    try:
        expire_time = int(time.time()) + settings.SESSION_COOKIE_AGE
        code = create_checkcode(user_id, expire_time)
        token = "%s|%s|%s" % (user_id, expire_time, code)
        # 对token进行encode,转换成bytearray可接收的类型
        token = strxor(token.encode(), int(settings.SECRET_KEY))
        # 去除base64编码中的等号, 避免cookie带引号
        token = base64.b64encode(token).decode().rstrip("=")
        return token
    except Exception as e:
        print(e)


def decode_token(token):
    """
    解析token, 成功返回{user_id:用户ID, expire:过期时间戳}, 失败返回None
    """
    if not token:
        return
    try:
        # 填充base64被去掉的等号
        token += '=' * (-len(token) % 4)
        token = base64.b64decode(token)
        token = strxor(token, int(settings.SECRET_KEY))
        # 将token转换成str类型
        token = token.decode("utf-8")
        user_id, expire_time, code = token.split('|')
        user_id = int(user_id)
        expire_time = int(expire_time)
        code = int(code)
    except Exception as e:
        print(e)
        return
    nowt = time.time()
    if nowt > expire_time:
        return
    check_code = create_checkcode(user_id, expire_time)
    if code != check_code:
        return
    return {'user_id': user_id, 'expire': expire_time}


def login(request, user_id):
    """
    登录: 创建新令牌并暂存起来, 由中间件添加cookie和响应头.
    --------------------------
    王晨光     2017-3-7
    --------------------------
    """
    request._newtoken = token = create_token(user_id)
    return token


def login_response(response, token):
    """
    登录: 设置浏览器cookie和相应头.
    --------------------------
    王晨光     2016-12-21
    --------------------------
    @param response: HttpResponse
    @param token: 如果不提供就自动创建一个token
    @return: 成功返回token值, 失败返回None
    """
    response.set_cookie(settings.SESSION_COOKIE_NAME,
                        token, max_age=settings.SESSION_COOKIE_AGE,
                        expires=None, domain=settings.SESSION_COOKIE_DOMAIN,
                        path=settings.SESSION_COOKIE_PATH,
                        secure=settings.SESSION_COOKIE_SECURE or None,
                        httponly=False)
    response['Tbkt-Token'] = token
    return token

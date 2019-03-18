# coding: utf-8
import logging
import traceback
import simplejson as json
from django.http.request import QueryDict
from django.http import HttpRequest, HttpResponse, Http404, HttpResponseRedirect
from libs.utils import ajax, casts, loads
log = logging.getLogger(__name__)
# 给request.GET, request.POST, request.QUERY注入新方法
QueryDict.casts = casts
HttpRequest.loads = loads
# 不跳转登录的路由
need_login = ["/apidoc/", "/login/", "/site_media/", "/school/login/", "/findpasswordpage/"]


class AuthenticationMiddleware(object):
    def process_request(self, request):
        try:
            path = str(request.path)
            # 如果请求的路径为js,css文件不处理
            if path.startswith('/site_media/'):
                return None
            # 如果请求的路径为模板文件不处理
            if path.startswith('/theme_media/'):
                return None
            if path.startswith('/s_theme_media/'):
                return None
            if path.startswith('/s_site_media/'):
                return None
            return self._process_request(request)
        except Exception as e:
            log.error(e)

    @staticmethod
    def cross_domain(request, response=None):
        """
        添加跨域头
        """
        origin = request.META.get('HTTP_ORIGIN', '*')
        if request.method == 'OPTIONS' and not response:
            response = HttpResponse()
        if not response:
            return
        response['Access-Control-Allow-Origin'] = origin
        response['Access-Control-Allow-Methods'] = 'GET,POST'
        response['Access-Control-Allow-Credentials'] = 'true'
        response['Access-Control-Allow-Headers'] = 'x-requested-with,content-type,Tbkt-Token,App-Type'
        response['Access-Control-Max-Age'] = '1728000'
        return response

    def _process_request(self, request):
        try:
            # REQUEST过期, 使用QUERY代替
            query = request.GET.copy()
            query.update(request.POST)
            path = str(request.path)
            # 把body参数合并到QUERY
            try:
                if request.body:
                    body = json.loads(request.body)
                    query.update(body)
            except Exception as e:
                pass
            request.QUERY = query
            r = self.cross_domain(request)
            if r:
                return r
            for d in need_login:
                if path.startswith(d):
                    return
            if request.user.is_anonymous():
                if path.startswith("/school/"):
                    return HttpResponseRedirect('/school/login/')
                else:
                    return HttpResponseRedirect('/login/')
        except Exception as e:
            log.error(e)

    def process_response(self, request, response):
        try:
            # 添加跨域头
            self.cross_domain(request, response)
            return response
        except Exception as e:
            log.error(e)

    def process_exception(self, request, exception):
        """
        功能说明:view函数抛出异常处理
        -------------------------------
        修改人     修改时间
        --------------------------------
        徐威      2013-07-17
        """
        if isinstance(exception, Http404):
            return
        exc = traceback.format_exc()
        log.error(exc)
        r = ajax.jsonp_fail(request, data='', error="500", message="抱歉，服务器开小差了，请联系客服12556185")
        r.status_code = 500
        return r



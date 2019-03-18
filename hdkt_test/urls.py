"""hdkt_test URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.views.static import serve

from hdkt_test import settings

urlpatterns = [
    # url(r'^site_media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_SITE}),
    # url(r'^theme_media/(?P<path>.*)$', serve, {'document_root': settings.THEME_SITE}),
    # url(r'^s_site_media/(?P<path>.*)$', serve, {'document_root': settings.S_MEDIA_SITE}),
    # url(r'^s_theme_media/(?P<path>.*)$', serve, {'document_root': settings.S_THEME_SITE}),

]
urlpatterns += [
    # url(r'^', include('account.urls')),
    # url(r'^', include('resources.urls')),
    url(r'^', include('jxhd.urls')),
]

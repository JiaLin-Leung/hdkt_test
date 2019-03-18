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
from django.conf.urls import url
from jxhd import view
urlpatterns = [
    url(r'^interaction_index/', view.jxhd_class_list),
    url(r'^get_unit_name/', view.get_unit_name),
    url(r'^send_message/', view.send_message),
    url(r'^send_message_list/', view.send_message_list),
]

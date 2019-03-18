"""
功能说明：数据分页
-------------------------------------------------------------
修改人                    修改时间
-------------------------------------------------------------
王泽华                    2018－4－9
"""
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from . import paginator as api_paginator


def Page(data_list, page, page_num=10):
    """
       数据分页
    """
    data_list = data_list
    page = page
    after_range_num = 3  # 当前页前显示页数
    befor_range_num = 2  # 当前页后显示页数
    try:  # 如果请求的页码少于1或者类型错误，则跳转到第1页
        if page < 1:
            page = 1
    except ValueError:
        page = 1
    paginator = Paginator(data_list, page_num)
    try:
        contacts = paginator.page(page)
    except PageNotAnInteger:
        contacts = paginator.page(1)
    except EmptyPage:
        contacts = paginator.page(paginator.num_pages)
    # paginator = Paginator(data_list, 8)  # 设置在每页显示的数量
    # try:  # 跳转到请求页面，如果该页不存在或者超过则跳转到尾页
    #     data_list = paginator.page(page)
    # except(EmptyPage, InvalidPage, PageNotAnInteger):
    #     data_list = paginator.page(paginator.num_pages)
    if page >= after_range_num:
        page_range = paginator.page_range[page - after_range_num:page + befor_range_num]
    else:
        page_range = paginator.page_range[0:int(page) + befor_range_num]
    return contacts, page_range


def api_page(page_data, page, page_total, page_num=10):
    """
    基于api接口分页功能
    王世成  2018-10-15
    :param page_data:  当前页数据
    :param page:       当前页
    :param page_total: 一共多少页
    :param page_num:   每页展示多少条
    :return: 
    """
    page = page
    after_range_num = 3  # 当前页前显示页数
    before_range_num = 2  # 当前页后显示页数
    try:  # 如果请求的页码少于1或者类型错误，则跳转到第1页
        if page < 1:
            page = 1
    except ValueError:
        page = 1
    paginator = api_paginator.Paginator(page_data, page_num, page_total)
    try:
        contacts = paginator.page(page)
    except PageNotAnInteger:
        contacts = paginator.page(1)
    except EmptyPage:
        contacts = paginator.page(paginator.num_pages)
    if page >= after_range_num:
        page_range = paginator.page_range[page - after_range_num:page + before_range_num]
    else:
        page_range = paginator.page_range[0:int(page) + before_range_num]
    return contacts, page_range

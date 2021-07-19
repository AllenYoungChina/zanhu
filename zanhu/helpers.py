#!/usr/bin/python3
# -*- coding:utf-8 -*-
# __author__ = '__AYC__'

from functools import wraps

from django.http import HttpResponseBadRequest
from django.views.generic import View
from django.core.exceptions import PermissionDenied


def ajax_required(f):
    """验证是否为AJAX请求"""

    @wraps(f)
    def wrap(request, *args, **kwargs):
        if not request.is_ajax():
            return HttpResponseBadRequest('不是AJAX请求！')
        return f(request, *args, **kwargs)

    return wrap


class AuthorRequiredMixin(View):
    """验证是否为原作者，用于动态删除、文章编辑等"""

    def dispatch(self, request, *args, **kwargs):
        # 动态和文章都有user属性
        if self.get_object().user.username != self.request.user.username:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

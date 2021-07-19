#!/usr/bin/python3
# -*- coding:utf-8 -*-
# __author__ = '__AYC__'

from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from zanhu.notifications.models import Notification


class NotificationListView(LoginRequiredMixin, ListView):
    """通知列表页"""
    model = Notification
    context_object_name = 'notification_list'
    template_name = 'notifications/notification_list.html'

    def get_queryset(self):
        """自定义查询范围"""
        return self.request.user.notifications.unread()


@login_required
def get_latest_notifications(request):
    """最近的未读通知"""
    notifications = request.user.notifications.get_most_recent()
    return render(request, 'notifications/most_recent.html',
                  {'notifications': notifications})


@login_required
def mark_all_as_read(request):
    """标记所有通知为已读"""
    request.user.notifications.mark_all_as_read()
    redirect_url = request.GET.get('next')
    messages.add_message(request, messages.SUCCESS,
                         f'{request.user.username}的所有通知已标为已读！')
    if redirect_url:
        return redirect(redirect_url)
    return redirect('notifications:unread')


@login_required
def mark_as_read(request, slug):
    """标记单条消息为已读"""
    notification = get_object_or_404(Notification, slug=slug)
    notification.mark_as_read()
    redirect_url = request.GET.get('next')
    messages.add_message(request, messages.SUCCESS,
                         f'通知{notification}已标为已读！')
    if redirect_url:
        return redirect(redirect_url)
    return redirect('notifications:unread')


def notification_handler(actor, recipient, verb, action_object, **kwargs):
    """
    通知处理器
    :param actor: request.user对象
    :param recipient: User Instance 接收者实例，可以是一个或多个对象
    :param verb: str 通知类别
    :param action_object: Instance 动作对象的实例
    :param kwargs: key，id_value等
    :return: None
    """
    key = kwargs.get('key', 'notification')
    id_value = kwargs.get('id_value', None)
    # 记录通知内容
    Notification.objects.create(
        actor=actor,
        recipient=recipient,
        verb=verb,
        action_object=action_object
    )
    # 将消息传递给consumer.py中的的receive方法
    channel_layer = get_channel_layer()  # 获取频道层
    payload = {
        'type': 'receive',  # 固定的，传递给consumer的receive方法
        'key': key,
        'actor_name': actor.username,
        'action_object': action_object.user.username,
        'id_value': id_value
    }
    async_to_sync(channel_layer.group_send)('notifications', payload)  # 将消息传递给consumer，并将异步代码转为同步

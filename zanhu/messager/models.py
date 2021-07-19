#!/usr/bin/python3
# -*- coding:utf-8 -*-
# __author__ = '__AYC__'

import uuid

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models


class MessageQuerySet(models.query.QuerySet):
    """自定义查询集"""

    def get_conversation(self, sender, recipient):
        """用户间的私信会话"""
        qs_one = self.filter(sender=sender, recipient=recipient).select_related('sender', 'recipient')
        qs_two = self.filter(sender=recipient, recipient=sender).select_related('sender', 'recipient')
        return qs_one.union(qs_two).order_by('created_at')

    def get_most_recent_conversation(self, recipient):
        """获取最近一次私信的用户"""
        try:
            qs_sent = self.filter(sender=recipient).select_related('sender', 'recipient')
            qs_received = self.filter(recipient=recipient).select_related('sender', 'recipient')
            qs = qs_sent.union(qs_received).latest('created_at')
            # 如果登录用户有发送消息，返回消息的接收者
            if qs.sender == recipient:
                return recipient
            # 否则返回消息的发送者
            return qs.sender
        except self.model.DoesNotExist:
            # 如果模型实例不存在，则返回当前登录的用户
            return get_user_model().objects.get(username=recipient.username)


class Message(models.Model):
    """用户间私信"""
    uuid_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='sent_messages',
                               blank=True, null=True, on_delete=models.SET_NULL, verbose_name='发送者')
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='received_messages',
                                  blank=True, null=True, on_delete=models.SET_NULL, verbose_name='接收者')
    message = models.TextField('内容', blank=True, null=True)
    unread = models.BooleanField('是否未读', default=True, db_index=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True, db_index=True)
    objects = MessageQuerySet.as_manager()

    class Meta:
        verbose_name = '私信'
        verbose_name_plural = verbose_name
        ordering = ('-created_at',)

    def __str__(self):
        return self.message

    def mark_as_read(self):
        """标记消息为已读"""
        if self.unread:
            self.unread = False
            self.save()

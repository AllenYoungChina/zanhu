#!/usr/bin/python3
# -*- coding:utf-8 -*-
# __author__ = '__AYC__'

import uuid

from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core import serializers
from slugify import slugify


class NotificationQuerySet(models.query.QuerySet):
    """自定义查询结果集"""

    def unread(self):
        """返回未读消息"""
        return self.filter(unread=True).select_related('actor', 'recipient')

    def read(self):
        """返回已读消息"""
        return self.filter(unread=False).select_related('actor', 'recipient')

    def mark_all_as_read(self, recipient=None):
        """标记已读，可以传入接收者参数"""
        qs = self.unread()
        if recipient:
            qs = qs.filter(recipient=recipient)
        return qs.update(unread=False)

    def mark_all_as_unread(self, recipient=None):
        """标记为未读，可以传入接收者参数"""
        qs = self.read()
        if recipient:
            qs = qs.filter(recipient=recipient)
        return qs.update(unread=True)

    def get_most_recent(self, recipient=None):
        """获取最近5条消息，可以传入接收者参数"""
        qs = self.unread()
        if recipient:
            qs = qs.filter(recipient=recipient)
        return qs[:5]

    def serialize_latest_notifications(self, recipient=None):
        """序列化最近5条通知，可以传入接收者参数"""
        qs = self.get_most_recent(recipient=recipient)
        notification_dic = serializers.serialize('json', qs)
        return notification_dic


class Notification(models.Model):
    """消息通知"""
    NOTIFICATION_TYPE = (
        ('L', '赞了'),  # like
        ('C', '评论了'),  # comment
        ('F', '收藏了'),  # favor
        ('A', '回答了'),  # answer
        ('W', '接受了回答'),  # accept
        ('R', '回复了'),  # reply
        ('I', '登录'),  # logged in
        ('O', '退出'),  # logged out
    )

    uuid_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='notify_actor',
                              on_delete=models.CASCADE, verbose_name='触发者')
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, related_name='notifications',
                                  on_delete=models.CASCADE, verbose_name='接收者')
    unread = models.BooleanField('是否未读', default=True, db_index=True)
    slug = models.SlugField('URL别名', max_length=80, blank=True, null=True)
    verb = models.CharField('通知类别', max_length=1, choices=NOTIFICATION_TYPE)
    created_at = models.DateTimeField('创建时间', auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    content_type = models.ForeignKey(ContentType, related_name='notify_action_object', blank=True, null=True,
                                     on_delete=models.CASCADE)
    object_id = models.CharField(max_length=255, blank=True, null=True)
    action_object = GenericForeignKey()

    objects = NotificationQuerySet.as_manager()  # 使用自定义查询结果集

    class Meta:
        verbose_name = '通知'
        verbose_name_plural = verbose_name
        ordering = ('-created_at',)

    def __str__(self):
        if self.action_object:
            return f'{self.actor} {self.get_verb_display()} {self.action_object}。'
        return f'{self.actor} {self.get_verb_display()}。'

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        """重写save方法，自动生成slug"""
        if not self.slug:
            self.slug = slugify(f'{self.recipient} {self.uuid_id} {self.verb}')
        super().save()

    def mark_as_read(self):
        """标记为已读"""
        if self.unread:
            self.unread = False
            self.save()

    def mark_as_unread(self):
        """标记为未读"""
        if not self.unread:
            self.unread = True
            self.save()

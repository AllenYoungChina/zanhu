#!/usr/bin/python3
# -*- coding:utf-8 -*-
# __author__ = '__AYC__'

import uuid

from django.db import models
from django.contrib.auth import settings
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from zanhu.notifications.views import notification_handler


class News(models.Model):
    uuid_id = models.UUIDField('主键', primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, on_delete=models.SET_NULL,
                             related_name='publisher', verbose_name='用户')
    parent = models.ForeignKey('self', blank=True, null=True, on_delete=models.CASCADE,
                               related_name='thread', verbose_name='自关联')
    content = models.TextField('内容')
    liked = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='liked_news',
                                   verbose_name='点赞用户')
    reply = models.BooleanField('是否为评论', default=False)
    created_at = models.DateTimeField('创建时间', auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '首页'
        verbose_name_plural = verbose_name
        ordering = ('-created_at',)

    def __str__(self):
        return self.content

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        """重写save方法，有新动态时候通知所有在线用户"""
        super().save()
        if not self.reply:
            channel_layer = get_channel_layer()
            payload = {
                'type': 'receive',
                'key': 'additional_news',
                'actor_name': self.user.username
            }
            async_to_sync(channel_layer.group_send)('notifications', payload)

    def switch_like(self, user):
        """点赞或取消赞"""
        # 用户已点过赞，则取消赞
        if user in self.liked.all():
            self.liked.remove(user)
        # 用户没有赞过，则添加赞
        else:
            self.liked.add(user)
            # 通知楼主，给自己点赞则不通知
            if user.username != self.user.username:
                notification_handler(user, self.user, 'L', self, id_value=str(self.uuid_id), key='social_update')

    def get_parent(self):
        """返回自关联中的上一级或本身（无上一级）"""
        return self.parent if self.parent else self

    def reply_this(self, user, text):
        """
        回复动态
        :param user: 评论用户
        :param text: 评论内容
        :return: 评论
        """
        parent = self.get_parent()
        reply = News.objects.create(
            user=user,
            parent=self.get_parent(),
            content=text,
            reply=True
        )
        notification_handler(user, parent.user, 'R', parent,
                             id_value=str(parent.uuid_id), key='social_update')
        return reply

    def get_thread(self):
        """获取关联到当前记录的所有记录"""
        parent = self.get_parent()
        return parent.thread.all()

    def comment_count(self):
        """获取动态的评论数量"""
        return self.get_thread().count()

    def count_likers(self):
        """获取动态的点赞数量"""
        return self.liked.count()

    def get_likers(self):
        """获取当前动态的所有点赞用户"""
        return self.liked.all()

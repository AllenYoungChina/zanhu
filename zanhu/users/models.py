#!/usr/bin/python3
# -*- coding:utf-8 -*-
# __author__ = '__AYC__'

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse


class User(AbstractUser):
    """自定义用户模型"""
    nickname = models.CharField('昵称', max_length=32, blank=True, null=True)
    job_title = models.CharField('职称', max_length=32, blank=True, null=True)
    introduction = models.TextField('简介', blank=True, null=True)
    picture = models.ImageField('头像', upload_to='profile_pics/', blank=True, null=True)
    location = models.CharField('地址', max_length=128, blank=True, null=True)
    personal_url = models.URLField('个人链接', max_length=255, blank=True, null=True)
    weibo = models.URLField('微博', max_length=255, blank=True, null=True)
    zhihu = models.URLField('知乎', max_length=255, blank=True, null=True)
    github = models.URLField('GitHub', max_length=255, blank=True, null=True)
    linkedin = models.URLField('Linkedin', max_length=255, blank=True, null=True)

    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '用户'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.username

    def get_absolute_url(self):
        return reverse("users:detail", kwargs={"username": self.username})

    def get_profile_name(self):
        return self.nickname if self.nickname else self.username

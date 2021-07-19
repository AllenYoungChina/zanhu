#!/usr/bin/python3
# -*- coding:utf-8 -*-
# __author__ = '__AYC__'

from test_plus.test import TestCase

from zanhu.news.models import News


class TestNewsModel(TestCase):

    def setUp(self):
        self.user = self.make_user('user01')
        self.other_user = self.make_user('user02')
        self.first_news = News.objects.create(user=self.user, content='第一条动态')

    def test__str__(self):
        self.assertEqual(self.first_news.__str__(), '第一条动态')

    def test_switch_like(self):
        # 点赞
        self.first_news.switch_like(self.other_user)
        self.assertIn(self.other_user, self.first_news.get_likers())
        self.assertEqual(self.first_news.count_likers(), 1)
        # 取消赞
        self.first_news.switch_like(self.other_user)
        self.assertNotIn(self.other_user, self.first_news.get_likers())
        self.assertEqual(self.first_news.count_likers(), 0)

    def test_reply_this(self):
        initial_count = News.objects.count()
        reply = self.first_news.reply_this(self.other_user, '第一条动态的评论')
        self.assertEqual(self.first_news.comment_count(), 1)
        self.assertEqual(News.objects.count(), initial_count + 1)
        self.assertIn(reply, self.first_news.get_thread())

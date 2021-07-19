#!/usr/bin/python3
# -*- coding:utf-8 -*-
# __author__ = '__AYC__'

from django.test import Client
from django.urls import reverse
from test_plus.test import TestCase

from zanhu.news.models import News


class TestNewsViews(TestCase):

    def setUp(self):
        # 创建用户
        self.user = self.make_user('user01')
        self.other_user = self.make_user('user02')
        # 创建客户端
        self.client = Client()
        self.other_client = Client()
        # 用户登录
        self.client.login(username='user01', password='password')
        self.other_client.login(username='user02', password='password')
        # 创建动态及评论
        self.first_news = News.objects.create(user=self.user, content='第一条动态')
        self.second_news = News.objects.create(user=self.other_user, content='第二条动态')
        self.first_comment = News.objects.create(
            user=self.other_user,
            content='第一条动态的评论',
            parent=self.first_news,
            reply=True
        )

    def test_news_list(self):
        """测试动态列表页"""
        response = self.client.get(reverse('news:list'))
        self.assert_http_200_ok(response)
        self.assertIn(self.first_news, response.context['news_list'])
        self.assertIn(self.second_news, response.context['news_list'])
        self.assertNotIn(self.first_comment, response.context['news_list'])

    def test_delete_news(self):
        """删除动态"""
        initial_count = News.objects.count()
        # 删除别人的动态
        response = self.client.post(reverse('news:delete_news', kwargs={'pk': self.second_news.pk}))
        self.assert_http_403_forbidden(response)
        self.assertEqual(News.objects.count(), initial_count)
        # 删除自己的动态
        response = self.client.post(reverse('news:delete_news', kwargs={'pk': self.first_news.pk}))
        self.assert_http_302_found(response)
        self.assertEqual(News.objects.count(), initial_count - 2)  # 级联删除了评论

    def test_post_news(self):
        """发送动态"""
        initial_count = News.objects.count()
        response = self.client.post(
            reverse('news:post_news'),
            {'post': '第三条动态'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'  # 表示发送Ajax Request请求
        )
        self.assert_http_200_ok(response)
        self.assertEqual(News.objects.count(), initial_count + 1)

    def test_like_news(self):
        """点赞"""
        response = self.other_client.post(
            reverse('news:like_post'),
            {'news': self.first_news.pk},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'  # 表示发送Ajax Request请求
        )
        self.assert_http_200_ok(response)
        self.assertIn(self.other_user, self.first_news.get_likers())
        self.assertEqual(self.first_news.count_likers(), 1)
        self.assertEqual(response.json()['likes'], 1)

    def test_get_thread(self):
        """获取评论"""
        response = self.client.get(
            reverse('news:get_thread'),
            {'news': self.first_news.pk},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'  # 表示发送Ajax Request请求
        )
        self.assert_http_200_ok(response)
        self.assertEqual(response.json()['uuid'], str(self.first_news.pk))
        self.assertIn('第一条动态', response.json()['news'])
        self.assertIn('第一条动态的评论', response.json()['thread'])

    def test_post_comment(self):
        """发表评论"""
        response = self.client.post(
            reverse('news:post_comment'),
            {'reply': '第二条动态的评论', 'parent': self.second_news.pk},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assert_http_200_ok(response)
        self.assertEqual(response.json()['comments'], 1)

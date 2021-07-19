#!/usr/bin/python3
# -*- coding:utf-8 -*-
# __author__ = '__AYC__'

from django.urls import reverse, resolve

from test_plus.test import TestCase


class TestNewsURLs(TestCase):

    def test_news_list_reverse(self):
        self.assertEqual(reverse('news:list'), '/news/')

    def test_news_list_resolve(self):
        self.assertEqual(resolve('/news/').view_name, 'news:list')

    def test_post_news_reverse(self):
        self.assertEqual(reverse('news:post_news'), '/news/post-news/')

    def test_post_news_resolve(self):
        self.assertEqual(resolve('/news/post-news/').view_name, 'news:post_news')

    def test_delete_news_reverse(self):
        self.assertEqual(reverse('news:delete_news', kwargs={'pk': 'news_id'}), '/news/delete/news_id/')

    def test_delete_news_resolve(self):
        self.assertEqual(resolve('/news/delete/news_id/').view_name, 'news:delete_news')

    def test_like_post_reverse(self):
        self.assertEqual(reverse('news:like_post'), '/news/like/')

    def test_like_post_resolve(self):
        self.assertEqual(resolve('/news/like/').view_name, 'news:like_post')

    def test_get_thread_reverse(self):
        self.assertEqual(reverse('news:get_thread'), '/news/get-thread/')

    def test_get_thread_resolve(self):
        self.assertEqual(resolve('/news/get-thread/').view_name, 'news:get_thread')

    def test_post_comment_reverse(self):
        self.assertEqual(reverse('news:post_comment'), '/news/post-comment/')

    def test_post_comment_resolve(self):
        self.assertEqual(resolve('/news/post-comment/').view_name, 'news:post_comment')

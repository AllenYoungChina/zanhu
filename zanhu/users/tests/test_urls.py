#!/usr/bin/python3
# -*- coding:utf-8 -*-
# __author__ = '__AYC__'

from test_plus.test import TestCase
from django.urls import reverse, resolve


class TestUserURLs(TestCase):

    def test_user_update_reverse(self):
        self.assertEqual(reverse('users:update'), '/users/update/')

    def test_user_update_resolve(self):
        self.assertEqual(resolve('/users/update/').view_name, 'users:update')

    def test_user_detail_reverse(self):
        self.assertEqual(reverse('users:detail', kwargs={'username': 'testuser'}), '/users/testuser/')

    def test_user_detail_resolve(self):
        self.assertEqual(resolve('/users/testuser/').view_name, 'users:detail')

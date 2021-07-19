#!/usr/bin/python3
# -*- coding:utf-8 -*-
# __author__ = '__AYC__'

from test_plus.test import TestCase
from django.test import RequestFactory

from zanhu.users.views import UserUpdateView


class BaseUserViewTest(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.user = self.make_user()


class TestUserUpdateView(BaseUserViewTest):

    def setUp(self):
        super().setUp()
        self.view = UserUpdateView()
        request = self.factory.get('/fake-url/')
        request.user = self.user
        self.view.request = request

    def test_get_success_url(self):
        self.assertEqual(self.view.get_success_url(), '/users/testuser/')

    def test_get_object(self):
        self.assertEqual(self.view.get_object(), self.user)

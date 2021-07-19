#!/usr/bin/python3
# -*- coding:utf-8 -*-
# __author__ = '__AYC__'

import json
from django.test import RequestFactory
from test_plus.test import CBVTestCase
from django.contrib.messages.storage.fallback import FallbackStorage

from zanhu.qa.models import Question, Answer
from zanhu.qa import views


class BaseQATest(CBVTestCase):

    def setUp(self):
        self.user = self.make_user('user01')
        self.other_user = self.make_user('user02')

        self.question_one = Question.objects.create(
            user=self.user,
            title='问题1',
            content='问题1的内容'
        )
        self.question_two = Question.objects.create(
            user=self.other_user,
            title='问题2',
            content='问题2的内容',
            has_answer=True
        )
        self.answer = Answer.objects.create(
            user=self.user,
            question=self.question_two,
            content='问题2被采纳的回答',
            is_answered=True
        )

        self.request = RequestFactory().get('/fake-url/')
        self.request.user = self.user


class TestQuestionListView(BaseQATest):
    """测试问题列表"""

    def test_context_data(self):
        response = self.get(views.QuestionListView, request=self.request)
        self.assert_http_200_ok(response)
        self.assertQuerysetEqual(response.context_data['questions'],
                                 map(repr, [self.question_one, self.question_two]), ordered=False)
        self.assertContext('popular_tags', Question.objects.get_counted_tags())
        self.assertContext('active', 'all')


class TestAnsweredQuestionListView(BaseQATest):
    """测试已有答案的问题列表"""

    def test_context_data(self):
        response = self.get(views.AnsweredQuestionListView, request=self.request)
        self.assert_http_200_ok(response)
        self.assertQuerysetEqual(response.context_data['questions'], [repr(self.question_two)])
        self.assertContext('active', 'answered')


class TestUnAnsweredQuestionListView(BaseQATest):
    """测试尚未有答案的问题列表"""

    def test_context_data(self):
        response = self.get(views.UnAnsweredQuestionListView, request=self.request)
        self.assert_http_200_ok(response)
        self.assertQuerysetEqual(response.context_data['questions'], [repr(self.question_one)])
        self.assertContext('active', 'unanswered')


class TestQuestionCreateView(BaseQATest):
    """测试创建问题"""

    def test_get(self):
        """GET请求"""
        response = self.get(views.QuestionCreateView, request=self.request)
        self.assert_http_200_ok(response)
        self.assertContains(response, '标题')
        self.assertContains(response, '编辑')
        self.assertContains(response, '预览')
        self.assertContains(response, '标签')
        self.assertIsInstance(response.context_data['view'], views.QuestionCreateView)

    def test_post(self):
        """POST请求"""
        data = {'title': 'title', 'content': 'content', 'tags': 'tag1,tag2', 'status': 'O'}
        request = RequestFactory().post('/fake-url/', data=data)
        request.user = self.user

        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)

        response = self.post(views.QuestionCreateView, request=request)
        self.assert_http_302_found(response)
        self.assertEqual(response.url, '/qa/')


class TestQuestionDetailView(BaseQATest):
    """测试问题详情"""

    def test_context_data(self):
        response = self.get(views.QuestionDetailView, request=self.request,
                            pk=self.question_one.pk)
        self.assert_http_200_ok(response)
        self.assertEqual(response.context_data['question'], self.question_one)


class TestAnswerCreateView(BaseQATest):
    """测试创建回答"""

    def test_get(self):
        """GET请求"""
        response = self.get(views.AnswerCreateView, request=self.request,
                            question_id=self.question_one.pk)
        self.assert_http_200_ok(response)
        self.assertContains(response, '编辑')
        self.assertContains(response, '预览')
        self.assertIsInstance(response.context_data['view'], views.AnswerCreateView)

    def test_post(self):
        """POST请求"""
        request = RequestFactory().post('/fake-url/', data={'content': 'content'})
        request.user = self.user

        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)

        response = self.post(views.AnswerCreateView, request=request, question_id=self.question_one.id)
        self.assert_http_302_found(response)
        self.assertEqual(response.url, '/qa/question-detail/{}/'.format(self.question_one.id))


class TestQAVote(BaseQATest):
    """测试投票功能（问题和回答）"""

    def setUp(self):
        super().setUp()
        self.request = RequestFactory().post('/fake-url/',
                                             HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.request.POST = self.request.POST.copy()
        self.request.user = self.other_user

    def test_question_upvote(self):
        """赞同问题"""
        self.request.POST['question'] = self.question_one.id
        self.request.POST['value'] = 'U'
        response = views.question_vote(self.request)
        self.assert_http_200_ok(response)
        self.assertEqual(json.loads(response.content)['votes'], 1)

    def test_question_downvote(self):
        """踩问题"""
        self.request.POST['question'] = self.question_two.id
        self.request.POST['value'] = 'D'
        response = views.question_vote(self.request)
        self.assert_http_200_ok(response)
        self.assertEqual(json.loads(response.content)['votes'], -1)

    def test_answer_upvote(self):
        """赞同回答"""
        self.request.POST['answer'] = self.answer.uuid_id
        self.request.POST['value'] = 'U'
        response = views.answer_vote(self.request)
        self.assert_http_200_ok(response)
        self.assertEqual(json.loads(response.content)['votes'], 1)

    def test_answer_downvote(self):
        """踩回答"""
        self.request.POST['answer'] = self.answer.uuid_id
        self.request.POST['value'] = 'D'
        response = views.answer_vote(self.request)
        self.assert_http_200_ok(response)
        self.assertEqual(json.loads(response.content)['votes'], -1)

    def test_accept_answer(self):
        """采纳回答"""
        self.request.POST['answer'] = self.answer.uuid_id
        response = views.accept_answer(self.request)
        self.assert_http_200_ok(response)
        self.assertEqual(json.loads(response.content)['status'], 'true')

#!/usr/bin/python3
# -*- coding:utf-8 -*-
# __author__ = '__AYC__'

from test_plus.test import TestCase

from zanhu.qa.models import Question, Answer


class TestQAModels(TestCase):

    def setUp(self):
        self.user = self.make_user('user01')
        self.other_user = self.make_user('user02')
        self.question_one = Question.objects.create(
            user=self.user,
            title='问题1',
            content='问题1的内容',
            tags='测试1, 测试2'
        )
        self.question_two = Question.objects.create(
            user=self.user,
            title='问题2',
            content='问题2的内容',
            has_answer=True,
            tags='测试1, 测试2'
        )
        self.answer = Answer.objects.create(
            user=self.user,
            question=self.question_two,
            content='问题2的回答',
            is_answered=True
        )

    def test_vote_question(self):
        """给问题投票"""
        # user01赞了question_one
        self.question_one.votes.update_or_create(user=self.user, defaults={'value': True})
        self.assertEqual(self.question_one.total_votes(), 1)
        self.assertIn(self.user, self.question_one.get_upvoters())
        # user02踩了question_one
        self.question_one.votes.update_or_create(user=self.other_user, defaults={'value': False})
        self.assertEqual(self.question_one.total_votes(), 0)
        self.assertIn(self.other_user, self.question_one.get_downvoters())

    def test_vote_answer(self):
        """给回答投票"""
        # user01赞了answer
        self.answer.votes.update_or_create(user=self.user, defaults={'value': True})
        self.assertEqual(self.answer.total_votes(), 1)
        self.assertIn(self.user, self.answer.get_upvoters())
        # user02踩了answer
        self.answer.votes.update_or_create(user=self.other_user, defaults={'value': False})
        self.assertEqual(self.answer.total_votes(), 0)
        self.assertIn(self.other_user, self.answer.get_downvoters())

    def test_get_question_voters(self):
        """获取给问题的投票用户"""
        self.question_one.votes.update_or_create(user=self.user, defaults={'value': True})
        self.question_one.votes.update_or_create(user=self.other_user, defaults={'value': False})
        self.assertIn(self.user, self.question_one.get_upvoters())
        self.assertNotIn(self.other_user, self.question_one.get_upvoters())
        self.assertIn(self.other_user, self.question_one.get_downvoters())
        self.assertNotIn(self.user, self.question_one.get_downvoters())

    def test_get_answer_voters(self):
        """获取给回答投票的用户"""
        self.answer.votes.update_or_create(user=self.user, defaults={'value': True})
        self.answer.votes.update_or_create(user=self.other_user, defaults={'value': False})
        self.assertIn(self.user, self.answer.get_upvoters())
        self.assertNotIn(self.other_user, self.answer.get_upvoters())
        self.assertIn(self.other_user, self.answer.get_downvoters())
        self.assertNotIn(self.user, self.answer.get_downvoters())

    def test_get_unanswered_questions(self):
        """获取尚未有已采纳答案的问题"""
        self.assertIn(self.question_one, Question.objects.get_unanswered())
        self.assertNotIn(self.question_two, Question.objects.get_unanswered())

    def test_get_answered_questions(self):
        """获取已有采纳答案的问题"""
        self.assertIn(self.question_two, Question.objects.get_answered())
        self.assertNotIn(self.question_one, Question.objects.get_answered())

    def test_question_get_answers(self):
        """获取问题的所有答案"""
        self.assertIn(self.answer, self.question_two.get_answers())
        self.assertEqual(self.question_two.count_answers(), 1)

    def test_question_accept_answer(self):
        """采纳答案"""
        answer_one = Answer.objects.create(
            user=self.user,
            question=self.question_one,
            content='回答1'
        )
        answer_two = Answer.objects.create(
            user=self.user,
            question=self.question_one,
            content='回答2'
        )
        self.assertIn(answer_one, self.question_one.get_answers())
        self.assertIn(answer_two, self.question_one.get_answers())
        self.assertEqual(self.question_one.count_answers(), 2)
        self.assertFalse(answer_one.is_answered)
        self.assertFalse(answer_two.is_answered)
        self.assertFalse(self.question_one.has_answer)
        answer_one.accept_answer()
        self.assertTrue(self.question_one.has_answer)
        self.assertTrue(answer_one.is_answered)
        self.assertFalse(answer_two.is_answered)
        self.assertEqual(answer_one, self.question_one.get_accepted_answer())

    def test_question__str__(self):
        "Question模型类的__str__方法"""
        self.assertIsInstance(self.question_one, Question)
        self.assertIsInstance(self.question_two, Question)
        self.assertEqual(self.question_one.__str__(), '问题1')
        self.assertEqual(self.question_two.__str__(), '问题2')

    def test_answer__str__(self):
        """Answer模型类的__str__方法"""
        self.assertIsInstance(self.answer, Answer)
        self.assertEqual(self.answer.__str__(), '问题2的回答')

#!/usr/bin/python3
# -*- coding:utf-8 -*-
# __author__ = '__AYC__'

from django.views.generic import ListView, CreateView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from zanhu.helpers import ajax_required
from zanhu.qa.models import Question, Answer
from zanhu.qa.forms import QuestionForm
from zanhu.notifications.views import notification_handler


class QuestionListView(LoginRequiredMixin, ListView):
    """所有问题列表"""
    queryset = Question.objects.select_related('user')
    paginate_by = 10
    context_object_name = 'questions'
    template_name = 'qa/question_list.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        """上下文添加标签信息"""
        context = super().get_context_data()
        context['popular_tags'] = Question.objects.get_counted_tags()  # 问题标签
        context['active'] = 'all'  # 用于前端问题分类Tab
        return context


class AnsweredQuestionListView(QuestionListView):
    """已有采纳答案的问题列表"""

    def get_queryset(self):
        return Question.objects.get_answered()

    def get_context_data(self, *, object_list=None, **kwargs):
        """上下文添加问题分类Tab信息"""
        context = super().get_context_data()
        context['active'] = 'answered'  # 用于前端问题分类Tab
        return context


class UnAnsweredQuestionListView(QuestionListView):
    """尚未有已采纳答案的问题列表"""

    def get_queryset(self):
        return Question.objects.get_unanswered()

    def get_context_data(self, *, object_list=None, **kwargs):
        """上下文添加问题分类Tab信息"""
        context = super().get_context_data()
        context['active'] = 'unanswered'  # 用于前端问题分类Tab
        return context


@method_decorator(cache_page(60 * 60), name='get')  # 把创建问题页的get请求返回页面缓存一个小时
class QuestionCreateView(LoginRequiredMixin, CreateView):
    """创建问题"""
    model = Question
    form_class = QuestionForm
    template_name = 'qa/question_form.html'
    message = '您的问题已提交！'

    def form_valid(self, form):
        """重写表单验证，将当前登录用户传递给表单实例"""
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        """问题创建成功后跳转，并添加消息提示"""
        messages.success(self.request, self.message)
        return reverse_lazy('qa:unanswered_q')


class QuestionDetailView(LoginRequiredMixin, DetailView):
    """问题详情"""
    model = Question
    context_object_name = 'question'
    template_name = 'qa/question_detail.html'

    def get_queryset(self):
        """添加select_related减少SQL查询次数"""
        return Question.objects.select_related('user').filter(pk=self.kwargs['pk'])


@method_decorator(cache_page(60 * 60), name='get')  # 把创建回答的get请求返回页面缓存一个小时
class AnswerCreateView(LoginRequiredMixin, CreateView):
    """创建回答"""
    model = Answer
    fields = ['content']
    template_name = 'qa/answer_form.html'
    message = '您的回答已提交！'

    def form_valid(self, form):
        """将当前登录用户，及当前问题ID传递给表单实例"""
        form.instance.user = self.request.user
        form.instance.question_id = self.kwargs['question_id']
        return super().form_valid(form)

    def get_success_url(self):
        """创建成功后跳转，并添加消息提示"""
        messages.success(self.request, self.message)
        return reverse_lazy('qa:question_detail', kwargs={'pk': self.kwargs['question_id']})


@login_required
@ajax_required
@require_http_methods(['POST'])
def question_vote(request):
    """给问题投票，AJAX POST请求"""
    question_id = request.POST['question']
    value = True if request.POST['value'] == 'U' else False
    question = Question.objects.get(pk=question_id)
    users = question.votes.values_list('user', flat=True)  # 当前问题的所有投票用户
    if request.user.pk in users and (question.votes.get(user=request.user).value == value):
        question.votes.get(user=request.user).delete()
    else:
        question.votes.update_or_create(user=request.user, defaults={'value': value})

    return JsonResponse({'votes': question.total_votes()})


@login_required
@ajax_required
@require_http_methods(['POST'])
def answer_vote(request):
    """给回答投票，AJAX POST请求"""
    answer_id = request.POST['answer']
    value = True if request.POST['value'] == 'U' else False
    answer = Answer.objects.get(pk=answer_id)
    users = answer.votes.values_list('user', flat=True)  # 当前回答的所有投票用户
    if request.user.pk in users and (answer.votes.get(user=request.user).value == value):
        answer.votes.get(user=request.user).delete()
    else:
        answer.votes.update_or_create(user=request.user, defaults={'value': value})

    return JsonResponse({'votes': answer.total_votes()})


@login_required
@ajax_required
@require_http_methods(['POST'])
def accept_answer(request):
    """接受回答（仅提问者可以），AJAX POST请求"""
    answer_id = request.POST['answer']
    answer = Answer.objects.get(pk=answer_id)
    # 验证请求是否为提问者发送
    if answer.question.user.username != request.user.username:
        raise PermissionDenied
    answer.accept_answer()
    # 通知回答者回答被采纳
    notification_handler(request.user, answer.user, 'W', answer)
    return JsonResponse({'status': 'true'})

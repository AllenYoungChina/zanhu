#!/usr/bin/python3
# -*- coding:utf-8 -*-
# __author__ = '__AYC__'

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.views.generic import DetailView, UpdateView

User = get_user_model()


class UserDetailView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'users/user_detail.html'
    slug_field = "username"
    slug_url_kwarg = "username"

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        user = User.objects.get(username=self.request.user.username)
        context['moments_num'] = user.publisher.filter(reply=False).count()
        context['article_num'] = user.author.filter(status='P').count()
        context['comment_num'] = user.publisher.filter(reply=True).count() + \
                                 user.comment_comments.all().count()
        context['question_num'] = user.q_author.all().count()
        context['answer_num'] = user.a_author.all().count()
        tmp = set()
        recipient_list = user.sent_messages.all()
        for r in recipient_list:
            tmp.add(r.recipient.username)
        sender_list = user.received_messages.all()
        for s in sender_list:
            tmp.add(s.sender.username)
        context['interaction_num'] = user.liked_news.all().count() + user.qa_vote.all().count() + \
                                     context['comment_num'] + len(tmp)
        return context


class UserUpdateView(LoginRequiredMixin, UpdateView):
    """用户只能更新自己的信息"""
    model = User
    fields = ['nickname', 'email', 'job_title', 'introduction', 'picture', 'location',
              'personal_url', 'weibo', 'zhihu', 'github', 'linkedin']
    template_name = 'users/user_form.html'

    def get_success_url(self):
        """更新成功后跳转到个人详情页"""
        return reverse("users:detail", kwargs={"username": self.request.user.username})

    def get_object(self, queryset=None):
        """获取需要返回给前端的对象（用户实例）"""
        return self.request.user

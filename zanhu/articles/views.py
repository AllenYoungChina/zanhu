#!/usr/bin/python3
# -*- coding:utf-8 -*-
# __author__ = '__AYC__'

from django.views.generic import CreateView, ListView, UpdateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django_comments.signals import comment_was_posted
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from zanhu.articles.models import Article
from zanhu.articles.forms import ArticleForm
from zanhu.helpers import AuthorRequiredMixin
from zanhu.notifications.views import notification_handler


class ArticleListView(LoginRequiredMixin, ListView):
    """已发布的文章列表"""
    model = Article
    paginate_by = 10
    template_name = 'articles/article_list.html'
    context_object_name = 'articles'

    def get_queryset(self):
        """筛选已发布的文章"""
        return Article.objects.get_published().select_related('user')

    def get_context_data(self, *, object_list=None, **kwargs):
        """添加标签信息到上下文"""
        context = super().get_context_data()
        context['popular_tags'] = Article.objects.get_counted_tags()
        return context


class DraftListView(ArticleListView):
    """草稿箱文章列表"""

    def get_queryset(self):
        """筛选当前用户的草稿箱文章"""
        return Article.objects.filter(user=self.request.user).get_drafts().select_related('user')


@method_decorator(cache_page(60 * 60), name='get')  # 把创建文章页的get请求返回页面缓存一个小时
class ArticleCreateView(LoginRequiredMixin, CreateView):
    """发表文章"""
    model = Article
    form_class = ArticleForm
    template_name = 'articles/article_create.html'
    message = '您的消息已创建成功！'

    def form_valid(self, form):
        # 将用户传递给表单实例
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        """文章创建成功后跳转"""
        messages.success(self.request, message=self.message)  # 消息传递给下一次请求
        return reverse_lazy('articles:list')


class ArticleDetailView(LoginRequiredMixin, DetailView):
    """文章详情"""
    model = Article
    template_name = 'articles/article_detail.html'

    def get_queryset(self):
        """添加select_related以减少SQL查询次数"""
        return Article.objects.select_related('user').filter(slug=self.kwargs['slug'])


class ArticleEditView(LoginRequiredMixin, AuthorRequiredMixin, UpdateView):
    """编辑文章（只能编辑自己的文章）"""
    model = Article
    form_class = ArticleForm
    template_name = 'articles/article_update.html'
    message = '您的文章已编辑成功！'

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        messages.success(self.request, message=self.message)
        return reverse('articles:article', kwargs={'slug': self.get_object().slug})  # 跳转到文章详情页


def notify_comment(**kwargs):
    """文章有评论时通知作者"""
    actor = kwargs['request'].user
    obj = kwargs['comment'].content_object
    notification_handler(actor, obj.user, 'C', obj)


comment_was_posted.connect(receiver=notify_comment)

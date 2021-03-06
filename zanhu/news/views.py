#!/usr/bin/python3
# -*- coding:utf-8 -*-
# __author__ = '__AYC__'

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DeleteView
from django.template.loader import render_to_string
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.urls import reverse_lazy

from zanhu.news.models import News
from zanhu.helpers import ajax_required, AuthorRequiredMixin


class NewsListView(LoginRequiredMixin, ListView):
    """首页动态列表"""
    model = News
    paginate_by = 20
    template_name = 'news/news_list.html'
    context_object_name = 'news_list'

    def get_queryset(self):
        return News.objects.filter(reply=False).select_related('user', 'parent').prefetch_related('liked')


class NewsDeleteView(LoginRequiredMixin, AuthorRequiredMixin, DeleteView):
    """删除动态（只能删除自己发表的动态）"""
    model = News
    template_name = 'news/news_confirm_delete.html'
    # slug_url_kwarg = 'slug'  # 通过URL传递的要删除对象的主键id，默认为slug
    # pk_url_kwarg = 'pk'  # 通过URL传递的要删除对象的主键id，默认为pk
    success_url = reverse_lazy('news:list')  # 删除成功后跳转的URL，在项目URLConf未加载前使用


@login_required
@ajax_required
@require_http_methods(['POST'])
def post_news(request):
    """发送动态，AJAX POST请求"""
    post = request.POST['post'].strip()
    if post:
        posted = News.objects.create(user=request.user, content=post)
        html = render_to_string('news/news_single.html', {'news': posted, 'request': request})
        return HttpResponse(html)
    else:
        return HttpResponseBadRequest('内容不能为空！')


@login_required
@ajax_required
@require_http_methods(['POST'])
def like(request):
    """给动态点赞，AJAX POST请求"""
    news_id = request.POST['news']
    news = News.objects.get(pk=news_id)
    # 添加或取消赞
    news.switch_like(request.user)
    # 返回动态赞的数量
    return JsonResponse({'likes': news.count_likers()})


@login_required
@ajax_required
@require_http_methods(['GET'])
def get_thread(request):
    """获取动态的评论，AJAX GET请求"""
    news_id = request.GET['news']
    news = News.objects.select_related('user').get(pk=news_id)
    news_html = render_to_string('news/news_single.html', {'news': news})
    thread_html = render_to_string('news/news_thread.html', {'thread': news.get_thread()})
    return JsonResponse({
        'uuid': news_id,
        'news': news_html,
        'thread': thread_html
    })


@login_required
@ajax_required
@require_http_methods(['POST'])
def post_comment(request):
    """评论动态，AJAX POST请求"""
    post = request.POST['reply'].strip()
    parent_id = request.POST['parent']
    parent = News.objects.get(pk=parent_id)
    if post:
        parent.reply_this(request.user, post)
        return JsonResponse({'comments': parent.comment_count()})
    else:
        return HttpResponseBadRequest('内容不能为空！')


@login_required
@ajax_required
@require_http_methods(['POST'])
def update_interactions(request):
    """更新互动信息"""
    id_value = request.POST['id_value']
    news = News.objects.get(pk=id_value)
    return JsonResponse({'likes': news.count_likers(), 'comments': news.comment_count()})

#!/usr/bin/python3
# -*- coding:utf-8 -*-
# __author__ = '__AYC__'

from slugify import slugify
import uuid
from collections import Counter

from django.db import models
from django.contrib.auth import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericRelation, GenericForeignKey
from markdownx.models import MarkdownxField
from markdownx.utils import markdownify
from taggit.managers import TaggableManager


class Vote(models.Model):
    """问题和回答的投票（使用Django的ContentType进行复合关联）"""
    uuid_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='qa_vote',
                             on_delete=models.CASCADE, verbose_name='投票者')
    value = models.BooleanField('赞或踩', default=True)  # True为赞，False为踩
    # GenericForeignKey设置
    content_type = models.ForeignKey(ContentType, related_name='vote_on', on_delete=models.CASCADE)
    object_id = models.CharField(max_length=255)
    vote = GenericForeignKey('content_type', 'object_id')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '投票'
        verbose_name_plural = verbose_name
        unique_together = ('user', 'content_type', 'object_id')  # 联合唯一键约束
        # SQL优化
        index_together = ('content_type', 'object_id')  # 联合唯一索引


class QuestionQuerySet(models.query.QuerySet):
    """自定义查询结果集"""

    def get_answered(self):
        """返回已有采纳答案的问题"""
        return self.filter(has_answer=True).select_related('user')

    def get_unanswered(self):
        """返回尚未有采纳答案的问题"""
        return self.filter(has_answer=False).select_related('user')

    def get_counted_tags(self):
        """统计所有问题标签，每一个标签的数量（数量大于0的）"""
        tag_dict = {}
        for obj in self.all():
            for tag in obj.tags.names():
                if tag not in tag_dict:
                    tag_dict[tag] = 1
                else:
                    tag_dict[tag] += 1
        return tag_dict.items()


class Question(models.Model):
    STATUS = (
        ('O', 'Open'),
        ('C', 'Close'),
        ('D', 'Draft')
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='q_author',
                             on_delete=models.CASCADE, verbose_name='提问者')
    title = models.CharField('标题', max_length=255, unique=True)
    slug = models.SlugField('URL别名', max_length=255, blank=True, null=True)
    status = models.CharField('状态', max_length=1, choices=STATUS, default='O')
    content = MarkdownxField('内容')
    tags = TaggableManager('标签', help_text='多个标签使用英文逗号隔开')
    has_answer = models.BooleanField('接受回答', default=False)  # 是否有接受的回答
    votes = GenericRelation(Vote, verbose_name='投票情况')  # 通过GenericRelation关联到Vote表
    created_at = models.DateTimeField('创建时间', auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    objects = QuestionQuerySet.as_manager()

    class Meta:
        verbose_name = '问题'
        verbose_name_plural = verbose_name
        ordering = ('-created_at',)

    def __str__(self):
        return self.title

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        """重写save方法，自动生成slug"""
        self.slug = slugify(self.title)
        super().save()

    def get_markdown(self):
        """将Markdown文本转换为HTML"""
        return markdownify(self.content)

    def total_votes(self):
        """得票数量（赞数-踩数）"""
        dic = Counter(self.votes.values_list('value', flat=True))  # Counter赞和踩的数量
        return dic[True] - dic[False]

    def get_answers(self):
        """获取问题的所有回答"""
        return Answer.objects.filter(question=self).select_related('user')

    def count_answers(self):
        """统计问题的回答数量"""
        return self.get_answers().count()

    def get_upvoters(self):
        """获取对问题点赞的用户"""
        return [vote.user for vote in self.votes.filter(value=True).select_related(
            'user').prefetch_related('vote')]

    def get_downvoters(self):
        """获取对问题踩的用户"""
        return [vote.user for vote in self.votes.filter(value=False).select_related(
            'user').prefetch_related('vote')]


class Answer(models.Model):
    uuid_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='a_author',
                             on_delete=models.CASCADE, verbose_name='回答者')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name='问题')
    content = MarkdownxField('内容')
    is_answered = models.BooleanField('是否被采纳', default=False)
    votes = GenericRelation(Vote, verbose_name='投票情况')  # 通过GenericRelation关联到Vote表
    created_at = models.DateTimeField('创建时间', auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '回答'
        verbose_name_plural = verbose_name
        ordering = ('-is_answered', '-created_at')  # 多字段排序，优先被采纳的回答，优先最新的回答

    def __str__(self):
        return self.content

    def get_markdown(self):
        """将Markdown文本转换为HTML"""
        return markdownify(self.content)

    def total_votes(self):
        """得票数量（赞数-踩数）"""
        dic = Counter(self.votes.values_list('value', flat=True))  # Counter赞和踩的数量
        return dic[True] - dic[False]

    def get_upvoters(self):
        """获取对问题点赞的用户"""
        return [vote.user for vote in self.votes.filter(value=True).select_related(
            'user').prefetch_related('vote')]

    def get_downvoters(self):
        """获取对问题踩的用户"""
        return [vote.user for vote in self.votes.filter(value=False).select_related(
            'user').prefetch_related('vote')]

    def accept_answer(self):
        """接受回答"""
        # 将所有的答案均设置为未被采纳
        answer_set = Answer.objects.filter(question=self.question)
        answer_set.update(is_answered=False)
        # 接受当前回答并保存
        self.is_answered = True
        self.save()
        # 设置关联问题已有答案并保存
        self.question.has_answer = True
        self.question.save()

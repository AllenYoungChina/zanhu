#!/usr/bin/python3
# -*- coding:utf-8 -*-
# __author__ = '__AYC__'

from django.db import models
from django.contrib.auth import settings
from slugify import slugify
from taggit.managers import TaggableManager
from markdownx.models import MarkdownxField
from markdownx.utils import markdownify


class ArticleQuerySet(models.query.QuerySet):
    """自定义QuerySet，提高模型类的可用性"""

    def get_published(self):
        """返回已发表的文章"""
        return self.filter(status='P')

    def get_drafts(self):
        """返回草稿箱的文章"""
        return self.filter(status='D')

    def get_counted_tags(self):
        """统计所有已发表的文章中，每一个标签的数量（数量大于0的）"""
        tag_dict = {}
        query = self.get_published()
        for obj in query:
            for tag in obj.tags.names():
                if tag not in tag_dict:
                    tag_dict[tag] = 1
                else:
                    tag_dict[tag] += 1
        return tag_dict.items()


class Article(models.Model):
    STATUS = (
        ('D', 'Draft'),
        ('P', 'Published')
    )

    title = models.CharField('标题', max_length=255, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, on_delete=models.SET_NULL,
                             related_name='author', verbose_name='作者')
    image = models.ImageField('文章图片', upload_to='articles_pictures/%Y/%m/%d/')
    slug = models.SlugField('URL别名', max_length=255)
    status = models.CharField('状态', max_length=1, choices=STATUS, default='D')
    content = MarkdownxField('内容')
    edited = models.BooleanField('是否可编辑', default=False)
    tags = TaggableManager('标签', help_text='多个标签使用英文逗号隔开')
    created_at = models.DateTimeField('创建时间', auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    objects = ArticleQuerySet.as_manager()  # 使用自定义查询结果集

    class Meta:
        verbose_name = '文章'
        verbose_name_plural = verbose_name
        ordering = ('created_at',)

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

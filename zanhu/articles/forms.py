#!/usr/bin/python3
# -*- coding:utf-8 -*-
# __author__ = '__AYC__'

from django import forms
from markdownx.fields import MarkdownxFormField
from zanhu.articles.models import Article


class ArticleForm(forms.ModelForm):
    status = forms.CharField(widget=forms.HiddenInput)  # 前端对用户隐藏
    edited = forms.BooleanField(widget=forms.HiddenInput, initial=False, required=False)  # 前端对用户隐藏
    content = MarkdownxFormField(label='文章')

    class Meta:
        model = Article
        fields = ['title', 'image', 'content', 'edited', 'status', 'tags']

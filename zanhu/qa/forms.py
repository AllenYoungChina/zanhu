#!/usr/bin/python3
# -*- coding:utf-8 -*-
# __author__ = '__AYC__'

from django import forms

from markdownx.fields import MarkdownxFormField

from zanhu.qa.models import Question, Answer


class QuestionForm(forms.ModelForm):
    status = forms.CharField(widget=forms.HiddenInput())  # 前端对用户隐藏
    content = MarkdownxFormField(label='内容')

    class Meta:
        model = Question
        fields = ['title', 'status', 'content', 'tags']

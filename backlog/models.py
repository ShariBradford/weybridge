from django.db import models
from django import forms
from django.forms import ModelForm, ValidationError
from django.contrib.auth.models import User
from django.conf import settings
from datetime import datetime, date, timedelta
from django.db.models import Avg, UniqueConstraint
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
from django.utils import timezone 
from django.shortcuts import reverse
# from django.utils import unique_slug_generator
import math
import string 
import random 

class Backlog(models.Model):
    
    class Category(models.IntegerChoices):
        URLS = 1
        VIEWS = 2
        MODELS = 3
        TEMPLATES = 4
        STATIC = 5
        ADMIN = 6
        FORMS = 7
        MEDIA = 8
        SETTINGS = 9
        SIGNALS = 10
        CONVERTERS = 11
        CUSTOM_TAGS = 12
        TESTS = 13
        OTHER = 99

    # CATEGORY_CHOICES = (
    #     (URLS, 'urls'),
    #     (VIEWS, 'views'),
    #     (MODELS, 'models'),
    #     (TEMPLATES, 'templates'),
    #     (STATIC, 'static'),
    #     (ADMIN, 'admin'),
    #     (FORMS, 'forms'),
    #     (MEDIA, 'media'),
    #     (SETTINGS, 'settings'),
    #     (SIGNALS, 'signals'),
    #     (CONVERTERS, 'converters'),
    #     (CUSTOM_TAGS, 'custom tags'),
    #     (TESTS, 'tests'),
    #     (OTHER, 'other'),
    # )

    class Status(models.IntegerChoices):
        PENDING = 1
        COMPLETED = 2
        WONT_FIX = 3

    class Priority(models.IntegerChoices):
        HIGH = 1
        MEDIUM = 2
        LOW = 3
        HORIZON = 4

    app_name = models.CharField(max_length=255)
    model_name = models.CharField(max_length=255, blank=True, null=True)
    category = models.IntegerField(
        choices=Category.choices,
        verbose_name = 'categories',
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    priority = models.IntegerField(
        choices=Priority.choices,
        verbose_name = 'priorities',
        default = Priority.MEDIUM
    )
    status = models.IntegerField(
        choices=Status.choices,
        verbose_name = 'statuses',
        default = Status.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User,related_name="backlog_items_updated", on_delete=models.CASCADE)
    created_by = models.ForeignKey(User,related_name="backlog_items_created", on_delete=models.CASCADE)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('backlog:backlog_details',kwargs={'pk': self.id})

class BacklogForm(ModelForm):
    class Meta:
        model = Backlog
        fields = ['app_name', 'model_name', 'category', 'title', 'description','priority', 'status']
        widgets = {
            'app_name' : forms.TextInput(attrs={'class':'form-control'}),
            'model_name' : forms.TextInput(attrs={'class':'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'title' : forms.TextInput(attrs={'class':'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
       }

# class Entries(models.Model):

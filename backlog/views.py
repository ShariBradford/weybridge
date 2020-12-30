from django.views.generic import ListView,DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.shortcuts import render, redirect, reverse, get_object_or_404,HttpResponseRedirect, HttpResponse
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Avg, F, Q, Count, FilteredRelation, Value, IntegerField, CharField
from datetime import datetime
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponseNotAllowed
from .models import *
from shop.views import get_breadcrumbs

class BacklogList(ListView):
    model = Backlog

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        context['breadcrumbs'] = get_breadcrumbs('page',None,'Backlog')
        return context

class BacklogDetail(DetailView):
    model = Backlog

class BacklogCreate(CreateView):
    model = Backlog
    form_class = BacklogForm

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)

class BacklogUpdate(UpdateView):
    model = Backlog
    form_class = BacklogForm

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        return super().form_valid(form)

class BacklogDelete(DeleteView):
    model = Backlog
    success_url = reverse_lazy('backlog:index')
    template_name = 'shop/object_confirm_delete.html'


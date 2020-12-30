from django.urls import path, include
from . import views

app_name = 'backlog'

urlpatterns = [
    # backlog/
    path('', views.BacklogList.as_view(), name='index'),
    path('add/', views.BacklogCreate.as_view(), name='backlog_add'),
    path('<int:pk>/', views.BacklogDetail.as_view(), name="backlog_details"),
    path('<int:pk>/update/', views.BacklogUpdate.as_view(), name="backlog_update"),
    path('<int:pk>/delete/', views.BacklogDelete.as_view(), name="backlog_delete"),
]

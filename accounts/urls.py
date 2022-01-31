from django.urls import path
from django.contrib.auth import views as aut_views
from . import views

app_name = 'accounts'

urlpatterns = [
    path('signup', views.signup, name='signup'),
    path('<int:profiled_user_id>', views.user_profile, name="user_profile"),
    path('<int:profiled_user_id>/update', views.update_user_profile, name="update_user_profile"),
    path('<int:profiled_user_id>/settimezone', views.set_timezone, name="set_user_timezone"),

    path('testing', views.testdata, name="test_data"),
    path('createusers', views.create_users, name="create_users"),
    path('resetusers', views.reset_users, name="reset_users"),
]
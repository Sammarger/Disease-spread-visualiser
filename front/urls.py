from django.urls import path
from django.contrib.auth import views as auth_views
from .views import SymptomsListView, SymptomsCreateView
from . import views
from users import views as user_views


#Urls.py used to redirect HTTP requests to the appropriate view based on the request URL
#Each path has an associated route, view function and name
urlpatterns = [
    path('', auth_views.LoginView.as_view(template_name="users/login.html"), name='login'),
    path('front/', SymptomsListView.as_view(), name='front'),
    path('front/new/', SymptomsCreateView.as_view(), name='usersymptoms-create'),
    path('about/', views.map_data, name='data_map'),
    path('local_map/', views.local_map, name='local_map'),
    path('raw_data/', views.view_table, name='raw_data_table'),
    path('register/', user_views.register, name='register'),
    path('logout/', auth_views.LogoutView.as_view(template_name="users/logout.html"), name='logout'),
]
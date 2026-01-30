from django.urls import path
from . import views


urlpatterns = [
    path('', views.login, name='login'),
    path('signin/', views.signin, name='signin'),
    path('home/', views.home, name='home'),
    path('conference/', views.conference, name='conference'),
    path('leave/', views.leave, name='leave'),
]


from django.urls import path
from . import views


urlpatterns = [
    path('', views.join, name='join'),
    path('conference/', views.conference, name='conference'),
    path('leave/', views.leave, name='leave'),
]

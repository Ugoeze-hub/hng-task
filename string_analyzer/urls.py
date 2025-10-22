from django.urls import path
from .views import *

urlpatterns = [
    path('', home, name='home'),
    path('strings/', strings, name='strings'),
    path('strings/<str:specific_string>/', get_string, name='get_string'),
    path('strings/filter-by-natural-language', natural_language_filter, name='natural_language_filter'),
    path('strings/<str:specific_string>/delete', delete_string, name='delete_string'),
]
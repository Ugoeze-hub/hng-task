from django.urls import path
from .views import *

urlpatterns = [
    path('', home, name='home'),
    path('strings/', strings, name='strings'),
    path('strings/filter-by-natural-language/', natural_language_filter, name='natural_language_filter'),
    path('strings/<str:specific_string>/', get_remove_string, name='get_remove_string'),
]
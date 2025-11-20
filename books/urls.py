"""
URLs for books app
"""
from django.urls import path
from . import views

app_name = 'books'

urlpatterns = [
    path('catalog/', views.catalog_view, name='catalog'),
    path('<int:pk>/', views.book_detail_view, name='detail'),
]
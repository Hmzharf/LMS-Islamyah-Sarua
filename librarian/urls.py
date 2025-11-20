"""
URLs for librarian app
"""
from django.urls import path
from . import views

app_name = 'librarian'

urlpatterns = [
    # Dashboard
    path('', views.dashboard_view, name='dashboard'),
    
    # Scan Barcode
    path('scan-borrow/', views.scan_borrow_view, name='scan_borrow'),
    path('scan-return/', views.scan_return_view, name='scan_return'),
    path('process-borrow/', views.process_borrow, name='process_borrow'),
    path('process-return/', views.process_return, name='process_return'),
    
    # Active Loans
    path('active-loans/', views.active_loans_view, name='active_loans'),
    
    # Members Management
    path('members/', views.members_list_view, name='members_list'),
    path('members/add/', views.member_add_view, name='member_add'),
    path('members/<int:pk>/', views.member_detail_view, name='member_detail'),
    path('members/<int:pk>/edit/', views.member_edit_view, name='member_edit'),
    path('members/<int:pk>/delete/', views.member_delete_view, name='member_delete'),
    path('members/<int:pk>/print-card/', views.member_print_card_view, name='member_print_card'),
    
    # Books Management
    path('books/', views.books_list_view, name='books_list'),
    path('books/add/', views.book_add_view, name='book_add'),
    path('books/<int:pk>/', views.book_detail_view, name='book_detail'),
    path('books/<int:pk>/edit/', views.book_edit_view, name='book_edit'),
    path('books/<int:pk>/delete/', views.book_delete_view, name='book_delete'),
]
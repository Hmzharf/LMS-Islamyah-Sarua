"""
URLs for reports app
"""
from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    # Dashboard
    path('', views.reports_dashboard, name='dashboard'),
    
    # Laporan Peminjaman
    path('loans/pdf/', views.loan_report_pdf, name='loan_pdf'),
    path('loans/excel/', views.loan_report_excel, name='loan_excel'),
    
    # Laporan Statistik Bulanan
    path('monthly/pdf/', views.monthly_report_pdf, name='monthly_pdf'),
    path('monthly/excel/', views.monthly_report_excel, name='monthly_excel'),
    
    # Laporan Anggota
    path('members/pdf/', views.member_report_pdf, name='member_pdf'),
    path('members/excel/', views.member_report_excel, name='member_excel'),
    
    # Laporan Buku
    path('books/pdf/', views.book_report_pdf, name='book_pdf'),
    path('books/excel/', views.book_report_excel, name='book_excel'),
    
    # Laporan Denda
    path('fines/pdf/', views.fine_report_pdf, name='fine_pdf'),
    path('fines/excel/', views.fine_report_excel, name='fine_excel'),
]

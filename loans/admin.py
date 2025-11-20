from django.contrib import admin
from .models import Loan
from django.utils import timezone


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    """Admin untuk Loan"""
    list_display = ['member', 'book_copy', 'borrowed_date', 'due_date', 'return_date', 'status', 'fine_amount']
    list_filter = ['status', 'borrowed_date', 'due_date']
    search_fields = ['member__name', 'member__nis', 'book_copy__book__title', 'book_copy__barcode']
    readonly_fields = ['created_at', 'fine_amount']
    date_hierarchy = 'borrowed_date'
    
    fieldsets = (
        ('Peminjam & Buku', {
            'fields': ('member', 'book_copy')
        }),
        ('Tanggal', {
            'fields': ('borrowed_date', 'due_date', 'return_date')
        }),
        ('Status & Denda', {
            'fields': ('status', 'fine_amount')
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        }),
    )
    
    actions = ['mark_as_returned', 'update_overdue_status']
    
    def mark_as_returned(self, request, queryset):
        """Action untuk menandai sebagai dikembalikan"""
        count = 0
        for loan in queryset:
            if loan.status != 'dikembalikan':
                loan.return_book()
                count += 1
        self.message_user(request, f'{count} peminjaman berhasil ditandai sebagai dikembalikan.')
    mark_as_returned.short_description = 'Tandai sebagai dikembalikan'
    
    def update_overdue_status(self, request, queryset):
        """Action untuk update status terlambat"""
        count = 0
        for loan in queryset:
            if loan.status == 'dipinjam' and timezone.now() > loan.due_date:
                loan.update_status()
                count += 1
        self.message_user(request, f'{count} peminjaman diupdate menjadi terlambat.')
    update_overdue_status.short_description = 'Update status terlambat'
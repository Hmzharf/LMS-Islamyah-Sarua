from django.contrib import admin
from .models import Book, BookCopy


class BookCopyInline(admin.TabularInline):
    """Inline untuk menampilkan salinan buku di halaman edit buku"""
    model = BookCopy
    extra = 1
    readonly_fields = ['barcode', 'barcode_image', 'created_at']


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    """Admin untuk Book"""
    list_display = ['title', 'author', 'isbn', 'category', 'total_copies', 'rating', 'created_at']
    list_filter = ['category', 'year_published']
    search_fields = ['title', 'author', 'isbn', 'publisher']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [BookCopyInline]
    
    fieldsets = (
        ('Informasi Buku', {
            'fields': ('title', 'author', 'publisher', 'year_published', 'isbn')
        }),
        ('Kategori & Deskripsi', {
            'fields': ('category', 'description', 'cover_image')
        }),
        ('Stok & Rating', {
            'fields': ('total_copies', 'rating')
        }),
        ('Timestamp', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(BookCopy)
class BookCopyAdmin(admin.ModelAdmin):
    """Admin untuk BookCopy"""
    list_display = ['book', 'copy_number', 'barcode', 'condition', 'is_available', 'created_at']
    list_filter = ['condition', 'is_available']
    search_fields = ['book__title', 'barcode']
    readonly_fields = ['barcode', 'barcode_image', 'created_at']
    
    fieldsets = (
        ('Informasi Salinan', {
            'fields': ('book', 'copy_number')
        }),
        ('Barcode', {
            'fields': ('barcode', 'barcode_image')
        }),
        ('Status', {
            'fields': ('condition', 'is_available')
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        }),
    )
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Member


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Admin untuk CustomUser"""
    list_display = ['username', 'email', 'role', 'is_staff', 'is_active']
    list_filter = ['role', 'is_staff', 'is_active']
    search_fields = ['username', 'email']
    
    # Tambahkan field role ke form
    fieldsets = UserAdmin.fieldsets + (
        ('Info Tambahan', {'fields': ('role', 'phone')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Info Tambahan', {'fields': ('role', 'phone')}),
    )


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    """Admin untuk Member"""
    list_display = ['name', 'nis', 'member_type', 'phone', 'is_active', 'created_at']
    list_filter = ['member_type', 'is_active', 'gender']
    search_fields = ['name', 'nis', 'phone', 'email', 'barcode']
    readonly_fields = ['barcode', 'barcode_image', 'created_at', 'updated_at']
    
    
    fieldsets = (
        ('Data Pribadi', {
            'fields': ('name', 'member_type', 'nis', 'gender', 'date_of_birth')
        }),
        ('Kontak', {
            'fields': ('phone', 'email', 'address', 'class_name')
        }),
        ('Barcode', {
            'fields': ('barcode', 'barcode_image')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamp', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Override save untuk generate barcode"""
        super().save_model(request, obj, form, change)
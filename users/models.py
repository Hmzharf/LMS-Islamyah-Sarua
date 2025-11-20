from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
import barcode
from barcode.writer import ImageWriter
from io import BytesIO
from django.core.files import File
import os

class CustomUser(AbstractUser):
    """Custom User Model dengan role"""
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('librarian', 'Librarian'),
        ('kepala_sekolah', 'Kepala Sekolah'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='librarian')
    phone = models.CharField(max_length=15, blank=True, null=True)
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class Member(models.Model):
    """Model untuk Anggota Perpustakaan"""
    MEMBER_TYPE_CHOICES = [
        ('siswa', 'Siswa'),
        ('guru', 'Guru'),
        ('staff', 'Staff'),
    ]
    
    GENDER_CHOICES = [
        ('L', 'Laki-laki'),
        ('P', 'Perempuan'),
    ]
    
    name = models.CharField(max_length=200, verbose_name='Nama Lengkap')
    member_type = models.CharField(max_length=10, choices=MEMBER_TYPE_CHOICES, verbose_name='Tipe Anggota')
    nis = models.CharField(max_length=20, unique=True, verbose_name='NIS/NIP')
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, verbose_name='Jenis Kelamin')
    date_of_birth = models.DateField(verbose_name='Tanggal Lahir')
    phone = models.CharField(max_length=15, verbose_name='Telepon')
    email = models.EmailField(blank=True, null=True, verbose_name='Email')
    address = models.TextField(verbose_name='Alamat')
    class_name = models.CharField(max_length=50, blank=True, null=True, verbose_name='Kelas')
    barcode = models.CharField(max_length=50, unique=True, blank=True, verbose_name='Barcode')
    barcode_image = models.ImageField(upload_to='members/barcodes/', blank=True, null=True)
    is_active = models.BooleanField(default=True, verbose_name='Status Aktif')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Anggota'
        verbose_name_plural = 'Anggota'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.nis})"
    
    def save(self, *args, **kwargs):
        # Generate barcode jika belum ada
        if not self.barcode:
            self.barcode = f"MBR{self.nis}"
        
        # Generate barcode image
        if not self.barcode_image:
            self.generate_barcode()
        
        super().save(*args, **kwargs)
    
    def generate_barcode(self):
        """Generate barcode image"""
        try:
            # Generate barcode
            CODE128 = barcode.get_barcode_class('code128')
            rv = BytesIO()
            CODE128(self.barcode, writer=ImageWriter()).write(rv)
            
            # Save to model
            self.barcode_image.save(
                f'{self.barcode}.png',
                File(rv),
                save=False
            )
        except Exception as e:
            print(f"Error generating barcode: {e}")
    
    def get_active_loans_count(self):
        """Hitung jumlah peminjaman aktif"""
        return self.loan_set.filter(status__in=['dipinjam', 'terlambat']).count()
    
    def has_overdue_loans(self):
        """Cek apakah ada peminjaman terlambat"""
        return self.loan_set.filter(status='terlambat').exists()
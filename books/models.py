from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import barcode
from barcode.writer import ImageWriter
from io import BytesIO
from django.core.files import File


class Book(models.Model):
    """
    Model untuk Buku
    Ini menyimpan informasi umum tentang buku
    """
    CATEGORY_CHOICES = [
        ('fiksi', 'Fiksi'),
        ('non_fiksi', 'Non-Fiksi'),
        ('referensi', 'Referensi'),
        ('majalah', 'Majalah'),
        ('komik', 'Komik'),
    ]
    
    # Informasi buku
    title = models.CharField(max_length=300, verbose_name='Judul Buku')
    author = models.CharField(max_length=200, verbose_name='Penulis')
    publisher = models.CharField(max_length=200, verbose_name='Penerbit')
    year_published = models.IntegerField(verbose_name='Tahun Terbit')
    isbn = models.CharField(max_length=13, unique=True, verbose_name='ISBN')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, verbose_name='Kategori')
    description = models.TextField(blank=True, null=True, verbose_name='Deskripsi')
    cover_image = models.ImageField(upload_to='books/covers/', blank=True, null=True, verbose_name='Cover Buku')
    
    # Informasi stok
    total_copies = models.IntegerField(default=1, verbose_name='Jumlah Salinan')
    
    # Rating
    rating = models.DecimalField(
        max_digits=2, 
        decimal_places=1, 
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        verbose_name='Rating'
    )
    
    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Buku'
        verbose_name_plural = 'Buku'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.author}"
    
    def get_available_copies_count(self):
        """Hitung jumlah salinan yang tersedia"""
        return self.bookcopy_set.filter(is_available=True).count()
    
    def get_borrowed_copies_count(self):
        """Hitung jumlah salinan yang dipinjam"""
        return self.bookcopy_set.filter(is_available=False).count()
    
    def is_available(self):
        """Cek apakah ada salinan yang tersedia"""
        return self.get_available_copies_count() > 0
    
    def get_rating_stars(self):
        """Get rating dalam bentuk bintang untuk template"""
        full_stars = int(self.rating)
        half_star = 1 if self.rating - full_stars >= 0.5 else 0
        empty_stars = 5 - full_stars - half_star
        return {
            'full': full_stars,
            'half': half_star,
            'empty': empty_stars
        }
    
    def get_total_borrowed(self):
        """Hitung total berapa kali buku ini dipinjam"""
        from loans.models import Loan
        return Loan.objects.filter(book_copy__book=self).count()


class BookCopy(models.Model):
    """
    Model untuk Salinan Buku
    Setiap buku bisa punya banyak salinan
    Contoh: Buku "Harry Potter" punya 3 salinan
    """
    CONDITION_CHOICES = [
        ('baik', 'Baik'),
        ('rusak_ringan', 'Rusak Ringan'),
        ('rusak_berat', 'Rusak Berat'),
    ]
    
    # Relasi ke buku
    book = models.ForeignKey(Book, on_delete=models.CASCADE, verbose_name='Buku')
    
    # Nomor salinan
    copy_number = models.IntegerField(verbose_name='Nomor Salinan')
    
    # Barcode
    barcode = models.CharField(max_length=50, unique=True, blank=True, verbose_name='Barcode')
    barcode_image = models.ImageField(upload_to='books/barcodes/', blank=True, null=True)
    
    # Kondisi dan ketersediaan
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='baik', verbose_name='Kondisi')
    is_available = models.BooleanField(default=True, verbose_name='Tersedia')
    
    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Salinan Buku'
        verbose_name_plural = 'Salinan Buku'
        ordering = ['book', 'copy_number']  # ✅ INI YANG DIPERBAIKI
        unique_together = ['book', 'copy_number']
    
    def __str__(self):
        return f"{self.book.title} - Copy #{self.copy_number}"
    
    def save(self, *args, **kwargs):
        """
        Override save method
        Auto generate barcode saat pertama kali save
        """
        # Generate barcode jika belum ada
        if not self.barcode:
            # Format: BK + ISBN + Copy Number
            # Contoh: BK9780545010221001
            self.barcode = f"BK{self.book.isbn}{str(self.copy_number).zfill(3)}"
        
        # Generate barcode image
        if not self.barcode_image:
            self.generate_barcode()
        
        super().save(*args, **kwargs)
    
    def generate_barcode(self):
        """Generate barcode image"""
        try:
            CODE128 = barcode.get_barcode_class('code128')
            rv = BytesIO()
            CODE128(self.barcode, writer=ImageWriter()).write(rv)
            
            self.barcode_image.save(
                f'{self.barcode}.png',
                File(rv),
                save=False
            )
        except Exception as e:
            print(f"Error generating barcode: {e}")
    
    def get_current_loan(self):
        """Get peminjaman aktif untuk salinan ini"""
        from loans.models import Loan
        return Loan.objects.filter(
            book_copy=self,
            status__in=['dipinjam', 'terlambat']
        ).first()
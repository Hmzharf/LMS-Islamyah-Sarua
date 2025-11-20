from django.db import models
from django.utils import timezone
from datetime import timedelta
from users.models import Member
from books.models import BookCopy


class Loan(models.Model):
    """
    Model untuk Peminjaman Buku
    Menyimpan record siapa pinjam buku apa, kapan, dll
    """
    STATUS_CHOICES = [
        ('dipinjam', 'Dipinjam'),
        ('terlambat', 'Terlambat'),
        ('dikembalikan', 'Dikembalikan'),
    ]
    
    # Relasi
    member = models.ForeignKey(
        Member, 
        on_delete=models.CASCADE, 
        verbose_name='Anggota'
    )
    book_copy = models.ForeignKey(
        BookCopy, 
        on_delete=models.CASCADE, 
        verbose_name='Salinan Buku'
    )
    
    # Tanggal
    borrowed_date = models.DateTimeField(
        default=timezone.now,
        verbose_name='Tanggal Pinjam'
    )
    due_date = models.DateTimeField(
        verbose_name='Tanggal Jatuh Tempo'
    )
    return_date = models.DateTimeField(
        blank=True, 
        null=True,
        verbose_name='Tanggal Kembali'
    )
    
    # Status dan denda
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='dipinjam',
        verbose_name='Status'
    )
    fine_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00,
        verbose_name='Jumlah Denda'
    )
    
    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Peminjaman'
        verbose_name_plural = 'Peminjaman'
        ordering = ['-borrowed_date']
    
    def __str__(self):
        return f"{self.member.name} - {self.book_copy.book.title}"
    
    def save(self, *args, **kwargs):
        """
        Override save method
        Auto set due_date jika belum ada (7 hari dari sekarang)
        """
        if not self.due_date:
            self.due_date = timezone.now() + timedelta(days=7)
        
        super().save(*args, **kwargs)
    
    def calculate_fine(self):
        """
        Hitung denda keterlambatan
        Rp 1.000 per hari
        """
        if self.status == 'dikembalikan' and self.return_date:
            # Jika sudah dikembalikan, hitung dari return_date
            if self.return_date > self.due_date:
                days_late = (self.return_date - self.due_date).days
                self.fine_amount = days_late * 1000
        elif self.status in ['dipinjam', 'terlambat']:
            # Jika belum dikembalikan, hitung dari sekarang
            if timezone.now() > self.due_date:
                days_late = (timezone.now() - self.due_date).days
                self.fine_amount = days_late * 1000
        
        return self.fine_amount
    
    def update_status(self):
        """
        Update status peminjaman
        Otomatis ubah jadi 'terlambat' jika lewat due_date
        """
        if self.status == 'dipinjam' and timezone.now() > self.due_date:
            self.status = 'terlambat'
            self.calculate_fine()
            self.save()
    
    def return_book(self):
        """
        Proses pengembalian buku
        """
        self.return_date = timezone.now()
        self.status = 'dikembalikan'
        self.calculate_fine()
        
        # Update ketersediaan book copy
        self.book_copy.is_available = True
        self.book_copy.save()
        
        self.save()
    
    def days_until_due(self):
        """Hitung berapa hari lagi jatuh tempo"""
        if self.status == 'dikembalikan':
            return 0
        delta = self.due_date - timezone.now()
        return delta.days
    
    def is_overdue(self):
        """Cek apakah sudah terlambat"""
        return self.status == 'terlambat' or (
            self.status == 'dipinjam' and timezone.now() > self.due_date
        )
            
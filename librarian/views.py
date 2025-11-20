from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count
from datetime import timedelta
from django.http import HttpResponse
import json

from users.models import Member
from books.models import Book, BookCopy
from loans.models import Loan

# Import untuk PDF
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import io

# Import Celery tasks
from loans.tasks import send_loan_success_email, send_return_success_email


@login_required
def dashboard_view(request):
    """
    Dashboard Librarian dengan Chart
    """
    # Update status peminjaman yang terlambat
    overdue_loans = Loan.objects.filter(
        status='dipinjam',
        due_date__lt=timezone.now()
    )
    for loan in overdue_loans:
        loan.update_status()
    
    # Statistik Utama
    total_books = Book.objects.count()
    total_members = Member.objects.filter(is_active=True).count()
    active_loans = Loan.objects.filter(status__in=['dipinjam', 'terlambat']).count()
    overdue_loans_count = Loan.objects.filter(status='terlambat').count()
    
    # Aktivitas hari ini
    today = timezone.now().date()
    today_borrows = Loan.objects.filter(borrowed_date__date=today).count()
    today_returns = Loan.objects.filter(return_date__date=today).count()
    
    # Alert jatuh tempo (3 hari ke depan)
    three_days_later = timezone.now() + timedelta(days=3)
    upcoming_due = Loan.objects.filter(
        status='dipinjam',
        due_date__lte=three_days_later,
        due_date__gte=timezone.now()
    ).select_related('member', 'book_copy__book').order_by('due_date')[:5]
    
    # Peminjaman terbaru
    recent_loans = Loan.objects.select_related(
        'member', 'book_copy__book'
    ).order_by('-borrowed_date')[:10]
    
    # Buku populer (top 5)
    popular_books = Book.objects.annotate(
        loan_count=Count('bookcopy__loan')
    ).order_by('-loan_count')[:5]
    
    # ========== DATA UNTUK CHART ==========
    
    # 1. Peminjaman per Kategori Buku (Bar Chart)
    category_stats = Book.objects.values('category').annotate(
        total_loans=Count('bookcopy__loan')
    ).order_by('-total_loans')
    
    categories = [dict(Book.CATEGORY_CHOICES).get(item['category'], item['category']) for item in category_stats]
    category_loans = [item['total_loans'] for item in category_stats]
    
    # 2. Trend Peminjaman 7 Hari Terakhir (Line Chart)
    last_7_days = []
    loans_per_day = []
    returns_per_day = []
    
    for i in range(6, -1, -1):
        date = timezone.now().date() - timedelta(days=i)
        last_7_days.append(date.strftime('%d %b'))
        
        # Hitung peminjaman per hari
        borrows = Loan.objects.filter(borrowed_date__date=date).count()
        loans_per_day.append(borrows)
        
        # Hitung pengembalian per hari
        returns = Loan.objects.filter(return_date__date=date).count()
        returns_per_day.append(returns)
    
    # 3. Distribusi Tipe Anggota (Pie Chart)
    member_types = Member.objects.filter(is_active=True).values('member_type').annotate(
        count=Count('id')
    )
    
    member_type_labels = [dict(Member.MEMBER_TYPE_CHOICES).get(item['member_type'], item['member_type']) for item in member_types]
    member_type_counts = [item['count'] for item in member_types]
    
    # 4. Status Peminjaman (Doughnut Chart)
    loan_status = Loan.objects.values('status').annotate(
        count=Count('id')
    )
    
    status_labels = []
    status_counts = []
    for item in loan_status:
        if item['status'] == 'dipinjam':
            status_labels.append('Dipinjam')
        elif item['status'] == 'terlambat':
            status_labels.append('Terlambat')
        elif item['status'] == 'dikembalikan':
            status_labels.append('Dikembalikan')
        status_counts.append(item['count'])
    
    context = {
        # Statistik Utama
        'total_books': total_books,
        'total_members': total_members,
        'active_loans': active_loans,
        'overdue_loans_count': overdue_loans_count,
        'today_borrows': today_borrows,
        'today_returns': today_returns,
        'upcoming_due': upcoming_due,
        'recent_loans': recent_loans,
        'popular_books': popular_books,
        
        # Data untuk Chart (JSON format)
        'categories': json.dumps(categories),
        'category_loans': json.dumps(category_loans),
        'last_7_days': json.dumps(last_7_days),
        'loans_per_day': json.dumps(loans_per_day),
        'returns_per_day': json.dumps(returns_per_day),
        'member_type_labels': json.dumps(member_type_labels),
        'member_type_counts': json.dumps(member_type_counts),
        'status_labels': json.dumps(status_labels),
        'status_counts': json.dumps(status_counts),
    }
    
    return render(request, 'librarian/dashboard.html', context)


@login_required
def scan_borrow_view(request):
    """
    Halaman scan barcode untuk peminjaman
    """
    return render(request, 'librarian/scan_borrow.html')


@login_required
def scan_return_view(request):
    """
    Halaman scan barcode untuk pengembalian
    """
    return render(request, 'librarian/scan_return.html')


@login_required
def process_borrow(request):
    """
    Proses peminjaman buku dengan email notification
    """
    if request.method == 'POST':
        member_barcode = request.POST.get('member_barcode', '').strip()
        book_barcode = request.POST.get('book_barcode', '').strip()
        
        # Validasi input
        if not member_barcode or not book_barcode:
            messages.error(request, 'Barcode anggota dan buku harus diisi!')
            return redirect('librarian:scan_borrow')
        
        # Cari member
        try:
            member = Member.objects.get(barcode=member_barcode, is_active=True)
        except Member.DoesNotExist:
            messages.error(request, 'Anggota tidak ditemukan atau tidak aktif!')
            return redirect('librarian:scan_borrow')
        
        # Cek apakah member punya tunggakan
        if member.has_overdue_loans():
            messages.error(request, f'{member.name} memiliki tunggakan! Harap kembalikan buku yang terlambat terlebih dahulu.')
            return redirect('librarian:scan_borrow')
        
        # Cari book copy
        try:
            book_copy = BookCopy.objects.get(barcode=book_barcode)
        except BookCopy.DoesNotExist:
            messages.error(request, 'Buku tidak ditemukan!')
            return redirect('librarian:scan_borrow')
        
        # Cek ketersediaan
        if not book_copy.is_available:
            messages.error(request, f'Buku "{book_copy.book.title}" sedang dipinjam!')
            return redirect('librarian:scan_borrow')
        
        # Buat loan record
        loan = Loan.objects.create(
            member=member,
            book_copy=book_copy,
            borrowed_date=timezone.now(),
            due_date=timezone.now() + timedelta(days=7),
            status='dipinjam'
        )
        
        # Update ketersediaan
        book_copy.is_available = False
        book_copy.save()
        
        # KIRIM EMAIL NOTIFICATION (ASYNC dengan Celery)
        try:
            # Kirim email secara asynchronous
            send_loan_success_email.delay(loan.id)
            
            messages.success(
                request, 
                f'Peminjaman berhasil! {member.name} meminjam "{book_copy.book.title}". '
                f'Jatuh tempo: {loan.due_date.strftime("%d %B %Y")}. '
                f'Email notifikasi telah dikirim ke {member.email}.'
            )
        except Exception as e:
            # Jika email gagal, tetap lanjutkan (peminjaman sudah berhasil)
            messages.success(
                request, 
                f'Peminjaman berhasil! {member.name} meminjam "{book_copy.book.title}". '
                f'Jatuh tempo: {loan.due_date.strftime("%d %B %Y")}. '
                f'(Email notifikasi gagal dikirim: {str(e)})'
            )
        
        return redirect('librarian:scan_borrow')
    
    return redirect('librarian:scan_borrow')


@login_required
def process_return(request):
    """
    Proses pengembalian buku dengan email notification
    """
    if request.method == 'POST':
        book_barcode = request.POST.get('book_barcode', '').strip()
        
        # Validasi input
        if not book_barcode:
            messages.error(request, 'Barcode buku harus diisi!')
            return redirect('librarian:scan_return')
        
        # Cari book copy
        try:
            book_copy = BookCopy.objects.get(barcode=book_barcode)
        except BookCopy.DoesNotExist:
            messages.error(request, 'Buku tidak ditemukan!')
            return redirect('librarian:scan_return')
        
        # Cari loan aktif
        try:
            loan = Loan.objects.get(
                book_copy=book_copy,
                status__in=['dipinjam', 'terlambat']
            )
        except Loan.DoesNotExist:
            messages.error(request, 'Tidak ada peminjaman aktif untuk buku ini!')
            return redirect('librarian:scan_return')
        
        # Proses pengembalian
        loan.return_book()
        
        # KIRIM EMAIL NOTIFICATION (ASYNC dengan Celery)
        try:
            send_return_success_email.delay(loan.id)
        except Exception as e:
            # Jika email gagal, tidak masalah (pengembalian sudah berhasil)
            pass
        
        # Pesan
        if loan.fine_amount > 0:
            messages.warning(request, f'Pengembalian berhasil! Denda keterlambatan: Rp {loan.fine_amount:,.0f}')
        else:
            messages.success(request, f'Pengembalian berhasil! Terima kasih.')
        
        return redirect('librarian:scan_return')
    
    return redirect('librarian:scan_return')


@login_required
def active_loans_view(request):
    """
    Daftar peminjaman aktif
    """
    # Update status
    overdue_loans = Loan.objects.filter(
        status='dipinjam',
        due_date__lt=timezone.now()
    )
    for loan in overdue_loans:
        loan.update_status()
    
    # Get active loans
    loans = Loan.objects.filter(
        status__in=['dipinjam', 'terlambat']
    ).select_related('member', 'book_copy__book').order_by('due_date')
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        loans = loans.filter(
            Q(member__name__icontains=search_query) |
            Q(member__nis__icontains=search_query) |
            Q(book_copy__book__title__icontains=search_query)
        )
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        loans = loans.filter(status=status_filter)
    
    context = {
        'loans': loans,
        'search_query': search_query,
        'status_filter': status_filter,
    }
    
    return render(request, 'librarian/active_loans.html', context)


# ============= MEMBERS MANAGEMENT =============

@login_required
def members_list_view(request):
    """
    Daftar anggota
    """
    members = Member.objects.all().order_by('-created_at')
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        members = members.filter(
            Q(name__icontains=search_query) |
            Q(nis__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    # Filter by type
    member_type = request.GET.get('type', '')
    if member_type:
        members = members.filter(member_type=member_type)
        # Filter by status
    status = request.GET.get('status', '')
    if status == 'active':
        members = members.filter(is_active=True)
    elif status == 'inactive':
        members = members.filter(is_active=False)
    
    context = {
        'members': members,
        'search_query': search_query,
        'selected_type': member_type,
        'selected_status': status,
        'member_types': Member.MEMBER_TYPE_CHOICES,
    }
    
    return render(request, 'librarian/members_list.html', context)


@login_required
def member_add_view(request):
    """
    Tambah anggota baru
    """
    if request.method == 'POST':
        # Get data from form
        name = request.POST.get('name')
        member_type = request.POST.get('member_type')
        nis = request.POST.get('nis')
        gender = request.POST.get('gender')
        date_of_birth = request.POST.get('date_of_birth')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        address = request.POST.get('address')
        class_name = request.POST.get('class_name')
        
        # Validasi
        if not all([name, member_type, nis, gender, date_of_birth, phone, address]):
            messages.error(request, 'Semua field wajib diisi kecuali email dan kelas!')
            return redirect('librarian:member_add')
        
        # Cek NIS duplikat
        if Member.objects.filter(nis=nis).exists():
            messages.error(request, f'NIS {nis} sudah terdaftar!')
            return redirect('librarian:member_add')
        
        # Buat member
        member = Member.objects.create(
            name=name,
            member_type=member_type,
            nis=nis,
            gender=gender,
            date_of_birth=date_of_birth,
            phone=phone,
            email=email if email else None,
            address=address,
            class_name=class_name if class_name else None,
        )
        
        messages.success(request, f'Anggota {member.name} berhasil ditambahkan!')
        return redirect('librarian:member_detail', pk=member.pk)
    
    return render(request, 'librarian/member_form.html', {'action': 'add'})


@login_required
def member_detail_view(request, pk):
    """
    Detail anggota
    """
    member = get_object_or_404(Member, pk=pk)
    
    # Get loan history
    loans = member.loan_set.all().select_related('book_copy__book').order_by('-borrowed_date')[:10]
    
    context = {
        'member': member,
        'loans': loans,
    }
    
    return render(request, 'librarian/member_detail.html', context)


@login_required
def member_edit_view(request, pk):
    """
    Edit anggota
    """
    member = get_object_or_404(Member, pk=pk)
    
    if request.method == 'POST':
        # Get data from form
        member.name = request.POST.get('name')
        member.member_type = request.POST.get('member_type')
        member.gender = request.POST.get('gender')
        member.date_of_birth = request.POST.get('date_of_birth')
        member.phone = request.POST.get('phone')
        member.email = request.POST.get('email') or None
        member.address = request.POST.get('address')
        member.class_name = request.POST.get('class_name') or None
        member.is_active = request.POST.get('is_active') == 'on'
        
        # Validasi
        if not all([member.name, member.member_type, member.gender, member.date_of_birth, member.phone, member.address]):
            messages.error(request, 'Semua field wajib diisi kecuali email dan kelas!')
            return redirect('librarian:member_edit', pk=pk)
        
        member.save()
        
        messages.success(request, f'Data anggota {member.name} berhasil diupdate!')
        return redirect('librarian:member_detail', pk=pk)
    
    context = {
        'member': member,
        'action': 'edit'
    }
    
    return render(request, 'librarian/member_form.html', context)


@login_required
def member_delete_view(request, pk):
    """
    Hapus anggota (soft delete)
    """
    member = get_object_or_404(Member, pk=pk)
    
    if request.method == 'POST':
        # Cek apakah ada peminjaman aktif
        if member.get_active_loans_count() > 0:
            messages.error(request, f'{member.name} masih memiliki peminjaman aktif! Tidak dapat dihapus.')
            return redirect('librarian:member_detail', pk=pk)
        
        # Soft delete
        member.is_active = False
        member.save()
        
        messages.success(request, f'Anggota {member.name} berhasil dinonaktifkan!')
        return redirect('librarian:members_list')
    
    return redirect('librarian:member_detail', pk=pk)


@login_required
def member_print_card_view(request, pk):
    """
    Print kartu anggota (PDF)
    """
    member = get_object_or_404(Member, pk=pk)
    
    # Buat PDF
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Ukuran kartu (credit card size: 3.375" x 2.125")
    card_width = 3.375 * inch
    card_height = 2.125 * inch
    
    # Posisi kartu di tengah halaman
    x = (width - card_width) / 2
    y = height - card_height - 2 * inch
    
    # Border kartu
    p.setStrokeColorRGB(0.4, 0.49, 0.92)  # Purple
    p.setLineWidth(2)
    p.rect(x, y, card_width, card_height)
    
    # Header dengan background purple
    p.setFillColorRGB(0.4, 0.49, 0.92)
    p.rect(x, y + card_height - 0.5*inch, card_width, 0.5*inch, fill=1)
    
    # Judul kartu
    p.setFillColorRGB(1, 1, 1)  # White
    p.setFont("Helvetica-Bold", 14)
    p.drawCentredString(x + card_width/2, y + card_height - 0.35*inch, "KARTU ANGGOTA PERPUSTAKAAN")
    
    # Data anggota
    p.setFillColorRGB(0, 0, 0)  # Black
    p.setFont("Helvetica-Bold", 10)
    p.drawString(x + 0.2*inch, y + card_height - 0.8*inch, "Nama:")
    p.drawString(x + 0.2*inch, y + card_height - 1.1*inch, "NIS/NIP:")
    p.drawString(x + 0.2*inch, y + card_height - 1.4*inch, "Tipe:")
    
    p.setFont("Helvetica", 10)
    p.drawString(x + 1*inch, y + card_height - 0.8*inch, member.name)
    p.drawString(x + 1*inch, y + card_height - 1.1*inch, member.nis)
    p.drawString(x + 1*inch, y + card_height - 1.4*inch, member.get_member_type_display())
    
    # Barcode
    if member.barcode_image:
        try:
            img_path = member.barcode_image.path
            img = ImageReader(img_path)
            p.drawImage(img, x + 1.8*inch, y + 0.1*inch, width=1.4*inch, height=0.5*inch)
        except:
            pass
    
    # Barcode text
    p.setFont("Helvetica", 8)
    p.drawCentredString(x + 2.5*inch, y + 0.05*inch, member.barcode)
    
    # Footer
    p.setFont("Helvetica", 7)
    p.drawCentredString(x + card_width/2, y - 0.3*inch, "Harap bawa kartu ini setiap kali meminjam buku")
    
    p.showPage()
    p.save()
    
    # Return PDF
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="kartu_{member.nis}.pdf"'
    
    return response


# ============= BOOKS MANAGEMENT =============

@login_required
def books_list_view(request):
    """
    Daftar buku
    """
    books = Book.objects.all().order_by('-created_at')
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        books = books.filter(
            Q(title__icontains=search_query) |
            Q(author__icontains=search_query) |
            Q(isbn__icontains=search_query) |
            Q(publisher__icontains=search_query)
        )
    
    # Filter by category
    category = request.GET.get('category', '')
    if category:
        books = books.filter(category=category)
    
    context = {
        'books': books,
        'search_query': search_query,
        'selected_category': category,
        'categories': Book.CATEGORY_CHOICES,
    }
    
    return render(request, 'librarian/books_list.html', context)


@login_required
def book_add_view(request):
    """
    Tambah buku baru
    """
    if request.method == 'POST':
        # Get data from form
        title = request.POST.get('title')
        author = request.POST.get('author')
        publisher = request.POST.get('publisher')
        year_published = request.POST.get('year_published')
        isbn = request.POST.get('isbn')
        category = request.POST.get('category')
        description = request.POST.get('description')
        total_copies = request.POST.get('total_copies', 1)
        rating = request.POST.get('rating', 0.0)
        cover_image = request.FILES.get('cover_image')
        
        # Validasi
        if not all([title, author, publisher, year_published, isbn, category]):
            messages.error(request, 'Semua field wajib diisi kecuali deskripsi dan cover!')
            return redirect('librarian:book_add')
        
        # Cek ISBN duplikat
        if Book.objects.filter(isbn=isbn).exists():
            messages.error(request, f'ISBN {isbn} sudah terdaftar!')
            return redirect('librarian:book_add')
        
        # Buat book
        book = Book.objects.create(
            title=title,
            author=author,
            publisher=publisher,
            year_published=int(year_published),
            isbn=isbn,
            category=category,
            description=description if description else None,
            total_copies=int(total_copies),
            rating=float(rating),
            cover_image=cover_image if cover_image else None,
        )
        
        # Buat book copies
        for i in range(1, int(total_copies) + 1):
            BookCopy.objects.create(
                book=book,
                copy_number=i,
                condition='baik',
                is_available=True
            )
        
        messages.success(request, f'Buku "{book.title}" berhasil ditambahkan dengan {total_copies} salinan!')
        return redirect('librarian:book_detail', pk=book.pk)
    
    return render(request, 'librarian/book_form.html', {'action': 'add'})


@login_required
def book_detail_view(request, pk):
    """
    Detail buku
    """
    book = get_object_or_404(Book, pk=pk)
    book_copies = book.bookcopy_set.all().order_by('copy_number')
    
    # Get loan history
    loans = Loan.objects.filter(
        book_copy__book=book
    ).select_related('member', 'book_copy').order_by('-borrowed_date')[:10]
    
    context = {
        'book': book,
        'book_copies': book_copies,
        'loans': loans,
    }
    
    return render(request, 'librarian/book_detail.html', context)


@login_required
def book_edit_view(request, pk):
    """
    Edit buku
    """
    book = get_object_or_404(Book, pk=pk)
    
    if request.method == 'POST':
        # Get data from form
        book.title = request.POST.get('title')
        book.author = request.POST.get('author')
        book.publisher = request.POST.get('publisher')
        book.year_published = int(request.POST.get('year_published'))
        book.category = request.POST.get('category')
        book.description = request.POST.get('description') or None
        book.rating = float(request.POST.get('rating', 0.0))
        
        # Cover image
        cover_image = request.FILES.get('cover_image')
        if cover_image:
            book.cover_image = cover_image
        
        # Validasi
        if not all([book.title, book.author, book.publisher, book.year_published, book.category]):
            messages.error(request, 'Semua field wajib diisi kecuali deskripsi dan cover!')
            return redirect('librarian:book_edit', pk=pk)
        
        book.save()
        
        messages.success(request, f'Data buku "{book.title}" berhasil diupdate!')
        return redirect('librarian:book_detail', pk=pk)
    
    context = {
        'book': book,
        'action': 'edit'
    }
    
    return render(request, 'librarian/book_form.html', context)


@login_required
def book_delete_view(request, pk):
    """
    Hapus buku
    """
    book = get_object_or_404(Book, pk=pk)
    
    if request.method == 'POST':
        # Cek apakah ada salinan yang sedang dipinjam
        borrowed_copies = book.bookcopy_set.filter(is_available=False).count()
        if borrowed_copies > 0:
            messages.error(request, f'Buku "{book.title}" memiliki {borrowed_copies} salinan yang sedang dipinjam! Tidak dapat dihapus.')
            return redirect('librarian:book_detail', pk=pk)
        
        # Hapus buku (akan otomatis hapus book copies karena CASCADE)
        title = book.title
        book.delete()
        
        messages.success(request, f'Buku "{title}" berhasil dihapus!')
        return redirect('librarian:books_list')
    
    return redirect('librarian:book_detail', pk=pk)
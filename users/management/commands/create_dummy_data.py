from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from users.models import Member
from books.models import Book, BookCopy
from loans.models import Loan
from django.utils import timezone
from datetime import timedelta
import random

User = get_user_model()


class Command(BaseCommand):
    help = 'Create dummy data for testing'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating dummy data...')
        
        # Create users
        self.create_users()
        
        # Create members
        self.create_members()
        
        # Create books
        self.create_books()
        
        # Create loans
        self.create_loans()
        
        self.stdout.write(self.style.SUCCESS('✓ Dummy data created successfully!'))

    def create_users(self):
        """Create admin and librarian users"""
        # Admin
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@perpustakaan.com',
                password='admin123',
                role='admin'
            )
            self.stdout.write('✓ Admin user created')
        
        # Librarian
        if not User.objects.filter(username='librarian').exists():
            User.objects.create_user(
                username='librarian',
                email='librarian@perpustakaan.com',
                password='librarian123',
                role='librarian',
                is_staff=True
            )
            self.stdout.write('✓ Librarian user created')

    def create_members(self):
        """Create dummy members"""
        members_data = [
            {
                'name': 'Ahmad Rizki',
                'member_type': 'siswa',
                'nis': '2024001',
                'gender': 'L',
                'date_of_birth': '2008-05-15',
                'phone': '081234567890',
                'email': 'ahmad.rizki@student.com',
                'address': 'Jl. Merdeka No. 123, Jakarta',
                'class_name': 'XII IPA 1',
            },
            {
                'name': 'Siti Nurhaliza',
                'member_type': 'siswa',
                'nis': '2024002',
                'gender': 'P',
                'date_of_birth': '2008-08-20',
                'phone': '081234567891',
                'email': 'siti.nurhaliza@student.com',
                'address': 'Jl. Sudirman No. 456, Jakarta',
                'class_name': 'XII IPA 2',
            },
            {
                'name': 'Budi Santoso',
                'member_type': 'guru',
                'nis': 'G001',
                'gender': 'L',
                'date_of_birth': '1985-03-10',
                'phone': '081234567892',
                'email': 'budi.santoso@teacher.com',
                'address': 'Jl. Thamrin No. 789, Jakarta',
                'class_name': None,
            },
            {
                'name': 'Dewi Lestari',
                'member_type': 'guru',
                'nis': 'G002',
                'gender': 'P',
                'date_of_birth': '1990-07-25',
                'phone': '081234567893',
                'email': 'dewi.lestari@teacher.com',
                'address': 'Jl. Gatot Subroto No. 321, Jakarta',
                'class_name': None,
            },
            {
                'name': 'Andi Wijaya',
                'member_type': 'staff',
                'nis': 'S001',
                'gender': 'L',
                'date_of_birth': '1995-11-30',
                'phone': '081234567894',
                'email': 'andi.wijaya@staff.com',
                'address': 'Jl. Kuningan No. 654, Jakarta',
                'class_name': None,
            },
        ]
        
        for data in members_data:
            if not Member.objects.filter(nis=data['nis']).exists():
                Member.objects.create(**data)
                self.stdout.write(f'✓ Member created: {data["name"]}')

    def create_books(self):
        """Create dummy books"""
        books_data = [
            {
                'title': 'Laskar Pelangi',
                'author': 'Andrea Hirata',
                'publisher': 'Bentang Pustaka',
                'year_published': 2005,
                'isbn': '9789793062792',
                'category': 'fiksi',
                'description': 'Novel tentang perjuangan anak-anak di Belitung untuk mendapatkan pendidikan.',
                'total_copies': 3,
                'rating': 4.5,
            },
            {
                'title': 'Bumi Manusia',
                'author': 'Pramoedya Ananta Toer',
                'publisher': 'Hasta Mitra',
                'year_published': 1980,
                'isbn': '9789799731234',
                'category': 'fiksi',
                'description': 'Novel sejarah tentang kehidupan di masa kolonial Belanda.',
                'total_copies': 2,
                'rating': 4.8,
            },
            {
                'title': 'Matematika SMA Kelas XII',
                'author': 'Tim Penulis',
                'publisher': 'Erlangga',
                'year_published': 2020,
                'isbn': '9786024344567',
                'category': 'referensi',
                'description': 'Buku pelajaran matematika untuk SMA kelas XII.',
                'total_copies': 5,
                'rating': 4.0,
            },
            {
                'title': 'Naruto Vol. 1',
                'author': 'Masashi Kishimoto',
                'publisher': 'Elex Media',
                'year_published': 2002,
                'isbn': '9789797803456',
                'category': 'komik',
                'description': 'Komik manga tentang ninja muda bernama Naruto.',
                'total_copies': 2,
                'rating': 4.7,
            },
            {
                'title': 'National Geographic Indonesia',
                'author': 'Tim Redaksi',
                'publisher': 'National Geographic',
                'year_published': 2023,
                'isbn': '9786028123456',
                'category': 'majalah',
                'description': 'Majalah tentang alam, budaya, dan sains.',
                'total_copies': 3,
                'rating': 4.3,
            },
        ]
        
        for data in books_data:
            if not Book.objects.filter(isbn=data['isbn']).exists():
                total_copies = data.pop('total_copies')
                book = Book.objects.create(**data)
                
                # Create book copies
                for i in range(1, total_copies + 1):
                    BookCopy.objects.create(
                        book=book,
                        copy_number=i,
                        condition='baik',
                        is_available=True
                    )
                
                self.stdout.write(f'✓ Book created: {book.title} ({total_copies} copies)')

    def create_loans(self):
        """Create dummy loans"""
        members = list(Member.objects.filter(is_active=True))
        book_copies = list(BookCopy.objects.all())
        
        if not members or not book_copies:
            self.stdout.write(self.style.WARNING('No members or books available for loans'))
            return
        
        # Create some active loans
        for i in range(3):
            member = random.choice(members)
            available_copies = [bc for bc in book_copies if bc.is_available]
            
            if not available_copies:
                break
            
            book_copy = random.choice(available_copies)
            
            # Random borrowed date (1-5 days ago)
            days_ago = random.randint(1, 5)
            borrowed_date = timezone.now() - timedelta(days=days_ago)
            due_date = borrowed_date + timedelta(days=7)
            
            loan = Loan.objects.create(
                member=member,
                book_copy=book_copy,
                borrowed_date=borrowed_date,
                due_date=due_date,
                status='dipinjam'
            )
            
            # Update book copy availability
            book_copy.is_available = False
            book_copy.save()
            
            self.stdout.write(f'✓ Loan created: {member.name} - {book_copy.book.title}')
        
        # Create some overdue loans
        for i in range(2):
            member = random.choice(members)
            available_copies = [bc for bc in book_copies if bc.is_available]
            
            if not available_copies:
                break
            
            book_copy = random.choice(available_copies)
            
            # Borrowed 10 days ago (overdue)
            borrowed_date = timezone.now() - timedelta(days=10)
            due_date = borrowed_date + timedelta(days=7)
            
            loan = Loan.objects.create(
                member=member,
                book_copy=book_copy,
                borrowed_date=borrowed_date,
                due_date=due_date,
                status='terlambat'
            )
            loan.calculate_fine()
            loan.save()
            
            # Update book copy availability
            book_copy.is_available = False
            book_copy.save()
            
            self.stdout.write(f'✓ Overdue loan created: {member.name} - {book_copy.book.title}')
        
        # Create some returned loans
        for i in range(3):
            member = random.choice(members)
            available_copies = [bc for bc in book_copies if bc.is_available]
            
            if not available_copies:
                break
            
            book_copy = random.choice(available_copies)
            
            # Borrowed 15 days ago, returned 8 days ago
            borrowed_date = timezone.now() - timedelta(days=15)
            due_date = borrowed_date + timedelta(days=7)
            return_date = timezone.now() - timedelta(days=8)
            
            loan = Loan.objects.create(
                member=member,
                book_copy=book_copy,
                borrowed_date=borrowed_date,
                due_date=due_date,
                return_date=return_date,
                status='dikembalikan'
            )
            loan.calculate_fine()
            loan.save()
            
            self.stdout.write(f'✓ Returned loan created: {member.name} - {book_copy.book.title}')

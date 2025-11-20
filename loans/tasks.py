"""
Celery tasks untuk loans app
"""
from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


@shared_task(bind=True, max_retries=3)
def send_loan_success_email(self, loan_id):
    """
    Task untuk kirim email saat peminjaman berhasil
    
    Args:
        loan_id: ID dari Loan object
    """
    try:
        from loans.models import Loan
        
        # Get loan object
        loan = Loan.objects.select_related('member', 'book_copy__book').get(id=loan_id)
        
        # Cek apakah member punya email
        if not loan.member.email:
            print(f"[CELERY] Member {loan.member.name} tidak punya email. Skip.")
            return f"Member {loan.member.name} tidak punya email"
        
        # Render email template
        html_message = render_to_string('emails/loan_success.html', {
            'member': loan.member,
            'loan': loan,
        })
        
        # Plain text version (fallback)
        plain_message = strip_tags(html_message)
        
        # Subject
        subject = f'Peminjaman Berhasil - {loan.book_copy.book.title}'
        
        # Send email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[loan.member.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        print(f"[CELERY] ✓ Email peminjaman berhasil dikirim ke {loan.member.email}")
        return f"Email sent to {loan.member.email}"
        
    except Loan.DoesNotExist:
        print(f"[CELERY] ✗ Loan ID {loan_id} tidak ditemukan")
        return f"Loan ID {loan_id} not found"
        
    except Exception as e:
        print(f"[CELERY] ✗ Error sending email: {str(e)}")
        # Retry task jika gagal (max 3x)
        raise self.retry(exc=e, countdown=60)  # Retry setelah 60 detik


@shared_task(bind=True, max_retries=3)
def send_return_success_email(self, loan_id):
    """
    Task untuk kirim email saat pengembalian berhasil
    
    Args:
        loan_id: ID dari Loan object
    """
    try:
        from loans.models import Loan
        
        # Get loan object
        loan = Loan.objects.select_related('member', 'book_copy__book').get(id=loan_id)
        
        # Cek apakah member punya email
        if not loan.member.email:
            print(f"[CELERY] Member {loan.member.name} tidak punya email. Skip.")
            return f"Member {loan.member.name} tidak punya email"
        
        # Render email template
        html_message = render_to_string('emails/return_success.html', {
            'member': loan.member,
            'loan': loan,
        })
        
        # Plain text version
        plain_message = strip_tags(html_message)
        
        # Subject
        if loan.fine_amount > 0:
            subject = f'Pengembalian Berhasil - Denda Rp {loan.fine_amount:,.0f}'
        else:
            subject = f'Pengembalian Berhasil - {loan.book_copy.book.title}'
        
        # Send email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[loan.member.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        print(f"[CELERY] ✓ Email pengembalian berhasil dikirim ke {loan.member.email}")
        return f"Email sent to {loan.member.email}"
        
    except Loan.DoesNotExist:
        print(f"[CELERY] ✗ Loan ID {loan_id} tidak ditemukan")
        return f"Loan ID {loan_id} not found"
        
    except Exception as e:
        print(f"[CELERY] ✗ Error sending email: {str(e)}")
        raise self.retry(exc=e, countdown=60)


@shared_task
def send_due_date_reminders():
    """
    Periodic task: Kirim reminder 1 hari sebelum jatuh tempo
    Dijalankan setiap hari jam 08:00 (lihat settings.py CELERY_BEAT_SCHEDULE)
    """
    from loans.models import Loan
    
    # Get loans yang jatuh tempo besok
    tomorrow = timezone.now().date() + timedelta(days=1)
    
    loans = Loan.objects.filter(
        status='dipinjam',
        due_date__date=tomorrow
    ).select_related('member', 'book_copy__book')
    
    count = 0
    for loan in loans:
        # Skip jika member tidak punya email
        if not loan.member.email:
            continue
        
        try:
            # Render email template
            html_message = render_to_string('emails/due_date_reminder.html', {
                'member': loan.member,
                'loan': loan,
            })
            
            plain_message = strip_tags(html_message)
            
            # Send email
            send_mail(
                subject=f'Reminder: Buku Jatuh Tempo Besok - {loan.book_copy.book.title}',
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[loan.member.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            count += 1
            print(f"[CELERY] ✓ Reminder sent to {loan.member.email}")
            
        except Exception as e:
            print(f"[CELERY] ✗ Error sending reminder to {loan.member.email}: {str(e)}")
    
    print(f"[CELERY] Total {count} reminder emails sent")
    return f"{count} reminder emails sent"


@shared_task
def send_overdue_notifications():
    """
    Periodic task: Kirim notifikasi untuk peminjaman yang terlambat
    Dijalankan setiap hari jam 09:00 (lihat settings.py CELERY_BEAT_SCHEDULE)
    """
    from loans.models import Loan
    
    # Get loans yang terlambat
    overdue_loans = Loan.objects.filter(
        status='terlambat'
    ).select_related('member', 'book_copy__book')
    
    count = 0
    for loan in overdue_loans:
        # Skip jika member tidak punya email
        if not loan.member.email:
            continue
        
        try:
            # Hitung hari terlambat
            days_overdue = (timezone.now().date() - loan.due_date.date()).days
            
            # Render email template
            html_message = render_to_string('emails/overdue_notification.html', {
                'member': loan.member,
                'loan': loan,
                'days_overdue': days_overdue,
            })
            
            plain_message = strip_tags(html_message)
            
            # Send email
            send_mail(
                subject=f'URGENT: Buku Terlambat {days_overdue} Hari - Denda Rp {loan.fine_amount:,.0f}',
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[loan.member.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            count += 1
            print(f"[CELERY] ✓ Overdue notification sent to {loan.member.email}")
            
        except Exception as e:
            print(f"[CELERY] ✗ Error sending overdue notification to {loan.member.email}: {str(e)}")
    
    print(f"[CELERY] Total {count} overdue notifications sent")
    return f"{count} overdue notifications sent"


@shared_task
def update_loan_status():
    """
    Periodic task: Update status peminjaman yang terlambat
    Dijalankan setiap jam (lihat settings.py CELERY_BEAT_SCHEDULE)
    """
    from loans.models import Loan
    
    # Get loans yang sudah lewat due date tapi masih status 'dipinjam'
    overdue_loans = Loan.objects.filter(
        status='dipinjam',
        due_date__lt=timezone.now()
    )
    
    count = 0
    for loan in overdue_loans:
        loan.update_status()
        count += 1
    
    print(f"[CELERY] Updated {count} loan statuses to 'terlambat'")
    return f"{count} loans updated to overdue"
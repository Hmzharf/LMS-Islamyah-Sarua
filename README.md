# 📚 Sistem Manajemen Perpustakaan Sekolah

Sistem manajemen perpustakaan berbasis web dengan fitur email notification menggunakan Django, PostgreSQL, Celery, dan Redis.

## ✨ Fitur

- 📖 Manajemen Buku (CRUD)
- 👥 Manajemen Anggota (Siswa, Guru, Staff)
- 📊 Dashboard dengan Statistik & Chart
- 🔍 Scan Barcode untuk Peminjaman & Pengembalian
- 📧 Email Notification (Celery + Redis)
  - Email saat peminjaman berhasil
  - Email saat pengembalian berhasil
  - Email reminder jatuh tempo (periodic)
  - Email notifikasi keterlambatan (periodic)
- 📈 Laporan & Statistik
- 🎫 Generate Barcode Otomatis
- 🖨️ Print Kartu Anggota (PDF)
- 💰 Sistem Denda Otomatis

## 🛠️ Teknologi

- **Backend:** Django 4.2.7
- **Database:** PostgreSQL
- **Task Queue:** Celery + Redis
- **Email:** SMTP Gmail
- **Frontend:** HTML, CSS, Bootstrap 5, JavaScript (Chart.js)
- **Barcode:** python-barcode
- **PDF:** ReportLab

## 📋 Requirements

- Python 3.8+
- PostgreSQL 12+
- Redis 6+

# 🚀 Instalasi

## 1. Clone Repository
````bash
git clone https://github.com/username/perpustakaan-sekolah.git
cd perpustakaan-sekolah

## Buat Virtual Environment
````bash
python -m venv venv
source venv/bin/activate  #Linux/Mac
#atau
venv\Scripts\activate  #Windows

## Install Dependencies
bash
pip install -r requirements.txt

Setup Database
bash
#Buat database PostgreSQL
sudo -u postgres psql
CREATE DATABASE namadb;
CREATE USER namauser WITH PASSWORD 'pasuser';
GRANT ALL PRIVILEGES ON DATABASE namadb TO namauser;
\q

Migrate database

python manage.py migrate

## Buat File .env
````bash
cp .env.example .env
nano .env

Isi .env:

### 5. Buat File .env (Lanjutan)

**Isi .env:**

env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=namadb
DB_USER=namauser
DB_PASSWORD=pass123
DB_HOST=localhost
DB_PORT=5432

EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password
DEFAULT_FROM_EMAIL=noreply@perpustakaan.com
ADMIN_EMAIL=admin@perpustakaan.com

Generate Secret Key
````bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
Copy output dan paste ke .env di bagian SECRET_KEY.

## Buat Dummy Data
````bash
python manage.py create_dummy_data

## Buat Superuser
````bash
python manage.py createsuperuser

## Install & Start Redis
````bash
# Ubuntu/Debian
sudo apt install redis-server -y
sudo systemctl start redis-server
sudo systemctl enable redis-server

## Verify
redis-cli ping  # Output: PONG

Cara Menjalankan Development Mode
Buka 3 terminal:

## Terminal 1: Celery Worker
````bash
celery -A library_system worker --loglevel=info
Terminal 2: Celery Beat

````bash
celery -A library_system beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
Terminal 3: Django Server

````bash
python manage.py runserver
Akses: http://127.0.0.1:8000

## 👤 Default Login
Librarian:

Username: librarian
Password: librarian123
Admin:

Username: admin
Password: admin123
📧 Konfigurasi Email
Gmail App Password
Buka: https://myaccount.google.com/apppasswords
Login dengan akun Gmail
Pilih "Mail" dan "Other (Custom name)"
Generate password (16 karakter)
Copy password dan paste ke .env di EMAIL_HOST_PASSWORD



## 👨‍💻 Author
Hamza Harifianto

## 🤝 Contributing
Pull requests are welcome!

## 📞 Contact
Email: hamzaharifianto88@gmail.com

### selesai
# Thanks 

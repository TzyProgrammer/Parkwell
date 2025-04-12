# 🅿️ Parkwell – Smart Parking System with Django

Parkwell adalah proyek berbasis Django yang dikembangkan untuk membangun sistem monitoring dan manajemen parkir berbasis web. Proyek ini dirancang untuk membantu pengguna menemukan slot parkir kosong secara efisien dengan integrasi IoT di masa mendatang.

## 🚀 Teknologi yang Digunakan
- Python 3.13.2
- Django
- SQLite (default untuk development)
- Virtual Environment (`.venv`)
- Git & GitHub

---

## 🔧 Cara Clone & Setup Project Ini

Ikuti langkah-langkah berikut untuk mulai bekerja di lokal:

```bash
# 1. Clone repository
git clone https://github.com/TzyProgrammer/Parkwell.git
cd Parkwell

# 2. Buat virtual environment
python -m venv .venv

# 3. Aktifkan virtual environment
.venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Jalankan migrasi database
python manage.py migrate

# 6. Jalankan development server
python manage.py runserver
```

<b>*Note<b>  

Semua perubahan dilakukan melalui branch develop.  

Gunakan branch test jika ingin melakukan percobaan fitur atau testing tertentu.

Setelah fitur stabil, merge ke develop → kemudian akan masuk ke main jika sudah production-ready.

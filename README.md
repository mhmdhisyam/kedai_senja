# Kedai Senja — CRUD Menu Cafe (Django + SQLite)

Dasbor admin untuk mengelola menu dan kategori sebuah kedai kopi.

## Fitur
- **Kasir**: pilih menu dengan satu ketukan, keranjang, pembayaran Tunai/QRIS/Kartu, hitung kembalian, stok berkurang otomatis
- **Pesanan**: riwayat per tanggal, ringkasan pendapatan harian, struk yang bisa dicetak, pembatalan (stok dikembalikan)
- **Login**: semua halaman dasbor wajib masuk (`/masuk/`); keluar lewat tombol di header
- CRUD **Menu** (nama, kategori, harga, stok, deskripsi, foto) dan **Kategori**
- Pencarian, filter kategori/status, dan paginasi
- Switch **Dijual/Habis** via AJAX tanpa reload
- Dialog konfirmasi hapus, notifikasi toast, pratinjau foto & harga
- Kategori yang masih berisi menu dilindungi dari penghapusan (`PROTECT`)
- Responsif (tabel jadi kartu di HP) dan mendukung dark mode

## Menjalankan
```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python manage.py makemigrations menu   # jalankan lagi jika ada perubahan model
python manage.py migrate
python manage.py seed_menu          # opsional: data contoh
python manage.py createsuperuser    # WAJIB: akun ini dipakai untuk masuk ke dasbor
python manage.py runserver
```
Buka http://127.0.0.1:8000/

## Struktur
```
config/            pengaturan proyek (settings, urls)
menu/models.py     Category, MenuItem
menu/forms.py      validasi form (ukuran foto, nama unik per kategori)
menu/views.py      class-based views, kasir (PosView), pesanan, endpoint toggle AJAX
menu/templates/    base, daftar, form
menu/static/       css/style.css, js/app.js
```

## Langkah lanjutan sebelum produksi
- Set `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=0`, `DJANGO_ALLOWED_HOSTS`.
- Sajikan `media/` lewat web server (Nginx) dan jalankan `collectstatic`.

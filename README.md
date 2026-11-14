# 📝 Python Local Web Quiz Server (Wi-Fi Router Edition)

Aplikasi kuis berbasis web ringan yang berjalan di atas server Python (`ThreadingHTTPServer`). Dirancang khusus untuk digunakan secara lokal dalam satu jaringan Wi-Fi router atau *Hotspot* (mendukung penuh penggunaan langsung dari iPhone menggunakan aplikasi terminal seperti **a-Shell** atau laptop), lengkap dengan sistem pencatatan rekap nilai otomatis ke dalam format Markdown (`.md`).

---

## 🚀 Fitur Utama
- **Dynamic Markdown Reader:** Soal kuis otomatis dibaca dan di-*generate* langsung dari file-file `.md` di dalam folder `materi/`.
- **Sistem Login Akun Siswa:** Dilengkapi autentikasi username & password (`AKUN_SISWA`) yang unik untuk setiap pengguna.
- **Multi-Mode Pengerjaan:** 
  - **Pilihan Ganda (ABCD):** Mengacak opsi jawaban secara dinamis dari bank soal.
  - **Mode Kejujuran (B/S):** Pertanyaan uji pemahaman dengan opsi Benar atau Salah.
  - **Esai (Isian Singkat):** Pertanyaan isian teks singkat dengan pencocokan jawaban presisi.
- **Auto-Save & Restore:** Menyimpan progres jawaban peserta di `localStorage` browser secara otomatis untuk mencegah data hilang jika halaman tertutup atau tertutup tidak sengaja.
- **Stopwatch (Waktu Maju):** Melacak durasi pengerjaan siswa secara *real-time* dari `00:00` dan merekam total waktu pengerjaan.
- **Auto-Logging Rekap Nilai:** Otomatis mencetak laporan hasil ujian ke dalam file Markdown (`.md`) di dalam folder `nilai/` setiap kali kuis diselesaikan, lengkap dengan durasi dan skor akhir.

---

## 📂 Struktur Folder Proyek
Pastikan direktori proyek Anda tersusun rapi seperti berikut:
```text
project-kuis/
│
├── server.py             # Script utama server Python (ThreadingHTTPServer)
├── index.html            # Template antarmuka web (UI)
├── materi/               # Folder tempat menyimpan file soal (.md)
│   ├── 01_Matematika.md
│   └── 02_Bahasa_Inggris.md
└── nilai/                # Folder penyimpanan rekap nilai siswa (.md - otomatis terbuat)

## 📚 Referensi Penyusunan Materi

Seluruh kosakata, tata bahasa, dan daftar Kanji dalam modul ini dikurasi secara mandiri berdasarkan standar kurikulum ujian **JLPT (The Japan Foundation & Japan Educational Exchanges and Services / JEES)** dengan mengacu pada pola pengajaran buku teks standar internasional berikut:

* **Minna no Nihongo I & II** *(Level N5 – N4)*
  * **Penyusun:** 3A Corporation (*3A Network*)
  * **Penerbit:** 3A Corporation, Tokyo
* **Genki: An Integrated Course in Elementary Japanese I & II** *(Level N5 – N4)*
  * **Pengarang:** Eri Banno, Yoko Ikeda, Yutaka Ohno, Chikako Shinagawa, dan Kyoko Tokashiki
  * **Penerbit:** The Japan Times Publishing
* **Nihongo Sou Matome (Seri N3, N2, N1)** *(Level Menengah – Mahir)*
  * **Pengarang:** Hitoko Sasaki dan Noriko Matsumoto
  * **Penerbit:** ASK Publishing
* **Shin Kanzen Master (Seri N3, N2, N1)** *(Level Menengah – Mahir)*
  * **Pengarang:** Chieko Kano, Makiko Tomomatsu, Jun Miyamoto, Masako Wakuri, dkk.
  * **Penerbit:** 3A Corporation

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from http.cookies import SimpleCookie
from urllib.parse import parse_qs
from datetime import datetime
import uuid
import html
import socket
import os
import random

SESSIONS = {}
QUIZ_SESSIONS = {}
FOLDER_MATERI = "materi"
FOLDER_NILAI = "nilai"  # Folder penyimpanan rekap nilai otomatis

# Daftar Akun Siswa & Password Unik Masing-masing
AKUN_SISWA = {
    "budi": "budi123",
    "ani": "ani456",
    "eko": "eko789",
    "siti": "siti321",
    "guru": "admin123"  # Akun untuk pengajar/admin
}

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

def baca_semua_file_markdown():
    if not os.path.exists(FOLDER_MATERI):
        os.makedirs(FOLDER_MATERI)

    file_md = sorted([f for f in os.listdir(FOLDER_MATERI) if f.endswith(".md")])
    daftar = []
    for indeks, nama_file in enumerate(file_md, start=1):
        nama_tanpa_ekstensi = os.path.splitext(nama_file)[0]
        judul = nama_tanpa_ekstensi.replace("_", " ")
        path_lengkap = os.path.join(FOLDER_MATERI, nama_file)
        daftar.append((str(indeks), judul, path_lengkap))
    return daftar

def parse_soal_markdown(path_file):
    with open(path_file, "r", encoding="utf-8") as f:
        baris_list = f.readlines()

    soal_mentah = []
    q_sekarang = None
    a_sekarang = None

    for baris in baris_list:
        teks = baris.strip()
        if teks.startswith("Q:"):
            if q_sekarang and a_sekarang:
                soal_mentah.append((q_sekarang, a_sekarang))
            q_sekarang = teks[2:].strip()
            a_sekarang = None
        elif teks.startswith("A:"):
            a_sekarang = teks[2:].strip()

    if q_sekarang and a_sekarang:
        soal_mentah.append((q_sekarang, a_sekarang))

    return soal_mentah[:20]

def buat_paket_pg(soal_mentah):
    semua_jawaban = list({a for _, a in soal_mentah})
    paket_kuis = []
    huruf_opsi = ["A", "B", "C", "D", "E"]

    for idx, (pertanyaan, jawaban_benar) in enumerate(soal_mentah, start=1):
        pengecoh_kandidat = [j for j in semua_jawaban if j != jawaban_benar]
        jumlah_pengecoh = min(4, len(pengecoh_kandidat))
        pengecoh = random.sample(pengecoh_kandidat, jumlah_pengecoh)

        while len(pengecoh) < 4:
            pengecoh.append(f"Opsi cadangan {len(pengecoh) + 1}")

        pilihan_teks = [jawaban_benar] + pengecoh
        random.shuffle(pilihan_teks)

        opsi_dict = {}
        kunci_huruf = "A"
        for i, teks_opsi in enumerate(pilihan_teks):
            huruf = huruf_opsi[i]
            opsi_dict[huruf] = teks_opsi
            if teks_opsi == jawaban_benar:
                kunci_huruf = huruf

        paket_kuis.append({
            "nomor": idx,
            "pertanyaan": pertanyaan,
            "opsi": opsi_dict,
            "kunci": kunci_huruf,
            "tipe": "pg"
        })
    return paket_kuis

def buat_paket_kejujuran(soal_mentah):
    semua_jawaban = [a for _, a in soal_mentah]
    paket_kuis = []

    for idx, (pertanyaan, jawaban_benar) in enumerate(soal_mentah, start=1):
        is_true = random.choice([True, False])
        if is_true:
            tampil_jawaban = jawaban_benar
            kunci = "Benar"
        else:
            pengecoh_kandidat = [j for j in semua_jawaban if j != jawaban_benar]
            if pengecoh_kandidat:
                tampil_jawaban = random.choice(pengecoh_kandidat)
            else:
                tampil_jawaban = "Arti lain"
            kunci = "Salah"

        paket_kuis.append({
            "nomor": idx,
            "pertanyaan": f"Apakah arti dari <strong>{html.escape(pertanyaan)}</strong> adalah <strong>{html.escape(tampil_jawaban)}</strong>?",
            "kunci": kunci,
            "tipe": "kejujuran"
        })
    return paket_kuis

def buat_paket_esai(soal_mentah):
    paket_kuis = []
    for idx, (pertanyaan, jawaban_benar) in enumerate(soal_mentah, start=1):
        paket_kuis.append({
            "nomor": idx,
            "pertanyaan": f"Ketik arti/jawaban untuk: <strong>{html.escape(pertanyaan)}</strong>",
            "kunci": jawaban_benar,
            "tipe": "esai"
        })
    return paket_kuis

class NamaSessionHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def get_session_id(self):
        if "Cookie" in self.headers:
            cookie = SimpleCookie(self.headers["Cookie"])
            if "session_id" in cookie:
                return cookie["session_id"].value
        return None

    def get_current_name(self):
        sid = self.get_session_id()
        return SESSIONS.get(sid) if sid else None

    def render_halaman_utama(self, nama, info_html="", form_kuis_html="", sid=None):
        nama_aman = html.escape(nama)

        if os.path.exists("index.html"):
            with open("index.html", "r", encoding="utf-8") as f:
                template = f.read()
        else:
            return "<h3>Error: File index.html tidak ditemukan!</h3>"

        sedang_kuis = sid and (sid in QUIZ_SESSIONS)

        tombol_html = ""
        if not sedang_kuis and not form_kuis_html:
            daftar_md = baca_semua_file_markdown()
            if daftar_md:
                tombol_html += '<p>Silakan pilih bab kuis di bawah ini:</p>'
                for nomor, judul, _ in daftar_md:
                    nomor_aman = html.escape(nomor)
                    judul_aman = html.escape(judul)
                    tombol_html += (
                        f'<form method="POST" action="/pilih_bab" style="display:block; margin-bottom: 8px;">'
                        f'<input type="hidden" name="nomor" value="{nomor_aman}">'
                        f'<button type="submit" style="width: 100%; text-align: left; padding: 12px 16px; background-color: #f8f9fa; color: #333; border: 1px solid #ddd; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer;">'
                        f'📁 <strong>{nomor_aman}.</strong> {judul_aman}'
                        f'</button>'
                        f'</form>\n'
                    )
            else:
                tombol_html = f"<p>Belum ada file .md di dalam folder '{FOLDER_MATERI}'.</p>"
        elif sedang_kuis:
            tombol_html = (
                '<div style="margin-top: 25px; text-align: center;">'
                '<a href="/reset" style="text-decoration: none; background-color: #6c757d; color: white; padding: 12px 24px; border-radius: 8px; font-size: 16px; font-weight: bold; display: inline-block;">&larr; Kembali ke Daftar Bab</a>'
                '</div>'
            )
        else:
            tombol_html = ""

        halaman = template.replace("{{NAMA}}", nama_aman)
        halaman = halaman.replace("{{INFO_PILIHAN}}", info_html)
        halaman = halaman.replace("{{FORM_KUIS}}", form_kuis_html)
        halaman = halaman.replace("{{DAFTAR_TOMBOL}}", tombol_html)
        return halaman

    def render_menu_metode(self, nomor_bab, judul_bab):
        judul_aman = html.escape(judul_bab)
        menu_html = f'<div class="kuis-box">'
        menu_html += f'<div style="margin-bottom: 15px;">'
        menu_html += f'<a href="/" style="text-decoration: none; background-color: #6c757d; color: white; padding: 8px 14px; border-radius: 6px; font-size: 14px; display: inline-block;">&larr; Ganti Bab</a>'
        menu_html += f'</div>'
        menu_html += f'<h3>Pilih Metode Kuis: {judul_aman}</h3>'
        menu_html += '<p style="color: #666; margin-bottom: 20px;">Silakan pilih cara belajar yang Anda inginkan di bawah ini:</p>'
        
        menu_html += f'<form method="POST" action="/mulai_kuis" style="margin-bottom: 10px;">'
        menu_html += f'<input type="hidden" name="nomor" value="{nomor_bab}">'
        menu_html += f'<input type="hidden" name="metode" value="pg">'
        menu_html += f'<button type="submit" style="width: 100%; padding: 12px; background-color: #007bff; color: white; border: none; border-radius: 6px; font-size: 16px; font-weight: bold; cursor: pointer;">Pilihan Ganda (ABCD)</button>'
        menu_html += f'</form>'

        menu_html += f'<form method="POST" action="/mulai_kuis" style="margin-bottom: 10px;">'
        menu_html += f'<input type="hidden" name="nomor" value="{nomor_bab}">'
        menu_html += f'<input type="hidden" name="metode" value="kejujuran">'
        menu_html += f'<button type="submit" style="width: 100%; padding: 12px; background-color: #28a745; color: white; border: none; border-radius: 6px; font-size: 16px; font-weight: bold; cursor: pointer;">Mode Kejujuran (Benar / Salah)</button>'
        menu_html += f'</form>'

        menu_html += f'<form method="POST" action="/mulai_kuis">'
        menu_html += f'<input type="hidden" name="nomor" value="{nomor_bab}">'
        menu_html += f'<input type="hidden" name="metode" value="esai">'
        menu_html += f'<button type="submit" style="width: 100%; padding: 12px; background-color: #ffc107; color: #333; border: none; border-radius: 6px; font-size: 16px; font-weight: bold; cursor: pointer;">Esai (Isian Singkat)</button>'
        menu_html += f'</form>'

        menu_html += '</div>'
        return menu_html

    def buat_html_form_kuis(self, judul_bab, paket_kuis):
        judul_aman = html.escape(judul_bab)
        blok_soal = f'<div class="kuis-box">'
        blok_soal += f'<div style="margin-bottom: 15px;">'
        blok_soal += f'<a href="/reset" style="text-decoration: none; background-color: #6c757d; color: white; padding: 8px 14px; border-radius: 6px; font-size: 14px; display: inline-block;">&larr; Kembali ke Daftar Bab</a>'
        blok_soal += f'</div>'
        
        # KOTAK STOPWATCH (WAKTU MAJU)
        blok_soal += f'''
        <div style="background: #e2f0d9; border: 1px solid #c8e6b9; padding: 12px; border-radius: 6px; margin-bottom: 20px; font-weight: bold; text-align: center; color: #274e13; font-size: 18px;">
            ⏱️ Waktu Pengerjaan: <span id="stopwatch">00:00</span>
        </div>
        '''

        blok_soal += f'<h3>Kuis: {judul_aman} ({len(paket_kuis)} Soal)</h3>'
        blok_soal += '<form method="POST" action="/jawab" id="form-kuis">'
        
        # Hidden input untuk mengirim durasi waktu ke server
        blok_soal += '<input type="hidden" name="durasi_pengerjaan" id="durasi_pengerjaan" value="00:00">'

        for item in paket_kuis:
            no = item["nomor"]
            tanya = item["pertanyaan"]
            tipe = item["tipe"]

            blok_soal += f'<div class="soal-item"><p><strong>{no}. {tanya}</strong></p>'

            if tipe == "pg":
                for huruf, teks_opsi in item["opsi"].items():
                    opsi_aman = html.escape(teks_opsi)
                    blok_soal += (
                        f'<label class="opsi-label">'
                        f'<input type="radio" name="q_{no}" value="{huruf}" required> '
                        f'<strong>{huruf}.</strong> {opsi_aman}'
                        f'</label>'
                    )
            elif tipe == "kejujuran":
                blok_soal += (
                    f'<label class="opsi-label" style="display:inline-block; margin-right:15px;"><input type="radio" name="q_{no}" value="Benar" required> <strong>Benar</strong></label>'
                    f'<label class="opsi-label" style="display:inline-block;"><input type="radio" name="q_{no}" value="Salah" required> <strong>Salah</strong></label>'
                )
            elif tipe == "esai":
                blok_soal += (
                    f'<input type="text" name="q_{no}" placeholder="Ketik jawaban di sini..." required '
                    f'style="width: 100%; padding: 10px; font-size: 16px; border: 1px solid #ccc; border-radius: 6px; box-sizing: border-box; margin-top: 5px;">'
                )

            blok_soal += '</div>'

        blok_soal += '<button type="submit" class="btn-submit">Kumpulkan Jawaban</button></form>'
        
        # SCRIPT JAVASCRIPT (STOPWATCH, AUTO-SAVE & RESTORE)
        blok_soal += '''
        <script>
        document.addEventListener("DOMContentLoaded", function() {
            const form = document.getElementById("form-kuis");
            const storageKey = "quiz_progress_" + window.location.pathname;
            
            // 1. Logika Stopwatch (Waktu Maju)
            let secondsElapsed = 0;
            const stopwatchEl = document.getElementById("stopwatch");
            const durasiInput = document.getElementById("durasi_pengerjaan");

            const timerInterval = setInterval(function() {
                secondsElapsed++;
                let minutes = Math.floor(secondsElapsed / 60);
                let seconds = secondsElapsed % 60;
                
                minutes = minutes < 10 ? "0" + minutes : minutes;
                seconds = seconds < 10 ? "0" + seconds : seconds;
                
                const waktuFormatted = minutes + " menit " + seconds + " detik";
                stopwatchEl.textContent = minutes + ":" + seconds;
                durasiInput.value = waktuFormatted;
            }, 1000);

            // 2. Pulihkan jawaban tersimpan sebelumnya
            const savedData = localStorage.getItem(storageKey);
            if (savedData) {
                try {
                    const parsedData = JSON.parse(savedData);
                    for (const [name, value] of Object.entries(parsedData)) {
                        if (name === "durasi_pengerjaan") continue;
                        const field = form.elements[name];
                        if (field) {
                            if (field.type === "radio" || field.length > 1) {
                                for (let r of field) {
                                    if (r.value === value) r.checked = true;
                                }
                            } else {
                                field.value = value;
                            }
                        }
                    }
                } catch(e) { console.error(e); }
            }

            // 3. Simpan otomatis ke localStorage saat ada perubahan
            form.addEventListener("input", function() {
                const formData = new FormData(form);
                const dataObj = {};
                formData.forEach((value, key) => { dataObj[key] = value; });
                localStorage.setItem(storageKey, JSON.stringify(dataObj));
            });

            // 4. Hentikan stopwatch dan bersihkan memori saat dikumpulkan
            form.addEventListener("submit", function() {
                clearInterval(timerInterval);
                localStorage.removeItem(storageKey);
            });
        });
        </script>
        '''
        
        blok_soal += '</div>'
        return blok_soal

    def do_GET(self):
        nama = self.get_current_name()
        sid = self.get_session_id()

        if self.path == "/":
            if nama:
                self.send_response(200)
                self.send_header("Content-type", "text/html; charset=utf-8")
                self.end_headers()
                halaman = self.render_halaman_utama(nama, sid=sid)
                self.wfile.write(halaman.encode("utf-8"))
            else:
                self.send_response(302)
                self.send_header("Location", "/masuk")
                self.end_headers()

        elif self.path == "/reset":
            if sid:
                QUIZ_SESSIONS.pop(sid, None)
            self.send_response(302)
            self.send_header("Location", "/")
            self.end_headers()
            return

        elif self.path == "/masuk":
            if nama:
                self.send_response(302)
                self.send_header("Location", "/")
                self.end_headers()
                return

            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            halaman = (
                '<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1"></head>'
                '<body style="font-family: sans-serif; padding: 20px; max-width: 400px; margin: auto;">'
                '<h2>Login Kuis Siswa</h2>'
                '<form method="POST" action="/masuk">'
                '<div style="margin-bottom: 12px;">'
                '<label><strong>Nama Pengguna:</strong></label><br>'
                '<input type="text" name="nama" placeholder="Ketik nama..." required style="padding: 10px; font-size: 16px; width: 100%; box-sizing: border-box; margin-top: 4px;">'
                '</div>'
                '<div style="margin-bottom: 18px;">'
                '<label><strong>Password:</strong></label><br>'
                '<input type="password" name="password" placeholder="Masukkan password..." required style="padding: 10px; font-size: 16px; width: 100%; box-sizing: border-box; margin-top: 4px;">'
                '</div>'
                '<button type="submit" style="padding: 12px 16px; font-size: 16px; width: 100%; background-color: #007bff; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: bold;">Masuk</button>'
                '</form></body></html>'
            )
            self.wfile.write(halaman.encode("utf-8"))

        elif self.path == "/selesai":
            if sid:
                SESSIONS.pop(sid, None)
                QUIZ_SESSIONS.pop(sid, None)

            self.send_response(200)
            self.send_header("Set-Cookie", "session_id=; Max-Age=0; Path=/")
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            halaman = (
                '<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1"><title>Selesai</title></head>'
                '<body style="font-family: sans-serif; padding: 40px 20px; max-width: 400px; margin: auto; text-align: center;">'
                '<h2>Selesai</h2><p>Terima kasih, sesi kamu telah berakhir.</p></body></html>'
            )
            self.wfile.write(halaman.encode("utf-8"))

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length).decode("utf-8")
        params = parse_qs(post_data)
        sid = self.get_session_id()

        if self.path == "/masuk":
            nama_list = params.get("nama", [""])
            pass_list = params.get("password", [""])
            
            nama_input = nama_list[0].strip() if nama_list else ""
            password_user = pass_list[0].strip() if pass_list else ""

            nama_terdaftar = None
            for user in AKUN_SISWA.keys():
                if user.lower() == nama_input.lower():
                    nama_terdaftar = user
                    break

            if nama_terdaftar and AKUN_SISWA[nama_terdaftar] == password_user:
                session_id = str(uuid.uuid4())
                SESSIONS[session_id] = nama_terdaftar
                waktu = datetime.now().strftime("%H:%M:%S")
                print(f"[+] [{waktu}] Login Berhasil: {nama_terdaftar}", flush=True)

                self.send_response(302)
                self.send_header("Set-Cookie", f"session_id={session_id}; HttpOnly; Path=/")
                self.send_header("Location", "/")
                self.end_headers()
                return
            else:
                waktu = datetime.now().strftime("%H:%M:%S")
                print(f"[-] [{waktu}] Gagal Login (Nama/Password Salah): {nama_input}", flush=True)
                
                self.send_response(302)
                self.send_header("Location", "/masuk")
                self.end_headers()
                return

        elif self.path == "/pilih_bab":
            nama = self.get_current_name()
            if not nama:
                self.send_response(302)
                self.send_header("Location", "/masuk")
                self.end_headers()
                return

            nomor_list = params.get("nomor", [""])
            nomor = nomor_list[0].strip() if nomor_list else ""
            daftar_md = baca_semua_file_markdown()
            terpilih = next((item for item in daftar_md if item[0] == nomor), None)

            menu_html = ""
            if terpilih:
                _, judul_bab, _ = terpilih
                menu_html = self.render_menu_metode(nomor, judul_bab)

            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            halaman = self.render_halaman_utama(nama, "", menu_html, sid=sid)
            self.wfile.write(halaman.encode("utf-8"))

        elif self.path == "/mulai_kuis":
            nama = self.get_current_name()
            if not nama:
                self.send_response(302)
                self.send_header("Location", "/masuk")
                self.end_headers()
                return

            nomor_list = params.get("nomor", [""])
            metode_list = params.get("metode", ["pg"])
            nomor = nomor_list[0].strip() if nomor_list else ""
            metode = metode_list[0].strip() if metode_list else "pg"

            daftar_md = baca_semua_file_markdown()
            terpilih = next((item for item in daftar_md if item[0] == nomor), None)

            form_kuis_html = ""
            if terpilih:
                _, judul_bab, path_lengkap = terpilih
                soal_mentah = parse_soal_markdown(path_lengkap)

                if metode == "pg":
                    paket_kuis = buat_paket_pg(soal_mentah)
                    tipe_teks = "Pilihan Ganda"
                elif metode == "kejujuran":
                    paket_kuis = buat_paket_kejujuran(soal_mentah)
                    tipe_teks = "Mode Kejujuran (B/S)"
                else:
                    paket_kuis = buat_paket_esai(soal_mentah)
                    tipe_teks = "Esai"

                if paket_kuis:
                    QUIZ_SESSIONS[sid] = {"judul": f"{judul_bab} ({tipe_teks})", "soal": paket_kuis}
                    form_kuis_html = self.buat_html_form_kuis(judul_bab, paket_kuis)
                    waktu = datetime.now().strftime("%H:%M:%S")
                    print(f"[>] [{waktu}] {nama} mulai mengerjakan {tipe_teks}: {judul_bab}", flush=True)

            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            halaman = self.render_halaman_utama(nama, "", form_kuis_html, sid=sid)
            self.wfile.write(halaman.encode("utf-8"))

        elif self.path == "/jawab":
            nama = self.get_current_name()
            if not nama or sid not in QUIZ_SESSIONS:
                self.send_response(302)
                self.send_header("Location", "/")
                self.end_headers()
                return

            quiz_data = QUIZ_SESSIONS[sid]
            paket_kuis = quiz_data["soal"]
            judul_bab = quiz_data["judul"]
            
            # Ambil durasi waktu pengerjaan
            durasi_pengerjaan = params.get("durasi_pengerjaan", ["Tidak diketahui"])[0]

            benar = 0
            total = len(paket_kuis)

            for item in paket_kuis:
                no = item["nomor"]
                kunci = item["kunci"]
                tipe = item["tipe"]
                jawaban_user = params.get(f"q_{no}", [""])[0].strip()

                if tipe == "esai":
                    if jawaban_user.lower() == kunci.lower():
                        benar += 1
                else:
                    if jawaban_user == kunci:
                        benar += 1

            skor = int((benar / total) * 100) if total > 0 else 0
            
            waktu = datetime.now().strftime("%H:%M:%S")
            tanggal_sekarang = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[*] [{waktu}] KUIS SELESAI -> Nama: {nama} | Bab: {judul_bab} | Skor: {skor} | Durasi: {durasi_pengerjaan}", flush=True)

            # --- OTOMATIS SIMPAN REKAP NILAI KE FOLDER .MD ---
            if not os.path.exists(FOLDER_NILAI):
                os.makedirs(FOLDER_NILAI)
            
            waktu_file = datetime.now().strftime("%Y%m%d_%H%M%S")
            nama_file_nilai = f"{nama.lower()}_{waktu_file}.md"
            path_file_nilai = os.path.join(FOLDER_NILAI, nama_file_nilai)

            isi_rekap_md = f"""# Rekap Nilai Kuis Siswa
- **Nama Siswa:** {nama}
- **Materi / Bab:** {judul_bab}
- **Waktu Kumpul:** {tanggal_sekarang}
- **Durasi Pengerjaan:** {durasi_pengerjaan}
- **Skor Akhir:** {skor}
- **Jawaban Benar:** {benar} dari {total} soal
"""
            with open(path_file_nilai, "w", encoding="utf-8") as f_nilai:
                f_nilai.write(isi_rekap_md)
            # -----------------------------------------------

            info_html = f'<div class="alert">Hasil Kuis <strong>{html.escape(judul_bab)}</strong>:<br>Waktu Pengerjaan: {html.escape(durasi_pengerjaan)}<br>Benar: {benar} dari {total} soal.<br>Skor Akhir: <strong>{skor}</strong></div>'

            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            halaman = self.render_halaman_utama(nama, info_html, "", sid=sid)
            self.wfile.write(halaman.encode("utf-8"))

if __name__ == "__main__":
    PORT = 8000
    local_ip = get_local_ip()
    server = ThreadingHTTPServer(("0.0.0.0", PORT), NamaSessionHandler)
    print("==================================================", flush=True)
    print(f"Server Kuis Berhasil Menyala!", flush=True)
    print(f"Buka di HP Anda sendiri : http://127.0.0.1:{PORT}", flush=True)
    print(f"Buka untuk Teman (WiFi)  : http://{local_ip}:{PORT}", flush=True)
    print("==================================================", flush=True)
    server.serve_forever()
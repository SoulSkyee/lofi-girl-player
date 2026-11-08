# Lofi Girl Player

Pemutar mini untuk stream lofi radio (Lofi Girl) **tanpa membuka YouTube**: audio saja lewat mpv, jadi jauh lebih hemat RAM daripada satu tab browser.

*Tiny Windows player for the Lofi Girl live stream, audio only through mpv, no browser tab needed.*

> Aplikasi tidak resmi dan tidak berafiliasi dengan Lofi Girl / YouTube. Stream-nya diputar langsung dari YouTube lewat yt-dlp.

## Fitur

- Pause, Stop/Play, dan slider volume
- Volume terakhir diingat
- Tombol **X** hanya menutup jendela, **musik tetap jalan di background**. Buka app lagi untuk menyambung
- Tombol **Tutup & matikan** menghentikan semuanya
- RAM: sekitar 80-90 MB saat jendela terbuka, sekitar 48 MB (hanya mpv) saat jendela ditutup

## Cara pakai

1. Pasang **mpv** dan **yt-dlp** (sekali saja):
   ```powershell
   winget install mpv yt-dlp
   ```
   atau lewat Chocolatey (terminal admin): `choco install mpv yt-dlp -y`
2. Unduh `LofiGirlPlayer.exe` dari halaman [Releases](../../releases/latest) lalu jalankan.

Windows SmartScreen mungkin memperingatkan karena `.exe` belum ditandatangani. Pilih **More info → Run anyway**, atau jalankan dari kode sumber (di bawah) kalau kamu lebih nyaman begitu.

## Jalankan dari kode sumber

Butuh Python 3.10+ (tkinter sudah termasuk di installer resmi Python).

```powershell
python lofi_gui.py
```

## Build `.exe` sendiri

```powershell
pip install pyinstaller pillow
python tools/make_icon.py          # opsional, buat ulang icon.ico
python -m PyInstaller --noconfirm --onefile --windowed --name LofiGirlPlayer --icon icon.ico --add-data "icon.ico;." lofi_gui.py
```

Hasilnya ada di `dist/LofiGirlPlayer.exe`.

## Cara kerja

App menjalankan `mpv --no-video` dengan `--input-ipc-server` (named pipe `\\.\pipe\lofi-mpv`), lalu mengirim perintah JSON (volume, pause, quit) lewat pipe itu. Karena mpv berdiri sendiri, jendela bisa ditutup tanpa menghentikan musik, dan app berikutnya tinggal menyambung ke pipe yang sama. Pengaturan disimpan di `%APPDATA%\LofiGirlPlayer\settings.json`.

## Lisensi

[MIT](LICENSE) untuk kode di repo ini. mpv dan yt-dlp punya lisensinya masing-masing.

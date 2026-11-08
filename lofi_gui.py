"""Lofi Girl Player: GUI mini untuk memutar stream lofi sebagai audio saja (mpv + yt-dlp).

Menutup jendela (X) hanya menutup GUI; musik tetap jalan di background.
Membuka app lagi menyambung ke mpv yang sudah jalan. "Tutup & matikan" menghentikan semuanya.
Aplikasi tidak resmi dan tidak berafiliasi dengan Lofi Girl.
"""
import json
import os
import shutil
import subprocess
import sys
import time
import tkinter as tk
import winreg
from tkinter import ttk

URL = "https://www.youtube.com/watch?v=rFZHOHl-L8A"
PIPE = r"\\.\pipe\lofi-mpv"

# Saat dibungkus PyInstaller, resource ada di _MEIPASS; pengaturan disimpan di %APPDATA% (bisa ditulis).
RES = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "LofiGirlPlayer")
SETTINGS = os.path.join(DATA, "settings.json")

MISSING_HELP = (
    "mpv / yt-dlp belum terpasang.\n\n"
    "Pasang lewat salah satu:\n"
    "  winget install mpv yt-dlp\n"
    "  choco install mpv yt-dlp   (terminal admin)\n\n"
    "Lalu buka app ini lagi."
)


def load_volume(default=60):
    try:
        with open(SETTINGS, encoding="utf-8") as f:
            return max(0, min(100, int(json.load(f)["volume"])))
    except (OSError, ValueError, KeyError, TypeError):
        return default


def save_volume(v):
    try:
        os.makedirs(DATA, exist_ok=True)
        with open(SETTINGS, "w", encoding="utf-8") as f:
            json.dump({"volume": int(v)}, f)
    except OSError:
        pass


def refresh_path():
    """Baca PATH terbaru dari registry (proses dari Explorer bisa mewarisi PATH lama)."""
    parts = []
    for hive, sub in ((winreg.HKEY_LOCAL_MACHINE,
                       r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"),
                      (winreg.HKEY_CURRENT_USER, "Environment")):
        try:
            with winreg.OpenKey(hive, sub) as k:
                parts.append(os.path.expandvars(winreg.QueryValueEx(k, "Path")[0]))
        except OSError:
            pass
    parts.append(os.environ.get("PATH", ""))
    os.environ["PATH"] = ";".join(p for p in parts if p)


def mpv_cmd(*cmd):
    """Kirim satu perintah ke mpv lewat pipe. Return `data` balasan, atau None kalau mpv tidak ada."""
    try:
        with open(PIPE, "r+b", buffering=0) as p:
            p.write((json.dumps({"command": list(cmd), "request_id": 7}) + "\n").encode())
            for _ in range(50):  # lewati event yang menyelip sampai balasan kita datang
                line = p.readline()
                if not line:
                    return None
                try:
                    msg = json.loads(line)
                except ValueError:
                    continue
                if msg.get("request_id") == 7:
                    return msg.get("data", True) if msg.get("error") == "success" else None
    except OSError:
        return None
    return None


def mpv_alive():
    return mpv_cmd("get_property", "pid") is not None


class Lofi:
    def __init__(self, root):
        self.root = root
        self.proc = None       # hanya terisi kalau kita yang menjalankan mpv
        self.paused = False
        self.loading = False
        self._save_job = None

        root.title("Lofi Girl Player")
        try:
            root.iconbitmap(os.path.join(RES, "icon.ico"))
        except tk.TclError:
            pass
        root.geometry("260x165")
        root.resizable(False, False)
        root.attributes("-topmost", True)
        root.protocol("WM_DELETE_WINDOW", self.close_keep_playing)

        self.status = tk.StringVar(value="Memulai...")
        ttk.Label(root, textvariable=self.status).pack(pady=(10, 4))

        row = ttk.Frame(root)
        row.pack(pady=4)
        self.btn_pause = ttk.Button(row, text="Pause", width=9, command=self.toggle_pause)
        self.btn_pause.pack(side="left", padx=4)
        self.btn_stop = ttk.Button(row, text="Stop", width=9, command=self.toggle_stop)
        self.btn_stop.pack(side="left", padx=4)

        vol = ttk.Frame(root)
        vol.pack(fill="x", padx=14, pady=(8, 0))
        ttk.Label(vol, text="Vol").pack(side="left")
        self.vol_label = ttk.Label(vol, text="", width=4, anchor="e")
        self.vol_label.pack(side="right")
        self.volume = tk.IntVar(value=load_volume())
        self.vol_label.config(text=str(self.volume.get()))
        ttk.Scale(vol, from_=0, to=100, variable=self.volume,
                  command=self.on_volume).pack(side="left", fill="x", expand=True, padx=6)

        ttk.Button(root, text="Tutup & matikan", command=self.close_and_stop).pack(pady=(10, 0))

        if mpv_alive():
            self.attach()
        else:
            self.start()
        self.poll()

    # --- mpv ---
    def attach(self):
        """Sambung ke mpv yang sudah jalan: ikuti volume dan status pause-nya."""
        vol = mpv_cmd("get_property", "volume")
        if isinstance(vol, (int, float)):
            self.volume.set(round(vol))
            self.vol_label.config(text=str(round(vol)))
        self.paused = bool(mpv_cmd("get_property", "pause"))
        self.loading = False
        self.btn_pause.config(text="Lanjut" if self.paused else "Pause")
        self.btn_stop.config(text="Stop")
        self.status.set("Dijeda" if self.paused else "Memutar")

    def start(self):
        mpv = shutil.which("mpv")
        if not mpv or not shutil.which("yt-dlp"):
            self.status.set("mpv / yt-dlp belum terpasang")
            self.btn_stop.config(text="Play")
            from tkinter import messagebox
            messagebox.showinfo("Lofi Girl Player", MISSING_HELP, parent=self.root)
            return
        self.proc = subprocess.Popen(
            [mpv, "--no-video", "--force-window=no", f"--volume={self.volume.get()}",
             f"--input-ipc-server={PIPE}", URL],
            creationflags=subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP,
        )
        self.paused = False
        self.loading = True
        self.btn_pause.config(text="Pause")
        self.btn_stop.config(text="Stop")
        self.status.set("Memuat stream...")

    def stop_mpv(self):
        mpv_cmd("quit")
        if self.proc is not None:
            try:
                self.proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.proc.kill()
            self.proc = None
        for _ in range(30):  # tunggu pipe benar-benar lepas (mpv yang disambung, bukan kita yang jalankan)
            if not mpv_alive():
                break
            time.sleep(0.1)

    # --- UI actions ---
    def toggle_pause(self):
        if not mpv_alive():
            return
        self.paused = not self.paused
        mpv_cmd("set_property", "pause", self.paused)
        self.btn_pause.config(text="Lanjut" if self.paused else "Pause")
        self.status.set("Dijeda" if self.paused else "Memutar")

    def toggle_stop(self):
        if mpv_alive() or self.loading:
            self.stop_mpv()
            self.loading = False
            self.btn_stop.config(text="Play")
            self.status.set("Berhenti")
        else:
            self.start()

    def on_volume(self, _=None):
        v = int(self.volume.get())
        self.vol_label.config(text=str(v))
        if self._save_job:
            self.root.after_cancel(self._save_job)
        self._save_job = self.root.after(500, lambda: save_volume(v))  # simpan setelah slider berhenti
        mpv_cmd("set_property", "volume", v)

    def poll(self):
        alive = mpv_alive()
        if alive and self.loading:
            self.loading = False
            self.status.set("Memutar")
        elif not alive and not self.loading and self.btn_stop.cget("text") == "Stop":
            # mpv mati dari luar (mis. proses dimatikan manual)
            self.btn_stop.config(text="Play")
            self.status.set("Berhenti")
        elif self.loading and self.proc is not None and self.proc.poll() is not None:
            self.loading = False
            self.proc = None
            self.btn_stop.config(text="Play")
            self.status.set("Gagal memuat stream")
        self.root.after(1500, self.poll)

    def close_keep_playing(self):
        save_volume(self.volume.get())
        self.root.destroy()

    def close_and_stop(self):
        save_volume(self.volume.get())
        self.stop_mpv()
        self.root.destroy()


if __name__ == "__main__":
    refresh_path()
    root = tk.Tk()
    Lofi(root)
    root.mainloop()

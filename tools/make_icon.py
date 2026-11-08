"""Buat icon.ico generik (headphone sederhana). Jalankan: python tools/make_icon.py"""
import os

from PIL import Image, ImageDraw

S = 1024  # gambar besar dulu, lalu diperkecil supaya tepinya halus
im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
d = ImageDraw.Draw(im)

d.ellipse((24, 24, S - 24, S - 24), fill=(38, 43, 84, 255))                      # latar bulat
d.arc((232, 190, S - 232, 800), 180, 360, fill=(240, 228, 208, 255), width=64)  # headband
for x in (190, S - 190 - 170):                                                    # ear cup
    d.rounded_rectangle((x, 520, x + 170, 800), radius=70, fill=(232, 120, 104, 255))
d.ellipse((470, 770, 554, 854), fill=(240, 228, 208, 255))                        # titik "nada"

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "icon.ico")
im.save(out, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
im.resize((256, 256), Image.LANCZOS).save(os.path.join(os.path.dirname(out), "icon_preview.png"))
print("ok:", os.path.abspath(out))

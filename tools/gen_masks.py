"""Genera 6 máscaras de papel rasgado reutilizables con ruido procedural."""
import random
from pathlib import Path
from PIL import Image, ImageFilter

random.seed(20261105)
MASKS = Path("assets/masks"); MASKS.mkdir(parents=True, exist_ok=True)

for idx in range(6):
    w, h = 512, 768
    img = Image.new("L", (w, h), 255)
    draw_pts = [[0,0],[w,0],[w,h],[0,h]]
    # agregar puntos de borde con ruido Perlin-like (senos superpuestos + jitter)
    for side, (x0, y0, x1, y1) in enumerate([(0,0,w,0),(w,0,w,h),(w,h,0,h),(0,h,0,0)]):
        n = 32
        dx = (x1 - x0) / n; dy = (y1 - y0) / n
        pts = [(x0 + i*dx, y0 + i*dy) for i in range(n+1)]
        rng = random.Random(20261105 + idx * 101)
        noisy = []
        for i, (px, py) in enumerate(pts):
            offset = int(30 * (rng.random() - 0.5))
            if side == 0 or side == 2:
                noisy.append((px, py + offset))
            else:
                noisy.append((px + offset, py))
        if idx > 2:
            # más forma de medallón / círculo roto
            center_x, center_y = w // 2, h // 2
            radius = min(w, h) // 3
            circ = []
            for i in range(48):
                t = 2 * 3.14159265 * i / 47
                r = radius + int(25 * (rng.random() - 0.5))
                circ.append((center_x + int(r * __import__("math").cos(t)),
                             center_y + int(r * __import__("math").sin(t))))
            Image.fromarray(__import__('numpy').array(Image.new("L", (w,h), 0)))  # dummy
            poly = Image.new("L", (w,h), 0)
            from PIL import ImageDraw
            ImageDraw.Draw(poly).polygon(circ, fill=255)
            # blur bordes
            poly = poly.filter(ImageFilter.GaussianBlur(6))
            img = Image.composite(poly, img, Image.new("L", (w,h),255))
            break
    img = img.filter(ImageFilter.GaussianBlur(4 + idx % 3))
    # trasero de corte estilo papelería artesanal
    img.save(MASKS / f"paper-{idx+1}.png")
    print("creada", MASKS / f"paper-{idx+1}.png")

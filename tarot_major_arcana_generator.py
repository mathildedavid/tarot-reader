# tarot_major_arcana_generator.py
# Generates 22 PNG images for the Major Arcana with a modern, glassy look.
# Requires: Pillow (pip install pillow)

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os
import math
import random

# ---------- Config ----------
W, H = 1024, 1536                 # Card size (3:2 aspect, print-friendly)
RADIUS = 64                       # Corner radius
DPI = 300                         # Metadata only; PNGs are resolution independent
OUT_DIR = "major_arcana_cards"
TITLE_FONT_SIZE = 92
NUM_FONT_SIZE = 72
ICON_SCALE = 0.26                 # relative to min(W, H)
SEED = 42                         # for reproducible sparkles/noise; set to None for fresh runs

# Fallback fonts (Pillow default). If you have a TTF, set FONT_PATH_* to that file for nicer typography.
FONT_PATH_TITLE = None
FONT_PATH_NUM = None

# Palette: per-card gradient (top, bottom) — tweak freely
PALETTES = [
    ("#12131a", "#2f3356"),  # 0 The Fool
    ("#1d1028", "#5b2a5e"),  # 1 The Magician
    ("#0f1b1e", "#1f5a66"),  # 2 The High Priestess
    ("#24120f", "#7a3e2a"),  # 3 The Empress
    ("#0f2416", "#2f7a4a"),  # 4 The Emperor
    ("#15131e", "#3f2c7a"),  # 5 The Hierophant
    ("#101820", "#0d5167"),  # 6 The Lovers
    ("#1c1720", "#6a3b8f"),  # 7 The Chariot
    ("#131313", "#494949"),  # 8 Strength
    ("#10141b", "#1a3b5c"),  # 9 The Hermit
    ("#1a100f", "#8c3b2f"),  # 10 Wheel of Fortune
    ("#0f1920", "#33626e"),  # 11 Justice
    ("#0e1320", "#253a86"),  # 12 The Hanged Man
    ("#201012", "#7a2f4a"),  # 13 Death
    ("#132017", "#2f7a60"),  # 14 Temperance
    ("#1b0f0f", "#7a2f2f"),  # 15 The Devil
    ("#11141b", "#23304a"),  # 16 The Tower
    ("#0f1812", "#1c6a3b"),  # 17 The Star
    ("#0f101a", "#2a326b"),  # 18 The Moon
    ("#1a140f", "#7a5a2a"),  # 19 The Sun
    ("#0f1518", "#2d5a7a"),  # 20 Judgement
    ("#101010", "#2f2f2f"),  # 21 The World
]

MAJORS = [
    (0,  "0",   "The Fool"),
    (1,  "I",   "The Magician"),
    (2,  "II",  "The High Priestess"),
    (3,  "III", "The Empress"),
    (4,  "IV",  "The Emperor"),
    (5,  "V",   "The Hierophant"),
    (6,  "VI",  "The Lovers"),
    (7,  "VII", "The Chariot"),
    (8,  "VIII","Strength"),
    (9,  "IX",  "The Hermit"),
    (10, "X",   "Wheel of Fortune"),
    (11, "XI",  "Justice"),
    (12, "XII", "The Hanged Man"),
    (13, "XIII","Death"),
    (14, "XIV", "Temperance"),
    (15, "XV",  "The Devil"),
    (16, "XVI", "The Tower"),
    (17, "XVII","The Star"),
    (18, "XVIII","The Moon"),
    (19, "XIX", "The Sun"),
    (20, "XX",  "Judgement"),
    (21, "XXI", "The World"),
]

# ---------- Utilities ----------

def load_font(size, path=None):
    try:
        if path:
            return ImageFont.truetype(path, size=size)
    except Exception:
        pass
    return ImageFont.load_default()

def rounded_rect_mask(w, h, r):
    m = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(m)
    d.rounded_rectangle([0, 0, w-1, h-1], radius=r, fill=255)
    return m

def vertical_gradient(size, top_hex, bottom_hex):
    w, h = size
    top = Image.new("RGB", (w, 1), top_hex)
    bottom = Image.new("RGB", (w, 1), bottom_hex)
    grad = Image.linear_gradient("L").resize((1, h))
    bg = Image.new("RGB", (w, h))
    for y in range(h):
        t = grad.getpixel((0, y)) / 255.0
        r = int((1-t)*int(top_hex[1:3], 16) + t*int(bottom_hex[1:3], 16))
        g = int((1-t)*int(top_hex[3:5], 16) + t*int(bottom_hex[3:5], 16))
        b = int((1-t)*int(top_hex[5:7], 16) + t*int(bottom_hex[5:7], 16))
        ImageDraw.Draw(bg).line([(0,y),(w,y)], fill=(r,g,b))
    return bg

def glass_panel(w, h, inset=48, blur=12, alpha=140):
    base = Image.new("RGBA", (w, h), (255,255,255,0))
    panel = Image.new("RGBA", (w - 2*inset, h - 2*inset), (255,255,255,alpha))
    panel = panel.filter(ImageFilter.GaussianBlur(blur))
    m = rounded_rect_mask(panel.width, panel.height, 48)
    base.paste(panel, (inset, inset), m)
    # highlight swipe
    swipe = Image.new("L", (panel.width, panel.height), 0)
    sdraw = ImageDraw.Draw(swipe)
    sdraw.ellipse([int(panel.width*0.2), -int(panel.height*0.5),
                   int(panel.width*1.2), int(panel.height*0.8)], fill=90)
    swipe = swipe.filter(ImageFilter.GaussianBlur(40))
    base.alpha_composite(Image.merge("RGBA", (swipe,swipe,swipe,swipe)), (inset, inset))
    return base

def metallic_text(draw, xy, text, font, base_color=(230,230,230), shine_height=0.6):
    x, y = xy
    # Soft shadow
    draw.text((x+2, y+2), text, font=font, fill=(0,0,0,120))
    # Body
    draw.text((x, y), text, font=font, fill=base_color)
    # Simple foil sweep (white band)
    tw, th = draw.textbbox((0,0), text, font=font)[2:]
    highlight = Image.new("L", (tw, th), 0)
    hdraw = ImageDraw.Draw(highlight)
    hdraw.rectangle([0, int(th*(1-shine_height)), tw, th], fill=180)
    highlight = highlight.filter(ImageFilter.GaussianBlur(6))
    band = Image.new("RGBA", (tw, th), (255,255,255,0))
    band.putalpha(highlight)
    return band

def ornate_border(img, inset=20, glow=80, line=2):
    d = ImageDraw.Draw(img, "RGBA")
    x0, y0 = inset, inset
    x1, y1 = img.width - inset, img.height - inset
    # outer rounded border
    for i in range(3):
        alpha = int(120 * (1 - i/3))
        d.rounded_rectangle([x0+i, y0+i, x1-i, y1-i], radius=RADIUS, outline=(255,255,255,alpha), width=line)
    # corner flourishes (simple arcs)
    arc_r = 40
    for (cx, cy) in [(x0+RADIUS, y0+RADIUS), (x1-RADIUS, y0+RADIUS), (x0+RADIUS, y1-RADIUS), (x1-RADIUS, y1-RADIUS)]:
        d.arc([cx-arc_r, cy-arc_r, cx+arc_r, cy+arc_r], 20, 110, fill=(255,255,255,180), width=2)
        d.arc([cx-arc_r, cy-arc_r, cx+arc_r, cy+arc_r], 200, 290, fill=(255,255,255,100), width=2)
    # subtle outer glow
    glow_mask = rounded_rect_mask(img.width, img.height, RADIUS).filter(ImageFilter.GaussianBlur(24))
    glow_layer = Image.new("RGBA", img.size, (255,255,255,0))
    ImageDraw.Draw(glow_layer).rounded_rectangle([inset-6, inset-6, x1+6, y1+6], radius=RADIUS+6, outline=(255,255,255,0), width=0)
    glow_layer.putalpha(glow_mask.point(lambda v: int(v * (glow/255))))
    img.alpha_composite(glow_layer)

def seed_noise_sparkles(img, count=650, intensity=140):
    rnd = random.Random(SEED) if SEED is not None else random
    d = ImageDraw.Draw(img, "RGBA")
    for _ in range(count):
        x = rnd.randint(10, img.width-10)
        y = rnd.randint(10, img.height-10)
        a = rnd.randint(30, intensity)
        d.point((x, y), fill=(255,255,255,a))

# Simple symbolic icon per card: composed of geometric primitives
def draw_icon(draw, card_idx, cx, cy, size):
    r = int(size/2)
    def ring(radius, width=8, fill=(230,230,230,200)):
        bbox = [cx-radius, cy-radius, cx+radius, cy+radius]
        draw.ellipse(bbox, outline=fill, width=width)

    def star(n, radius, inner_ratio=0.45, width=8):
        pts = []
        for i in range(n*2):
            ang = math.pi * i / n
            rad = radius if i % 2 == 0 else radius*inner_ratio
            pts.append((cx + rad*math.cos(ang - math.pi/2), cy + rad*math.sin(ang - math.pi/2)))
        draw.line(pts + [pts[0]], fill=(230,230,230,220), width=width, joint="curve")

    def tower():
        w = int(size*0.42)
        h = int(size*0.62)
        x0, y0 = cx - w//2, cy - h//2
        draw.rectangle([x0, y0, x0+w, y0+h], outline=(230,230,230,220), width=10)
        draw.line([(x0, y0+int(h*0.25)), (x0+w, y0+int(h*0.25))], fill=(230,230,230,180), width=8)
        draw.polygon([(cx, y0-20), (cx-30, y0+20), (cx+30, y0+20)], outline=(230,230,230,220), width=8)

    def sun():
        ring(int(size*0.45), width=10)
        for i in range(16):
            ang = 2*math.pi*i/16
            x = cx + int(size*0.65)*math.cos(ang)
            y = cy + int(size*0.65)*math.sin(ang)
            draw.line([(cx, cy), (x, y)], fill=(230,230,230,200), width=6)

    def moon():
        ring(int(size*0.4), width=10)
        # crescent cut
        draw.ellipse([cx-int(size*0.2), cy-int(size*0.35), cx+int(size*0.55), cy+int(size*0.35)], fill=(0,0,0,160))

    def scales():
        # Justice scales
        w = int(size*0.6)
        bar_y = cy - int(size*0.15)
        draw.line([(cx-w//2, bar_y), (cx+w//2, bar_y)], fill=(230,230,230,220), width=8)
        # pans
        for dx in (-w//2+10, w//2-10):
            draw.line([(cx+dx, bar_y), (cx+dx, bar_y+int(size*0.25))], fill=(230,230,230,220), width=6)
            draw.arc([cx+dx-60, bar_y+int(size*0.25), cx+dx+60, bar_y+int(size*0.25)+60], 200, -20, fill=(230,230,230,220), width=6)

    def wheel():
        ring(int(size*0.48), width=12)
        for i in range(8):
            ang = 2*math.pi*i/8
            x = cx + int(size*0.48)*math.cos(ang)
            y = cy + int(size*0.48)*math.sin(ang)
            draw.line([(cx, cy), (x, y)], fill=(230,230,230,200), width=8)

    def devil():
        ring(int(size*0.42), width=10)
        # horns
        draw.arc([cx-120, cy-160, cx-20, cy-60], 220, 340, fill=(230,230,230,220), width=10)
        draw.arc([cx+20, cy-160, cx+120, cy-60], 200, 320, fill=(230,230,230,220), width=10)

    def lovers():
        # two interlocking rings
        draw.ellipse([cx-110, cy-60, cx-10, cy+40], outline=(230,230,230,220), width=10)
        draw.ellipse([cx+10, cy-60, cx+110, cy+40], outline=(230,230,230,220), width=10)

    def chariot():
        # wheels and canopy line
        wheel_y = cy + int(size*0.22)
        draw.ellipse([cx-140, wheel_y-50, cx-60, wheel_y+30], outline=(230,230,230,220), width=10)
        draw.ellipse([cx+60, wheel_y-50, cx+140, wheel_y+30], outline=(230,230,230,220), width=10)
        draw.line([(cx-160, cy-60), (cx+160, cy-60)], fill=(230,230,230,220), width=10)

    # Map some iconic shapes; others fall back to star/ring combos
    if card_idx == 16:           # Tower
        tower()
    elif card_idx == 19:         # Sun
        sun()
    elif card_idx == 18:         # Moon
        moon()
    elif card_idx == 11:         # Justice
        scales()
    elif card_idx == 10:         # Wheel
        wheel()
    elif card_idx == 15:         # Devil
        devil()
    elif card_idx == 6:          # Lovers
        lovers()
    elif card_idx == 7:          # Chariot
        chariot()
    elif card_idx == 17:         # Star
        star(8, int(size*0.42))
    else:
        ring(int(size*0.46), width=10)
        star(6, int(size*0.34))

def center_text(draw, text, font, y, fill=(230,230,230,230)):
    bbox = draw.textbbox((0,0), text, font=font)
    w = bbox[2] - bbox[0]
    x = (W - w) // 2
    draw.text((x, y), text, font=font, fill=fill)
    return x, y, w, bbox[3]-bbox[1]

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    if SEED is not None:
        random.seed(SEED)

    title_font = load_font(TITLE_FONT_SIZE, FONT_PATH_TITLE)
    num_font = load_font(NUM_FONT_SIZE, FONT_PATH_NUM)

    for idx, roman, name in MAJORS:
        top, bot = PALETTES[idx]
        # Base with rounded corners
        bg = vertical_gradient((W, H), top, bot).convert("RGBA")
        mask = rounded_rect_mask(W, H, RADIUS)
        card = Image.new("RGBA", (W, H), (0,0,0,0))
        card.paste(bg, (0,0), mask)

        # Glass panel and sparkles
        card.alpha_composite(glass_panel(W, H, inset=48, blur=10, alpha=110))
        seed_noise_sparkles(card, count=700, intensity=110)

        # Ornate border
        ornate_border(card, inset=20, glow=70, line=2)

        draw = ImageDraw.Draw(card, "RGBA")

        # Header: Roman numeral
        num_x, num_y, num_w, num_h = center_text(draw, roman, num_font, y=70)
        # Add simple metallic sweep to numeral
        num_band = metallic_text(draw, (num_x, 70), roman, num_font, base_color=(235,235,235))
        card.alpha_composite(num_band, (num_x, 70))

        # Icon
        icon_size = int(min(W, H) * ICON_SCALE)
        draw_icon(draw, idx, W//2, H//2 - 40, icon_size)

        # Title
        title_y = H - 70 - TITLE_FONT_SIZE - 20
        t_x, t_y, t_w, t_h = center_text(draw, name, title_font, y=title_y)
        t_band = metallic_text(draw, (t_x, title_y), name, title_font, base_color=(240,240,240))
        card.alpha_composite(t_band, (t_x, title_y))

        # Subtle vignette
        vignette = Image.new("L", (W, H), 0)
        vdraw = ImageDraw.Draw(vignette)
        vdraw.ellipse([-W*0.2, -H*0.2, W*1.2, H*1.2], fill=255)
        vignette = vignette.filter(ImageFilter.GaussianBlur(180)).point(lambda v: int(v*0.7))
        # no need to change alpha here, just proceed
        dark = Image.new("RGBA", (W, H), (0,0,0,140))
        dark.putalpha(Image.eval(vignette, lambda v: 255 - v))
        card = Image.alpha_composite(card, dark)

        # Save
        safe = name.lower().replace(" ", "_")
        out_path = os.path.join(OUT_DIR, f"{idx:02d}_{safe}.png")
        card.save(out_path, "PNG", pnginfo=None)
        print(f"Saved {out_path}")

if __name__ == "__main__":
    # Pillow imports used inside main (to keep top tidy)
    from PIL import ImageChops  # noqa: F401 (side-effect: ensures PIL loads this module if needed)
    main()

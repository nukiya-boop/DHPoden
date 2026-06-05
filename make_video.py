import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os

FONT_PATH = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
WP_DIR = "/home/user/DHPoden/wp"
OUTPUT = "/home/user/DHPoden/wp/promo.mp4"

W, H = 1080, 1080
FPS = 30
IMG_SEC = 2.5    # 通常スライド表示秒
QR_SEC = 5       # QR表示秒（12×2.5+5=35秒）
FADE_FRAMES = int(FPS * 0.3)  # フェード0.3秒

# 画像順序とテロップ定義
slides = [
    ("gp_41.jpg",    "おでんだけじゃない、\nここにしかない一皿。",       "冷菜・鮮魚 全品揃ってます"),
    ("gp_17.jpg",    "梅水晶・子持ちこんにゃく\nたこ刺身・サーモン刺身",  "〆まで飽きさせない冷菜盛り"),
    ("gp_18.jpg",    "鮮度抜群の刺身を\nリーズナブルに。",               "毎日仕入れ・季節の旬をお届け"),
    ("gp_19.jpg",    "一皿一皿に\nこだわりの仕込み。",                   "おでん屋の「刺身」、侮れません"),
    ("gp_20.jpg",    "サーモンも、たこも\n今が旬！",                     "鮮魚は毎日変わります"),
    ("gp_43.jpg",    "秋冬はお酒が\nおいしい季節。",                     "旬の肴と一緒にどうぞ"),
    ("gp_46.jpg",    "サワーはノンアルでも\nご提供できます！",            "お酒が飲めない方もぜひ🙌"),
    ("gp_47.jpg",    "ドリンクも充実。\nノンアルサワー再プッシュ中！",   "お気軽にご相談ください"),
    ("gp_52.jpg",    "おでんはもちろん\n一品料理も豊富。",               "飲み会・女子会・ひとり飲みにも"),
    ("gp_53.jpg",    "季節の食材を使った\nその日限りのメニューも。",      "黒板メニューをお見逃しなく"),
    ("gp_55.jpg",    "〆のおでんまで\nゆっくりどうぞ。",                  "おでんスタンド D・H・Poden"),
    ("gp_60 (1).jpg","また来たくなる\n味があります。",                    "ご来店お待ちしています"),
    (None, "ご予約・お問い合わせは\nこちらから", ""),  # QR: loaded dynamically
]


def load_img(fname):
    path = os.path.join(WP_DIR, fname)
    img = Image.open(path).convert("RGB")
    # クロップしてスクエアに
    w, h = img.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    img = img.crop((left, top, left + side, top + side))
    img = img.resize((W, H), Image.LANCZOS)
    return np.array(img)[:, :, ::-1]  # RGB→BGR


def add_telop(frame_bgr, main_text, sub_text):
    img_pil = Image.fromarray(frame_bgr[:, :, ::-1])
    draw = ImageDraw.Draw(img_pil)

    # 半透明グラデーション帯（下部）
    overlay = Image.new("RGBA", img_pil.size, (0, 0, 0, 0))
    ov_draw = ImageDraw.Draw(overlay)
    for i in range(300):
        alpha = int(180 * (i / 300))
        ov_draw.rectangle([0, H - 300 + i, W, H - 300 + i + 1], fill=(0, 0, 0, alpha))
    img_pil = Image.alpha_composite(img_pil.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img_pil)

    # メインテロップ
    if main_text:
        fsize = 62
        font = ImageFont.truetype(FONT_PATH, fsize)
        lines = main_text.split("\n")
        y = H - 280
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            tw = bbox[2] - bbox[0]
            x = (W - tw) // 2
            # 影
            draw.text((x + 2, y + 2), line, font=font, fill=(0, 0, 0, 180))
            draw.text((x, y), line, font=font, fill=(255, 255, 255))
            y += fsize + 8

    # サブテロップ
    if sub_text:
        fsize_s = 36
        font_s = ImageFont.truetype(FONT_PATH, fsize_s)
        bbox = draw.textbbox((0, 0), sub_text, font=font_s)
        tw = bbox[2] - bbox[0]
        x = (W - tw) // 2
        y_s = H - 55
        draw.text((x + 1, y_s + 1), sub_text, font=font_s, fill=(0, 0, 0, 180))
        draw.text((x, y_s), sub_text, font=font_s, fill=(255, 220, 100))

    return np.array(img_pil)[:, :, ::-1]


fourcc = cv2.VideoWriter_fourcc(*"mp4v")
OUTPUT = "/home/user/DHPoden/wp/promo35.mp4"
out = cv2.VideoWriter(OUTPUT, fourcc, FPS, (W, H))

prev_frame = None

for i, (fname, main_text, sub_text) in enumerate(slides):
    is_qr = i == len(slides) - 1
    duration = QR_SEC if is_qr else IMG_SEC
    total_frames = int(FPS * duration)

    actual_fname = fname
    if fname is None:
        actual_fname = next(f for f in os.listdir(WP_DIR) if "QR" in f or "おでん" in f)
    raw = load_img(actual_fname)
    frame = add_telop(raw, main_text, sub_text)

    for f in range(total_frames):
        if f < FADE_FRAMES and prev_frame is not None:
            alpha = f / FADE_FRAMES
            blended = cv2.addWeighted(prev_frame, 1 - alpha, frame, alpha, 0)
            out.write(blended)
        else:
            out.write(frame)

    prev_frame = frame.copy()
    print(f"  [{i+1}/{len(slides)}] {fname}")

out.release()
print(f"\n完成: {OUTPUT}")

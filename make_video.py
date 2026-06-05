import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os

FONT_PATH = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
WP_DIR = "/home/user/DHPoden/wp"

W, H = 1080, 1080
FPS = 30
IMG_SEC = 2.5
QR_SEC = 5
FADE_FRAMES = int(FPS * 0.4)

# テロップ定義（ノンアル再プッシュ削除・渋めに統一）
slides = [
    ("gp_41.jpg",    "おでんだけじゃない、\nここにしかない一皿。",      "冷菜・鮮魚 全品揃ってます"),
    ("gp_17.jpg",    "梅水晶・子持ちこんにゃく\nたこ刺身・サーモン刺身", ""),
    ("gp_18.jpg",    "鮮度抜群の刺身を\nリーズナブルに。",              "毎日仕入れ、季節の旬をお届け"),
    ("gp_19.jpg",    "一皿一皿に\nこだわりの仕込み。",                  ""),
    ("gp_20.jpg",    "旬の魚が、今夜も揃っています。",                  ""),
    ("gp_43.jpg",    "秋冬は、肴が旨い季節。",                          "旬の一品と、ゆっくりどうぞ"),
    ("gp_46.jpg",    "サワーはノンアルでも\nご用意できます。",           ""),
    ("gp_52.jpg",    "おでんはもちろん\n一品料理も豊富に。",            ""),
    ("gp_53.jpg",    "その日だけの\n黒板メニューも。",                  ""),
    ("gp_55.jpg",    "〆のおでんまで\nゆっくりと。",                    "おでんスタンド  D・H・Poden"),
    ("gp_60 (1).jpg","また来たくなる\n味がある。",                      ""),
    (None,           "",                                                 ""),  # QR: テロップなし
]


def load_img(fname, fit=False):
    path = os.path.join(WP_DIR, fname)
    img = Image.open(path).convert("RGB")
    if fit:
        # 全体が収まるようにレターボックス（黒背景）
        img.thumbnail((W, H), Image.LANCZOS)
        bg = Image.new("RGB", (W, H), (0, 0, 0))
        offset = ((W - img.width) // 2, (H - img.height) // 2)
        bg.paste(img, offset)
        return np.array(bg)[:, :, ::-1]
    w, h = img.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    img = img.crop((left, top, left + side, top + side))
    img = img.resize((W, H), Image.LANCZOS)
    return np.array(img)[:, :, ::-1]


def add_telop(frame_bgr, main_text, sub_text, is_qr=False):
    img_pil = Image.fromarray(frame_bgr[:, :, ::-1])

    if is_qr or (not main_text and not sub_text):
        return np.array(img_pil)[:, :, ::-1]

    # グラデーション帯（より深く・広め）
    overlay = Image.new("RGBA", img_pil.size, (0, 0, 0, 0))
    ov_draw = ImageDraw.Draw(overlay)
    grad_h = 340
    for i in range(grad_h):
        alpha = int(200 * (i / grad_h) ** 1.5)
        ov_draw.rectangle([0, H - grad_h + i, W, H - grad_h + i + 1], fill=(0, 0, 0, alpha))
    img_pil = Image.alpha_composite(img_pil.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img_pil)

    # メインテロップ（細め・控えめサイズで渋く）
    if main_text:
        fsize = 54
        font = ImageFont.truetype(FONT_PATH, fsize)
        lines = main_text.split("\n")
        total_h = len(lines) * (fsize + 10)
        y = H - 80 - total_h - (40 if sub_text else 0)
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            tw = bbox[2] - bbox[0]
            x = (W - tw) // 2
            # 薄い影のみ（白抜きなし）
            draw.text((x + 2, y + 2), line, font=font, fill=(0, 0, 0, 160))
            draw.text((x, y), line, font=font, fill=(240, 235, 220))  # オフホワイト
            y += fsize + 10

    # サブテロップ（より小さく控えめに）
    if sub_text:
        fsize_s = 30
        font_s = ImageFont.truetype(FONT_PATH, fsize_s)
        bbox = draw.textbbox((0, 0), sub_text, font=font_s)
        tw = bbox[2] - bbox[0]
        x = (W - tw) // 2
        y_s = H - 60
        draw.text((x + 1, y_s + 1), sub_text, font=font_s, fill=(0, 0, 0, 140))
        draw.text((x, y_s), sub_text, font=font_s, fill=(180, 160, 120))  # 薄いゴールド

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
    raw = load_img(actual_fname, fit=is_qr)
    frame = add_telop(raw, main_text, sub_text, is_qr=is_qr)

    for f in range(total_frames):
        if f < FADE_FRAMES and prev_frame is not None:
            alpha = f / FADE_FRAMES
            blended = cv2.addWeighted(prev_frame, 1 - alpha, frame, alpha, 0)
            out.write(blended)
        else:
            out.write(frame)

    prev_frame = frame.copy()
    print(f"  [{i+1}/{len(slides)}] {actual_fname}")

out.release()
print(f"\n完成: {OUTPUT}")

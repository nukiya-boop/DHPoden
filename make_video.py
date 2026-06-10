import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os

FONT_PATH = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
WP_DIR = "/home/user/DHPoden/wp"

W, H = 1080, 1920  # Instagram Reels 9:16
FPS = 30
IMG_SEC = 2.5
QR_SEC = 5
FADE_FRAMES = int(FPS * 0.4)

# テロップ定義（ノンアル再プッシュ削除・渋めに統一）
slides = [
    ("gp_41.jpg",    "おでんだけじゃない、\nここにしかない一皿。",      "冷菜・鮮魚、色々揃ってます"),
    ("gp_17.jpg",    "梅水晶・子持ちこんにゃく\nたこ刺身・サーモン刺身", ""),
    ("gp_18.jpg",    "鮮度抜群の刺身を\nリーズナブルに。",              "職人の目利きで、旬をお届け"),
    ("gp_19.jpg",    "一皿一皿に\nこだわりの仕込み。",                  ""),
    ("gp_20.jpg",    "旬の魚が、今夜も揃っています。",                  ""),
    ("gp_43.jpg",    "夏酒、入荷続々。",                                "旬の一品と、ゆっくりどうぞ"),
    ("gp_60 (1).jpg","サワーはノンアルでも\nご用意できます。",           ""),
    ("__一品_0007__", "おでんはもちろん\n一品料理も豊富に。", ""),
    ("gp_53.jpg",    "期間限定、\n季節のメニューも。",                  ""),
    ("__0002__",     "〆のおでんまで\nゆっくりと。",  ""),
    ("__おでん釜__", "また来たくなる\n味がある。",           ""),
    (None,           "",                                                 ""),  # QR: テロップなし
]


def load_img(fname, fit=False):
    path = os.path.join(WP_DIR, fname)
    img = Image.open(path).convert("RGB")
    # 全画像: アスペクト比を保ったまま幅1080に合わせて中央配置
    w, h = img.size
    scale = W / w
    new_h = int(h * scale)
    img = img.resize((W, new_h), Image.LANCZOS)
    bg = Image.new("RGB", (W, H), (10, 10, 10))
    top = (H - new_h) // 2
    bg.paste(img, (0, top))
    return np.array(bg)[:, :, ::-1]


def add_telop(frame_bgr, main_text, sub_text, is_qr=False):
    img_pil = Image.fromarray(frame_bgr[:, :, ::-1])

    if is_qr or (not main_text and not sub_text):
        return np.array(img_pil)[:, :, ::-1]

    # 下部グラデーション帯を画像に重ねる
    overlay = Image.new("RGBA", img_pil.size, (0, 0, 0, 0))
    ov_draw = ImageDraw.Draw(overlay)
    grad_h = 500
    for i in range(grad_h):
        alpha = int(210 * (i / grad_h) ** 1.4)
        ov_draw.rectangle([0, H - grad_h + i, W, H - grad_h + i + 1], fill=(0, 0, 0, alpha))
    img_pil = Image.alpha_composite(img_pil.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img_pil)

    if main_text:
        fsize = 62
        font = ImageFont.truetype(FONT_PATH, fsize)
        lines = main_text.split("\n")
        total_h = len(lines) * (fsize + 14)
        y = H - 160 - total_h - (50 if sub_text else 0)
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            tw = bbox[2] - bbox[0]
            x = (W - tw) // 2
            draw.text((x + 2, y + 2), line, font=font, fill=(0, 0, 0, 160))
            draw.text((x, y), line, font=font, fill=(240, 235, 220))
            y += fsize + 14

    if sub_text:
        fsize_s = 36
        font_s = ImageFont.truetype(FONT_PATH, fsize_s)
        bbox = draw.textbbox((0, 0), sub_text, font=font_s)
        tw = bbox[2] - bbox[0]
        x = (W - tw) // 2
        y_s = H - 100
        draw.text((x + 1, y_s + 1), sub_text, font=font_s, fill=(0, 0, 0, 140))
        draw.text((x, y_s), sub_text, font=font_s, fill=(180, 160, 120))

    return np.array(img_pil)[:, :, ::-1]


fourcc = cv2.VideoWriter_fourcc(*"mp4v")
OUTPUT = "/home/user/DHPoden/wp/promo35_reel.mp4"
out = cv2.VideoWriter(OUTPUT, fourcc, FPS, (W, H))

prev_frame = None

for i, (fname, main_text, sub_text) in enumerate(slides):
    is_qr = i == len(slides) - 1
    duration = QR_SEC if is_qr else IMG_SEC
    total_frames = int(FPS * duration)

    actual_fname = fname
    if fname is None:
        actual_fname = next(f for f in os.listdir(WP_DIR) if "QR" in f)
    elif fname == "__一品_0007__":
        actual_fname = next(f for f in os.listdir(WP_DIR) if "一品" in f and "0007" in f)
    elif fname == "__0002__":
        actual_fname = next(f for f in os.listdir(WP_DIR) if "0002" in f)
    elif fname == "__おでん釜__":
        actual_fname = next(f for f in os.listdir(WP_DIR) if "0007" in f and "一品" not in f and not f.startswith("gp"))
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

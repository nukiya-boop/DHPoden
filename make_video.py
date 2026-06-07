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
        # QR: 全体が収まるよう中央配置（黒背景）
        img.thumbnail((W, H), Image.LANCZOS)
        bg = Image.new("RGB", (W, H), (10, 10, 10))
        offset = ((W - img.width) // 2, (H - img.height) // 2)
        bg.paste(img, offset)
        return np.array(bg)[:, :, ::-1]
    # 通常: 幅基準でリサイズ→中央クロップして1080×1920に
    w, h = img.size
    scale = W / w
    new_h = int(h * scale)
    img = img.resize((W, new_h), Image.LANCZOS)
    if new_h < H:
        # 高さが足りない場合は高さ基準でリサイズ
        scale = H / h
        new_w = int(w * scale)
        img = img.resize((new_w, H), Image.LANCZOS)
        left = (new_w - W) // 2
        img = img.crop((left, 0, left + W, H))
    else:
        top = (new_h - H) // 2
        img = img.crop((0, top, W, top + H))
    return np.array(img)[:, :, ::-1]


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

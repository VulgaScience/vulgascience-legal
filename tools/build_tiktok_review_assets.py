import math
import shutil
from pathlib import Path

import numpy as np
from moviepy.editor import VideoClip
from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "storage" / "review_assets" / "tiktok_developer_review"
OUT.mkdir(parents=True, exist_ok=True)

FONT_DIR = Path("C:/Windows/Fonts")
FONT_REGULAR = FONT_DIR / "segoeui.ttf"
FONT_SEMIBOLD = FONT_DIR / "seguisb.ttf"
FONT_BOLD = FONT_DIR / "segoeuib.ttf"
FONT_MONO = FONT_DIR / "consola.ttf"

BG = (11, 16, 27)
PANEL = (22, 30, 45)
PANEL_2 = (29, 39, 58)
TEXT = (240, 247, 255)
MUTED = (150, 166, 186)
CYAN = (21, 220, 232)
BLUE = (37, 156, 255)
YELLOW = (255, 207, 55)
GREEN = (70, 218, 138)
RED = (255, 96, 118)


def font(size, bold=False, mono=False):
    path = FONT_MONO if mono else (FONT_BOLD if bold else FONT_REGULAR)
    if not path.exists():
        path = FONT_BOLD if FONT_BOLD.exists() else FONT_REGULAR
    return ImageFont.truetype(str(path), size)


def rounded(draw, box, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def text(draw, pos, value, size=28, fill=TEXT, bold=False, mono=False, anchor=None):
    draw.text(pos, value, font=font(size, bold=bold, mono=mono), fill=fill, anchor=anchor)


def alpha_composite(base, layer):
    base.alpha_composite(layer)
    return base


def draw_logo(size=1024, with_label=True):
    img = Image.new("RGBA", (size, size), BG + (255,))
    d = ImageDraw.Draw(img)
    pad = int(size * 0.08)

    for i in range(size):
        shade = int(18 + 14 * (i / size))
        d.line([(0, i), (size, i)], fill=(8, shade, 32 + shade // 2, 255))

    d.rounded_rectangle((0, 0, size - 1, size - 1), radius=int(size * 0.12), outline=(35, 48, 72), width=max(2, size // 128))

    center = size / 2
    radius = size * 0.34
    stroke = max(14, size // 34)
    d.arc(
        (center - radius, center - radius, center + radius, center + radius),
        start=128,
        end=318,
        fill=CYAN + (255,),
        width=stroke,
    )
    d.arc(
        (center - radius, center - radius, center + radius, center + radius),
        start=318,
        end=54,
        fill=YELLOW + (255,),
        width=stroke,
    )
    node_r = size * 0.027
    for deg, color in [(128, CYAN), (318, YELLOW)]:
        a = math.radians(deg)
        x = center + radius * math.cos(a)
        y = center + radius * math.sin(a)
        d.ellipse((x - node_r, y - node_r, x + node_r, y + node_r), fill=color + (255,))

    grid_x = int(size * 0.22)
    grid_y = int(size * 0.54)
    grid_gap = int(size * 0.072)
    for n in range(4):
        x = grid_x + n * grid_gap
        d.line((x, grid_y, x, grid_y + grid_gap * 3), fill=(21, 220, 232, 90), width=max(2, size // 180))
        y = grid_y + n * grid_gap
        d.line((grid_x, y, grid_x + grid_gap * 3, y), fill=(21, 220, 232, 90), width=max(2, size // 180))
    d.ellipse((grid_x + grid_gap * 2 - node_r / 2, grid_y + grid_gap * 2 - node_r / 2, grid_x + grid_gap * 2 + node_r / 2, grid_y + grid_gap * 2 + node_r / 2), fill=CYAN + (255,))

    vs_font = font(int(size * 0.34), bold=True)
    bbox_v = d.textbbox((0, 0), "V", font=vs_font)
    bbox_s = d.textbbox((0, 0), "S", font=vs_font)
    total_w = (bbox_v[2] - bbox_v[0]) + (bbox_s[2] - bbox_s[0]) - int(size * 0.02)
    x = (size - total_w) / 2
    y = size * 0.34
    d.text((x, y), "V", font=vs_font, fill=CYAN + (255,))
    d.text((x + bbox_v[2] - bbox_v[0] - int(size * 0.02), y), "S", font=vs_font, fill=YELLOW + (255,))

    if with_label:
        label_font = font(int(size * 0.065), bold=True)
        d.text((size / 2, size * 0.79), "VulgaScience", font=label_font, fill=TEXT + (255,), anchor="mm")
        d.text((size / 2, size * 0.85), "Publisher", font=font(int(size * 0.04)), fill=MUTED + (255,), anchor="mm")

    return img


def save_logos():
    logo = draw_logo(1024, with_label=True)
    logo.save(OUT / "vulgascience_logo_full_1024.png")
    logo.resize((512, 512), Image.Resampling.LANCZOS).save(OUT / "vulgascience_logo_full_512.png")

    app_icon = draw_logo(1024, with_label=False)
    app_icon.save(OUT / "vulgascience_app_icon_1024.png")
    app_icon.resize((512, 512), Image.Resampling.LANCZOS).save(OUT / "vulgascience_app_icon_512.png")
    app_icon.resize((256, 256), Image.Resampling.LANCZOS).save(OUT / "vulgascience_app_icon_256.png")


def copy_concept():
    generated_root = Path.home() / ".codex" / "generated_images"
    if not generated_root.exists():
        return
    images = sorted(generated_root.rglob("*.png"), key=lambda p: p.stat().st_mtime, reverse=True)
    if images:
        shutil.copy2(images[0], OUT / "vulgascience_logo_imagegen_concept.png")


def ease(x):
    x = max(0, min(1, x))
    return 3 * x * x - 2 * x * x * x


def progress_between(t, start, end):
    return ease((t - start) / (end - start))


def cursor_position(t):
    keyframes = [
        (0, (1050, 600)),
        (4, (1050, 600)),
        (7, (860, 520)),
        (12, (860, 520)),
        (15, (930, 536)),
        (19, (930, 536)),
        (23, (404, 454)),
        (30, (404, 454)),
        (34, (1030, 604)),
        (43, (1030, 604)),
        (48, (1048, 585)),
        (56, (1048, 585)),
        (62, (1048, 585)),
    ]
    for i in range(len(keyframes) - 1):
        t0, p0 = keyframes[i]
        t1, p1 = keyframes[i + 1]
        if t0 <= t <= t1:
            u = progress_between(t, t0, t1)
            return (p0[0] + (p1[0] - p0[0]) * u, p0[1] + (p1[1] - p0[1]) * u)
    return keyframes[-1][1]


def click_active(t):
    return any(abs(t - c) < 0.22 for c in [7.2, 15.2, 23.4, 34.4, 48.2])


def base_frame():
    img = Image.new("RGBA", (1280, 720), BG + (255,))
    d = ImageDraw.Draw(img)
    for y in range(720):
        d.line((0, y, 1280, y), fill=(8, 12 + y // 64, 24 + y // 46, 255))
    for x in range(0, 1280, 64):
        d.line((x, 0, x, 720), fill=(29, 46, 69, 36), width=1)
    for y in range(0, 720, 64):
        d.line((0, y, 1280, y), fill=(29, 46, 69, 36), width=1)
    return img


def topbar(d, title="VulgaScience Publisher"):
    rounded(d, (40, 30, 1240, 94), 18, (12, 18, 30), outline=(38, 54, 78), width=1)
    mini = draw_logo(50)
    return mini


def draw_nav(img, section):
    d = ImageDraw.Draw(img)
    logo = draw_logo(50)
    img.alpha_composite(logo, (58, 37))
    text(d, (120, 48), "VulgaScience Publisher", 24, bold=True)
    text(d, (120, 74), "TikTok Content Posting API demo", 15, fill=MUTED)
    text(d, (956, 54), "Sandbox flow", 18, fill=CYAN, bold=True)
    rounded(d, (1110, 48, 1218, 78), 15, (20, 70, 58), outline=(55, 180, 126))
    text(d, (1164, 63), "No public post", 14, fill=(190, 255, 220), bold=True, anchor="mm")
    text(d, (64, 126), section, 26, bold=True)


def pill(d, box, label, color, fill=None):
    fill = fill or (20, 42, 56)
    rounded(d, box, 14, fill, outline=color, width=1)
    text(d, ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2), label, 15, fill=color, bold=True, anchor="mm")


def button(d, box, label, fill=BLUE, active=False):
    if active:
        fill = tuple(min(255, c + 25) for c in fill)
    shadow = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle((box[0], box[1] + 7, box[2], box[3] + 7), radius=18, fill=(0, 0, 0, 80))
    return shadow, fill


def draw_cursor(img, t):
    d = ImageDraw.Draw(img)
    x, y = cursor_position(t)
    if click_active(t):
        r = 34 + 20 * (1 - min(1, abs((t % 1) - 0.2) * 4))
        d.ellipse((x - r, y - r, x + r, y + r), outline=YELLOW + (180,), width=4)
    pts = [(x, y), (x + 2, y + 34), (x + 11, y + 26), (x + 22, y + 50), (x + 33, y + 45), (x + 22, y + 22), (x + 34, y + 21)]
    d.polygon(pts, fill=(255, 255, 255, 255), outline=(21, 30, 44, 255))


def scene_intro(img, t):
    d = ImageDraw.Draw(img)
    draw_nav(img, "Review asset: end-to-end TikTok integration")
    logo = draw_logo(190)
    img.alpha_composite(logo, (110, 235))
    text(d, (350, 255), "VulgaScience Publisher", 54, bold=True)
    text(d, (352, 324), "Creates a science video, validates quality, then uploads it to TikTok inbox.", 25, fill=MUTED)
    pill(d, (354, 374, 520, 414), "video.upload", CYAN)
    pill(d, (540, 374, 714, 414), "user.info.basic", YELLOW)
    pill(d, (734, 374, 928, 414), "Content Posting API", GREEN)
    text(d, (352, 466), "Demo purpose: show the sandbox flow used for TikTok Developer review.", 22)
    text(d, (352, 506), "No automatic public posting. The creator keeps final control inside TikTok.", 22, fill=(192, 255, 221))


def scene_login(img, t):
    d = ImageDraw.Draw(img)
    draw_nav(img, "Step 1 - Connect TikTok account")
    rounded(d, (84, 170, 1196, 634), 22, PANEL, outline=(44, 62, 90), width=1)
    text(d, (124, 220), "Connection", 34, bold=True)
    text(d, (124, 265), "The creator signs in with TikTok OAuth. The app never asks for a password.", 24, fill=MUTED)
    rounded(d, (124, 325, 560, 560), 18, PANEL_2, outline=(50, 69, 101))
    text(d, (152, 365), "Requested scopes", 24, bold=True)
    pill(d, (152, 410, 330, 450), "video.upload", CYAN)
    pill(d, (152, 466, 360, 506), "user.info.basic", YELLOW)
    text(d, (600, 355), "Product used", 22, fill=MUTED)
    text(d, (600, 392), "Content Posting API", 38, bold=True)
    text(d, (600, 440), "Upload only: the final publish action happens in TikTok.", 24, fill=TEXT)
    rounded(d, (746, 496, 1050, 556), 18, BLUE if t > 7 else (34, 126, 210), outline=(94, 190, 255))
    text(d, (898, 526), "Connect with TikTok", 22, bold=True, anchor="mm")


def scene_oauth(img, t):
    d = ImageDraw.Draw(img)
    draw_nav(img, "Step 2 - TikTok sandbox authorization")
    rounded(d, (314, 158, 966, 626), 24, (246, 248, 252), outline=(210, 218, 230), width=2)
    text(d, (640, 210), "TikTok", 42, fill=(12, 16, 25), bold=True, anchor="mm")
    text(d, (640, 270), "VulgaScience Publisher requests access", 27, fill=(26, 31, 44), bold=True, anchor="mm")
    text(d, (640, 312), "Sandbox environment - developer review demo", 19, fill=(92, 104, 124), anchor="mm")
    rounded(d, (392, 360, 888, 444), 18, (235, 241, 248), outline=(202, 213, 226))
    text(d, (424, 390), "Allow uploading videos to TikTok inbox", 20, fill=(24, 30, 42), bold=True)
    text(d, (424, 420), "Scope: video.upload", 16, fill=(88, 102, 120), mono=True)
    rounded(d, (392, 462, 888, 542), 18, (235, 241, 248), outline=(202, 213, 226))
    text(d, (424, 492), "Read basic profile info", 20, fill=(24, 30, 42), bold=True)
    text(d, (424, 522), "Scope: user.info.basic", 16, fill=(88, 102, 120), mono=True)
    rounded(d, (742, 556, 968, 616), 18, (20, 20, 22), outline=(45, 45, 52))
    text(d, (855, 586), "Authorize", 22, fill=(255, 255, 255), bold=True, anchor="mm")


def scene_dashboard(img, t):
    d = ImageDraw.Draw(img)
    draw_nav(img, "Step 3 - Select generated video")
    rounded(d, (64, 170, 450, 638), 20, PANEL, outline=(42, 60, 88))
    text(d, (96, 220), "TikTok account", 28, bold=True)
    pill(d, (96, 262, 256, 302), "Connected", GREEN, fill=(18, 52, 42))
    text(d, (96, 344), "Scopes granted", 20, fill=MUTED)
    text(d, (96, 382), "video.upload", 24, fill=CYAN, mono=True)
    text(d, (96, 420), "user.info.basic", 24, fill=YELLOW, mono=True)
    text(d, (96, 506), "Secrets are stored locally in .env", 20, fill=MUTED)

    rounded(d, (486, 170, 1216, 638), 20, PANEL, outline=(42, 60, 88))
    text(d, (522, 220), "Pending review draft", 28, bold=True)
    rounded(d, (522, 270, 1178, 520), 18, PANEL_2, outline=(52, 73, 106))
    text(d, (554, 315), "VulgaScience_001_monetisable_60s_technique_v3.mp4", 24, bold=True)
    text(d, (554, 358), "Topic: predictive coding in the brain", 21, fill=MUTED)
    checks = ["60.5 s long-form candidate", "720 x 1280 vertical", "Audio present", "Subtitle encoding OK"]
    for i, item in enumerate(checks):
        y = 410 + i * 28
        d.ellipse((554, y - 11, 574, y + 9), fill=GREEN)
        text(d, (584, y - 15), item, 18)
    rounded(d, (850, 556, 1110, 616), 18, BLUE, outline=(94, 190, 255))
    text(d, (980, 586), "Send to TikTok inbox", 21, bold=True, anchor="mm")


def scene_upload(img, t):
    d = ImageDraw.Draw(img)
    draw_nav(img, "Step 4 - Content Posting API upload")
    rounded(d, (72, 168, 1208, 632), 20, PANEL, outline=(42, 60, 88))
    text(d, (110, 218), "API call", 30, bold=True)
    rounded(d, (110, 270, 1170, 492), 16, (10, 14, 24), outline=(45, 64, 94))
    lines = [
        "POST https://open.tiktokapis.com/v2/post/publish/inbox/video/init/",
        'Authorization: Bearer <access_token>',
        '{',
        '  "source_info": {',
        '    "source": "FILE_UPLOAD",',
        '    "video_size": 18462143,',
        '    "chunk_size": 8388608,',
        '    "total_chunk_count": 3',
        '  }',
        '}',
    ]
    for i, line in enumerate(lines):
        text(d, (136, 304 + i * 19), line, 16, fill=(198, 219, 238), mono=True)
    p = progress_between(t, 36, 45)
    rounded(d, (110, 538, 1170, 578), 20, (18, 25, 38), outline=(44, 64, 92))
    rounded(d, (110, 538, 110 + int(1060 * p), 578), 20, BLUE if p < 1 else GREEN)
    text(d, (640, 602), f"Uploading chunks... {int(p * 100)}%", 21, fill=TEXT, bold=True, anchor="mm")


def scene_success(img, t):
    d = ImageDraw.Draw(img)
    draw_nav(img, "Step 5 - Draft arrives in TikTok inbox")
    rounded(d, (70, 170, 640, 632), 22, PANEL, outline=(42, 60, 88))
    d.ellipse((118, 226, 178, 286), fill=GREEN)
    d.line((136, 256, 146, 268, 164, 242), fill=BG, width=7, joint="curve")
    text(d, (206, 230), "Upload complete", 34, bold=True)
    text(d, (206, 278), "Status: uploaded_to_tiktok_inbox", 22, fill=GREEN, mono=True)
    text(d, (112, 352), "Returned fields", 22, fill=MUTED)
    text(d, (112, 392), "publish_id: sandbox_20260613_demo", 21, fill=TEXT, mono=True)
    text(d, (112, 432), "caption: predictive coding + hashtags", 21, fill=TEXT, mono=True)
    text(d, (112, 500), "The app does not publish publicly.", 23, fill=YELLOW, bold=True)

    rounded(d, (730, 136, 1010, 654), 42, (8, 10, 16), outline=(65, 76, 96), width=4)
    rounded(d, (750, 164, 990, 626), 28, (18, 20, 28), outline=(34, 44, 66))
    text(d, (870, 202), "TikTok Inbox", 22, bold=True, anchor="mm")
    rounded(d, (776, 244, 964, 354), 16, PANEL_2, outline=(62, 82, 116))
    text(d, (870, 284), "VulgaScience draft", 20, bold=True, anchor="mm")
    text(d, (870, 318), "Ready to edit", 16, fill=GREEN, anchor="mm")
    rounded(d, (776, 390, 964, 434), 14, (37, 48, 66), outline=(72, 94, 126))
    text(d, (870, 412), "Add trending sound", 15, fill=CYAN, bold=True, anchor="mm")
    rounded(d, (776, 452, 964, 496), 14, (37, 48, 66), outline=(72, 94, 126))
    text(d, (870, 474), "Review cover", 15, fill=YELLOW, bold=True, anchor="mm")
    rounded(d, (776, 530, 964, 586), 18, BLUE)
    text(d, (870, 558), "Post manually", 18, bold=True, anchor="mm")


def scene_end(img, t):
    d = ImageDraw.Draw(img)
    draw_nav(img, "Review summary")
    rounded(d, (98, 184, 1182, 604), 26, PANEL, outline=(42, 60, 88))
    text(d, (144, 244), "Products and scopes demonstrated", 36, bold=True)
    rows = [
        ("Login Kit / OAuth", "User authorizes the app in sandbox", GREEN),
        ("Content Posting API", "Video uploaded to TikTok inbox", CYAN),
        ("video.upload", "Required for inbox upload", CYAN),
        ("user.info.basic", "Used only to identify the connected creator", YELLOW),
        ("video.publish", "Not used in this flow", RED),
    ]
    for i, (a, b, c) in enumerate(rows):
        y = 316 + i * 48
        d.ellipse((150, y - 10, 170, y + 10), fill=c)
        text(d, (190, y - 17), a, 23, bold=True)
        text(d, (480, y - 15), b, 21, fill=MUTED)
    text(d, (640, 566), "Final human validation happens inside TikTok before posting.", 25, fill=(195, 255, 222), bold=True, anchor="mm")


def make_frame(t):
    img = base_frame()
    d = ImageDraw.Draw(img)
    topbar(d)

    if t < 6:
        scene_intro(img, t)
    elif t < 12:
        scene_login(img, t)
    elif t < 20:
        scene_oauth(img, t)
    elif t < 34:
        scene_dashboard(img, t)
    elif t < 46:
        scene_upload(img, t)
    elif t < 56:
        scene_success(img, t)
    else:
        scene_end(img, t)

    draw_cursor(img, t)
    return np.array(img.convert("RGB"))


def write_submission_notes():
    notes = """# TikTok Developer review package

Upload these files in the app review page:

- `vulgascience_app_icon_1024.png` as app logo.
- `tiktok_developer_review_demo.mp4` as the demo video.

Recommended products/scopes for this review:

- Content Posting API
- Login/OAuth for authorization
- `video.upload`
- `user.info.basic`

Remove `video.publish` unless you also want direct public posting. The current product flow uploads the video to TikTok inbox, then the creator adds a sound, reviews the draft, and posts manually inside TikTok.

Suggested review note:

`VulgaScience Publisher is a local/web-assisted creator tool that generates an original vertical science video, validates audio/subtitles/format, then uses TikTok Content Posting API with the video.upload scope to upload the draft to the creator's TikTok inbox. The creator performs the final review, optional sound selection, cover choice, and manual posting in TikTok. The demo video shows OAuth authorization, granted scopes, video selection, quality checks, Content Posting API upload initialization, chunk upload, and TikTok inbox final review.`
"""
    (OUT / "submission_notes.md").write_text(notes, encoding="utf-8")


def main():
    save_logos()
    copy_concept()
    write_submission_notes()

    clip = VideoClip(make_frame, duration=62)
    clip.write_videofile(
        str(OUT / "tiktok_developer_review_demo.mp4"),
        fps=24,
        codec="libx264",
        audio=False,
        bitrate="1600k",
        preset="medium",
        threads=4,
        ffmpeg_params=["-pix_fmt", "yuv420p", "-movflags", "+faststart"],
        logger=None,
    )
    clip.close()


if __name__ == "__main__":
    main()

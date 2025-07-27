import uuid
import json
import subprocess
import requests
import os
from pyrogram import Client, filters

# تنظیمات ربات
api_id = 12345678      # api id
api_hash = ""    # api hash
bot_token = ""  # توکن ربات

app = Client("my_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# پسوندهای صدای قابل‌قبول
AUDIO_EXTS = ['mp3', 'm4a', 'aac', 'wav', 'flac', 'ogg']


def call_insta_api(link):

    url = f"https://vkrdownloader.xyz/server/?api_key=vkrdownloader&vkr={link}"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return None


def get_media_info(url):

    cmd = [
        'ffprobe', '-v', 'quiet',
        '-print_format', 'json',
        '-show_streams', '-show_format',
        '-analyzeduration', '3000000',
        '-probesize', '3000000',
        url
    ]
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=15)
        if res.returncode != 0:
            return None
        return json.loads(res.stdout)
    except:
        return None


def detect_file_type_and_resolution(info, ext):

    if not info or 'streams' not in info:
        if ext.lower() in AUDIO_EXTS:
            return "Audio", "Audio"
        return "Video", "Unknown"

    streams = info['streams']
    vs = [s for s in streams if s.get('codec_type') == 'video']
    as_ = [s for s in streams if s.get('codec_type') == 'audio']


    if not vs and as_:
        br = as_[0].get('bit_rate')
        if br:
            try:
                return "Audio", f"{int(int(br)/1000)}kbps"
            except:
                pass
        return "Audio", "Audio"


    if vs and not as_:
        w, h = vs[0].get('width'), vs[0].get('height')
        return "GIF", f"{w}x{h}" if w and h else "Unknown"


    if vs:
        w, h = vs[0].get('width'), vs[0].get('height')
        if w and h:
            return "Video", f"{w}x{h}"
    return "Video", "Unknown"


async def download_file(url, path, status_msg, label):

    await status_msg.edit_text(f"در حال دانلود {label}…")
    with requests.get(url, stream=True) as r:
        total = int(r.headers.get("content-length", 0))
        if total == 0:
            await status_msg.edit_text(f"خطا در دریافت اندازه‌ی {label}.")
            return False
        done = 0
        chunk = 1024 * 512
        with open(path, "wb") as f:
            for data in r.iter_content(chunk_size=chunk):
                f.write(data)
                done += len(data)
                perc = int(done * 100 / total)

                if perc % 10 == 0:
                    await status_msg.edit_text(f"{label}: {perc}%")
    return True


@app.on_message(filters.text)
async def insta_handler(client, message):
    link = message.text.strip()

    if "instagram.com" not in link:
        return

    status = await message.reply_text("در حال پردازش لینک…")
    api_res = call_insta_api(link)
    if not api_res or not api_res.get("data") or not api_res["data"].get("downloads"):
        return await status.edit_text("خطا در واکشی اطلاعات از API.")

    downloads = api_res["data"]["downloads"]


    video_items = []
    audio_items = []
    for item in downloads:
        url = item.get("url")
        ext = item.get("ext", "mp4").replace("_dash", "").lower()
        info = get_media_info(url)
        ftype, qual = detect_file_type_and_resolution(info, ext)
        if ftype == "Video" and "x" in qual:
            w, h = map(int, qual.split("x"))
            video_items.append((w*h, url))
        elif ftype == "Audio" and qual.endswith("kbps"):
            br = int(qual[:-4])
            audio_items.append((br, url))

    if not video_items or not audio_items:
        return await status.edit_text("رسانهٔ قابل دانلود یافت نشد.")


    best_video_url = max(video_items, key=lambda x: x[0])[1]
    best_audio_url = max(audio_items, key=lambda x: x[0])[1]


    vid_path = f"video_{uuid.uuid4().hex}.mp4"
    aud_path = f"audio_{uuid.uuid4().hex}.mp3"


    if not await download_file(best_video_url, vid_path, status, "ویدیو"):
        return
    if not await download_file(best_audio_url, aud_path, status, "صدا"):
        os.remove(vid_path)
        return


    await status.edit_text("در حال آپلود ویدیو…")
    await client.send_video(
        chat_id=message.chat.id,
        video=vid_path,
        reply_to_message_id=message.id
    )
    await status.edit_text("در حال آپلود صدا…")
    await client.send_audio(
        chat_id=message.chat.id,
        audio=aud_path,
        reply_to_message_id=message.id
    )


    os.remove(vid_path)
    os.remove(aud_path)
    await status.delete()


if __name__ == "__main__":
    app.run()

import requests
import uuid
import os
from pyrogram import Client, filters

# Created By @ImSoheilOfficial
api_id = "....." # api id
api_hash = "....." # api hash
bot_token = "......" # توکن ربات

app = Client("my_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)


def get_video_url(link):
    api_url = f"https://api.silohost.ir/api/api.php?link={link}"
    response = requests.get(api_url)
    if response.status_code == 200:
        data = response.json()
        if data.get('status') == True:
                if data['data'].get('status') == "redirect":
                    return data['data'].get('url')
                else:
                    print("Unexpected data status:", data['data'].get('status'))
    return None


@app.on_message(filters.text)
async def handle_message(client, message):
    link = message.text

    
    if link.startswith("https://www.instagram.com") or link.startswith("http://www.instagram.com"):
        reply_message = await message.reply_text("در حال پردازش لینک...\nلطفا منتظر بمانید!", reply_to_message_id=message.id)
        
        video_url = get_video_url(link)
        if video_url:
            
            file_name = f"video_{uuid.uuid4().hex}.mp4"

            
            chunk_size = 1024 * 500  
            with requests.get(video_url, stream=True) as r:
                total_size = int(r.headers.get('content-length', 0))
                if total_size == 0:
                    await reply_message.edit_text("مشکلی در دریافت اطلاعات اندازه ویدیو پیش آمده است.")
                    return

                downloaded_size = 0
                with open(file_name, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=chunk_size):
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        done = int(50 * downloaded_size / total_size)
                        if downloaded_size % (500 * 1024) == 0:  
                            await reply_message.edit_text(f"در حال دانلود ویدیو... {done}%")

            
            await reply_message.edit_text("دانلود کامل شد. در حال آپلود ویدیو...")
            await client.send_video(chat_id=message.chat.id, video=file_name, reply_to_message_id=message.id)

           
            os.remove(file_name)
        else:
            await reply_message.edit_text("مشکلی در دریافت ویدیو از لینک مورد نظر پیش آمده است.")
    
    else:
        pass

if __name__ == "__main__":
    app.run()

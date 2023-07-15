import os
import asyncio
import datetime
import aiogram
import cv2
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from config import TOKEN, CHAT_ID

bot_token = TOKEN
bot = aiogram.Bot(token=bot_token)
dp = aiogram.Dispatcher(bot)

motion_active = False
videos_dir = 'videos/'

lock_button = KeyboardButton('Lock')
unlock_button = KeyboardButton('Unlock')
drop_video_button = KeyboardButton('Drop Video')
drop_photo_button = KeyboardButton('Drop Photo')
keyboard = ReplyKeyboardMarkup(resize_keyboard=True).row(
    lock_button, unlock_button, drop_video_button, drop_photo_button
)

@dp.message_handler(commands=['start'])
async def start_handler(message: Message):
    print(f"user:{message.from_user.id}")
    
@dp.message_handler(lambda message: message.text == 'Lock')
async def lock_handler(message: Message):
    global motion_active
    motion_active = True
    await message.answer('Motion detection locked.')

@dp.message_handler(lambda message: message.text == 'Unlock')
async def unlock_handler(message: Message):
    global motion_active
    motion_active = False
    await message.answer('Motion detection unlocked.')

@dp.message_handler(lambda message: message.text == 'Drop Video')
async def drop_video_handler(message: Message):
    await message.answer('Recording video...')
    video_name = datetime.datetime.now().strftime('%d.%m.%Y.%H.%M.%S') + '.mp4'
    video_path = os.path.join(videos_dir, video_name)
    await record_video(video_path, duration=30)  # Record video for 30 seconds
    await message.answer('Video recorded.')
    if os.path.exists(video_path) and CHAT_ID:
        await bot.send_video(chat_id=CHAT_ID, video=open(video_path, 'rb'))
        os.remove(video_path)

@dp.message_handler(lambda message: message.text == 'Drop Photo')
async def drop_photo_handler(message: Message):
    await message.answer('Taking photo...')
    photo_name = datetime.datetime.now().strftime('%d.%m.%Y.%H.%M.%S') + '.jpg'
    photo_path = os.path.join(videos_dir, photo_name)
    await capture_photo(photo_path)
    if CHAT_ID:
        await bot.send_photo(chat_id=CHAT_ID, photo=open(photo_path, 'rb'))
    os.remove(photo_path)

async def motion_detection():
    while True:
        await asyncio.sleep(1)
        if motion_active:
            video_name = datetime.datetime.now().strftime('%d.%m.%Y.%H.%M.%S') + '.mp4'
            video_path = os.path.join(videos_dir, video_name)
            await record_video(video_path, duration=30)
            if os.path.exists(video_path) and CHAT_ID:
                await bot.send_video(chat_id=CHAT_ID, video=open(video_path, 'rb'))
                os.remove(video_path)

async def record_video(output_path, duration):
    capture = cv2.VideoCapture(0)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, 20.0, (640, 480))

    start_time = datetime.datetime.now()
    while (datetime.datetime.now() - start_time).seconds < duration:
        ret, frame = capture.read()
        if ret:
            out.write(frame)

    capture.release()
    out.release()

async def capture_photo(output_path):
    capture = cv2.VideoCapture(0)
    ret, frame = capture.read()
    if ret:
        cv2.imwrite(output_path, frame)

    capture.release()

async def start_motion_detection():
    while True:
        await motion_detection()

async def main():
    os.makedirs(videos_dir, exist_ok=True)
    asyncio.create_task(start_motion_detection())
    if CHAT_ID:
        try:
            await bot.send_message(chat_id=CHAT_ID, text='Bot started', reply_markup=keyboard)
        except aiogram.utils.exceptions.ChatNotFound:
            print(f"Chat ID {CHAT_ID} is not valid. Bot started without sending the initial message.")
    else:
        print("No valid Chat ID provided. Bot started without sending the initial message.")
    await dp.start_polling()

if __name__ == '__main__':
    asyncio.run(main())

import os
import asyncio
import json
import requests
import websockets
import openai

from misskey import Misskey

TOKEN = os.environ['MISS_KEY']
api = Misskey('misskey.neos.love', i=TOKEN)
MY_ID = api.i()['id']
WS_URL = 'wss://misskey.neos.love/streaming?i=' + TOKEN
openai.api_key = os.environ["OPENAI_API_KEY"]

promptCache = ''

print("ORANGE AI INIT")


def update_prompt():
    try:
        global promptCache
        URL = "https://script.googleusercontent.com/macros/echo?user_content_key=mbLWIiqcBzXW7eQD1QDMzn5g6s4w9I8jygodjuK55U3yXzfMuMFp3TbsgIkqEz77sOmBMf5X5cSGn_DbEOHsdp4-6mgUMb4pm5_BxDlH2jW0nuo2oDemN9CCS2h10ox_1xSncGQajx_ryfhECjZEnLTsv47l6UqMICpTZmGaB0qM2hj85kz50yrA8gxf5hBaF7abmW5_3xXlTbCBNGfIl2qMHmbzOmsDhOkHKZJo9zEE-JKdvrdyItz9Jw9Md8uu&lib=Mv2XLQz63jRhLbNOfAuwx_LqhQws80kCz"
        r = requests.get(URL)
        promptCache = r.text
        print('prompt updated')
    except:
        print('prompt update failed')


# update prompt every 1 min
update_prompt()
loop = asyncio.get_event_loop()
loop.call_later(60, update_prompt)


def make_reply(text):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": promptCache},
            {"role": "user", "content": text},
        ],
    )
    return response.choices[0].message.content

ws = None

async def runner():
    global ws
    async with websockets.connect(WS_URL) as wss:
        ws = wss
        await ws.send(json.dumps({
            "type": "connect",
            "body": {
                "channel": "localTimeline",
                "id": "test"
            }}))
        while True:
            data = json.loads(await ws.recv())
            if data['type'] == 'channel':
                if data['body']['type'] == 'note':
                    note = data['body']['body']
                    print("note")
                    await on_note(note)

# ws send ping every 30 sec
async def ping():
    while True:
        await asyncio.sleep(30)
        await ws.send(json.dumps({"type": "ping"}))
        print('ping')

asyncio.get_event_loop().create_task(ping())


async def on_note(note):
    if note.get('mentions'):
        if MY_ID in note['mentions']:
            if note["user"]["host"] is None:
                text = note['text']
                reply = make_reply(text)
                api.notes_create(text=reply, reply_id=note['id'])
            else:
                print('not local note')


asyncio.get_event_loop().run_until_complete(runner())

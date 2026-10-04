"""Phone channel: Twilio routes the call, all speech and decision work runs on this laptop.

Needs env vars TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN and PUBLIC_URL (the public tunnel https URL).
If TWILIO_PHONE_NUMBER is set, its voice webhook is pointed at {PUBLIC_URL}/voice on start.
Run: python -m coop_assistant.apps.call_server   (scripts/start_call.ps1 does all of this)
"""

import asyncio
import base64
import hashlib
import hmac
import json
import os
import pathlib
import re
import shutil
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse

from coop_assistant.core.responses import T
from coop_assistant.core.store import connect
from coop_assistant.nlu import business_qa
from coop_assistant.pipeline import Assistant
from coop_assistant.speech import voice

SID = os.environ["TWILIO_ACCOUNT_SID"]
TOKEN = os.environ["TWILIO_AUTH_TOKEN"]
PUBLIC_URL = os.environ["PUBLIC_URL"].rstrip("/")
AUTH = "Basic " + base64.b64encode(f"{SID}:{TOKEN}".encode()).decode()

AUDIO_DIR = pathlib.Path(tempfile.mkdtemp(prefix="coffee-call-"))
CONN = connect()
WORK_LOCK = threading.Lock()
calls = {}
jobs = {}

PROMPTS = {
    "greeting": "Hi, thanks for calling Demo Co-op Nyeri. I'm Relay, the co-op's assistant. "
                "This is a demo line, so all information is sample data. "
                "You can ask me anything about the co-op, or check a buyer's coffee price, in your own language. "
                "Go ahead after the beep. And if you'd like a person, just press zero.",
    "hold": "Sure, give me a moment.",
    "again": "Anything else I can help with? Go ahead after the beep.",
    "bye": "Thanks for calling. Have a great day!",
    "error": "Sorry, I didn't quite get that. Could you try again?",
}

app = FastAPI()


def _save_tts(text, lang, name=None):
    src, _ = voice.speak(text, lang)
    if src is None:
        src, _ = voice.speak(text, "en")
    name = name or f"{uuid.uuid4().hex}.wav"
    shutil.move(src, AUDIO_DIR / name)
    return name


def _play(name):
    return f"<Play>{PUBLIC_URL}/audio/{name}</Play>"


RECORD = (f'<Record action="{PUBLIC_URL}/turn" method="POST" maxLength="20" timeout="3" '
          f'playBeep="true" finishOnKey="0#" trim="trim-silence"/>')
END = _play("bye.wav") + "<Hangup/>"


def _twiml(*parts):
    body = '<?xml version="1.0" encoding="UTF-8"?><Response>' + "".join(parts) + "</Response>"
    return Response(body, media_type="application/xml")


async def _verified_form(request):
    form = {k: str(v) for k, v in (await request.form()).items()}
    url = PUBLIC_URL + request.url.path + (f"?{request.url.query}" if request.url.query else "")
    payload = url + "".join(k + form[k] for k in sorted(form))
    expected = base64.b64encode(hmac.new(TOKEN.encode(), payload.encode(), hashlib.sha1).digest()).decode()
    if not hmac.compare_digest(expected, request.headers.get("X-Twilio-Signature", "")):
        raise HTTPException(403, "bad signature")
    return form


def _download(url):
    req = urllib.request.Request(url + ".wav", headers={"Authorization": AUTH})
    for _ in range(10):
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                path = AUDIO_DIR / f"in-{uuid.uuid4().hex}.wav"
                path.write_bytes(resp.read())
                return path
        except urllib.error.HTTPError as e:
            if e.code != 404:
                raise
            time.sleep(0.5)
    raise RuntimeError("recording not available")


def _delete_remote(url):
    try:
        req = urllib.request.Request(url + ".json", method="DELETE", headers={"Authorization": AUTH})
        urllib.request.urlopen(req, timeout=10).close()
    except OSError as e:
        print("could not delete recording:", e)


def _process(job, bot, recording_url):
    try:
        path = _download(recording_url)
        _delete_remote(recording_url)
        with WORK_LOCK:
            text, lang, _ = voice.transcribe(str(path))
            path.unlink(missing_ok=True)
            result = bot.handle(text, lang)
            reply = _save_tts(result["reply"], result["lang"])
        state = result["decision"]["state"]
        print(f"[{job[:6]}] heard ({result['lang']}): {text!r} -> {state}")
        jobs[job] = _twiml(_play(reply), END) if state == "REFER" else _twiml(_play(reply), _play("again.wav"), RECORD, END)
    except Exception as e:
        print(f"[{job[:6]}] failed: {e!r}")
        jobs[job] = _twiml(_play("error.wav"), RECORD, END)


for _key, _text in PROMPTS.items():
    _save_tts(_text, "en", f"{_key}.wav")
voice.transcribe(str(AUDIO_DIR / "hold.wav"))  # load models before the first caller waits on them
business_qa.answer("What are your opening hours?", "en")


@app.post("/voice")
async def incoming(request: Request):
    form = await _verified_form(request)
    calls[form["CallSid"]] = Assistant(CONN)
    return _twiml(_play("greeting.wav"), RECORD, END)


@app.post("/turn")
async def turn(request: Request):
    form = await _verified_form(request)
    bot = calls.setdefault(form["CallSid"], Assistant(CONN))
    if form.get("Digits") == "0":
        return _twiml(_play(_save_tts(T["en"]["human_requested"], "en")), END)
    if not form.get("RecordingUrl"):
        return _twiml(_play("again.wav"), RECORD, END)
    job = uuid.uuid4().hex
    jobs[job] = None
    threading.Thread(target=_process, args=(job, bot, form["RecordingUrl"]), daemon=True).start()
    return _twiml(_play("hold.wav"), f'<Redirect method="POST">{PUBLIC_URL}/result/{job}</Redirect>')


@app.post("/result/{job}")
async def result(job: str, request: Request):
    await _verified_form(request)
    if job not in jobs:
        raise HTTPException(404)
    for _ in range(20):
        if jobs[job] is not None:
            return jobs.pop(job)
        await asyncio.sleep(0.5)
    return _twiml('<Pause length="1"/>', f'<Redirect method="POST">{PUBLIC_URL}/result/{job}</Redirect>')


@app.get("/audio/{name}")
def audio(name: str):
    if not re.fullmatch(r"[a-z0-9_-]+\.wav", name) or not (AUDIO_DIR / name).exists():
        raise HTTPException(404)
    return FileResponse(AUDIO_DIR / name, media_type="audio/wav")


def _point_number_here(number):
    api = f"https://api.twilio.com/2010-04-01/Accounts/{SID}/IncomingPhoneNumbers"
    query = urllib.parse.urlencode({"PhoneNumber": number})
    with urllib.request.urlopen(urllib.request.Request(f"{api}.json?{query}", headers={"Authorization": AUTH})) as r:
        found = json.load(r)["incoming_phone_numbers"]
    if not found:
        print(f"{number} is not in this Twilio account. Set the webhook manually to {PUBLIC_URL}/voice (HTTP POST)")
        return
    data = urllib.parse.urlencode({"VoiceUrl": f"{PUBLIC_URL}/voice", "VoiceMethod": "POST"}).encode()
    urllib.request.urlopen(urllib.request.Request(f"{api}/{found[0]['sid']}.json", data,
                                                  headers={"Authorization": AUTH})).close()
    print(f"{number} now rings this laptop via {PUBLIC_URL}/voice")


def main():
    import uvicorn
    if os.environ.get("TWILIO_PHONE_NUMBER"):
        _point_number_here(os.environ["TWILIO_PHONE_NUMBER"])
    else:
        print("call server ready; set the Twilio webhook to", f"{PUBLIC_URL}/voice")
    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()

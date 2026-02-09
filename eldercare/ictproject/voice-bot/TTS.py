import datetime
import json
import base64
import hashlib
import hmac
import wave
import websocket
from websocket import create_connection
from urllib.parse import urlencode
from wsgiref.handlers import format_date_time
from time import mktime
import ssl
from config import *


class XunfeiTTS:
    def __init__(self, appid, api_key, api_secret):
        self.appid = appid
        self.api_key = api_key
        self.api_secret = api_secret
        self.tts_url = "wss://tts-api.xfyun.cn/v2/tts"

    def create_auth_url(self):
        now = datetime.datetime.now()
        date = format_date_time(mktime(now.timetuple()))
        signature_origin = f"host: ws-api.xfyun.cn\ndate: {date}\nGET /v2/tts HTTP/1.1"
        signature_sha = hmac.new(
            self.api_secret.encode('utf-8'),
            signature_origin.encode('utf-8'),
            hashlib.sha256
        ).digest()
        signature = base64.b64encode(signature_sha).decode()
        authorization = base64.b64encode(
            f'api_key="{self.api_key}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature}"'.encode()
        ).decode()
        return f"{self.tts_url}?{urlencode({'authorization': authorization, 'date': date, 'host': 'ws-api.xfyun.cn'})}"

    def synthesize(self, text, output_file="temp_tts.wav"):
        if not text.strip():
            print("TTS无有效文本")
            return None
        data = {
            "common": {"app_id": self.appid},
            "business": {"aue": "raw", "auf": "audio/L16;rate=16000", "vcn": "x4_yezi",
                         "speed": 40, "volume": 80, "tte": "utf8"},
            "data": {"status": 2, "text": base64.b64encode(text.encode('utf-8')).decode()}
        }
        try:
            ws = create_connection(self.create_auth_url(), sslopt={"cert_reqs": ssl.CERT_NONE})
            ws.send(json.dumps(data))
            audio_chunks = []
            while True:
                res = json.loads(ws.recv())
                if res.get("code") != 0:
                    print(f"TTS错误：{res.get('message')}（错误码{res.get('code')}）")
                    ws.close()
                    return None
                if "data" in res and "audio" in res["data"]:
                    audio_chunks.append(base64.b64decode(res["data"]["audio"]))
                if res.get("data", {}).get("status") == 2:
                    ws.close()
                    break
            with wave.open(output_file, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                wf.writeframes(b''.join(audio_chunks))
            return output_file
        except Exception as e:
            print(f"TTS合成失败：{str(e)}")
            return None
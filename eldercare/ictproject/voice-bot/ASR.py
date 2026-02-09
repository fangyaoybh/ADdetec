import time
import json
import base64
import hashlib
import hmac
import websocket
from websocket import create_connection
from urllib.parse import quote
import ssl
import threading
import re
from config import *


class XunfeiRTASR:
    def __init__(self, app_id, api_key):
        self.app_id = app_id
        self.api_key = api_key
        self.rtasr_ws_url = "wss://rtasr.xfyun.cn/v1/ws"
        self.ws = None
        self.recv_thread = None
        self.recognize_result = ""
        self.is_finished = False

    def get_auth_url(self):
        ts = str(int(time.time()))
        tt = (self.app_id + ts).encode('utf-8')
        md5 = hashlib.md5()
        md5.update(tt)
        base_string = md5.hexdigest().encode('utf-8')
        signa = hmac.new(self.api_key.encode('utf-8'), base_string, hashlib.sha1).digest()
        signa = base64.b64encode(signa).decode('utf-8')
        auth_params = (
            f"appid={self.app_id}&ts={ts}&signa={quote(signa)}"
            f"&vad_enable=1&vad_threshold=4&vad_pause=800&speech_timeout=5000"
        )
        return f"{self.rtasr_ws_url}?{auth_params}"

    def _recv_result(self):
        try:
            while self.ws.connected and not self.is_finished:
                result = self.ws.recv()
                if not result:
                    break
                result_dict = json.loads(result)
                if result_dict["action"] == "result":
                    try:
                        data_json = json.loads(result_dict["data"])
                        rt_list = data_json.get("cn", {}).get("st", {}).get("rt", [])
                        if rt_list:
                            for ws_item in rt_list[0].get("ws", []):
                                for cw_item in ws_item.get("cw", []):
                                    self.recognize_result += cw_item.get("w", "")
                    except Exception as e:
                        self.recognize_result += result_dict["data"]
                        print(f"ASR解析失败：{str(e)}")
                elif result_dict["action"] == "error":
                    print(f"ASR错误：{result_dict.get('message', '未知错误')}")
                    self.ws.close()
                    break
        except websocket.WebSocketConnectionClosedException:
            pass
        finally:
            self.is_finished = True

    def _clean_recognize_text(self, text):
        if not text.strip():
            return "没听清，请再说一次"
        text = re.sub(r'(\w\w)\1+', r'\1', text)
        text = re.sub(r'(\w)\1+', r'\1', text)
        repeat_patterns = [r'你感觉你感觉', r'你觉得你觉得', r'天气天气', r'夏天夏天', r'春天春天']
        for pattern in repeat_patterns:
            half_length = len(pattern) // 2
            text = re.sub(pattern, pattern[:half_length], text)
        redundant_patterns = [r'这能', r'给能', r'你能', r'这会', r'你会', r'能个', r'给个', r'会个']
        for pattern in redundant_patterns:
            text = re.sub(pattern, lambda m: m.group(0)[1:], text)
        error_correction = {"推出": "退出", "退岀": "退出", "讲个笑": "讲个笑话", "天汽": "天气", "气天": "天气"}
        for wrong, right in error_correction.items():
            text = text.replace(wrong, right)
        if text.strip() and text.strip()[-1] not in {"。", "？", "！"}:
            if "吗" in text or "怎么" in text or "什么" in text:
                text += "？"
            else:
                text += "。"
        return text.strip()

    def recognize(self, audio_file):
        self.recognize_result = ""
        self.is_finished = False
        try:
            self.ws = create_connection(self.get_auth_url(), sslopt={"cert_reqs": ssl.CERT_NONE})
            self.recv_thread = threading.Thread(target=self._recv_result)
            self.recv_thread.start()

            with open(audio_file, 'rb') as f:
                while chunk := f.read(1280):
                    self.ws.send(chunk)
                    time.sleep(0.04)
            self.ws.send(json.dumps({"end": True}).encode('utf-8'))

            self.recv_thread.join(timeout=10)
            self.ws.close()

            return self._clean_recognize_text(self.recognize_result) or "没听清，请再说一次"
        except Exception as e:
            print(f"ASR识别失败：{str(e)}")
            if self.ws:
                self.ws.close()
            return "语音识别服务连接失败"

    def recognize_short_audio(self, audio_file):
        self.recognize_result = ""
        self.is_finished = False
        try:
            self.ws = create_connection(self.get_auth_url(), sslopt={"cert_reqs": ssl.CERT_NONE})
            self.recv_thread = threading.Thread(target=self._recv_result)
            self.recv_thread.start()

            with open(audio_file, 'rb') as f:
                audio_data = f.read()
                self.ws.send(audio_data)
            self.ws.send(json.dumps({"end": True}).encode('utf-8'))

            self.recv_thread.join(timeout=3)
            self.ws.close()
            return self._clean_recognize_text(self.recognize_result).strip()
        except Exception as e:
            print(f"短语音识别失败：{str(e)}")
            if self.ws:
                self.ws.close()
            return ""

    def record_audio_dynamic(self, audio, silence_threshold=SILENCE_THRESHOLD, min_duration=MIN_RECORD_DURATION):
        import webrtcvad
        vad = webrtcvad.Vad(VAD_MODE)
        frame_duration_ms = FRAME_DURATION_MS
        frame_samples = FRAME_SAMPLES
        silence_frames = int(silence_threshold / frame_duration_ms)
        min_frames = int(min_duration / frame_duration_ms)

        stream = audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=frame_samples
        )

        audio_frames = []
        current_silence_frames = 0
        recording_started = False
        temp_file = "temp_asr_dynamic.pcm"

        print("\n请说您的需求...（停顿超1.5秒自动结束）")
        try:
            while True:
                frame = stream.read(frame_samples)
                is_speech = vad.is_speech(frame, RATE)

                if is_speech:
                    audio_frames.append(frame)
                    current_silence_frames = 0
                    recording_started = True
                else:
                    if recording_started:
                        current_silence_frames += 1
                        if current_silence_frames >= silence_frames:
                            if len(audio_frames) < min_frames:
                                print("录音时长过短，未保存")
                                return None
                            with open(temp_file, "wb") as f:
                                f.write(b''.join(audio_frames))
                            print("录音结束，正在识别...")
                            return temp_file
                    else:
                        continue
        except Exception as e:
            print(f"动态录音失败：{str(e)}")
            return None
        finally:
            stream.stop_stream()
            stream.close()
import time
import pyaudio
import os
import sys
import re  # 用于文本去重的正则处理
from ASR import XunfeiRTASR
from TTS import XunfeiTTS
from LLM import SparkProLLM
# from wakeup import WakeupSDK, WakeupCallback  # 已移除唤醒功能依赖
from utils import play_audio, clean_temp_files
from config import *


class PCVoiceAssistant:
    def __init__(self, cloud_uploader=None):
        self.cloud_uploader = cloud_uploader
        self.running = True
        self.wakeup_triggered = False
        self.audio = pyaudio.PyAudio()
        self.is_windows = sys.platform.startswith('win')  # 判断是否为Windows系统

        # 初始化各模块（非唤醒相关模块正常初始化）
        self.asr = XunfeiRTASR(XUNFEI_APPID, XUNFEI_RTASR_API_KEY)
        self.tts = XunfeiTTS(XUNFEI_APPID, XUNFEI_TTS_API_KEY, XUNFEI_TTS_API_SECRET)
        self.spark = SparkProLLM(
            appid=XUNFEI_APPID,
            api_key=SPARK_PRO_API_KEY,
            api_secret=SPARK_PRO_API_SECRET,
            spark_url=SPARK_PRO_URL,
            domain=SPARK_PRO_DOMAIN
        )

        # 初始化唤醒SDK（已移除唤醒功能）
        self.wakeup_sdk = None
        self.audio_stream = None
        # 直接模拟唤醒触发，进入对话流程
        print("唤醒功能已移除，直接进入对话流程～")
        self.wakeup_triggered = True  # 模拟唤醒已触发

    def _optimize_recognized_text(self, recognized_text):
        """
        优化识别结果：去除所有重复内容，只保留最后一个完整识别的句子
        :param recognized_text: 原始ASR识别结果（可能含重复）
        :return: 去重后的最后一个完整句子
        """
        if not recognized_text.strip():
            return recognized_text

        # 1. 逐步去除连续和非连续重复片段
        text = recognized_text.strip()
        
        # 增强的去重算法：从长到短检查重复子串
        for length in range(min(20, len(text)//2), 2, -1):  # 从最长20字符到3字符检查
            for i in range(len(text) - length):
                substring = text[i:i+length]
                # 查找子串在剩余文本中的重复
                remaining_text = text[i+length:]
                if substring in remaining_text:
                    # 去除从i开始到剩余文本中第一次出现substring后的重复部分
                    start_idx = i
                    end_idx = i + length + remaining_text.find(substring)
                    text = text[:start_idx] + text[end_idx:]
                    # 重新开始检查，因为文本已经改变
                    break
            else:
                # 没有找到该长度的重复，继续检查更短的长度
                continue
            # 找到了重复并删除，重新从最长长度开始检查
            continue
        
        # 2. 针对常见的口语重复模式进行特殊处理
        # 如"最近天变冷了要感觉最近天变冷了" -> "最近天变冷了"
        text = re.sub(r'([^。，！？]{3,})[，,](要|感觉|想|是)[^。，！？]*?\1', r'\1', text)
        text = re.sub(r'([^。，！？]{3,})([^。，！？]*?)\1', r'\1', text)
        
        # 3. 按标点分割句子，提取所有可能的句子
        sentences = []
        current_sentence = ""
        
        for char in text:
            current_sentence += char
            # 遇到结束标点时保存句子
            if char in ["。", "！", "？", ".", "!", "?"]:
                clean_sentence = current_sentence.strip()
                if clean_sentence and len(re.sub(r'[。，！？.!,?]', '', clean_sentence)) >= 3:  # 提高最小长度要求
                    sentences.append(clean_sentence)
                current_sentence = ""
        
        # 4. 如果有句子，返回最后一个；如果没有，尝试从文本末尾提取有意义的部分
        if sentences:
            # 对最后一个句子再次进行去重检查
            last_sentence = sentences[-1]
            # 进一步清理句子内的重复
            last_sentence = re.sub(r'([^。，！？]{2,})\1+', r'\1', last_sentence)
            return last_sentence
        else:
            # 没有明显的句子边界，尝试从文本末尾提取最可能完整的内容
            # 查找最后一个逗号或句号后的内容
            last_comma_idx = max(text.rfind('，'), text.rfind(','))
            if last_comma_idx != -1:
                # 提取逗号后的内容
                candidate = text[last_comma_idx+1:].strip()
                if len(re.sub(r'[。，！？.!,?]', '', candidate)) >= 3:
                    return candidate
            # 如果没有找到合适的候选，返回去重后的整个文本
            return text.strip()

    def start_conversation(self):
        """主对话循环"""
        while self.running:
            if self.wakeup_triggered:
                self.wakeup_triggered = False
                self._speak("我在呢，有啥想问的都能跟我说～")

                # 动态录音
                audio_file = self.asr.record_audio_dynamic(self.audio)
                if not audio_file:
                    self._speak("没听到您的声音，有需要再叫我哦～")
                    # Windows下：如果没录音，再次模拟唤醒（方便重复测试）
                    if self.is_windows:
                        self.wakeup_triggered = True
                    continue

                # ASR转文字 + 文本去重优化
                raw_user_text = self.asr.recognize(audio_file)
                user_text = self._optimize_recognized_text(raw_user_text)  # 调用修改后的优化函数
                # 打印原始与优化后的对比（方便调试）
                if raw_user_text != user_text:
                    print(f"\n原始识别：{raw_user_text}")
                    print(f"优化后：{user_text}")
                else:
                    print(f"\n你说：{user_text}")

                # 结束对话
                if "再见" in user_text:
                    self._speak("再见啦，有需要再找我哦！")
                    self.running = False
                    break

                # 生成回复
                print("助手回复：", end="")
                assistant_text = self.spark.get_response(user_text)
                print(f"\n")

                # 保存到云（仅OBS，删除RDS相关逻辑）
                if self.cloud_uploader:
                    self._save_to_cloud(user_text, assistant_text)

                # 播放回复并清理
                self._speak(assistant_text)
                clean_temp_files(audio_file)

                # Windows下：对话结束后再次模拟唤醒（方便连续测试）
                if self.is_windows:
                    self.wakeup_triggered = True
            time.sleep(WAKE_LISTEN_INTERVAL)

    def _speak(self, text):
        """语音合成并播放"""
        if not text or not text.strip():
            text = "我没太理解，你再说说呗～"
        tts_file = self.tts.synthesize(text)
        if tts_file:
            play_audio(tts_file, self.audio)
            clean_temp_files(tts_file)
        else:
            print("TTS合成失败，无法播放语音")
            # 可以在这里添加默认的错误提示音或者文本播放

    def _save_to_cloud(self, user_text, assistant_text):
        """仅保留OBS存储"""
        try:
            # 上传对话文本到OBS
            dialog_success, dialog_url = self.cloud_uploader.save_conversation(
                device_sn=DEVICE_SN,
                user_text=user_text,
                assistant_text=assistant_text
            )
            if dialog_success:
                print(f"对话文本已上传OBS：URL={dialog_url}")
        except Exception as e:
            print(f"华为云OBS存储失败：{str(e)}")

    def close(self):
        """释放资源（已移除唤醒功能依赖）"""
        self.running = False
        # 已移除唤醒SDK相关代码
        # 仅在音频流已创建时关闭
        if self.audio_stream:
            self.audio_stream.stop_stream()
            self.audio_stream.close()
        self.audio.terminate()
        print("语音助手资源已释放")
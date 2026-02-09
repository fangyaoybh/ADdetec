import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from TTS import XunfeiTTS
from config import XUNFEI_APPID, XUNFEI_TTS_API_KEY, XUNFEI_TTS_API_SECRET

def test_tts():
    print("初始化TTS服务...")
    tts = XunfeiTTS(XUNFEI_APPID, XUNFEI_TTS_API_KEY, XUNFEI_TTS_API_SECRET)
    
    # 测试文本
    test_texts = [
        "你好，世界！",
        "今天天气怎么样？",
        "",  # 空文本测试
        None  # None值测试
    ]
    
    for i, text in enumerate(test_texts):
        print(f"\n测试 {i+1}: {repr(text)}")
        try:
            if text is None:
                print("跳过None值测试")
                continue
                
            result = tts.synthesize(text, f"test_output_{i+1}.wav")
            if result:
                print(f"合成成功: {result}")
            else:
                print("合成失败，返回None")
        except Exception as e:
            print(f"合成出错: {e}")

if __name__ == "__main__":
    test_tts()
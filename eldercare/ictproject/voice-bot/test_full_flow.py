import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from TTS import XunfeiTTS
from LLM import SparkProLLM
from config import *

def test_full_flow():
    print("=== 测试完整流程 ===")
    
    # 初始化TTS
    tts = XunfeiTTS(XUNFEI_APPID, XUNFEI_TTS_API_KEY, XUNFEI_TTS_API_SECRET)
    
    # 初始化LLM
    llm = SparkProLLM(
        appid=XUNFEI_APPID,
        api_key=SPARK_PRO_API_KEY,
        api_secret=SPARK_PRO_API_SECRET,
        spark_url=SPARK_PRO_URL,
        domain=SPARK_PRO_DOMAIN
    )
    
    # 测试用例
    test_cases = [
        "你好",
        "今天天气怎么样？",
        "讲个笑话吧",
        ""  # 空输入
    ]
    
    for i, user_input in enumerate(test_cases):
        print(f"\n--- 测试用例 {i+1}: '{user_input}' ---")
        
        # 获取LLM响应
        try:
            if user_input == "":
                assistant_text = "我没太理解，你再说说呗～"
            else:
                print("正在获取LLM响应...")
                assistant_text = llm.get_response(user_input)
            
            print(f"LLM响应: {repr(assistant_text)}")
            
            # 检查响应是否为None或空
            if assistant_text is None:
                print("警告: LLM返回了None")
                assistant_text = "我没太理解，你再说说呗～"
            elif not assistant_text.strip():
                print("警告: LLM返回了空文本")
                assistant_text = "我没太理解，你再说说呗～"
                
            # TTS合成
            print("正在进行TTS合成...")
            tts_result = tts.synthesize(assistant_text, f"full_test_{i+1}.wav")
            
            if tts_result:
                print(f"TTS合成成功: {tts_result}")
            else:
                print("TTS合成失败，返回None")
                
        except Exception as e:
            print(f"测试过程中出错: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_full_flow()
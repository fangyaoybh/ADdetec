#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
同时启动语音助手主程序和API服务的脚本
此脚本使用多进程技术同时运行两个独立的服务
"""

import multiprocessing
import subprocess
import sys
import os
import time
import signal
import socket

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def is_port_in_use(port):
    """检查端口是否被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            # 设置超时时间
            s.settimeout(1)
            # 尝试连接到端口，如果能连接说明端口被占用
            result = s.connect_ex(('127.0.0.1', port))
            return result == 0
        except Exception:
            # 如果连接出错，尝试绑定端口来检查
            try:
                s.bind(('127.0.0.1', port))
                s.close()
                return False
            except OSError:
                return True

def run_main_program():
    """运行语音助手主程序"""
    try:
        print("正在启动语音助手主程序...")
        # 直接执行main.py文件而不是导入main函数
        from core import PCVoiceAssistant
        from config import SPARK_PRO_API_KEY, SPARK_PRO_API_SECRET

        # 导入华为云整合类（仅保留 OBS 相关，支持可选启用）
        try:
            from cloud_uploader import HuaweiCloudUploader
            CLOUD_MODULE_AVAILABLE = True  # 标记华为云（OBS）模块是否可用
        except ImportError:
            CLOUD_MODULE_AVAILABLE = False  # 未找到云模块时，默认不启用

        # ------------------- 1. 校验 Spark Pro API 密钥 -------------------
        if not SPARK_PRO_API_KEY or not SPARK_PRO_API_SECRET:
            print("错误：请先在 config.py 中填写 Spark Pro 的 API Key 和 API Secret！")
            print("获取地址：https://console.xfyun.cn/services/bm35")
            return

        # ------------------- 2. 华为云（OBS）功能开关 -------------------
        USE_CLOUD_UPLOAD = True  # 启用 OBS 功能
        cloud_uploader = None

        try:
            # ------------------- 3. 初始化华为云 OBS 模块 -------------------
            if USE_CLOUD_UPLOAD and CLOUD_MODULE_AVAILABLE:
                print("\n正在初始化华为云 OBS 模块...")
                cloud_uploader = HuaweiCloudUploader()
                # OBS 状态提示
                cloud_status = ["OBS（文本上传）就绪" if cloud_uploader.obs_ready else "OBS（文本上传）未就绪（文本不上传）"]
                print(f"华为云模块状态：{', '.join(cloud_status)}")
            elif USE_CLOUD_UPLOAD and not CLOUD_MODULE_AVAILABLE:
                print("\n提示：未找到华为云 OBS 相关文件，自动禁用云功能")
                USE_CLOUD_UPLOAD = False
            else:
                print("\n已禁用华为云 OBS 功能")

            # ------------------- 4. 初始化语音助手（跳过唤醒功能） -------------------
            print("\n正在初始化语音助手...")
            assistant = PCVoiceAssistant(cloud_uploader=cloud_uploader)
            # 移除唤醒词提示（因跳过唤醒功能）
            print("\n语音助手启动成功！说「再见」可结束对话\n")
            # 直接进入对话流程（不依赖唤醒词）
            assistant.start_conversation()

        # ------------------- 5. 异常处理 -------------------
        except KeyboardInterrupt:
            print("\n程序已手动停止（Ctrl+C）")
        except Exception as e:
            print(f"\n程序运行错误：{str(e)}")
        finally:
            # ------------------- 6. 资源释放 -------------------
            print("\n正在释放资源...")
            if 'assistant' in locals():
                assistant.close()
            if 'cloud_uploader' in locals() and cloud_uploader is not None:
                cloud_uploader.close()
            print("所有资源已释放，程序退出")
    except Exception as e:
        print(f"语音助手主程序运行出错: {e}")
        raise

def run_api_service():
    """运行API服务"""
    try:
        print("正在启动API服务...")
        # 使用subprocess运行API服务并传递端口参数
        import subprocess
        import sys
        
        # 检查端口是否可用，如果不可用则尝试其他端口
        port = 9002
        while is_port_in_use(port):
            print(f"端口 {port} 已被占用，尝试端口 {port + 1}")
            port += 1
            if port > 9010:  # 限制端口范围
                print("无法找到可用端口，请手动释放端口 9002-9010")
                return
        
        if port != 9002:
            print(f"API服务将在端口 {port} 上运行")
        
        # 使用subprocess运行API服务
        api_script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'api', 'api_service.py')
        subprocess.run([sys.executable, api_script_path, str(port)])
    except Exception as e:
        print(f"API服务运行出错: {e}")
        raise

def signal_handler(sig, frame):
    """信号处理函数，用于优雅关闭所有进程"""
    print("\n正在关闭所有服务...")
    sys.exit(0)

def main():
    """主函数：同时启动两个服务"""
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 创建两个进程
    main_process = multiprocessing.Process(target=run_main_program)
    api_process = multiprocessing.Process(target=run_api_service)
    
    # 启动进程
    print("正在启动语音助手主程序和API服务...")
    main_process.start()
    api_process.start()
    
    print(f"语音助手主程序进程ID: {main_process.pid}")
    print(f"API服务进程ID: {api_process.pid}")
    print("两个服务均已启动，按 Ctrl+C 可以同时关闭它们")
    
    try:
        # 等待任意一个进程结束
        while True:
            if not main_process.is_alive() and not api_process.is_alive():
                print("两个服务都已结束")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n收到中断信号，正在关闭所有服务...")
    finally:
        # 确保所有进程都被终止
        if main_process.is_alive():
            main_process.terminate()
            main_process.join(timeout=5)
            if main_process.is_alive():
                main_process.kill()
                
        if api_process.is_alive():
            api_process.terminate()
            api_process.join(timeout=5)
            if api_process.is_alive():
                api_process.kill()
        
        print("所有服务已关闭")

if __name__ == "__main__":
    main()
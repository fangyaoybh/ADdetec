from core import PCVoiceAssistant
from config import SPARK_PRO_API_KEY, SPARK_PRO_API_SECRET

# 导入华为云整合类（仅保留 OBS 相关，支持可选启用）
try:
    from cloud_uploader import HuaweiCloudUploader
    CLOUD_MODULE_AVAILABLE = True  # 标记华为云（OBS）模块是否可用
except ImportError:
    CLOUD_MODULE_AVAILABLE = False  # 未找到云模块时，默认不启用

if __name__ == "__main__":
    # ------------------- 1. 校验 Spark Pro API 密钥 -------------------
    if not SPARK_PRO_API_KEY or not SPARK_PRO_API_SECRET:
        print("错误：请先在 config.py 中填写 Spark Pro 的 API Key 和 API Secret！")
        print("获取地址：https://console.xfyun.cn/services/bm35")
        exit(1)

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
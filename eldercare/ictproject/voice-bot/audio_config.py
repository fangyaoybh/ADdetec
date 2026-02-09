"""
音频设备配置
自动生成的配置文件，用于解决音频设备错误
"""

# 输入设备ID（None表示使用默认设备）
INPUT_DEVICE_ID = 1

# 输出设备ID（None表示使用默认设备）
OUTPUT_DEVICE_ID = 5

# 音频格式配置
FORMAT = 8  # pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024
SILENCE_THRESHOLD = 500

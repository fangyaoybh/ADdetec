import os
import wave
import pyaudio
import logging
import time
import threading
from config import *

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('VoiceAssistantUtils')


def play_audio(filename, audio, timeout=30):
    """
    播放音频文件，支持超时机制
    
    Args:
        filename: 音频文件名
        audio: pyaudio实例
        timeout: 播放超时时间（秒）
        
    Returns:
        bool: 播放是否成功
    """
    if not filename or not os.path.exists(filename):
        logger.error(f"音频文件不存在：{filename}")
        return False
    
    stream = None
    wf = None
    
    try:
        wf = wave.open(filename, 'rb')
        
        # 创建音频流
        stream = audio.open(
            format=audio.get_format_from_width(wf.getsampwidth()),
            channels=wf.getnchannels(),
            rate=wf.getframerate(),
            output=True
        )
        
        # 播放音频，支持超时
        start_time = time.time()
        data = wf.readframes(CHUNK)
        while data:
            if time.time() - start_time > timeout:
                logger.warning(f"音频播放超时：{filename}")
                return False
            
            stream.write(data)
            data = wf.readframes(CHUNK)
            
        logger.info(f"成功播放音频：{os.path.basename(filename)}")
        return True
        
    except wave.Error as e:
        logger.error(f"音频文件格式错误：{str(e)}")
        return False
    except Exception as e:
        logger.error(f"播放音频失败：{str(e)}")
        return False
    finally:
        # 确保资源正确释放
        if stream is not None:
            stream.stop_stream()
            stream.close()
        if wf is not None:
            wf.close()


def clean_temp_files(*files):
    """
    安全清理临时文件
    
    Args:
        *files: 要清理的文件路径列表
        
    Returns:
        int: 成功清理的文件数量
    """
    success_count = 0
    
    for f in files:
        if f and isinstance(f, str) and os.path.exists(f):
            try:
                os.remove(f)
                logger.info(f"成功清理临时文件：{os.path.basename(f)}")
                success_count += 1
            except PermissionError:
                logger.warning(f"无权限删除文件：{os.path.basename(f)}")
            except OSError as e:
                logger.error(f"清理文件{os.path.basename(f)}失败：{str(e)}")
    
    return success_count


def record_audio(filename, audio, duration=None, chunk_size=CHUNK, 
                channels=CHANNELS, rate=RATE, format=FORMAT, 
                silence_threshold=None, max_silence_duration=2):
    """
    录制音频文件，支持固定时长或基于静音检测的自动停止
    
    Args:
        filename: 保存的文件名
        audio: pyaudio实例
        duration: 录制时长（秒），None表示使用静音检测
        chunk_size: 音频块大小
        channels: 通道数
        rate: 采样率
        format: 音频格式
        silence_threshold: 静音阈值（用于检测静音）
        max_silence_duration: 最大静音持续时间（秒）
        
    Returns:
        bool: 录制是否成功
    """
    if not filename:
        logger.error("文件名不能为空")
        return False
    
    stream = None
    frames = []
    
    try:
        # 创建音频流
        stream = audio.open(
            format=format,
            channels=channels,
            rate=rate,
            input=True,
            frames_per_buffer=chunk_size
        )
        
        logger.info(f"开始录制音频，将保存为：{os.path.basename(filename)}")
        
        # 录制音频
        if duration is not None:
            # 固定时长录制
            frames_count = int(rate / chunk_size * duration)
            for i in range(frames_count):
                data = stream.read(chunk_size, exception_on_overflow=False)
                frames.append(data)
        else:
            # 基于静音检测的录制
            if silence_threshold is None:
                silence_threshold = SILENCE_THRESHOLD
                
            silence_count = 0
            max_silence_count = int(rate / chunk_size * max_silence_duration)
            
            while True:
                data = stream.read(chunk_size, exception_on_overflow=False)
                frames.append(data)
                
                # 检测静音
                if len(frames) > 0:
                    # 简单的音量检测（使用绝对值平均）
                    import numpy as np
                    audio_data = np.frombuffer(data, dtype=np.int16)
                    avg_volume = np.abs(audio_data).mean()
                    
                    if avg_volume < silence_threshold:
                        silence_count += 1
                    else:
                        silence_count = 0
                    
                    # 如果静音时间超过阈值，则停止录制
                    if silence_count > max_silence_count and len(frames) > int(rate / chunk_size * 0.5):
                        logger.info("检测到静音，停止录制")
                        break
        
        # 保存音频文件
        wf = wave.open(filename, 'wb')
        wf.setnchannels(channels)
        wf.setsampwidth(audio.get_sample_size(format))
        wf.setframerate(rate)
        wf.writeframes(b''.join(frames))
        wf.close()
        
        logger.info(f"音频录制完成，文件大小：{os.path.getsize(filename) / 1024:.2f} KB")
        return True
        
    except KeyboardInterrupt:
        logger.info("录制被用户中断")
        # 仍然尝试保存已录制的内容
        if frames:
            try:
                wf = wave.open(filename, 'wb')
                wf.setnchannels(channels)
                wf.setsampwidth(audio.get_sample_size(format))
                wf.setframerate(rate)
                wf.writeframes(b''.join(frames))
                wf.close()
                logger.info(f"已保存部分录制内容：{os.path.basename(filename)}")
            except Exception as e:
                logger.error(f"保存中断的录制内容失败：{str(e)}")
        return False
    except Exception as e:
        logger.error(f"录制音频失败：{str(e)}")
        return False
    finally:
        # 确保资源正确释放
        if stream is not None:
            stream.stop_stream()
            stream.close()


def ensure_directory(directory_path):
    """
    确保目录存在，如果不存在则创建
    
    Args:
        directory_path: 目录路径
        
    Returns:
        bool: 操作是否成功
    """
    if not directory_path:
        return False
        
    try:
        os.makedirs(directory_path, exist_ok=True)
        logger.debug(f"确保目录存在：{directory_path}")
        return True
    except Exception as e:
        logger.error(f"创建目录失败：{str(e)}")
        return False


def get_audio_duration(filename):
    """
    获取音频文件的时长
    
    Args:
        filename: 音频文件名
        
    Returns:
        float: 音频时长（秒），失败返回0
    """
    if not filename or not os.path.exists(filename):
        return 0
        
    try:
        with wave.open(filename, 'rb') as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            duration = frames / float(rate)
            return duration
    except Exception as e:
        logger.error(f"获取音频时长失败：{str(e)}")
        return 0
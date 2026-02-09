#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试LLM与天气服务集成的脚本
"""

from LLM import SparkProLLM
import config

def test_llm_weather_integration():
    """测试LLM与天气服务的集成"""
    print("初始化LLM...")
    llm = SparkProLLM(
        config.XUNFEI_APPID,
        config.SPARK_PRO_API_KEY,
        config.SPARK_PRO_API_SECRET,
        config.SPARK_PRO_URL,
        config.SPARK_PRO_DOMAIN
    )
    print("LLM初始化成功！")
    
    print("\n测试1: 获取当前天气信息...")
    weather_info = llm.get_current_weather('北京')
    print(f"北京天气: {weather_info}")
    
    print("\n测试2: 获取天气预报信息...")
    forecast_info = llm.get_weather_forecast('北京', 3)
    print(f"北京3天预报: {forecast_info}")
    
    print("\n所有测试完成！")

if __name__ == "__main__":
    test_llm_weather_integration()
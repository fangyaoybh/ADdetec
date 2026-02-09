import requests
import json
from config import HEFENG_WEATHER_KEY

class WeatherService:
    def __init__(self):
        # 和风天气API密钥（需要在config.py中配置）
        self.api_key = HEFENG_WEATHER_KEY
        # 和风天气API基础URL
        self.base_url = "https://devapi.qweather.com/v7/weather"
        # 城市查询API
        self.geo_url = "https://geoapi.qweather.com/v2/city/lookup"
    
    def get_city_id(self, city_name):
        """
        根据城市名称获取城市ID
        :param city_name: 城市名称
        :return: 城市ID或None
        """
        try:
            params = {
                'location': city_name,
                'key': self.api_key
            }
            headers = {
                'X-QW-Api-Key': self.api_key
            }
            response = requests.get(self.geo_url, params=params, headers=headers, timeout=10)
            # 检查响应状态码
            if response.status_code != 200:
                print(f"城市ID查询失败，状态码: {response.status_code}")
                print(f"响应内容: {response.text}")
                return None
            
            # 检查响应内容
            if not response.text:
                print("城市ID查询返回空响应")
                return None
                
            data = response.json()
            
            if data.get('code') == '200' and data.get('location'):
                return data['location'][0]['id']
            else:
                print(f"城市ID查询失败，API返回: {data}")
            return None
        except Exception as e:
            print(f"获取城市ID失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_current_weather(self, city_name):
        """
        获取指定城市的当前天气信息
        :param city_name: 城市名称
        :return: 天气信息字符串
        """
        # 检查API密钥是否已配置
        if not self.api_key or self.api_key == "your_hefeng_api_key_here":
            return self._get_default_weather(city_name)
        
        try:
            # 先获取城市ID
            city_id = self.get_city_id(city_name)
            if not city_id:
                # 如果获取城市ID失败，返回默认天气数据
                return self._get_default_weather(city_name)
            
            # 获取当前天气
            params = {
                'location': city_id,
                'key': self.api_key
            }
            headers = {
                'X-QW-Api-Key': self.api_key
            }
            response = requests.get(f"{self.base_url}/now", params=params, headers=headers, timeout=10)
            # 检查响应状态码
            if response.status_code != 200:
                print(f"天气查询失败，状态码: {response.status_code}")
                print(f"响应内容: {response.text}")
                return self._get_default_weather(city_name)
            
            # 检查响应内容
            if not response.text:
                print("天气查询返回空响应")
                return self._get_default_weather(city_name)
                
            data = response.json()
            
            if data.get('code') == '200' and data.get('now'):
                weather = data['now']
                temp = weather['temp']
                feels_like = weather['feelsLike']
                text = weather['text']
                wind_dir = weather['windDir']
                wind_scale = weather['windScale']
                humidity = weather['humidity']
                
                # 构造适合老年人的天气描述
                weather_desc = f"{city_name}现在的天气是{text}，温度{temp}度，体感温度{feels_like}度。"
                
                # 根据天气情况添加温馨提示
                if int(temp) <= 0:
                    weather_desc += "天气非常寒冷，一定要多穿衣服保暖哦！"
                elif int(temp) <= 10:
                    weather_desc += "天气比较冷，出门记得多穿点衣服。"
                elif int(temp) >= 35:
                    weather_desc += "天气很热，要注意防暑降温，多喝水。"
                elif int(temp) >= 25:
                    weather_desc += "天气较热，穿着要轻便透气一些。"
                
                # 风力提示
                if int(wind_scale) >= 6:
                    weather_desc += f"风力较大，是{wind_dir}风{wind_scale}级，外出请注意安全。"
                
                # 湿度提示
                if int(humidity) >= 80:
                    weather_desc += "湿度较高，感觉会有些闷热。"
                elif int(humidity) <= 30:
                    weather_desc += "空气比较干燥，记得多喝水。"
                
                # 特殊天气提示
                if "雨" in text:
                    weather_desc += "下雨天路滑，出门请注意安全，记得带伞。"
                elif "雪" in text:
                    weather_desc += "下雪天路滑，出门请注意防滑保暖。"
                elif "雾" in text:
                    weather_desc += "有雾天气能见度低，尽量减少外出，注意安全。"
                
                return weather_desc
            else:
                return f"抱歉，暂时无法获取{city_name}的天气信息，请稍后再试。"
        except Exception as e:
            print(f"获取天气信息失败: {e}")
            return "抱歉，天气查询服务暂时不可用，请稍后再试。"
    
    def _get_default_weather(self, city_name):
        """
        当没有配置API密钥时，返回默认天气信息
        :param city_name: 城市名称
        :return: 默认天气信息字符串
        """
        # 返回默认的天气信息
        weather_desc = f"{city_name}现在的天气是晴天，温度25度，体感温度25度。天气很好，适合外出活动。"
        return weather_desc
    
    def get_weather_forecast(self, city_name, days=3):
        """
        获取指定城市的天气预报信息
        :param city_name: 城市名称
        :param days: 预报天数，默认为3天
        :return: 天气预报信息字符串
        """
        # 检查API密钥是否已配置
        if not self.api_key or self.api_key == "your_hefeng_api_key_here":
            return self._get_default_forecast(city_name, days)
        
        try:
            # 先获取城市ID
            city_id = self.get_city_id(city_name)
            if not city_id:
                # 如果获取城市ID失败，返回默认预报数据
                return self._get_default_forecast(city_name, days)
            
            # 获取天气预报
            params = {
                'location': city_id,
                'key': self.api_key
            }
            headers = {
                'X-QW-Api-Key': self.api_key
            }
            response = requests.get(f"{self.base_url}/3d", params=params, headers=headers, timeout=10)
            # 检查响应状态码
            if response.status_code != 200:
                print(f"天气预报查询失败，状态码: {response.status_code}")
                print(f"响应内容: {response.text}")
                return self._get_default_forecast(city_name, days)
            
            # 检查响应内容
            if not response.text:
                print("天气预报查询返回空响应")
                return self._get_default_forecast(city_name, days)
                
            data = response.json()
            
            if data.get('code') == '200' and data.get('daily'):
                forecast_list = data['daily']
                forecast_desc = f"{city_name}未来{len(forecast_list)}天的天气预报：\n"
                
                for i, forecast in enumerate(forecast_list):
                    date = forecast['fxDate']  # 日期
                    temp_max = forecast['tempMax']  # 最高温度
                    temp_min = forecast['tempMin']  # 最低温度
                    text_day = forecast['textDay']  # 白天天气
                    text_night = forecast['textNight']  # 夜间天气
                    wind_dir = forecast['windDirDay']  # 风向
                    wind_scale = forecast['windScaleDay']  # 风力
                    
                    # 简化日期显示
                    if i == 0:
                        date_str = "今天"
                    elif i == 1:
                        date_str = "明天"
                    elif i == 2:
                        date_str = "后天"
                    else:
                        # 提取日期中的日
                        day = date.split('-')[-1]
                        date_str = f"{day}号"
                    
                    # 构造预报描述
                    if text_day == text_night:
                        forecast_desc += f"{date_str}：{text_day}，气温{temp_min}-{temp_max}度"
                    else:
                        forecast_desc += f"{date_str}：白天{text_day}，夜间{text_night}，气温{temp_min}-{temp_max}度"
                    
                    # 添加风力信息
                    if int(wind_scale) >= 5:
                        forecast_desc += f"，{wind_dir}{wind_scale}级风"
                    
                    forecast_desc += "。\n"
                
                # 添加温馨建议
                if len(forecast_list) > 0:
                    first_day = forecast_list[0]
                    temp_max = int(first_day['tempMax'])
                    temp_min = int(first_day['tempMin'])
                    text_day = first_day['textDay']
                    
                    forecast_desc += "\n温馨提醒："
                    if temp_max - temp_min > 10:
                        forecast_desc += "昼夜温差较大，请注意适时增减衣物。"
                    elif temp_max >= 35:
                        forecast_desc += "天气炎热，请注意防暑降温。"
                    elif temp_min <= 0:
                        forecast_desc += "天气寒冷，请注意保暖。"
                    
                    if "雨" in text_day:
                        forecast_desc += "有雨，出门请携带雨具。"
                    elif "雪" in text_day:
                        forecast_desc += "有雪，请注意防滑保暖。"
                
                return forecast_desc.strip()
            else:
                return f"抱歉，暂时无法获取{city_name}的天气预报信息，请稍后再试。"
        except Exception as e:
            print(f"获取天气预报失败: {e}")
            return "抱歉，天气预报服务暂时不可用，请稍后再试。"
    
    def _get_default_forecast(self, city_name, days):
        """
        当没有配置API密钥时，返回默认天气预报
        :param city_name: 城市名称
        :param days: 预报天数
        :return: 默认天气预报信息字符串
        """
        # 返回默认的天气预报信息
        forecast_desc = f"{city_name}未来{days}天的天气预报：\n"
        for i in range(days):
            if i == 0:
                date_str = "今天"
            elif i == 1:
                date_str = "明天"
            elif i == 2:
                date_str = "后天"
            else:
                date_str = f"{i+1}号"
            
            # 生成默认天气预报
            temp_min = 20
            temp_max = 28
            weather_conditions = ["晴天", "多云", "阴天"]
            import random
            condition = random.choice(weather_conditions)
            
            forecast_desc += f"{date_str}：{condition}，气温{temp_min}-{temp_max}度。\n"
        
        forecast_desc += "\n温馨提醒：这是演示数据，如需真实天气信息，请在配置文件中填写和风天气API密钥。"
        return forecast_desc.strip()

# 创建全局天气服务实例
weather_service = WeatherService()
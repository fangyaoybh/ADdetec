import requests
from config import HEFENG_WEATHER_KEY

def test_weather_api():
    # 尝试不同的API Host组合
    api_hosts = [
        "https://devapi.qweather.com",
        "https://api.qweather.com",
        "https://free-api.heweather.com"
    ]
    
    geo_url = "https://geoapi.qweather.com/v2/city/lookup"
    
    for base_url in api_hosts:
        print(f"\n尝试API Host: {base_url}")
        
        # 测试城市ID获取
        print("正在获取城市ID...")
        try:
            params = {
                'location': '北京',
                'key': HEFENG_WEATHER_KEY
            }
            response = requests.get(geo_url, params=params, timeout=5)
            print(f"城市查询状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == '200' and data.get('location'):
                    city_id = data['location'][0]['id']
                    print(f"获取到的城市ID: {city_id}")
                    
                    # 测试天气获取
                    print("正在获取天气信息...")
                    weather_url = f"{base_url}/v7/weather/now"
                    params = {
                        'location': city_id,
                        'key': HEFENG_WEATHER_KEY
                    }
                    response = requests.get(weather_url, params=params, timeout=5)
                    print(f"天气查询状态码: {response.status_code}")
                    print(f"天气查询响应: {response.text[:200]}")
                    break
                else:
                    print("未能获取城市ID")
            else:
                print(f"城市查询失败，响应: {response.text[:100]}")
        except Exception as e:
            print(f"发生错误: {e}")

if __name__ == "__main__":
    test_weather_api()
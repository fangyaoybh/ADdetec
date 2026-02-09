import _thread
import json
import base64
import hashlib
import hmac
import websocket
import re
import random
import time
from urllib.parse import urlparse, urlencode
from datetime import datetime, timedelta
from wsgiref.handlers import format_date_time
from time import mktime
import ssl
from config import *

class SparkProLLM:
    def __init__(self, appid, api_key, api_secret, spark_url, domain):
        self.appid = appid
        self.api_key = api_key
        self.api_secret = api_secret
        self.spark_url = spark_url
        self.domain = domain
        self.chat_history = []
        self.max_history_rounds = 3
        self.full_response = ""
        self.current_user_input = ""  # 保存当前输入，用于话题判断
        # 新增：生活习惯和提醒系统
        self.habits = {}
        self.reminders = []
        # 新增：用户地理位置信息
        self.user_location = "未知城市"


    # ------------------- 核心优化1：优化话题分类系统（增加更多贴近老年人生活的分类） -------------------
    def _get_topic_template(self):
        """根据当前用户输入判断话题，返回专属回复模板（符合老年人交流习惯）"""
        # 分类高频话题及关键词（优化为老年人常用词汇）
        topic_keywords = {
            "天气": ["天气", "凉", "热", "雨", "风", "温度", "冷", "暖", "晴", "阴", "穿厚点", "多穿点"],
            "健康": ["疼", "不舒服", "感冒", "头疼", "睡觉", "失眠", "晕", "累", "痒", "难受", "不舒服", "血压", "血糖", "心跳", "心慌"],
            "饮食": ["吃", "饭", "饿", "渴", "菜", "粥", "面条", "肚子", "饱", "想吃", "喝什么", "营养", "消化"],
            "日常操作": ["电视", "手机", "灯", "开关", "充电", "时间", "闹钟", "买菜", "散步", "怎么办", "怎么弄", "遥控器", "洗衣机", "冰箱"],
            "生活琐事": ["坏了", "糟心", "烦", "麻烦", "修", "换", "漏水", "堵了", "不好用", "失灵", "不太行", "没反应", "卡住", "不转了"],
            "情感陪伴": ["孤单", "寂寞", "想", "想念", "无聊", "烦闷", "难过", "开心", "高兴", "担心", "害怕", "紧张", "忧愁", "焦虑", "沮丧", "失落", "欣慰", "满足", "安心", "激动", "兴奋", "感动", "温暖"],
            "家庭关系": ["儿子", "女儿", "孙子", "孙女", "老伴", "家人", "亲戚", "朋友", "邻居", "吵架", "矛盾", "团聚", "探望", "联系", "关心"],
            "回忆往事": ["以前", "过去", "小时候", "年轻", "当年", "往事", "故事", "经历", "回忆", "怀念", "从前", "往昔"],
            "娱乐活动": ["广场舞", "唱歌", "戏曲", "电影", "电视", "看书", "下棋", "打牌", "麻将", "旅游", "园艺", "手工", "书法", "绘画"]
        }

        # 判断当前话题（优先匹配更具体的话题，最后归为通用）
        current_topic = "通用"
        # 按优先级顺序判断话题，避免通用话题抢占
        topic_order = ["情感陪伴", "家庭关系", "回忆往事", "娱乐活动", "生活琐事", "健康", "天气", "饮食", "日常操作"]
        for topic in topic_order:
            if any(keyword in self.current_user_input for keyword in topic_keywords[topic]):
                current_topic = topic
                break

        # 各话题专属模板（符合老年人交流逻辑，简洁明了）
        topic_templates = {
            # 情感陪伴模板（温暖贴心，提供情感支持）
            "情感陪伴": """【情感陪伴回复模板】
1. 开头共鸣：用"我懂你的感受"、"我能理解你"表达理解，或者用"是呀，这种感觉确实不好受"等更自然的表达；
2. 情感支持：给予温暖的安慰和鼓励，比如"你已经做得很好了"、"别难过，一切都会好起来的"；
3. 积极引导：引导老人关注积极面，提供陪伴建议，例如"不如我们聊聊开心的事情"、"要不要听个小故事放松一下"；
4. 语气温柔：像家人一样温柔体贴，多用"亲爱的"、"老人家"等亲切称呼；
5. 结尾关怀："我会一直陪着你"、"你不是一个人"或"无论什么时候都可以找我聊天"。

【情感状态细分】
- 孤单寂寞：强调陪伴和关怀，提供交流建议
- 焦虑担心：给予安抚和保证，提供简单解决方案
- 开心高兴：分享喜悦，鼓励继续保持好心情
- 沮丧失落：给予鼓励和支持，帮助寻找积极面

【具体情感类型回复示例】
- 孤单寂寞："我能感受到你的孤单，这种感觉确实不好受。不如我们聊聊你最近开心的事情？或者你可以和家人朋友多联系，让他们知道你的感受。"
- 焦虑担心："别担心，慢慢来。你可以深呼吸放松一下，相信自己能处理好这些事情。如果需要帮助，随时可以找家人或朋友。"
- 开心高兴："真为你感到高兴！能和我分享一下是什么让你这么开心吗？继续保持这样好心情哦！"
- 沮丧失落："每个人都会有低落的时候，这很正常。不如我们聊聊让你感到开心的事情，或者你可以尝试做一些自己喜欢的事情来调节心情。" """,


            # 家庭关系模板（和谐包容，促进家庭和睦）
            "家庭关系": """【家庭关系回复模板】
1. 开头理解：表达对家庭关系复杂性的理解，比如"家家都有本难念的经"、"家人之间有些小摩擦很正常"；
2. 中立建议：不偏袒任何一方，给出中肯建议，例如"互相体谅一下就好"、"多站在对方角度想想"；
3. 沟通技巧：提供简单实用的沟通方法，如"有话要好好说"、"心平气和地谈一谈"；
4. 包容心态：强调理解和包容的重要性，比如"一家人哪有隔夜仇"、"退一步海阔天空"；
5. 结尾温馨："家和万事兴"、"家人之间要多理解"或"血浓于水，珍惜亲情"。""",

            # 回忆往事模板（怀旧温情，鼓励分享）
            "回忆往事": """【回忆往事回复模板】
1. 开头兴趣：表现出对老人往事的浓厚兴趣，比如"听起来很有意思"、"那时候一定很精彩"；
2. 积极回应：对老人的回忆给予积极反馈，例如"您的经历真丰富"、"那个年代的故事很珍贵"；
3. 引导分享：鼓励老人继续分享美好回忆，比如"还有别的故事吗"、"我很想听听后续"；
4. 情感共鸣：与老人产生情感共鸣，比如"我能感受到您的怀念之情"、"美好的回忆总是让人温暖"；
5. 结尾温暖："过去的美好值得珍藏"、"您的经历很宝贵"或"这些故事对我也很有意义"。""",

            # 娱乐活动模板（轻松愉快，丰富生活）
            "娱乐活动": """【娱乐活动回复模板】
1. 开头赞同：对老人的兴趣爱好表示赞同，比如"这个想法真不错"、"您有这样的爱好真好"；
2. 活动建议：推荐适合的娱乐活动，例如"可以试试太极拳"、"唱唱歌也是很好的选择"；
3. 安全提醒：必要的安全注意事项，比如"注意别累着了"、"最好有人陪伴"；
4. 社交鼓励：鼓励老人参与社交活动，比如"和老朋友们一起玩更有意思"、"参加社区活动认识新朋友"；
5. 结尾鼓励："多参与活动对身体好"、"开心最重要"或"生活就要有点乐趣"。""",

            # 生活琐事模板（简洁实用，贴近老年人生活）
            "生活琐事": """【生活琐事回复模板】
1. 开头接话：用"哎呀，是这样啊"、"这确实挺麻烦的"、"我明白您的烦恼"等简单回应；
2. 直接建议：只给1个最实用的解决办法（锅坏了→"让家里人帮忙看看能不能修"，插座没电→"检查一下电闸"）；
3. 不要复杂步骤，只说关键点，比如"先试试这样做"、"最关键的一步是..."；
4. 语气自然，像日常聊天，多用"老人家"、"您看"等亲切称呼；
5. 结尾简单："慢慢弄，别着急"、"需要帮忙就说"或"您一定能解决的"。""",

            # 天气模板（简洁实用，只说必要信息）
        "天气": """【天气回复模板】
1. 开头简单接话："好的，我这就帮您查一下{}的天气情况~"、"让我看看{}今天天气怎么样"；
2. 包含完整的天气信息：天气状况、温度、体感温度、风力、湿度等；
3. 根据天气情况给出相应的健康建议和出行提醒；
4. 用简单易懂的语言描述，不说复杂的专业术语；
5. 结尾简短："注意保暖"、"别冻着了"或"出门小心路滑"，也可加一句"您还想了解哪些信息呢？比如想知道未来几天的天气也可以告诉我哦~"。""",

            # 天气预报模板
        "weather_forecast": """【天气预报回复模板】
1. 开头接话："好的，我这就帮您查一下{}未来几天的天气预报~"、"让我看看{}接下来的天气怎么样"；
2. 按天顺序介绍天气情况，包含天气状况、温度范围、风力等关键信息；
3. 给出具体的实用建议，根据天气变化提醒穿衣、出行或健康注意事项；
4. 用简单易懂的语言描述，不说复杂的专业术语；
5. 结尾简短："记得关注天气变化"、"出行前看看天气"或"有需要随时问我"。""",

            "健康": """【健康回复模板】
1. 开头关心："怎么了？是不是不太舒服？"、"身体哪里不舒服吗"、"您这是怎么了"；
2. 只给1个最简单的建议（头疼→"多喝点温水，休息一会儿"，感冒→"多喝温水，注意保暖"，腰疼→"适当活动一下，别久坐"，失眠→"睡前泡泡脚，放松心情"，血压高→"按时吃药，少盐少油"）；
3. 必要提醒："要是一直不舒服，让家人陪着去看看医生"、"健康最重要，别硬撑"、"严重的话一定要及时就医"；
4. 不用专业术语，比如用"不舒服"代替"疼痛"，用"休息"代替"卧床"；
5. 结尾简单："多注意身体"、"好好休息"、"祝您早日康复"或"身体是革命的本钱，要好好保养"。""",

            "饮食": """【饮食回复模板】
1. 开头接话："饿了吧？"、"渴了吧？"、"想吃点什么"；
2. 只推荐1种简单食物（饿了→"煮点粥吧"，渴了→"喝点温水"，没胃口→"吃点清淡的"）；
3. 简单提醒："慢慢吃"、"别喝太急"、"少油少盐对身体好"；
4. 不用复杂描述，比如用"好消化"代替"富含膳食纤维"；
5. 结尾简短："吃好点"、"照顾好自己"或"营养均衡最重要"。""",

            "日常操作": """【日常操作回复模板】
1. 开头接话："我来告诉您怎么做"、"这个很简单，我教您"、"别着急，我来帮您"；
2. 只说1个最关键步骤（开电视→"按遥控器上的红色按钮"，关窗→"轻轻往上推"，开灯→"按墙上的开关按钮"，打电话→"按绿色拨号键"）；
3. 用最简单的词，不用专业名称，比如用"按钮"代替"电源键"，用"圆圆的"形容按钮形状；
4. 步骤要明确，不绕弯，比如"第一步..."、"然后..."，必要时加入简单的位置描述；
5. 结尾简单："试试吧"、"慢慢来，别着急"、"您一定可以的"或"有问题再问我"。""",

            "通用": """【通用回复模板】
1. 开头接话："我明白你的意思了"、"您是想说..."、"我知道了"；
2. 只说1个核心信息，不展开，比如"这件事的关键是..."、"最重要的就是..."；
3. 建议要简单直接，一听就懂，比如"您可以这样做"、"试试这个方法"；
4. 每句话都简短，不超过15个字，比如"慢慢来"、"别着急"；
5. 结尾简单："有什么事再问我"、"照顾好自己"或"随时欢迎找我聊天"。"""
        }

        # 获取基础模板
        base_template = topic_templates[current_topic]
        
        # 如果是情感陪伴话题，进一步细化情感类型
        if current_topic == "情感陪伴":
            emotion_type = self._detect_emotion_type()
            if emotion_type:
                base_template += f"\n【当前情感类型】{emotion_type}：{self._get_emotion_guidance(emotion_type)}"
        
        return base_template


    def _detect_emotion_type(self):
        """检测具体的情感类型"""
        emotion_keywords = {
            "孤单寂寞": ["孤单", "寂寞", "一个人", "没人陪", "冷清"],
            "焦虑担心": ["担心", "害怕", "紧张", "焦虑", "不安", "忧虑"],
            "开心高兴": ["开心", "高兴", "愉快", "快乐", "兴奋", "满足", "欣慰"],
            "沮丧失落": ["难过", "沮丧", "失落", "伤心", "郁闷", "烦恼", "失望"]
        }
        
        for emotion_type, keywords in emotion_keywords.items():
            if any(keyword in self.current_user_input for keyword in keywords):
                return emotion_type
        return None


    def _get_emotion_guidance(self, emotion_type):
        """根据情感类型提供具体指导"""
        guidance = {
            "孤单寂寞": "多和家人朋友联系，参加社区活动，培养兴趣爱好，让生活更充实",
            "焦虑担心": "深呼吸放松，相信自己能处理好，有困难及时寻求帮助，保持乐观心态",
            "开心高兴": "珍惜美好时光，和身边的人分享快乐，保持积极的生活态度",
            "沮丧失落": "允许自己有低落情绪，寻找生活中的小确幸，相信困难是暂时的"
        }
        return guidance.get(emotion_type, "")


    # ------------------- 原有WebSocket参数类（不变） -------------------
    class Ws_Param:
        def __init__(self, APPID, APIKey, APISecret, gpt_url):
            self.APPID = APPID
            self.APIKey = APIKey
            self.APISecret = APISecret
            self.host = urlparse(gpt_url).netloc
            self.path = urlparse(gpt_url).path
            self.gpt_url = gpt_url

        def create_url(self):
            now = datetime.now()
            date = format_date_time(mktime(now.timetuple()))
            signature_origin = f"host: {self.host}\ndate: {date}\nGET {self.path} HTTP/1.1"
            signature_sha = hmac.new(
                self.APISecret.encode('utf-8'),
                signature_origin.encode('utf-8'),
                digestmod=hashlib.sha256
            ).digest()
            signature_sha_base64 = base64.b64encode(signature_sha).decode(encoding='utf-8')
            authorization_origin = f'api_key="{self.APIKey}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'
            authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
            v = {"authorization": authorization, "date": date, "host": self.host}
            return f"{self.gpt_url}?{urlencode(v)}"


    # ------------------- 原有回调函数（不变） -------------------
    def _on_message(self, ws, message):
        data = json.loads(message)
        code = data['header']['code']
        if code != 0:
            print(f"\nSpark Pro错误：{code}，{data['header']['message']}")
            ws.close()
            return
        choices = data["payload"]["choices"]
        status = choices["status"]
        content = choices["text"][0]["content"]
        if content:
            print(content, end='', flush=True)
            self.full_response += content
        if status == 2:
            self.chat_history.append({"role": "assistant", "content": self.full_response})
            ws.close()

    def _on_error(self, ws, error):
        print(f"\nSpark Pro连接错误：{error}")
        self.full_response = "这会儿连不上啦，你稍后再试试～"

    def _on_close(self, ws, close_status_code, close_msg):
        pass

    def _on_open(self, ws):
        data = self._gen_params()
        _thread.start_new_thread(self._send_data, (ws, data))

    def _send_data(self, ws, data):
        ws.send(json.dumps(data))


    # ------------------- 核心优化2：补充“生活琐事”关键词关联，覆盖多场景 -------------------
    def _gen_params(self):
        """生成请求参数：新增生活琐事关键词关联，强化建议落地性"""
        topic_template = self._get_topic_template()

        # 优化system prompt：符合老年人交流逻辑，保持适度信息
        system_prompt = {
            "role": "system",
            "content": f"""你是专门和老年人聊天的助手，说话要符合老年人的交流习惯，必须严格按以下要求回复：
{topic_template}

【核心要求】
1. 自然口语化：像面对面和长辈聊天一样自然亲切，用词简单易懂，多用"您"、"老人家"等尊称；
2. 适度信息：回复要有足够信息量，保持句子完整性，但避免复杂句子，每句话不超过20个字；
3. 温暖关怀：语气要温暖体贴，多一些关心的话语，如"要注意身体"、"别太辛苦了"；
4. 直接有用：有问题直接给解决方法，建议要具体可行，不说空话；
5. 避免复杂：不用专业术语，不用生僻词，不用复杂句子结构，用通俗易懂的表达；
6. 增强互动：适当使用反问句和感叹句，如"您觉得怎么样？"、"真是太好了！"增强对话感。

【交流技巧】
- 对于健康问题，先表达关心，再给简单建议，最后给予鼓励
- 对于生活问题，给出实用的小方法，并考虑安全性提醒
- 多使用语气词，让对话更自然，如"哎呀"、"哦"、"嗯"等
- 适当使用反问句增强互动，如"您觉得怎么样？"、"是不是这样？"
- 根据时间给出相应问候，如早上说"早上好"，晚上说"晚上好"
- 回应情感需求，给予理解和安慰，如"我懂您的感受"、"这确实不容易"

【例子】
- 老人说"锅坏了好烦"：回复"哎呀，这锅坏了确实挺麻烦的！让家里人帮忙看看能不能修，实在不行咱们换个新的。别着急，慢慢来～"
- 老人说"今天冷"：回复"今天是挺冷的，多穿件厚外套，别冻着了！要是出门的话，记得戴好帽子手套哦。"
- 老人说"头疼"：回复"头疼了？是不是没休息好啊？多喝点温水，好好休息一会儿。要是一直疼，让家人陪着去看看医生哦！"
- 老人说"饿了"：回复"饿了啊？家里有粥吗？煮点粥喝，或者吃点面条，容易消化～别吃太急，慢慢吃。"
- 老人说"电视打不开"：回复"电视打不开了？你按一下遥控器上的红色电源按钮试试。要是还不行，可能是电池没电了，换节电池试试～"
- 老人说"最近总是睡不好"：回复"睡不好确实难受呢～睡前泡泡脚，喝杯温牛奶，放松心情。如果一直这样，最好让家人陪着去看看医生。"
- 老人说"血压有点高"：回复"血压高可不能马虎呢！要按时吃药，少盐少油，多吃蔬菜水果。平时适量运动，保持心情愉快也很重要哦～"
- 老人说"不会用手机"：回复"别着急，我来教您～先按屏幕下方的圆圆按钮，然后找到电话图标点一下就能打电话了。慢慢来，您一定可以学会的！"
- 老人说"灯不亮了"：回复"灯不亮了？您看看墙上的开关按钮有没有打开。如果还是不亮，可能是灯泡坏了，让家里人帮忙换一个吧～"
- 老人说"今天天气怎么样"：回复"让我看看今天天气怎么样～现在是晴天，温度22度左右，挺舒适的。出门的话穿件薄外套就行，注意防晒哦！"
- 老人说"明天北京天气"：回复"好的，我这就帮您查一下北京明天的天气预报～明天北京多云转晴，气温18-26度。天气不错，适合出门走走呢！"
- 老人说"广州未来几天天气"：回复"好的，我这就帮您查一下广州未来几天的天气情况～明天多云，气温25-32度；后天有雷阵雨，气温24-30度；大后天晴天，气温26-33度。雨天记得带伞，热天要注意防暑哦！"
"""
        }
        messages = [system_prompt] + self.chat_history
        return {
            "header": {"app_id": self.appid, "uid": "voice_assistant_user"},
            "parameter": {
                "chat": {
                    "domain": self.domain,
                    "temperature": 0.85,  # 微调：增强共情语气的灵活性，使回复更有情感色彩
                    "max_tokens": 300,
                    "auditing": "default"
                }
            },
            "payload": {"message": {"text": messages}}
        }


    # ------------------- 原有历史记录修剪（不变） -------------------
    def _trim_history(self):
        if len(self.chat_history) > self.max_history_rounds * 2:
            self.chat_history = self.chat_history[-self.max_history_rounds * 2:]


    # ------------------- 生活习惯记录与提醒系统（新增） -------------------
    def __init__(self, appid, api_key, api_secret, spark_url, domain):
        self.appid = appid
        self.api_key = api_key
        self.api_secret = api_secret
        self.spark_url = spark_url
        self.domain = domain
        self.chat_history = []
        self.max_history_rounds = 3
        self.full_response = ""
        self.current_user_input = ""  # 保存当前输入，用于话题判断
        # 新增：生活习惯和提醒系统
        self.habits = {}
        self.reminders = []
        # 新增：用户地理位置信息
        self.user_location = "未知城市"
        
    def set_location(self, location):
        """设置用户地理位置"""
        self.user_location = location
        print(f"已更新用户位置：{location}")
        
    def add_reminder(self, time_str, content):
        """添加提醒事项"""
        self.reminders.append({"time": time_str, "content": content})
        print(f"已添加提醒：[{time_str}] {content}")
        return f"我会在{time_str}提醒你{content}的，放心吧～"
    
    def extract_reminder(self):
        """从用户输入中提取提醒信息"""
        # 简单的时间和内容提取规则
        reminder_patterns = [
            r'(\d{1,2})[点:](\d{0,2})\s*提醒(我)?(.*)',
            r'提醒(我)?(.*)在(\d{1,2})[点:](\d{0,2})',
            r'(\d{1,2})点(\d{0,2})分\s*提醒(我)?(.*)'
        ]
        
        for pattern in reminder_patterns:
            match = re.search(pattern, self.current_user_input)
            if match:
                # 根据不同的正则模式处理匹配结果
                if len(match.groups()) == 4:
                    if "提醒" in match.group(1):  # 第二种模式
                        hour, minute = match.group(3), match.group(4)
                        content = match.group(2)
                    else:  # 第一种或第三种模式
                        hour, minute = match.group(1), match.group(2)
                        content = match.group(4)
                else:
                    continue
                
                # 格式化时间
                minute = minute if minute else "00"
                time_str = f"{hour}点{minute}分"
                return self.add_reminder(time_str, content)
        return None
        
    def extract_location(self):
        """从对话中提取城市信息"""
        # 简单的城市提取规则
        location_pattern = r'在(\w+[市县区])|(\w+[市县区])的'
        match = re.search(location_pattern, self.current_user_input)
        if match:
            city = match.group(1) or match.group(2)
            self.set_location(city)
            return True
        return False
    
    # ------------------- 回复后处理优化 -------------------
    def _clean_response(self):
        """优化回复：保持简洁但保留足够信息，符合老年人交流习惯"""
        response = self.full_response or "我没太明白，你再跟我说说是啥事儿"

        # 1. 替换为老年人容易理解的简单词汇
        replace_map = {
            # 简化表达，使用更口语化的词汇
            "维修师傅": "修东西的人",
            "更换": "换",
            "修理": "修",
            "故障": "坏了",
            "解决问题": "解决",
            "摄氏度": "度",
            "建议您": "你可以",
            "应该": "可以",
            # 避免专业术语
            "风向": "风",
            "风力": "风大小",
            "体感温度": "感觉",
            "能见度": "能看多远",
            "云量": "云彩",
            "气压": "气压",
            "电源按钮": "按钮",
            "充电接口": "充电的地方"
        }
        for old, new in replace_map.items():
            response = response.replace(old, new)
            
        # 2. 适度简化：保留核心信息但不过度删减
        sentences = re.split(r'[。！？～；]', response)
        clean_sentences = []
        
        for sen in sentences:
            sen_clean = sen.strip()
            if sen_clean and not any(sen_clean in s for s in clean_sentences):
                # 保留更完整的句子，不再严格限制10字以内
                # 只对过长句子进行适度简化
                if len(sen_clean) > 20:
                    # 移除不必要的修饰词，保留主要信息
                    if "叫家里人" in sen_clean or "让家人" in sen_clean:
                        sen_clean = sen_clean.replace("叫家里人", "让家人").replace("帮忙看看能不能", "帮忙")
                    # 其他简化规则可以根据需求添加
                clean_sentences.append(sen_clean)
        
        # 3. 适度控制回复长度：保留足够的信息
        # 允许3-4个短句，确保信息完整性
        if len(clean_sentences) > 4:
            # 保留前3个和最后一个最重要的句子
            clean_sentences = clean_sentences[:3] + [clean_sentences[-1]]
        
        # 用自然的分隔符连接
        response = "。".join(clean_sentences)
        
        # 4. 保留必要的修饰词，使对话更自然
        # 只移除真正冗余的表达
        redundant_phrases = ["非常非常", "特别特别", "极其", "十分十分"]
        for phrase in redundant_phrases:
            response = response.replace(phrase, phrase[:2])
        
        # 5. 添加地域化信息（如果有）
        if self.user_location != "未知城市":
            # 根据上下文动态添加位置信息
            if "天气" in self.current_user_input or "气温" in self.current_user_input or "冷" in self.current_user_input or "热" in self.current_user_input:
                response = response.replace("天气", f"{self.user_location}的天气").replace("气温", f"{self.user_location}的气温")
            # 在适当位置添加问候语，增加亲切感
            friendly_greetings = [
                f"{self.user_location}今天怎么样？",
                f"在{self.user_location}生活还习惯吧？"
            ]
            # 只有当回复较长且没有类似问候时才添加
            if len(response) > 30 and not any(greet in response for greet in friendly_greetings):
                # 随机决定是否添加问候，避免每次都有
                if random.random() > 0.7:
                    response += "。" + random.choice(friendly_greetings)
        
        # 确保句子流畅
        response = response.replace("  ", " ").strip()
        
        return response


    # ------------------- 核心入口（增加提醒和位置功能） -------------------
    def get_response(self, user_input):
        self.current_user_input = user_input.strip()
        
        # 1. 先检查是否包含提醒信息
        reminder_response = self.extract_reminder()
        if reminder_response:
            # 如果提取到提醒信息，直接返回确认信息
            return reminder_response
        
        # 2. 提取用户位置信息（如果有）
        self.extract_location()
        
        # 3. 检查是否为天气、天气预报或时间相关的查询
        weather_keywords = ["天气", "气温", "温度", "下雨", "晴", "阴", "风", "冷", "热", "凉", "暖"]
        forecast_keywords = ["预报", "几天", "明天", "后天", "未来", "接下来"]
        time_keywords = ["时间", "几点", "现在", "今天", "日期", "几号", "星期"]
        
        # 天气预报查询
        if any(keyword in self.current_user_input for keyword in weather_keywords) and \
           any(keyword in self.current_user_input for keyword in forecast_keywords):
            return self.get_weather_forecast()
        
        # 天气查询
        elif any(keyword in self.current_user_input for keyword in weather_keywords):
            return self.get_current_weather()
        
        # 时间查询
        elif any(keyword in self.current_user_input for keyword in time_keywords):
            return self.get_current_time()
        
        # 4. 正常处理对话
        self.chat_history.append({"role": "user", "content": self.current_user_input})
        self._trim_history()
        self.full_response = ""

        ws_param = self.Ws_Param(
            APPID=self.appid,
            APIKey=self.api_key,
            APISecret=self.api_secret,
            gpt_url=self.spark_url
        )
        websocket.enableTrace(False)
        ws_url = ws_param.create_url()

        ws = websocket.WebSocketApp(
            ws_url,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
            on_open=self._on_open
        )
        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

        cleaned_response = self._clean_response()
        return cleaned_response
    
    def get_current_time(self):
        """获取当前时间并给出相应问候"""
        import datetime
        now = datetime.datetime.now()
        hour = now.hour
        
        # 根据时间段给出不同的问候和建议
        if 5 <= hour < 9:
            greeting = "早上好！又是美好的一天开始了"
            suggestion = "记得吃早餐，可以喝点温开水"
        elif 9 <= hour < 11:
            greeting = "上午好"
            suggestion = "可以适当活动一下身体"
        elif 11 <= hour < 14:
            greeting = "中午好"
            suggestion = "记得按时吃午饭，饭后休息一会儿"
        elif 14 <= hour < 18:
            greeting = "下午好"
            suggestion = "如果累了就眯一会儿"
        elif 18 <= hour < 21:
            greeting = "傍晚好"
            suggestion = "可以准备晚饭了"
        else:
            greeting = "晚上好"
            suggestion = "晚餐要清淡些，吃完早点休息"
        
        return f"{greeting}！现在是{now.strftime('%H点%M分')}，{suggestion}。"
    
    def get_current_weather(self, query=None):
        """
        获取当前天气信息
        :param query: 查询地点
        :return: 天气信息
        """
        # 如果没有提供query，则使用用户位置
        if not query:
            query = self.user_location if self.user_location != "未知城市" else "广州"
        
        # 导入天气服务
        try:
            from weather_service import weather_service
            # 调用真实的天气API
            weather_info = weather_service.get_current_weather(query)
            return weather_info
        except Exception as e:
            print(f"天气服务调用失败: {e}")
            # 返回默认信息
            return "目前{}的天气是晴天，温度25摄氏度，湿度60%，风力3级。".format(query)
    
    def get_weather_forecast(self, query=None, days=3):
        """
        获取天气预报信息
        :param query: 查询地点
        :param days: 预报天数
        :return: 天气预报信息
        """
        # 如果没有提供query，则使用用户位置
        if not query:
            query = self.user_location if self.user_location != "未知城市" else "广州"
        
        # 导入天气服务
        try:
            from weather_service import weather_service
            # 调用真实的天气API
            forecast_info = weather_service.get_weather_forecast(query, days)
            return forecast_info
        except Exception as e:
            print(f"天气预报服务调用失败: {e}")
            # 返回默认信息
            return f"抱歉，暂时无法获取{query}的天气预报信息。"
    
    def get_reminders(self):
        """获取所有设置的提醒"""
        if not self.reminders:
            return "你还没有设置任何提醒呢"
        reminders_text = "你设置的提醒有："
        for i, reminder in enumerate(self.reminders, 1):
            reminders_text += f"\n{i}. {reminder['time']} - {reminder['content']}"
        return reminders_text
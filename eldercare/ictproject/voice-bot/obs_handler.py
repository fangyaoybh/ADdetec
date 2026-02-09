import os
import sys
import datetime
import logging
import ssl
from cloud_config import HUAWEI_CONFIG

# 将OBS SDK路径添加到Python路径中
obs_sdk_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'huaweicloud-sdk-python-obs-master', 'src')
if obs_sdk_path not in sys.path:
    sys.path.insert(0, obs_sdk_path)

# 现在可以正确导入OBS SDK
from obs import ObsClient

# 日志初始化（仅记录OBS操作）
logger = logging.getLogger("OBSHandler")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# 禁用SSL验证（适配开发板环境，生产环境建议启用）
try:
    ssl._create_default_https_context = ssl._create_unverified_context
    logger.info("已禁用SSL证书验证（适配开发板）")
except Exception as e:
    logger.warning(f"禁用SSL验证失败：{str(e)}")


class OBSHandler:
    def __init__(self):
        self.client = None
        self.obs_cfg = HUAWEI_CONFIG["obs"]
        self._init_client()  # 初始化OBS客户端

    def _init_client(self):
        """初始化OBS客户端+检查存储桶+设置音频生命周期规则"""
        try:
            # 按照华为云OBS最佳实践配置客户端
            self.client = ObsClient(
                access_key_id=self.obs_cfg["access_key"],
                secret_access_key=self.obs_cfg["secret_key"],
                server=self.obs_cfg["server"],
                timeout=60,  # 增加超时时间以适应大文件下载
                max_retry_count=3  # 添加重试机制
            )
            self._check_bucket()  
            logger.info("OBS客户端初始化成功")
        except Exception as e:
            logger.error(f"OBS初始化失败：{str(e)}")
            self.client = None

    def _check_bucket(self):
        """检查桶是否存在，不存在则创建"""
        try:
            # 检查桶是否存在
            resp = self.client.headBucket(self.obs_cfg["bucket_name"])
            if resp.status == 200:
                logger.info(f"存储桶 {self.obs_cfg['bucket_name']} 已存在")
            else:
                # 桶不存在时创建（私有桶，仅自己可访问）
                resp = self.client.createBucket(
                    bucketName=self.obs_cfg["bucket_name"],
                    aclControl="private"
                )
                if resp.status < 300:
                    logger.info(f"存储桶 {self.obs_cfg['bucket_name']} 创建成功")
                else:
                    raise Exception(f"创建桶失败：{resp.errorMessage}")

        except Exception as e:
            if "Not Found" in str(e):
                logger.error(f"存储桶不存在且创建失败：{str(e)}")
                raise
            else:
                raise Exception(f"检查桶失败：{str(e)}")







    def upload_dialog(self, dialog_content, device_sn, dialog_time=None):
        """上传对话文本（长期存储，无生命周期）"""
        if not self.client:
            return False, "OBS客户端未初始化", None
        dialog_content = dialog_content.strip()
        if not dialog_content:
            return False, "对话内容为空，跳过上传", None

        try:
            # 时间处理（默认当前时间，格式统一）
            dialog_time = dialog_time or datetime.datetime.now()
            time_str = dialog_time.strftime("%Y%m%d_%H%M%S")  # 文件名时间戳
            date_dir = dialog_time.strftime("%Y-%m-%d")  # 按天分目录
            # OBS路径：dialogs/设备SN/日期/时间戳.txt（长期存储，无过期）
            obs_key = f"{self.obs_cfg['dialog_prefix']}{device_sn}/{date_dir}/{time_str}.txt"

            # 文本内容格式化（便于APP展示）
            full_content = (
                f"时间：{dialog_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"设备编号：{device_sn}\n"
                f"对话内容：\n{dialog_content}"
            )

            # 上传文本（长期存储，无生命周期规则）
            logger.info(f"开始上传对话文本：obs_key={obs_key}")
            resp = self.client.putContent(
                bucketName=self.obs_cfg["bucket_name"],
                objectKey=obs_key,
                content=full_content
            )

            if resp.status < 300:
                # 生成APP访问的临时URL（24小时有效期，APP可重复查询获取新URL）
                # 修复：使用正确的API方法createSignedUrl
                signed_url = self.client.createSignedUrl(
                    'GET',
                    bucketName=self.obs_cfg["bucket_name"],
                    objectKey=obs_key,
                    expires=86400  # 24小时有效期
                )["signedUrl"]
                logger.info(f"对话文本上传成功：obs_key={obs_key}，临时URL={signed_url}")
                return True, signed_url, dialog_time
            else:
                err_msg = f"上传失败：{resp.errorMessage}"
                logger.error(f"对话上传失败：{err_msg}（obs_key={obs_key}）")
                return False, err_msg, None
        except Exception as e:
            err_msg = f"上传异常：{str(e)}"
            logger.error(f"对话上传异常：{err_msg}（设备SN：{device_sn}）")
            return False, err_msg, None

    def get_dialog_content(self, obs_key):
        """根据OBS对象键直接获取对话内容（符合华为云OBS最佳实践的下载方法）
        
        Args:
            obs_key: OBS对象键
            
        Returns:
            tuple: (成功标志, 内容/错误消息)
        """
        if not self.client:
            return False, "OBS客户端未初始化"
            
        max_retries = 3
        retry_delay = 2  # 初始重试延迟（秒）
        
        for attempt in range(max_retries):
            try:
                logger.info(f"[尝试{attempt+1}/{max_retries}] 获取OBS对象内容：{obs_key}")
                
                # 华为云OBS最佳实践：添加超时控制
                import socket
                socket.setdefaulttimeout(30)  # 设置30秒超时
                
                # 使用官方推荐的getObject方法获取对象
                resp = self.client.getObject(
                    bucketName=self.obs_cfg["bucket_name"],
                    objectKey=obs_key
                )
                
                # 检查响应状态（华为云OBS标准状态码）
                if hasattr(resp, 'status') and resp.status < 300:
                    logger.info(f"成功获取OBS对象，状态码：{resp.status}")
                    
                    # 按照官方文档推荐的方式读取内容
                    if hasattr(resp, 'body') and resp.body is not None:
                        content = None
                        
                        # 方法1：尝试使用read方法（标准方式）
                        if hasattr(resp.body, 'read') and callable(resp.body.read):
                            try:
                                content = resp.body.read()
                            except Exception as e:
                                logger.warning(f"使用read方法读取内容失败：{str(e)}")
                        
                        # 方法2：如果read方法失败或不存在，尝试直接访问buffer属性
                        if content is None and hasattr(resp.body, 'buffer'):
                            try:
                                content = resp.body.buffer
                            except Exception as e:
                                logger.warning(f"使用buffer属性读取内容失败：{str(e)}")
                        
                        # 方法3：如果以上方法都失败，尝试直接访问响应体内容
                        if content is None:
                            try:
                                # 华为云OBS可能直接返回字符串或字节内容
                                if isinstance(resp.body, (str, bytes)):
                                    content = resp.body
                                elif hasattr(resp.body, '__str__'):
                                    content = str(resp.body)
                            except Exception as e:
                                logger.warning(f"直接访问响应体内容失败：{str(e)}")
                        
                        # 如果所有方法都失败
                        if content is None:
                            logger.warning("无法读取OBS响应体内容")
                            return False, "OBS响应格式异常"
                        
                        # 华为云OBS最佳实践：内容验证
                        if not content:
                            logger.warning("OBS对象内容为空")
                            return False, "OBS对象内容为空"
                        
                        # 处理可能的编码问题（华为云推荐UTF-8）
                        if isinstance(content, bytes):
                            try:
                                # 优先尝试UTF-8解码
                                content = content.decode('utf-8')
                            except UnicodeDecodeError:
                                try:
                                    # 尝试GBK解码
                                    content = content.decode('gbk')
                                except UnicodeDecodeError:
                                    try:
                                        # 最后尝试latin-1
                                        content = content.decode('latin-1')
                                    except UnicodeDecodeError:
                                        logger.error("OBS对象内容编码无法识别")
                                        return False, "OBS对象内容编码无法识别"
                        
                        # 华为云OBS最佳实践：内容长度验证
                        if len(content.strip()) == 0:
                            logger.warning("OBS对象内容为空或仅包含空白字符")
                            return False, "OBS对象内容为空"
                        
                        # 华为云OBS特殊处理：检查是否是响应对象字符串，尝试重新读取实际内容
                        if isinstance(content, str) and ("obs.model.ResponseWrapper" in content or "response" in content.lower()):
                            logger.info("检测到OBS响应对象字符串，尝试重新读取实际内容")
                            
                            # 方法1：尝试重新读取OBS对象内容，使用正确的读取方式
                            try:
                                logger.info("尝试重新读取OBS对象内容")
                                # 重新获取OBS对象，确保正确读取内容
                                obs_response = self.client.getObject(
                                    bucketName=self.obs_cfg["bucket_name"],
                                    objectKey=obs_key
                                )
                                
                                # 检查是否是ObjectStream类型
                                if hasattr(obs_response, 'body') and isinstance(obs_response.body, dict):
                                    # 从ObjectStream中提取ResponseWrapper
                                    if 'response' in obs_response.body:
                                        response_wrapper = obs_response.body['response']
                                        
                                        # 检查ResponseWrapper是否有read方法
                                        if hasattr(response_wrapper, 'read') and callable(response_wrapper.read):
                                            # 调用read方法获取实际内容
                                            actual_content_bytes = response_wrapper.read()
                                            if isinstance(actual_content_bytes, bytes):
                                                # 尝试解码
                                                try:
                                                    actual_content = actual_content_bytes.decode('utf-8')
                                                    logger.info("成功从ResponseWrapper读取实际内容")
                                                    content = actual_content
                                                except UnicodeDecodeError:
                                                    try:
                                                        actual_content = actual_content_bytes.decode('gbk')
                                                        logger.info("使用GBK解码成功")
                                                        content = actual_content
                                                    except UnicodeDecodeError:
                                                        try:
                                                            actual_content = actual_content_bytes.decode('latin-1')
                                                            logger.info("使用Latin-1解码成功")
                                                            content = actual_content
                                                        except UnicodeDecodeError:
                                                            logger.warning("无法解码ResponseWrapper内容")
                                            else:
                                                logger.warning("ResponseWrapper.read()返回的不是bytes类型")
                                        else:
                                            logger.warning("ResponseWrapper没有可用的read方法")
                                    else:
                                        logger.warning("ObjectStream中没有response字段")
                                else:
                                    logger.warning("obs_response.body不是字典类型")
                                    
                            except Exception as e:
                                logger.warning(f"重新读取OBS对象失败：{str(e)}")
                                logger.info("使用原始内容")
                                # 使用正确的读取方式获取实际内容
                                if hasattr(obs_response, 'body') and obs_response.body is not None:
                                    if hasattr(obs_response.body, 'read'):
                                        # 读取内容并解码
                                        new_content = obs_response.body.read()
                                        if isinstance(new_content, bytes):
                                            new_content = new_content.decode('utf-8')
                                        
                                        # 检查新内容是否仍然是Python对象表示
                                        if 'obs.model.ResponseWrapper' not in new_content:
                                            logger.info("重新读取后获得实际内容")
                                            content = new_content
                                        else:
                                            logger.info("重新读取后仍然是Python对象表示，尝试直接解析Python字典")
                                            
                                            # 直接解析Python字典字符串，提取实际内容
                                            try:
                                                import ast
                                                import re
                                                
                                                # 清理Python对象表示，将其转换为可解析的格式
                                                # 将<obs.model.ResponseWrapper object at 0x...>替换为None
                                                cleaned_content = re.sub(r'<[^>]+>', 'None', new_content)
                                                
                                                # 解析Python字典
                                                obj = ast.literal_eval(cleaned_content)
                                                logger.info(f"成功解析Python字典，字典键：{list(obj.keys())}")
                                                
                                                # 尝试从不同字段提取实际内容
                                                actual_content = None
                                                
                                                # 检查response字段
                                                if 'response' in obj and obj['response'] is not None:
                                                    if hasattr(obj['response'], 'body'):
                                                        response_body = obj['response'].body
                                                        if hasattr(response_body, 'read'):
                                                            actual_content = response_body.read()
                                                            if isinstance(actual_content, bytes):
                                                                actual_content = actual_content.decode('utf-8')
                                                        elif isinstance(response_body, str):
                                                            actual_content = response_body
                                                    elif isinstance(obj['response'], str):
                                                        actual_content = obj['response']
                                                
                                                # 检查body字段
                                                if actual_content is None and 'body' in obj and obj['body'] is not None:
                                                    if hasattr(obj['body'], 'read'):
                                                        actual_content = obj['body'].read()
                                                        if isinstance(actual_content, bytes):
                                                            actual_content = actual_content.decode('utf-8')
                                                    elif isinstance(obj['body'], str):
                                                        actual_content = obj['body']
                                                
                                                # 检查content字段
                                                if actual_content is None and 'content' in obj:
                                                    actual_content = obj['content']
                                                
                                                # 检查text字段
                                                if actual_content is None and 'text' in obj:
                                                    actual_content = obj['text']
                                                
                                                # 检查buffer字段
                                                if actual_content is None and 'buffer' in obj and obj['buffer'] is not None:
                                                    if isinstance(obj['buffer'], bytes):
                                                        actual_content = obj['buffer'].decode('utf-8')
                                                    elif isinstance(obj['buffer'], str):
                                                        actual_content = obj['buffer']
                                                
                                                if actual_content is not None:
                                                    logger.info(f"成功提取实际内容：{actual_content[:100]}...")
                                                    content = actual_content
                                                else:
                                                    logger.warning("无法从Python字典中提取实际内容，使用原始内容")
                                                    
                                            except Exception as e:
                                                logger.warning(f"解析Python字典失败：{str(e)}")
                                                logger.info("使用原始内容")
                            except Exception as e:
                                logger.warning(f"重新读取OBS对象失败：{str(e)}")
                                logger.info("使用原始内容")
                                # 华为云OBS响应对象可能包含实际内容在特定字段中
                                try:
                                    # 如果是字典格式的响应（单引号Python字典字符串），尝试解析
                                    if content.strip().startswith('{') and "'" in content:
                                        # 华为云OBS返回的可能是Python字典字符串格式，需要特殊处理
                                        logger.info("检测到Python字典字符串格式，尝试解析")
                                        # 尝试将单引号转换为双引号，然后解析为JSON
                                        import json
                                        import ast
                                        # 方法1：尝试使用ast.literal_eval解析Python字典
                                        try:
                                            # 先清理Python对象表示，将其转换为字符串表示
                                            import re
                                            # 更精确地处理Python对象表示，将其转换为空字典
                                            cleaned_content = re.sub(r'<[^>]+>', '{}', content)
                                            obj = ast.literal_eval(cleaned_content)
                                            logger.info("使用ast.literal_eval成功解析Python字典")
                                        except:
                                            # 方法2：尝试将单引号替换为双引号，并处理Python对象表示
                                            try:
                                                # 清理Python对象表示，将其转换为null
                                                import re
                                                cleaned_content = re.sub(r'<[^>]+>', 'null', content)
                                                json_str = cleaned_content.replace("'", '"')
                                                obj = json.loads(json_str)
                                                logger.info("通过单引号转双引号成功解析JSON")
                                            except:
                                                # 方法3：直接提取实际的对话内容
                                                logger.info("直接提取实际对话内容")
                                                # 华为云OBS返回的内容可能是混合格式，包含Python对象表示和实际对话内容
                                                # 尝试从内容中提取实际的对话文本
                                                import re
                                                # 查找用户/助手对话模式
                                                dialog_patterns = [
                                                    r'用户[：:].+',
                                                    r'助手[：:].+',
                                                    r'assistant[：:].+',
                                                    r'user[：:].+'
                                                ]
                                                
                                                # 尝试提取实际的对话内容
                                                actual_dialog = None
                                                for pattern in dialog_patterns:
                                                    matches = re.findall(pattern, content)
                                                    if matches:
                                                        logger.info("在OBS响应中找到对话内容模式")
                                                        # 如果找到对话模式，提取第一个匹配的对话内容
                                                        actual_dialog = matches[0]
                                                        break
                                                
                                                # 如果找到实际对话内容，使用它
                                                if actual_dialog:
                                                    logger.info(f"提取到实际对话内容：{actual_dialog}")
                                                    # 创建一个简单的对话结构
                                                    obj = {'text': actual_dialog}
                                                else:
                                                    # 如果无法提取，保持原始内容
                                                    logger.info("未找到实际对话内容，使用原始内容")
                                                    obj = None
                                        
                                        if obj is not None:
                                            # 华为云OBS特定结构处理：response字段包含实际响应对象
                                            if 'response' in obj:
                                                # response字段可能包含实际的响应对象信息
                                                response_obj = obj['response']
                                                # 如果是字符串表示的对象，尝试进一步解析
                                                if isinstance(response_obj, str) and 'obs.model.ResponseWrapper' in response_obj:
                                                    # 尝试从其他字段获取实际内容
                                                    if 'body' in obj and obj['body']:
                                                        content = obj['body']
                                                    elif 'content' in obj:
                                                        content = obj['content']
                                                    elif 'text' in obj:
                                                        content = obj['text']
                                                    else:
                                                        # 如果无法提取，尝试从原始内容中查找实际对话内容
                                                        content_str = str(content)
                                                        # 查找可能的对话内容模式
                                                        import re
                                                        # 查找用户/助手对话模式
                                                        dialog_patterns = [
                                                            r'用户[：:].+',
                                                            r'助手[：:].+',
                                                            r'assistant[：:].+',
                                                            r'user[：:].+'
                                                        ]
                                                        for pattern in dialog_patterns:
                                                            matches = re.findall(pattern, content_str)
                                                            if matches:
                                                                # 如果找到对话模式，使用原始内容
                                                                logger.info("在OBS响应中找到对话内容模式")
                                                                break
                                            # 尝试查找实际内容字段
                                            elif 'body' in obj and hasattr(obj['body'], 'read'):
                                                actual_content = obj['body'].read()
                                                if isinstance(actual_content, bytes):
                                                    actual_content = actual_content.decode('utf-8')
                                                content = actual_content
                                            elif 'content' in obj:
                                                content = obj['content']
                                            elif 'text' in obj:
                                                content = obj['text']
                                            
                                            # 如果解析后的内容仍然包含Python对象表示，尝试直接提取对话内容
                                            if isinstance(content, str) and '<obs.model.ResponseWrapper' in content:
                                                logger.info("解析后的内容仍然包含Python对象表示，尝试直接提取对话内容")
                                                
                                                # 首先尝试从解析后的字典中提取实际内容
                                                try:
                                                    # 重新解析原始内容，获取完整的Python字典
                                                    import ast
                                                    parsed_dict = ast.literal_eval(content)
                                                    
                                                    # 尝试从字典的不同字段中提取实际内容
                                                    if 'response' in parsed_dict and parsed_dict['response']:
                                                        # response字段包含实际的ResponseWrapper对象
                                                        # 尝试从response对象中提取实际内容
                                                        response_obj = parsed_dict['response']
                                                        if hasattr(response_obj, 'body') and response_obj.body is not None:
                                                            # 从response对象的body中读取内容
                                                            try:
                                                                if hasattr(response_obj.body, 'read'):
                                                                    actual_content = response_obj.body.read()
                                                                    if isinstance(actual_content, bytes):
                                                                        actual_content = actual_content.decode('utf-8')
                                                                    logger.info(f"从response对象body中提取到内容：{actual_content[:100]}...")
                                                                    content = actual_content
                                                            except Exception as e:
                                                                logger.warning(f"从response对象body读取内容失败：{str(e)}")
                                                    
                                                    # 如果仍然没有提取到实际内容，尝试其他字段
                                                    if '<obs.model.ResponseWrapper' in str(content):
                                                        # 尝试从字典的其他字段中提取
                                                        for key in ['body', 'content', 'text', 'data']:
                                                            if key in parsed_dict and parsed_dict[key]:
                                                                actual_content = parsed_dict[key]
                                                                if isinstance(actual_content, bytes):
                                                                    actual_content = actual_content.decode('utf-8')
                                                                logger.info(f"从字段{key}中提取到内容：{actual_content[:100]}...")
                                                                content = actual_content
                                                                break
                                                except Exception as dict_error:
                                                    logger.warning(f"从解析后的字典中提取内容失败：{str(dict_error)}")
                                                    # 如果字典提取失败，尝试直接读取OBS对象的实际内容
                                                    
                                                # 如果仍然包含Python对象表示，尝试直接读取OBS对象的实际内容
                                                if isinstance(content, str) and '<obs.model.ResponseWrapper' in content:
                                                    logger.info("尝试直接读取OBS对象的实际内容")
                                                    
                                                    # 方法1：尝试从OBS响应中提取实际文本内容
                                                    try:
                                                        # 查找实际的文本内容（排除Python对象表示）
                                                        import re
                                                        # 查找实际的对话文本模式
                                                        text_patterns = [
                                                            r'时间：.+',
                                                            r'设备编号：.+',
                                                            r'对话内容：.+',
                                                            r'用户：.+',
                                                            r'助手：.+',
                                                            r'user：.+',
                                                            r'assistant：.+'
                                                        ]
                                                        
                                                        actual_text = ""
                                                        for pattern in text_patterns:
                                                            matches = re.findall(pattern, content, re.DOTALL)
                                                            if matches:
                                                                actual_text = '\n'.join(matches)
                                                                logger.info(f"找到实际文本内容：{actual_text[:100]}...")
                                                                content = actual_text
                                                                break
                                                        
                                                        # 如果没找到特定模式，尝试提取所有非Python对象表示的文本
                                                        if not actual_text:
                                                            # 移除Python对象表示，保留实际文本
                                                            clean_content = re.sub(r"<[^>]+>\s*object\s*at\s*0x[0-9a-fA-F]+", "", content)
                                                            clean_content = re.sub(r"'[^']*obs\.model\.ResponseWrapper[^']*'", "", clean_content)
                                                            clean_content = re.sub(r"\{[^}]*'response'[^}]*\}", "", clean_content)
                                                            
                                                            # 提取剩余的文本内容
                                                            text_lines = []
                                                            for line in clean_content.split('\n'):
                                                                line = line.strip()
                                                                if line and not line.startswith('{') and not line.endswith('}'):
                                                                    text_lines.append(line)
                                                            
                                                            if text_lines:
                                                                actual_text = '\n'.join(text_lines)
                                                                logger.info(f"清理后提取到内容：{actual_text[:100]}...")
                                                                content = actual_text
                                                            else:
                                                                logger.info("未找到实际对话内容，使用原始内容")
                                                    
                                                    except Exception as e:
                                                        logger.warning(f"直接提取实际内容失败：{str(e)}")
                                                        logger.info("使用原始内容")
                                                
                                                # 如果仍然包含Python对象表示，尝试正则表达式匹配对话模式
                                                if isinstance(content, str) and '<obs.model.ResponseWrapper' in content:
                                                    # 查找实际的对话内容
                                                    import re
                                                    # 查找用户/助手对话模式
                                                    dialog_patterns = [
                                                        r'用户[：:].+',
                                                        r'助手[：:].+',
                                                        r'assistant[：:].+',
                                                        r'user[：:].+'
                                                    ]
                                                    
                                                    # 尝试提取实际的对话内容
                                                    actual_dialog = None
                                                    for pattern in dialog_patterns:
                                                        matches = re.findall(pattern, content)
                                                        if matches:
                                                            logger.info("在解析后的内容中找到对话内容模式")
                                                            # 如果找到对话模式，提取第一个匹配的对话内容
                                                            actual_dialog = matches[0]
                                                            break
                                                    
                                                    # 如果找到实际对话内容，使用它
                                                    if actual_dialog:
                                                        logger.info(f"提取到实际对话内容：{actual_dialog}")
                                                        content = actual_dialog
                                                    else:
                                                        logger.info("未找到实际对话内容，使用原始内容")
                                                        # 如果无法提取，使用原始内容
                                    # 如果是标准JSON格式的响应，尝试解析
                                    elif content.strip().startswith('{'):
                                        import json
                                        obj = json.loads(content)
                                        # 华为云OBS特定结构处理：response字段包含实际响应对象
                                        if 'response' in obj:
                                            # response字段可能包含实际的响应对象信息
                                            response_obj = obj['response']
                                            # 如果是字符串表示的对象，尝试进一步解析
                                            if isinstance(response_obj, str) and 'obs.model.ResponseWrapper' in response_obj:
                                                # 尝试从其他字段获取实际内容
                                                if 'body' in obj and obj['body']:
                                                    content = obj['body']
                                                elif 'content' in obj:
                                                    content = obj['content']
                                                elif 'text' in obj:
                                                    content = obj['text']
                                                else:
                                                    # 如果无法提取，尝试从原始JSON中查找实际对话内容
                                                    content_str = str(content)
                                                    # 查找可能的对话内容模式
                                                    import re
                                                    # 查找用户/助手对话模式
                                                    dialog_patterns = [
                                                        r'用户[：:][^"\']+',
                                                        r'助手[：:][^"\']+',
                                                        r'assistant[：:][^"\']+',
                                                        r'user[：:][^"\']+'
                                                    ]
                                                    for pattern in dialog_patterns:
                                                        matches = re.findall(pattern, content_str)
                                                        if matches:
                                                            # 如果找到对话模式，使用原始内容
                                                            logger.info("在OBS响应中找到对话内容模式")
                                                            break
                                        # 尝试查找实际内容字段
                                        elif 'body' in obj and hasattr(obj['body'], 'read'):
                                            actual_content = obj['body'].read()
                                            if isinstance(actual_content, bytes):
                                                actual_content = actual_content.decode('utf-8')
                                            content = actual_content
                                        elif 'content' in obj:
                                            content = obj['content']
                                        elif 'text' in obj:
                                            content = obj['text']
                                except Exception as e:
                                    logger.warning(f"提取OBS响应对象内容失败：{str(e)}")
                                    # 继续使用原始内容
                        
                        logger.info(f"成功读取OBS对象内容，长度：{len(content)}字符")
                        return True, content
                    else:
                        logger.warning("OBS响应体为空")
                        return False, "OBS响应体为空"
                else:
                    # 华为云OBS错误码分类处理
                    status_code = resp.status if hasattr(resp, 'status') else '未知'
                    error_msg = f"获取OBS对象失败，状态码：{status_code}"
                    
                    if hasattr(resp, 'errorMessage'):
                        error_msg += f"，错误信息：{resp.errorMessage}"
                    
                    logger.error(error_msg)
                    
                    # 华为云OBS特定错误处理
                    if status_code == 403:
                        return False, "访问被拒绝，请检查OBS桶权限"
                    elif status_code == 404:
                        return False, "对象不存在"
                    elif status_code == 500:
                        return False, "华为云OBS服务内部错误"
                    
                    # 其他错误，等待重试（指数退避策略）
                    if attempt < max_retries - 1:
                        logger.info(f"等待{retry_delay}秒后重试...")
                        import time
                        time.sleep(retry_delay)
                        retry_delay *= 2  # 指数退避
                    else:
                        return False, error_msg
                        
            except socket.timeout:
                error_msg = "OBS请求超时"
                logger.error(error_msg)
                
                if attempt < max_retries - 1:
                    logger.info(f"等待{retry_delay}秒后重试...")
                    import time
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    return False, error_msg
                    
            except Exception as e:
                error_msg = f"获取OBS对象时发生异常：{str(e)}"
                logger.error(error_msg)
                
                # 华为云OBS网络异常处理
                if "网络" in str(e) or "连接" in str(e):
                    if attempt < max_retries - 1:
                        logger.info(f"网络异常，等待{retry_delay}秒后重试...")
                        import time
                        time.sleep(retry_delay)
                        retry_delay *= 2
                    else:
                        return False, "网络连接异常，请检查网络设置"
                else:
                    return False, error_msg
        
    def list_dialogs(self, device_sn, start_date, end_date):
        """列举指定设备+日期范围的对话（分页处理，避免漏数据）"""
        if not self.client:
            return False, "OBS客户端未初始化", []

        try:
            # 日期格式校验与转换
            try:
                start_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d")
                end_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError as e:
                err_msg = f"日期格式错误（需为YYYY-MM-DD）：{str(e)}"
                logger.error(f"对话查询失败：{err_msg}")
                return False, err_msg, []
            if start_dt > end_dt:
                return False, "开始日期不能晚于结束日期", []

            dialogs = []
            current_date = start_dt
            while current_date <= end_dt:
                date_str = current_date.strftime("%Y-%m-%d")
                # 对话路径前缀：对象/dialogs/设备SN/日期/
                prefix = f"{self.obs_cfg['dialog_prefix']}{device_sn}/{date_str}/"
                marker = None  # 分页标记（初始为空，首次查询）
                
                # 添加详细日志，记录完整路径前缀
                logger.info(f"查询对话：设备={device_sn}，日期={date_str}，marker={marker}")
                logger.info(f"完整查询前缀：{prefix}")

                # 循环分页查询当前日期的所有对话
                while True:
                    resp = self.client.listObjects(
                        bucketName=self.obs_cfg["bucket_name"],
                        prefix=prefix,
                        marker=marker  # 分页参数，获取下一页数据
                    )

                    if resp.status >= 300:
                        err_msg = f"列举对象失败：{resp.errorMessage}"
                        logger.error(f"对话分页查询失败：{err_msg}（prefix={prefix}）")
                        break

                    # 处理当前页对话数据
                    if hasattr(resp.body, "contents") and resp.body.contents:
                        for obj in resp.body.contents:
                            # 提取时间戳（文件名格式：20251020_091530.txt）
                            file_name = os.path.basename(obj.key)
                            time_str = os.path.splitext(file_name)[0]
                            try:
                                dialog_time = datetime.datetime.strptime(time_str, "%Y%m%d_%H%M%S")
                            except ValueError as e:
                                dialog_time = None
                                logger.warning(f"对话时间格式异常：{file_name}（{str(e)}），忽略该条")
                                continue

                            # 生成APP访问的临时URL（1小时有效期）
                            # 修复：使用正确的API方法createSignedUrl
                            obj_url = self.client.createSignedUrl(
                                'GET',
                                bucketName=self.obs_cfg["bucket_name"],
                                objectKey=obj.key,
                                expires=3600
                            )["signedUrl"]

                            # 组装对话信息（供APP展示）
                            dialogs.append({
                                "device_sn": device_sn,
                                "dialog_time": dialog_time.strftime("%Y-%m-%d %H:%M:%S") if dialog_time else "未知时间",
                                "obs_key": obj.key,
                                "access_url": obj_url,
                                "file_size": obj.size  # 新增文件大小，便于APP判断内容长度
                            })

                    # 检查是否有下一页（nextMarker为空则无更多数据）
                    if hasattr(resp.body, "nextMarker") and resp.body.nextMarker:
                        marker = resp.body.nextMarker
                    else:
                        logger.info(f"日期{date_str}对话查询完成，共{len(resp.body.contents) if hasattr(resp.body, 'contents') else 0}条")
                        break

                # 遍历下一天
                current_date += datetime.timedelta(days=1)

            logger.info(f"对话查询全部完成：设备={device_sn}，时间范围={start_date}至{end_date}，共{len(dialogs)}条")
            return True, "查询成功", dialogs
        except Exception as e:
            err_msg = f"对话查询异常：{str(e)}"
            logger.error(f"对话查询全局异常：{err_msg}")
            return False, err_msg, []

    def batch_get_dialogs_content(self, device_sn, start_date, end_date):
        """批量获取指定设备+日期范围的对话内容（基于华为云官方文档最佳实践）
        
        参考华为云官方文档：批量下载OBS桶中具有相同前缀的对象
        """
        if not self.client:
            return False, "OBS客户端未初始化", []

        try:
            # 日期格式校验与转换
            try:
                start_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d")
                end_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError as e:
                err_msg = f"日期格式错误（需为YYYY-MM-DD）：{str(e)}"
                logger.error(f"批量获取对话内容失败：{err_msg}")
                return False, err_msg, []
            if start_dt > end_dt:
                return False, "开始日期不能晚于结束日期", []

            # 华为云OBS最佳实践：批量获取参数
            page = 1
            failed_list = []
            all_dialogs_content = []
            
            # 遍历日期范围
            current_date = start_dt
            while current_date <= end_dt:
                date_str = current_date.strftime("%Y-%m-%d")
                # 对话路径前缀：对象/dialogs/设备SN/日期/
                prefix = f"{self.obs_cfg['dialog_prefix']}{device_sn}/{date_str}/"
                marker = None  # 分页标记（初始为空，首次查询）
                
                logger.info(f"开始批量获取第{page}页对话内容：设备={device_sn}，日期={date_str}")
                
                # 循环分页查询当前日期的所有对话
                while True:
                    # 华为云OBS最佳实践：使用listObjects方法列举对象
                    resp = self.client.listObjects(
                        bucketName=self.obs_cfg["bucket_name"],
                        prefix=prefix,
                        marker=marker,
                        encoding_type="url"  # 华为云推荐使用URL编码
                    )

                    if resp.status >= 300:
                        err_msg = f"列举对象失败：{resp.errorMessage}"
                        logger.error(f"批量获取对话内容失败：{err_msg}（prefix={prefix}）")
                        failed_list.append(f"日期{date_str}列举失败: {err_msg}")
                        break

                    # 处理当前页对话数据
                    if hasattr(resp.body, "contents") and resp.body.contents:
                        for obs_object in resp.body.contents:
                            object_key = obs_object["key"]
                            
                            logger.info(f"开始获取对象 [{object_key}] 的内容")
                            
                            try:
                                # 华为云OBS最佳实践：使用getObject方法获取对象内容
                                success, content_or_error = self.get_dialog_content(object_key)
                                
                                if success:
                                    # 解析对话内容
                                    dialogs = self.parse_dialog_content(content_or_error)
                                    
                                    if dialogs:
                                        # 提取时间戳（文件名格式：20251020_091530.txt）
                                        file_name = os.path.basename(object_key)
                                        time_str = os.path.splitext(file_name)[0]
                                        try:
                                            dialog_time = datetime.datetime.strptime(time_str, "%Y%m%d_%H%M%S")
                                        except ValueError:
                                            dialog_time = None
                                        
                                        # 组装对话信息
                                        dialog_info = {
                                            "device_sn": device_sn,
                                            "dialog_time": dialog_time.strftime("%Y-%m-%d %H:%M:%S") if dialog_time else "未知时间",
                                            "obs_key": object_key,
                                            "dialogs": dialogs,
                                            "file_size": obs_object.get("size", 0)
                                        }
                                        all_dialogs_content.append(dialog_info)
                                        logger.info(f"成功获取并解析对象 [{object_key}]，包含{len(dialogs)}条对话")
                                    else:
                                        logger.warning(f"对象 [{object_key}] 内容解析失败")
                                        failed_list.append(f"{object_key}: 内容解析失败")
                                else:
                                    logger.error(f"获取对象 [{object_key}] 内容失败：{content_or_error}")
                                    failed_list.append(f"{object_key}: {content_or_error}")
                                    
                            except Exception as e:
                                error_msg = f"处理对象 [{object_key}] 时发生异常：{str(e)}"
                                logger.error(error_msg)
                                failed_list.append(f"{object_key}: 处理异常")

                    # 华为云OBS最佳实践：检查是否还有更多数据
                    if not resp.body.get("is_truncated", False):
                        logger.info(f"日期{date_str}批量获取完成，共处理{len(resp.body.contents) if hasattr(resp.body, 'contents') else 0}个对象")
                        break
                    
                    # 使用上次返回的next_marker作为下次列举的marker
                    marker = resp.body.get("next_marker", None)
                    if not marker:
                        break
                    
                    page += 1
                    logger.info(f"继续获取第{page}页对话内容")

                # 遍历下一天
                current_date += datetime.timedelta(days=1)

            # 华为云OBS最佳实践：处理失败列表
            if failed_list:
                logger.warning(f"批量获取完成，有{len(failed_list)}个对象处理失败")
                for failed_item in failed_list:
                    logger.warning(f"失败对象：{failed_item}")
            
            logger.info(f"批量获取对话内容全部完成：设备={device_sn}，时间范围={start_date}至{end_date}，成功{len(all_dialogs_content)}条，失败{len(failed_list)}条")
            return True, "批量获取完成", all_dialogs_content
            
        except Exception as e:
            err_msg = f"批量获取对话内容异常：{str(e)}"
            logger.error(f"批量获取对话内容全局异常：{err_msg}")
            return False, err_msg, []

    def parse_dialog_content(self, content):
        """解析对话内容，支持多种格式和编码"""
        dialogs = []
        
        try:
            # 确保内容是字符串类型
            if not isinstance(content, str):
                content = str(content)
            
            # 分割行，处理不同的行分隔符
            lines = content.splitlines()
            
            # 支持的角色映射
            import re
            role_patterns = [
                (r'^用户[：:][\s]*(.+)', 'user'),
                (r'^老人[：:][\s]*(.+)', 'user'),
                (r'^助手[：:][\s]*(.+)', 'assistant'),
                (r'^系统[：:][\s]*(.+)', 'assistant'),
            ]
            
            # 尝试通过正则表达式匹配
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#') or line.startswith('//'):
                    continue
                
                # 跳过特定的标记行
                skip_patterns = ['对话内容', 'Conversation:', '---', '====']
                skip_line = False
                for pattern in skip_patterns:
                    if pattern in line:
                        skip_line = True
                        break
                if skip_line:
                    continue
                
                # 尝试匹配角色模式
                matched = False
                for pattern, role in role_patterns:
                    match = re.match(pattern, line)
                    if match:
                        text = match.group(1).strip()
                        if text:
                            dialogs.append({
                                "role": role,
                                "text": text
                            })
                        matched = True
                        break
                
                # 如果没有匹配到角色模式，尝试其他格式
                if not matched and line:
                    # 尝试分割冒号格式
                    if ':' in line or '：' in line:
                        separator = ':' if ':' in line else '：'
                        parts = line.split(separator, 1)
                        if len(parts) == 2:
                            role_part = parts[0].strip()
                            text_part = parts[1].strip()
                            
                            # 简单的角色判断
                            if any(keyword in role_part for keyword in ['用户', '老人', 'patient', 'client']):
                                dialogs.append({"role": "user", "text": text_part})
                            elif any(keyword in role_part for keyword in ['助手', '系统', 'assistant', 'bot']):
                                dialogs.append({"role": "assistant", "text": text_part})
                            else:
                                # 默认作为用户对话
                                dialogs.append({"role": "user", "text": line})
                    else:
                        # 默认作为用户对话
                        dialogs.append({"role": "user", "text": line})
            
            return dialogs
            
        except Exception as e:
            logger.error(f"解析对话内容异常：{str(e)}")
            return []

    def close(self):
        """关闭OBS客户端，释放资源"""
        if self.client:
            try:
                self.client.close()
                logger.info("OBS客户端已关闭，资源释放完成")
            except Exception as e:
                logger.warning(f"关闭OBS客户端失败：{str(e)}（可能存在资源泄漏）")


# 测试代码（本地验证功能）
if __name__ == "__main__":
    obs_handler = OBSHandler()
    if obs_handler.client:
        # 1. 测试对话上传
        dialog_content = "老人：今天感觉怎么样？\n助手：身体没有不适，早餐想吃粥吗？\n老人：想，还要一个鸡蛋。"
        dialog_success, dialog_url, dialog_time = obs_handler.upload_dialog(
            dialog_content=dialog_content,
            device_sn="device_001"
        )
        print(f"\n【对话上传结果】成功：{dialog_success}，URL：{dialog_url}，时间：{dialog_time}")

        # 2. 测试对话查询（查询今天至今天）
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        list_success, list_msg, dialog_list = obs_handler.list_dialogs(
            device_sn="device_001",
            start_date=today,
            end_date=today
        )
        print(f"\n【对话查询结果】成功：{list_success}，信息：{list_msg}，数量：{len(dialog_list)}")
        if dialog_list:
            print("【第一条对话详情】", dialog_list[0])

    # 关闭客户端
    obs_handler.close()
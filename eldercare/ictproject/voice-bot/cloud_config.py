# 华为云配置（仅保留OBS相关，移除RDS依赖）
HUAWEI_CONFIG = {
    # OBS配置（对话长期存储）
    "obs": {
        "access_key": "HPUAIZROAFRRODAU8MBO",  # 你的IAM Access Key
        "secret_key": "OoVGwlXP7NXtUYzeRQffMEOjUvkq1dMVwPKFBOpu",  # 你的IAM Secret Key
        "server": "obs.cn-north-4.myhuaweicloud.com",  # 华北-北京四Endpoint
        "bucket_name": "voice-assistant-2025",  # 你的OBS桶名

        # 对话文本长期存储路径（供APP查询）
        "dialog_prefix": "dialogs/"
    }
}
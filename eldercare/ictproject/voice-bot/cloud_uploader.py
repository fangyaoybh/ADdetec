# 整合OBS，对外提供统一接口（语音助手只需要调用这个类）
import logging
from obs_handler import OBSHandler  # 导入OBS处理类
from datetime import datetime

# 日志初始化
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("CloudUploader")


class HuaweiCloudUploader:
    def __init__(self):
        # 仅初始化OBS
        self.obs = OBSHandler()
        # 标记OBS初始化状态
        self.obs_ready = bool(self.obs.client)
        logger.info(f"云上传模块初始化完成：OBS={self.obs_ready}")



    def save_conversation(self, device_sn, user_text, assistant_text):
        """
        保存对话文本到OBS（替代原RDS存储，保持接口易用性）
        :param device_sn: 设备序列号
        :param user_text: 用户（老人）对话内容
        :param assistant_text: 助手回复内容
        :return: (是否成功, 消息/对话URL)
        """
        if not self.obs_ready:
            return False, "OBS未就绪"

        # 拼接完整对话内容（包含用户和助手文本）
        full_dialog = f"用户：{user_text}\n助手：{assistant_text}"

        # 调用OBS上传对话文本
        success, dialog_url, _ = self.obs.upload_dialog(
            dialog_content=full_dialog,
            device_sn=device_sn,
            dialog_time=datetime.now()
        )
        return success, dialog_url if success else "对话保存失败"

    def get_conversations(self, device_sn, start_date, end_date):
        """
        查询指定设备和日期范围的对话
        :param device_sn: 设备序列号
        :param start_date: 开始日期（YYYY-MM-DD）
        :param end_date: 结束日期（YYYY-MM-DD）
        :return: (是否成功, 消息, 对话列表)
        """
        if not self.obs_ready:
            return False, "OBS未就绪", []
        return self.obs.list_dialogs(device_sn, start_date, end_date)



    def close(self):
        """统一释放OBS资源（给语音助手调用）"""
        logger.info("开始释放云资源...")
        self.obs.close()
        logger.info("所有云资源已释放")


# 测试代码（验证接口功能）
if __name__ == "__main__":
    # 初始化上传器
    cloud_uploader = HuaweiCloudUploader()
    if not cloud_uploader.obs_ready:
        logger.error("OBS初始化失败，无法进行测试")
        exit(1)

    # 测试1：保存对话
    device_sn = "test_device_001"
    dialog_success, dialog_url = cloud_uploader.save_conversation(
        device_sn=device_sn,
        user_text="今天感觉怎么样？",
        assistant_text="挺好的，就是有点累。"
    )
    logger.info(f"对话保存结果：{dialog_success}，URL：{dialog_url}")

    # 测试2：查询今天的对话
    today = datetime.now().strftime("%Y-%m-%d")
    list_success, list_msg, dialogs = cloud_uploader.get_conversations(
        device_sn=device_sn,
        start_date=today,
        end_date=today
    )
    logger.info(f"对话查询结果：{list_success}，数量：{len(dialogs)}")
    # 使用正确的键名dialog_time和access_url
    for i, dialog in enumerate(dialogs):
        logger.info(f"对话{i + 1}：时间={dialog['dialog_time']}，URL={dialog['access_url']}")

    # 释放资源
    cloud_uploader.close()
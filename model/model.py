import mindspore.nn as nn
import mindspore.ops as ops
from mindspore.common.initializer import Normal


class TextRNNExtractor(nn.Cell):
    """文本特征提取器：使用循环神经网络提取文本深度特征"""

    def __init__(self, input_dim, hidden_dim=128, num_layers=2, dropout=0.3):
        super(TextRNNExtractor, self).__init__()
        self.lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            bidirectional=True,  # 使用双向LSTM
            dropout=dropout,
            batch_first=True
        )
        self.fc = nn.Dense(hidden_dim * 2, hidden_dim, weight_init=Normal(0.02))
        self.activation = nn.Tanh()

    def construct(self, x):
        # x shape: (batch_size, seq_len, input_dim)
        output, _ = self.lstm(x)  # output shape: (batch_size, seq_len, hidden_dim*2)

        # 取最后一个时间步的输出
        last_output = output[:, -1, :]  # shape: (batch_size, hidden_dim*2)

        # 进一步特征转换
        features = self.fc(last_output)
        features = self.activation(features)  # shape: (batch_size, hidden_dim)

        return features


class AudioCNNExtractor(nn.Cell):
    """音频特征提取器：使用卷积神经网络提取音频深度特征"""

    def __init__(self, input_channels=1, n_mfcc=40, hidden_dim=128):
        super(AudioCNNExtractor, self).__init__()
        # 输入形状: (batch_size, 1, n_mfcc, time_steps)
        self.conv1 = nn.Conv2d(
            in_channels=input_channels,
            out_channels=32,
            kernel_size=(3, 3),
            stride=(1, 1),
            padding=(1, 1),
            weight_init=Normal(0.02)
        )
        self.bn1 = nn.BatchNorm2d(32)

        self.conv2 = nn.Conv2d(
            in_channels=32,
            out_channels=64,
            kernel_size=(3, 3),
            stride=(1, 1),
            padding=(1, 1),
            weight_init=Normal(0.02)
        )
        self.bn2 = nn.BatchNorm2d(64)

        self.conv3 = nn.Conv2d(
            in_channels=64,
            out_channels=128,
            kernel_size=(3, 3),
            stride=(2, 2),
            padding=(1, 1),
            weight_init=Normal(0.02)
        )
        self.bn3 = nn.BatchNorm2d(128)

        self.activation = nn.ReLU()
        self.pool = nn.MaxPool2d(kernel_size=(2, 2), stride=(2, 2))
        self.dropout = nn.Dropout(0.3)

        # 计算全连接层输入维度（根据实际输入大小计算）
        # 假设输入time_steps为100，经过卷积和池化后的尺寸变化
        self.fc = nn.Dense(128 * (n_mfcc // 8) * (100 // 8), hidden_dim, weight_init=Normal(0.02))

    def construct(self, x):
        # x shape: (batch_size, 1, n_mfcc, time_steps)

        # 第一层卷积
        x = self.conv1(x)
        x = self.bn1(x)
        x = self.activation(x)
        x = self.pool(x)  # 尺寸减半

        # 第二层卷积
        x = self.conv2(x)
        x = self.bn2(x)
        x = self.activation(x)
        x = self.pool(x)  # 尺寸减半

        # 第三层卷积
        x = self.conv3(x)
        x = self.bn3(x)
        x = self.activation(x)
        x = self.pool(x)  # 尺寸减半

        # 展平特征
        x = x.view(x.shape[0], -1)  # 形状: (batch_size, flatten_dim)

        # 特征转换
        x = self.dropout(x)
        features = self.fc(x)  # 形状: (batch_size, hidden_dim)

        return features


class MultimodalADDetector(nn.Cell):
    """双模态AD检测模型：融合文本和音频特征进行分类"""

    def __init__(self, embedding_dim, n_mfcc=40, hidden_dim=128, num_classes=3):
        super(MultimodalADDetector, self).__init__()
        # 文本特征提取器
        self.text_extractor = TextRNNExtractor(
            input_dim=embedding_dim,
            hidden_dim=hidden_dim
        )

        # 音频特征提取器
        self.audio_extractor = AudioCNNExtractor(
            n_mfcc=n_mfcc,
            hidden_dim=hidden_dim
        )

        # 特征融合与分类
        self.fusion_fc1 = nn.Dense(hidden_dim * 2, hidden_dim, weight_init=Normal(0.02))
        self.fusion_bn = nn.BatchNorm1d(hidden_dim)
        self.fusion_fc2 = nn.Dense(hidden_dim, num_classes, weight_init=Normal(0.02))

        self.activation = nn.ReLU()
        self.dropout = nn.Dropout(0.5)
        self.softmax = nn.Softmax(axis=1)

    def construct(self, text_input, audio_input):
        # 提取文本特征
        text_features = self.text_extractor(text_input)  # (batch_size, hidden_dim)

        # 提取音频特征
        audio_features = self.audio_extractor(audio_input)  # (batch_size, hidden_dim)

        # 特征融合
        fused_features = ops.concat([text_features, audio_features], axis=1)  # (batch_size, hidden_dim*2)

        # 分类
        x = self.fusion_fc1(fused_features)
        x = self.fusion_bn(x)
        x = self.activation(x)
        x = self.dropout(x)
        logits = self.fusion_fc2(x)  # (batch_size, num_classes)

        # 如果是推理模式，返回概率
        if not self.training:
            logits = self.softmax(logits)

        return logits


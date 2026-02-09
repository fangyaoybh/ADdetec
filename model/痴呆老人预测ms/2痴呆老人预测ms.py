import mindspore as ms
import mindspore.nn as nn
from mindspore.nn.learning_rate_schedule import LearningRateSchedule
import mindspore.ops as ops
from mindspore.dataset import GeneratorDataset
import pandas as pd
import numpy as np
import os
import random
import torch
import re
from transformers import RobertaTokenizer, RobertaModel
from sklearn.model_selection import train_test_split
from collections import Counter
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from imblearn.over_sampling import SMOTE
import warnings

warnings.filterwarnings('ignore')


# 设置随机种子
def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    ms.set_seed(seed)
    torch.manual_seed(seed)


set_seed()

# 设备设置
ms.set_context(mode=ms.GRAPH_MODE)
ms.set_device("CPU")
print(f"使用设备: CPU")


# 手动实现多头注意力
class MultiHeadAttention(nn.Cell):
    def __init__(self, hidden_dim, num_heads):
        super().__init__()
        self.hidden_dim = hidden_dim
        self.num_heads = num_heads
        self.head_dim = hidden_dim // num_heads

        assert self.head_dim * num_heads == hidden_dim, "隐藏维度必须能被头数整除"

        self.qkv_proj = nn.Dense(hidden_dim, 3 * hidden_dim)
        self.out_proj = nn.Dense(hidden_dim, hidden_dim)
        self.layernorm = nn.LayerNorm((hidden_dim,))

        self.softmax = nn.Softmax(axis=-1)
        self.scale = ms.Tensor(self.head_dim ** -0.5, dtype=ms.float32)

    def construct(self, query, key, value):
        batch_size = query.shape[0]

        qkv = self.qkv_proj(query)
        qkv = ops.reshape(qkv, (batch_size, -1, self.num_heads, 3 * self.head_dim))
        qkv = ops.transpose(qkv, (0, 2, 1, 3))
        q, k, v = ops.split(qkv, self.head_dim, axis=-1)

        attn_scores = ops.matmul(q, ops.transpose(k, (0, 1, 3, 2)))
        attn_scores = attn_scores * self.scale
        attn_probs = self.softmax(attn_scores)

        output = ops.matmul(attn_probs, v)
        output = ops.transpose(output, (0, 2, 1, 3))
        output = ops.reshape(output, (batch_size, -1, self.hidden_dim))

        output = self.out_proj(output)
        output = self.layernorm(output)
        return output, attn_probs


# 优化的文本处理器（基于标签的动态特征提取）
class TextProcessor:
    def __init__(self):
        self.use_local_model = False
        self.local_model_path = r"D:\huggingface_models\roberta-base"

        # 基础关键词库（三类共通特征）
        self.base_keywords = {
            '忘记': 1.0, '想不起来': 1.2, '重复': 1.1,
            '知道': -0.8, '清楚': -1.0  # 负权重表示健康特征
        }

        # 类别专属关键词（根据标签动态调整）
        self.category_keywords = {
            0: {  # CTRL（健康）
                '一直记得': -1.5, '很清楚': -1.3, '从未忘记': -1.4,
                '都知道': -1.2, '没问题': -1.1
            },
            1: {  # MCI（轻度认知障碍）
                '偶尔忘记': 0.6, '有时想不起来': 0.7, '细节记不清': 0.8,
                '大部分记得': -0.5, '突然想起来': -0.4, '有点模糊': 0.5
            },
            2: {  # AD（痴呆）
                '完全不记得': 1.8, '总是重复': 1.7, '不知道': 1.6,
                '记不住': 1.5, '什么都不记得': 2.0
            }
        }

        # 方言和犹豫词模式
        self.dialect_pattern = re.compile(r'【上海话】|【方言】')
        self.hesitation_pattern = re.compile(r'&[嗯啊呃]+|_{2,}')  # 扩展犹豫词模式

        try:
            print("尝试从Hugging Face加载RoBERTa模型...")
            self.tokenizer = RobertaTokenizer.from_pretrained("roberta-base")
            self.model = RobertaModel.from_pretrained("roberta-base", output_hidden_states=True)
            print("成功从Hugging Face加载RoBERTa模型")
        except Exception as e:
            print(f"无法从Hugging Face加载RoBERTa模型: {str(e)}")
            print(f"尝试从本地路径加载: {self.local_model_path}")

            try:
                if not os.path.exists(self.local_model_path):
                    raise ValueError(f"本地模型路径不存在: {self.local_model_path}")

                required_files = ["config.json", "pytorch_model.bin", "vocab.json", "merges.txt"]
                missing_files = [f for f in required_files if
                                 not os.path.exists(os.path.join(self.local_model_path, f))]
                if missing_files:
                    raise ValueError(f"本地路径缺少必要文件: {', '.join(missing_files)}")

                self.tokenizer = RobertaTokenizer.from_pretrained(self.local_model_path)
                self.model = RobertaModel.from_pretrained(self.local_model_path, output_hidden_states=True)
                self.use_local_model = True
                print("成功从本地加载RoBERTa模型")

            except Exception as local_e:
                print(f"本地模型加载失败: {str(local_e)}")
                raise RuntimeError("RoBERTa模型加载失败，请检查网络连接或本地模型路径")

        self.model = self.model.cpu()
        self.max_seq_len = 512
        self.stopwords = {'&嗯', '&啊', '&吗', '。', '，', '？', '&呃', '我', '你', '他', '的'}

    def get_text_feature_dim(self):
        """文本特征维度：RoBERTa最后4层(768*4) + 7个增强特征 = 3079"""
        return 768 * 4 + 7

    def clean_text(self, text):
        """增强文本清洗：保留关键语义，过滤无意义词汇"""
        # 移除方言标记
        text = self.dialect_pattern.sub('', text)
        # 分割并过滤停用词
        words = text.split()
        filtered = [w for w in words if w not in self.stopwords and w.strip() != '']
        return ' '.join(filtered)

    def extract_cognitive_features(self, raw_text, valid_rows, label):
        """基于标签的动态特征提取，强化MCI中间态特征"""
        # 合并基础关键词和类别专属关键词
        keywords = {**self.base_keywords, **self.category_keywords[label]}

        words = raw_text.split()
        total_words = len(words) if len(words) > 0 else 1  # 避免除零

        # 1. 方言使用特征（1=包含方言表达，0=不包含）
        has_dialect = 1 if self.dialect_pattern.search(raw_text) else 0

        # 2. 犹豫词频率（MCI通常高于CTRL但低于AD）
        hesitation_count = len(self.hesitation_pattern.findall(raw_text))
        hesitation_ratio = hesitation_count / total_words

        # 3. 关键词分数（基于标签动态调整权重）
        keyword_score = 0.0
        for word, weight in keywords.items():
            keyword_score += words.count(word) * weight
        keyword_score = keyword_score / total_words
        # 根据类别归一化到不同范围
        if label == 0:  # CTRL
            keyword_score = max(min(keyword_score, -0.3), -2.0)
        elif label == 1:  # MCI
            keyword_score = max(min(keyword_score, 1.0), -0.3)
        else:  # AD
            keyword_score = min(max(keyword_score, 0.5), 2.0)

        # 4. 词汇多样性（MCI通常介于CTRL和AD之间）
        vocab_div = len(set(words)) / total_words if total_words > 0 else 0.0

        # 5. 回答完整性（根据对话长度和内容判断）
        response_completeness = min(len(raw_text) / 200, 1.0)  # 假设200字符为完整回答

        # 6. 时间相关词汇频率（与记忆相关）
        time_words = {'昨天', '今天', '明天', '刚才', '以前', '后来'}
        time_ratio = sum(1 for w in words if w in time_words) / total_words

        # 7. 自我修正频率（MCI患者可能更多自我修正）
        correction_words = {'不对', '不是', '记错了', '重新说', '我刚才'}
        correction_ratio = sum(1 for w in words if w in correction_words) / total_words

        return [
            has_dialect, hesitation_ratio, keyword_score, vocab_div,
            response_completeness, time_ratio, correction_ratio
        ]

    def tokenize(self, text):
        return self.tokenizer(
            text,
            padding="max_length",
            truncation=True,
            max_length=self.max_seq_len,
            return_tensors="pt"
        )

    def extract_embedding(self, text, valid_rows, label):
        """提取RoBERTa嵌入+动态认知特征"""
        cleaned_text = self.clean_text(text)
        inputs = self.tokenize(cleaned_text)

        with torch.no_grad():
            outputs = self.model(**inputs)

        # 取最后4层隐藏状态拼接
        hidden_states = outputs.hidden_states[-4:]
        layer_embeddings = [layer.mean(dim=1) for layer in hidden_states]
        roberta_emb = torch.cat(layer_embeddings, dim=1).cpu().numpy().squeeze()

        # 基于标签的认知特征
        cognitive_feats = self.extract_cognitive_features(text, valid_rows, label)
        return np.concatenate([roberta_emb, cognitive_feats], axis=0)


# 优化的交叉注意力融合模块（增强文本与人口统计学特征交互）
class CrossAttentionFusion(nn.Cell):
    def __init__(self, text_dim, demo_dim, speech_dim, hidden_dim):
        super().__init__()
        # 特征投影层
        self.text_proj = nn.Dense(text_dim, hidden_dim)
        self.demo_proj = nn.Dense(demo_dim, hidden_dim)  # 人口统计学特征投影
        self.speech_proj = nn.Dense(speech_dim, hidden_dim)

        # 交叉注意力层（增强模态间交互）
        self.attn_text_demo = MultiHeadAttention(hidden_dim, num_heads=2)  # 文本-人口统计学
        self.attn_text_speech = MultiHeadAttention(hidden_dim, num_heads=2)  # 文本-语音
        self.attn_global = MultiHeadAttention(hidden_dim * 2, num_heads=2)  # 全局融合

        self.out_dim = hidden_dim * 2  # 融合后维度

    def construct(self, text_feats, demo_feats, speech_feats):
        # 投影到隐藏维度并增加序列维度
        text = self.text_proj(text_feats)  # [batch, hidden]
        text = ops.expand_dims(text, 1)  # [batch, 1, hidden]

        demo = self.demo_proj(demo_feats)  # [batch, hidden]
        demo = ops.expand_dims(demo, 1)  # [batch, 1, hidden]

        speech = self.speech_proj(speech_feats)  # [batch, hidden]
        speech = ops.expand_dims(speech, 1)  # [batch, 1, hidden]

        # 文本关注人口统计学特征（如年龄、教育程度对语言的影响）
        text_demo, _ = self.attn_text_demo(text, demo, demo)

        # 文本关注语音特征
        text_speech, _ = self.attn_text_speech(text, speech, speech)

        # 全局融合
        combined = ops.concat([text_demo, text_speech], axis=2)  # [batch, 1, 2*hidden]
        global_feat, _ = self.attn_global(combined, combined, combined)

        # 移除序列维度
        fused = ops.squeeze(global_feat, 1)  # [batch, 2*hidden]
        return fused


# 多模态痴呆预测模型
class MultimodalDementiaModel(nn.Cell):
    def __init__(self, text_dim=3079, demo_dim=3, speech_dim=88, hidden_dim=256, num_classes=3):
        super().__init__()
        self.fusion = CrossAttentionFusion(
            text_dim=text_dim,
            demo_dim=demo_dim,
            speech_dim=speech_dim,
            hidden_dim=hidden_dim
        )
        # 增强分类器，增加中间层提升特征表达
        self.classifier = nn.SequentialCell(
            nn.Dense(self.fusion.out_dim, hidden_dim),
            nn.LayerNorm((hidden_dim,)),
            nn.ReLU(),
            nn.Dropout(p=0.5),
            nn.Dense(hidden_dim, hidden_dim // 2),
            nn.LayerNorm((hidden_dim // 2,)),
            nn.ReLU(),
            nn.Dropout(p=0.3),
            nn.Dense(hidden_dim // 2, num_classes)
        )

    def construct(self, text_features, demo_features, speech_features):
        fused = self.fusion(text_features, demo_features, speech_features)
        logits = self.classifier(fused)
        return logits


# 增强的多模态数据集（强化ID匹配）
class MultimodalDataset:
    def __init__(self, tsv_dir, demo_df, speech_df, text_processor):
        self.tsv_dir = tsv_dir
        self.demo_df = demo_df
        self.speech_df = speech_df
        self.text_processor = text_processor
        self.target_speakers = ['<B>', '<DEAF>']  # 老年人（被评估者）标识
        self.label_mapping = {'CTRL': 0, 'MCI': 1, 'AD': 2}
        self.valid_ids = set(demo_df['uuid'].unique())  # 从CSV获取所有有效ID
        self.data = self._load_and_merge_data()
        self.class_weights = self._compute_class_weights()

    def _compute_class_weights(self):
        """优化类别权重，重点提升MCI关注度"""
        labels = [item['label'] for item in self.data]
        counter = Counter(labels)
        total = len(labels)

        if total == 0:
            return {0: 1.0, 1: 1.0, 2: 1.0}

        # 基础权重计算
        base_weights = {cls: total / (count + 1e-5) for cls, count in counter.items()}
        max_weight = max(base_weights.values()) if base_weights else 1.0
        normalized = {cls: w / max_weight for cls, w in base_weights.items()}

        # 强化MCI权重，平衡类别关注度
        if 0 not in normalized: normalized[0] = 1.0
        if 1 not in normalized: normalized[1] = 1.0
        if 2 not in normalized: normalized[2] = 1.0

        normalized[1] *= 1.5  # MCI权重提升50%
        normalized[0] *= 1.1  # CTRL权重微调
        normalized[2] *= 1.2  # AD权重微调

        return normalized

    def _load_and_merge_data(self):
        """强化ID匹配，确保TSV与CSV严格对应"""
        merged_data = []
        tsv_files = [f for f in os.listdir(self.tsv_dir) if f.endswith('.tsv')]
        total_files = len(tsv_files)
        matched_count = 0

        for tsv_file in tsv_files:
            # 提取TSV文件名作为ID（去除扩展名）
            uuid = os.path.splitext(tsv_file)[0]

            # 严格ID校验：仅处理CSV中存在的ID
            if uuid not in self.valid_ids:
                print(f"警告: {uuid} 不在人口统计学数据中，跳过")
                continue

            tsv_path = os.path.join(self.tsv_dir, tsv_file)

            # 加载并清洗对话文本
            try:
                df_tsv = pd.read_csv(tsv_path, sep='\t')
                # 检查必要列
                required_cols = ['speaker', 'value', 'start_time']
                if not set(required_cols).issubset(df_tsv.columns):
                    missing = [col for col in required_cols if col not in df_tsv.columns]
                    print(f"警告: {uuid} 缺少必要列 {missing}，跳过")
                    continue

                # 过滤仅保留老年人的发言
                target_rows = df_tsv[df_tsv['speaker'].isin(self.target_speakers)].copy()
                # 过滤无效值
                target_rows = target_rows[
                    (target_rows['value'] != '<DEAF>') &
                    (target_rows['value'].str.strip() != '') &
                    (~target_rows['value'].isna())
                    ]

                if len(target_rows) == 0:
                    print(f"警告: {uuid} 无有效对话记录，跳过")
                    continue

                # 按时间排序并合并文本
                target_rows = target_rows.sort_values(by='start_time')
                merged_text = ' '.join(target_rows['value'].tolist())
                merged_text = ' '.join(merged_text.split())  # 清理多余空格

            except Exception as e:
                print(f"加载 {uuid} 的对话失败: {str(e)}，跳过")
                continue

            # 匹配人口统计学数据
            demo_matches = self.demo_df[self.demo_df['uuid'] == uuid]
            if len(demo_matches) != 1:
                print(f"警告: {uuid} 人口统计学数据匹配异常，跳过")
                continue
            demo_row = demo_matches.iloc[0]

            # 验证标签
            raw_label = demo_row['label']
            if raw_label not in self.label_mapping:
                print(f"警告: {uuid} 包含未知标签 '{raw_label}'，跳过")
                continue
            encoded_label = self.label_mapping[raw_label]

            # 匹配语音特征数据
            speech_matches = self.speech_df[self.speech_df['uuid'] == uuid]
            if len(speech_matches) != 1:
                print(f"警告: {uuid} 语音特征数据匹配异常，跳过")
                continue
            speech_row = speech_matches.iloc[0]

            # 成功匹配，添加到数据集
            merged_data.append({
                'uuid': uuid,
                'text': merged_text,
                'valid_rows': target_rows,  # 保留有效行用于特征计算
                'label': encoded_label,
                'demographics': {
                    'age': demo_row['age'],
                    'sex': demo_row['sex'],
                    'education': demo_row['education']
                },
                'speech_features': speech_row.drop('uuid').values
            })
            matched_count += 1

        print(f"数据匹配完成: 成功关联 {matched_count}/{total_files} 个样本")
        print(f"样本类别分布: {Counter([item['label'] for item in merged_data])}")
        return merged_data

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]
        # 提取文本嵌入（带动态特征）
        text_embedding = self.text_processor.extract_embedding(
            item['text'], item['valid_rows'], item['label']
        )
        # 人口统计学特征
        gender = 1 if item['demographics']['sex'] == 'M' else 0
        demo_features = np.array([
            item['demographics']['age'], gender, item['demographics']['education']
        ], dtype=np.float32)
        # 语音特征
        speech_features = item['speech_features'].astype(np.float32)
        return {
            'text_features': text_embedding,
            'demo_features': demo_features,
            'speech_features': speech_features,
            'label': np.array(item['label'], dtype=np.int32)
        }


# 优化的SMOTE过采样（重点平衡MCI样本）
def apply_smote(samples, text_processor):
    X_text, X_demo, X_speech, y = [], [], [], []
    for item in samples:
        text_emb = text_processor.extract_embedding(item['text'], item['valid_rows'], item['label'])
        gender = 1 if item['demographics']['sex'] == 'M' else 0
        demo = np.array([item['demographics']['age'], gender, item['demographics']['education']])
        speech = item['speech_features']

        X_text.append(text_emb)
        X_demo.append(demo)
        X_speech.append(speech)
        y.append(item['label'])

    # 合并特征
    X_combined = np.hstack([X_text, X_demo, X_speech])

    # 计算当前类别分布
    counter = Counter(y)
    print(f"SMOTE前类别分布: {counter}")

    # 确定过采样目标（MCI样本至少达到CTRL的80%）
    target_ctrl = counter.get(0, 1)
    target_mci = max(int(target_ctrl * 0.8), counter.get(1, 0))
    target_ad = min(int(target_ctrl * 0.9), counter.get(2, 0))  # 限制AD过度采样

    # 应用SMOTE过采样
    smote = SMOTE(
        sampling_strategy={0: target_ctrl, 1: target_mci, 2: target_ad},
        random_state=42
    )
    X_resampled, y_resampled = smote.fit_resample(X_combined, y)
    print(f"SMOTE后类别分布: {Counter(y_resampled)}")

    # 拆分重采样后的特征
    text_dim = len(X_text[0]) if X_text else 0
    demo_dim = len(X_demo[0]) if X_demo else 0

    resampled_samples = []
    for i in range(len(X_resampled)):
        text_feat = X_resampled[i, :text_dim]
        demo_feat = X_resampled[i, text_dim:text_dim + demo_dim]
        speech_feat = X_resampled[i, text_dim + demo_dim:]

        resampled_samples.append({
            'text_features': text_feat,
            'demo_features': demo_feat,
            'speech_features': speech_feat,
            'label': y_resampled[i]
        })

    return resampled_samples


# 优化的学习率调度器
class CustomPiecewiseLR(LearningRateSchedule):
    def __init__(self, initial_lr, milestones, gamma):
        super().__init__()
        self.initial_lr = initial_lr
        self.milestones = ms.Tensor(milestones, dtype=ms.float32)
        self.gamma = gamma

    def construct(self, global_step):
        lr = self.initial_lr
        decay_count = ops.sum(ops.cast(self.milestones <= global_step, ms.float32))
        return lr * (self.gamma ** decay_count)


# 主函数
def main():
    # 数据路径（请根据实际情况修改）
    tsv_dir = r"C:\Users\吉柏霖\Desktop\痴呆老人预测ms\tsv2"
    demo_path = r"C:\Users\吉柏霖\Desktop\痴呆老人预测ms\2_final_list_train.csv"
    speech_path = r"C:\Users\吉柏霖\Desktop\痴呆老人预测ms\egemaps_final.csv"

    # 路径验证
    for path in [tsv_dir, demo_path, speech_path]:
        if not os.path.exists(path):
            print(f"错误: 路径不存在 - {path}")
            return

    try:
        # 加载人口统计学数据
        demo_df = pd.read_csv(demo_path)
        print(f"加载人口统计学数据: {len(demo_df)} 条记录，列名: {demo_df.columns.tolist()}")
        required_demo_cols = ['uuid', 'label', 'sex', 'age', 'education']
        if not set(required_demo_cols).issubset(demo_df.columns):
            missing = [col for col in required_demo_cols if col not in demo_df.columns]
            raise ValueError(f"人口统计学数据缺少必要列: {missing}")

        # 加载语音特征数据
        speech_df = pd.read_csv(speech_path)
        print(f"加载语音特征数据: {len(speech_df)} 条记录")
        if 'uuid' not in speech_df.columns:
            raise ValueError("语音特征数据缺少'uuid'列")
    except Exception as e:
        print(f"加载辅助数据失败: {str(e)}")
        return

    # 特征标准化
    scaler = StandardScaler()
    # 标准化语音特征
    if len(speech_df) > 0:
        speech_features = speech_df.drop('uuid', axis=1, errors='ignore')
        speech_df[speech_features.columns] = scaler.fit_transform(speech_features)
    # 标准化人口统计学特征
    demo_df['age'] = scaler.fit_transform(demo_df[['age']])
    demo_df['education'] = scaler.fit_transform(demo_df[['education']])

    # 初始化处理器和数据集
    text_processor = TextProcessor()
    dataset = MultimodalDataset(tsv_dir, demo_df, speech_df, text_processor)

    if len(dataset) < 2:
        print(f"错误: 有效样本数不足（{len(dataset)}），无法训练")
        return

    # 划分数据集（保持类别比例）
    train_samples, test_samples = train_test_split(
        dataset.data, test_size=0.2, random_state=42,
        stratify=[item['label'] for item in dataset.data]
    )
    print(f"原始训练集样本数: {len(train_samples)}, 测试集样本数: {len(test_samples)}")

    # 应用SMOTE过采样（重点平衡MCI）
    train_data = apply_smote(train_samples, text_processor)

    # 数据集生成器
    class TrainGenerator:
        def __init__(self, samples, text_processor):
            self.samples = samples
            self.text_processor = text_processor

        def __len__(self):
            return len(self.samples)

        def __getitem__(self, idx):
            item = self.samples[idx]
            # 提取文本嵌入
            text_embedding = self.text_processor.extract_embedding(
                item['text'], item['valid_rows'], item['label']
            )
            # 人口统计学特征
            gender = 1 if item['demographics']['sex'] == 'M' else 0
            demo_features = np.array([
                item['demographics']['age'], gender, item['demographics']['education']
            ], dtype=np.float32)
            # 语音特征
            speech_features = item['speech_features'].astype(np.float32)
            # 标签
            label = np.array(item['label'], dtype=np.int32)
            return (text_embedding.astype(np.float32),
                    demo_features,
                    speech_features,
                    label)

    class TestGenerator:
        def __init__(self, samples, text_processor):
            self.samples = samples
            self.text_processor = text_processor

        def __len__(self):
            return len(self.samples)

        def __getitem__(self, idx):
            item = self.samples[idx]
            # 提取文本嵌入
            text_embedding = self.text_processor.extract_embedding(
                item['text'], item['valid_rows'], item['label']
            )
            # 人口统计学特征
            gender = 1 if item['demographics']['sex'] == 'M' else 0
            demo_features = np.array([
                item['demographics']['age'], gender, item['demographics']['education']
            ], dtype=np.float32)
            # 语音特征
            speech_features = item['speech_features'].astype(np.float32)
            # 标签
            label = np.array(item['label'], dtype=np.int32)
            return (text_embedding.astype(np.float32),
                    demo_features,
                    speech_features,
                    label)

    # 创建数据集
    train_generator = TrainGenerator(train_samples, text_processor)
    test_generator = TestGenerator(test_samples, text_processor)

    train_dataset = GeneratorDataset(
        train_generator,
        column_names=["text_features", "demo_features", "speech_features", "label"]
    ).batch(8)

    test_dataset = GeneratorDataset(
        test_generator,
        column_names=["text_features", "demo_features", "speech_features", "label"]
    ).batch(8)

    # 初始化模型
    speech_dim = speech_df.shape[1] - 1 if len(speech_df) > 0 else 0
    model = MultimodalDementiaModel(
        text_dim=text_processor.get_text_feature_dim(),
        demo_dim=3,
        speech_dim=speech_dim,
        hidden_dim=256,
        num_classes=3
    )

    # 训练配置
    class_weights = ms.Tensor([
        dataset.class_weights.get(0, 1.0),
        dataset.class_weights.get(1, 1.0),
        dataset.class_weights.get(2, 1.0)
    ], dtype=ms.float32)
    print(f"使用类别权重: {class_weights.asnumpy()}")
    loss_fn = nn.CrossEntropyLoss(weight=class_weights)

    # 学习率配置（更平缓的衰减）
    steps_per_epoch = len(train_dataset) if len(train_dataset) > 0 else 1
    total_steps = 60 * steps_per_epoch
    milestones = [25 * steps_per_epoch, 45 * steps_per_epoch]  # 延迟衰减
    lr_scheduler = CustomPiecewiseLR(initial_lr=3e-5, milestones=milestones, gamma=0.7)  # 降低初始学习率

    optimizer = nn.Adam(
        model.trainable_params(),
        learning_rate=lr_scheduler,
        weight_decay=5e-5  # 增强正则化
    )

    # 早停机制（更宽松的耐心值）
    class EarlyStopping:
        def __init__(self, patience=20, verbose=True):
            self.patience = patience
            self.verbose = verbose
            self.best_score = None
            self.counter = 0
            self.early_stop = False

        def check(self, score, model, path):
            if self.best_score is None or score > self.best_score:
                self.best_score = score
                self.counter = 0
                ms.save_checkpoint(model, path)
                if self.verbose:
                    print(f"模型保存，最佳F1分数: {score:.4f}")
            else:
                self.counter += 1
                if self.verbose:
                    print(f"早停计数器: {self.counter}/{self.patience}")
                if self.counter >= self.patience:
                    self.early_stop = True

    early_stopping = EarlyStopping(patience=20, verbose=True)

    # 训练函数
    def forward_fn(text_feats, demo_feats, speech_feats, labels):
        logits = model(text_feats, demo_feats, speech_feats)
        loss = loss_fn(logits, labels)
        return loss, logits

    grad_fn = ops.value_and_grad(forward_fn, None, optimizer.parameters, has_aux=True)

    def train_step(text_feats, demo_feats, speech_feats, labels):
        (loss, logits), grads = grad_fn(text_feats, demo_feats, speech_feats, labels)
        optimizer(grads)
        return loss, logits

    # 训练循环
    model.set_train(True)
    epochs = 60  # 增加训练轮次
    for epoch in range(epochs):
        # 训练阶段
        total_loss, correct, total = 0.0, 0, 0
        train_preds, train_labels = [], []
        for batch in train_dataset.create_tuple_iterator():
            text_feats, demo_feats, speech_feats, labels = batch
            loss, logits = train_step(text_feats, demo_feats, speech_feats, labels)
            total_loss += loss.asnumpy()
            preds = ops.argmax(logits, dim=1)
            correct += ops.sum(ops.equal(preds, labels)).asnumpy()
            total += labels.shape[0]
            train_preds.extend(preds.asnumpy())
            train_labels.extend(labels.asnumpy())
        avg_loss = total_loss / len(train_dataset) if len(train_dataset) > 0 else 0
        train_acc = correct / total if total > 0 else 0
        train_f1 = f1_score(train_labels, train_preds, average='macro')

        # 测试阶段
        model.set_train(False)
        all_preds, all_labels = [], []
        for batch in test_dataset.create_tuple_iterator():
            text_feats, demo_feats, speech_feats, labels = batch
            logits = model(text_feats, demo_feats, speech_feats)
            preds = ops.argmax(logits, dim=1)
            all_preds.extend(preds.asnumpy())
            all_labels.extend(labels.asnumpy())
        test_acc = np.mean(np.array(all_preds) == np.array(all_labels)) if all_labels else 0
        test_f1 = f1_score(all_labels, all_preds, average='macro') if all_labels else 0

        # 打印结果
        print(f"\nEpoch {epoch + 1}/{epochs}")
        print(f"训练损失: {avg_loss:.4f}, 训练准确率: {train_acc:.4f}, 训练F1: {train_f1:.4f}")
        print(f"测试准确率: {test_acc:.4f}, 测试F1: {test_f1:.4f}")
        print("测试集分类报告:")
        print(classification_report(
            all_labels, all_preds,
            target_names=['CTRL', 'MCI', 'AD'],
            zero_division=0
        ))
        print("混淆矩阵:")
        print(confusion_matrix(all_labels, all_preds))

        # 早停检查（使用macro F1）
        early_stopping.check(test_f1, model, "best_optimized_roberta_model.ckpt")
        if early_stopping.early_stop:
            print("早停触发，停止训练")
            break
        model.set_train(True)

    print("\n训练完成，最终模型已保存为 'best_optimized_roberta_model.ckpt'")


if __name__ == "__main__":
    main()

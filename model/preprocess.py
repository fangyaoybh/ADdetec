import os
import numpy as np
import mindspore.dataset as ds
import mindspore.dataset.transforms as C
import mindspore.dataset.vision as CV
import librosa
from mindspore import Tensor, dtype as mstype


class ADDataPreprocessor:
    def __init__(self, glove_path, max_seq_len=100, sample_rate=16000, n_mfcc=40):
        self.max_seq_len = max_seq_len
        self.sample_rate = sample_rate
        self.n_mfcc = n_mfcc
        self.word2vec, self.embedding_dim = self._load_glove(glove_path)

    def _load_glove(self, glove_path):
        """加载GloVe词向量"""
        print(f"加载GloVe词向量从 {glove_path}")
        word2vec = {}
        with open(glove_path, encoding='utf8') as f:
            for line in f:
                word, vec = line.split(maxsplit=1)
                word2vec[word] = np.fromstring(vec, 'f', sep=' ')
        # 获取嵌入维度
        embedding_dim = next(iter(word2vec.values())).shape[0]
        # 添加未知词和填充词的嵌入
        word2vec['<unk>'] = np.random.randn(embedding_dim) * 0.01
        word2vec['<pad>'] = np.zeros(embedding_dim)
        print(f"已加载 {len(word2vec)} 个词向量，维度为 {embedding_dim}")
        return word2vec, embedding_dim

    def text_to_embedding(self, text):

        words = text.lower().split()

        # 初始化嵌入序列
        embedding = np.zeros((self.max_seq_len, self.embedding_dim), dtype=np.float32)

        # 填充嵌入序列
        for i, word in enumerate(words[:self.max_seq_len]):
            embedding[i] = self.word2vec.get(word, self.word2vec['<unk>'])

        return embedding

    def audio_to_mfcc(self, audio_path):
        # 加载音频文件
        y, sr = librosa.load(audio_path, sr=self.sample_rate)

        # 提取MFCC特征
        mfcc = librosa.feature.mfcc(
            y=y,
            sr=sr,
            n_mfcc=self.n_mfcc
        )

        # 标准化MFCC特征
        mfcc = (mfcc - np.mean(mfcc)) / np.std(mfcc)

        return mfcc.astype(np.float32)

    def preprocess_text_data(self, text_data_dir, output_dir):
        """批量预处理文本数据"""
        os.makedirs(output_dir, exist_ok=True)

        for filename in os.listdir(text_data_dir):
            if filename.endswith('.txt'):
                text_path = os.path.join(text_data_dir, filename)
                with open(text_path, 'r', encoding='utf8') as f:
                    text = f.read()

                embedding = self.text_to_embedding(text)
                output_path = os.path.join(output_dir, f"{os.path.splitext(filename)[0]}.npy")
                np.save(output_path, embedding)

        print(f"文本数据预处理完成，保存至 {output_dir}")

    def preprocess_audio_data(self, audio_data_dir, output_dir):
        """批量预处理音频数据"""
        os.makedirs(output_dir, exist_ok=True)

        for filename in os.listdir(audio_data_dir):
            if filename.endswith(('.wav', '.mp3', '.flac')):
                audio_path = os.path.join(audio_data_dir, filename)
                try:
                    mfcc = self.audio_to_mfcc(audio_path)
                    output_path = os.path.join(output_dir, f"{os.path.splitext(filename)[0]}.npy")
                    np.save(output_path, mfcc)
                except Exception as e:
                    print(f"处理 {filename} 时出错: {str(e)}")

        print(f"音频数据预处理完成，保存至 {output_dir}")


class ADataset:
    """自定义数据集类，用于加载预处理后的双模态数据"""

    def __init__(self, text_dir, audio_dir, label_file):
        self.text_dir = text_dir
        self.audio_dir = audio_dir

        # 加载标签
        self.labels = {}
        with open(label_file, 'r') as f:
            for line in f:
                filename, label = line.strip().split(',')
                self.labels[filename] = int(label)

        self.data_ids = list(self.labels.keys())

    def __len__(self):
        return len(self.data_ids)

    def __getitem__(self, idx):
        data_id = self.data_ids[idx]

        # 加载文本特征
        text_feature = np.load(os.path.join(self.text_dir, f"{data_id}.npy"))

        # 加载音频特征
        audio_feature = np.load(os.path.join(self.audio_dir, f"{data_id}.npy"))

        # 确保音频特征具有一致的时间维度（可根据需要调整）
        # 这里简单截断或填充到固定长度，实际应用中可能需要更复杂的处理
        target_length = 100  # 示例目标长度
        if audio_feature.shape[1] > target_length:
            audio_feature = audio_feature[:, :target_length]
        else:
            pad_width = ((0, 0), (0, target_length - audio_feature.shape[1]))
            audio_feature = np.pad(audio_feature, pad_width, mode='constant')

        # 添加通道维度，适应CNN输入
        audio_feature = np.expand_dims(audio_feature, axis=0)

        label = self.labels[data_id]

        return text_feature, audio_feature, label


def create_dataset(text_dir, audio_dir, label_file, batch_size=32, shuffle=True):
    """创建MindSpore数据集"""
    dataset = ds.GeneratorDataset(
        source=ADataset(text_dir, audio_dir, label_file),
        column_names=["text", "audio", "label"],
        shuffle=shuffle
    )

    # 转换为MindSpore张量
    type_cast_op = C.TypeCast(mstype.int32)
    dataset = dataset.map(operations=type_cast_op, input_columns="label")

    # 批量处理
    dataset = dataset.batch(batch_size)

    return dataset

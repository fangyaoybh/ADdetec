import os
import time
import numpy as np
import mindspore as ms
import mindspore.nn as nn
import mindspore.ops as ops
from mindspore import context, Model, save_checkpoint
from mindspore.train.callback import Callback, ModelCheckpoint, CheckpointConfig, LossMonitor, TimeMonitor
from mindspore.nn.metrics import Accuracy, Precision, Recall, F1Score
import matplotlib.pyplot as plt

from data_preprocessing import create_dataset
from ad_detection_model import MultimodalADDetector


class EvalCallback(Callback):
    """自定义评估回调类，在每个epoch结束后进行验证"""

    def __init__(self, model, eval_dataset, eval_interval=1, save_best=True):
        self.model = model
        self.eval_dataset = eval_dataset
        self.eval_interval = eval_interval
        self.save_best = save_best
        self.best_acc = 0.0
        self.eval_acc_list = []
        self.eval_loss_list = []

    def epoch_end(self, run_context):
        cb_params = run_context.original_args()
        epoch_num = cb_params.cur_epoch_num

        if epoch_num % self.eval_interval == 0:
            # 在验证集上评估
            metrics = self.model.eval(self.eval_dataset, dataset_sink_mode=False)
            acc = metrics["Accuracy"]
            loss = metrics["Loss"]

            self.eval_acc_list.append(acc)
            self.eval_loss_list.append(loss)

            print(f"Epoch {epoch_num} 验证结果: 准确率 = {acc:.4f}, 损失 = {loss:.4f}")

            # 保存最佳模型
            if self.save_best and acc > self.best_acc:
                self.best_acc = acc
                save_checkpoint(cb_params.train_network, "best_model.ckpt")
                print(f"保存最佳模型，当前最佳准确率: {self.best_acc:.4f}")


class MultimodalWithLossCell(nn.Cell):
    """包含损失函数的模型包装类"""

    def __init__(self, network, loss_fn):
        super(MultimodalWithLossCell, self).__init__(auto_prefix=False)
        self.network = network
        self.loss_fn = loss_fn

    def construct(self, text, audio, label):
        logits = self.network(text, audio)
        loss = self.loss_fn(logits, label)
        return loss


class TrainStepWrap(nn.TrainOneStepCell):
    """训练步骤包装类，返回损失和预测结果用于评估指标计算"""

    def __init__(self, network, optimizer, sens=1.0):
        super(TrainStepWrap, self).__init__(network, optimizer, sens)
        self.acc = Accuracy()
        self.precision = Precision(average="weighted")
        self.recall = Recall(average="weighted")
        self.f1 = F1Score(average="weighted")

    def construct(self, text, audio, label):
        weights = self.weights
        loss = self.network(text, audio, label)
        grads = self.grad(self.network, weights)(text, audio, label)
        grads = self.grad_reducer(grads)
        loss = ops.depend(loss, self.optimizer(grads))

        # 计算训练指标
        logits = self.network.network(text, audio)
        self.acc.update(logits, label)
        self.precision.update(logits, label)
        self.recall.update(logits, label)
        self.f1.update(logits, label)

        return loss


def train_model(args):
    """模型训练主函数"""
    # 设置运行环境
    context.set_context(mode=context.GRAPH_MODE, device_target=args.device)

    # 创建数据集
    print("加载数据集...")
    train_dataset = create_dataset(
        text_dir=args.text_train_dir,
        audio_dir=args.audio_train_dir,
        label_file=args.train_label_file,
        batch_size=args.batch_size,
        shuffle=True
    )

    eval_dataset = create_dataset(
        text_dir=args.text_eval_dir,
        audio_dir=args.audio_eval_dir,
        label_file=args.eval_label_file,
        batch_size=args.batch_size,
        shuffle=False
    )

    # 获取数据集大小
    train_size = train_dataset.get_dataset_size()
    eval_size = eval_dataset.get_dataset_size()
    print(f"训练集批次: {train_size}, 验证集批次: {eval_size}")

    # 创建模型
    print("创建模型...")
    model = MultimodalADDetector(
        embedding_dim=args.embedding_dim,
        n_mfcc=args.n_mfcc,
        hidden_dim=args.hidden_dim,
        num_classes=args.num_classes
    )

    # 定义损失函数和优化器
    loss_fn = nn.SoftmaxCrossEntropyWithLogits(sparse=True, reduction="mean")
    optimizer = nn.Adam(
        params=model.trainable_params(),
        learning_rate=args.learning_rate,
        weight_decay=args.weight_decay
    )

    # 包装训练网络
    loss_net = MultimodalWithLossCell(model, loss_fn)
    train_net = TrainStepWrap(loss_net, optimizer)
    train_net.set_train()

    # 定义评估指标
    metrics = {
        "Accuracy": Accuracy(),
        "Precision": Precision(average="weighted"),
        "Recall": Recall(average="weighted"),
        "F1": F1Score(average="weighted"),
        "Loss": nn.Loss()
    }

    # 创建模型对象
    model = Model(
        train_net,
        loss_fn=loss_fn,
        optimizer=optimizer,
        metrics=metrics
    )

    # 定义回调函数
    callbacks = [
        TimeMonitor(data_size=train_size),
        LossMonitor(per_print_times=train_size),
        EvalCallback(model, eval_dataset, eval_interval=1)
    ]

    # 模型保存配置
    if args.save_checkpoint:
        config_ck = CheckpointConfig(
            save_checkpoint_steps=train_size,
            keep_checkpoint_max=args.keep_checkpoint_max
        )
        ckpoint_cb = ModelCheckpoint(
            prefix="ad_detector",
            directory=args.checkpoint_dir,
            config=config_ck
        )
        callbacks.append(ckpoint_cb)

    # 创建保存目录
    os.makedirs(args.checkpoint_dir, exist_ok=True)
    os.makedirs(args.log_dir, exist_ok=True)

    # 开始训练
    print("开始训练...")
    start_time = time.time()

    train_acc_list = []
    train_loss_list = []

    for epoch in range(args.epochs):
        # 训练一个epoch
        train_net.acc.clear()
        train_net.precision.clear()
        train_net.recall.clear()
        train_net.f1.clear()

        epoch_loss = 0.0
        for i, (text, audio, label) in enumerate(train_dataset.create_tuple_iterator()):
            loss = train_net(text, audio, label)
            epoch_loss += loss.asnumpy()

            # 打印批次信息
            if (i + 1) % args.log_interval == 0 or i == train_size - 1:
                print(f"Epoch [{epoch + 1}/{args.epochs}], Step [{i + 1}/{train_size}], Loss: {loss.asnumpy():.4f}")

        # 计算训练集指标
        avg_loss = epoch_loss / train_size
        train_acc = train_net.acc.eval()

        train_acc_list.append(train_acc)
        train_loss_list.append(avg_loss)

        print(f"Epoch [{epoch + 1}/{args.epochs}] 训练结果: 准确率 = {train_acc:.4f}, 平均损失 = {avg_loss:.4f}")

        # 调用评估回调
        callbacks[2].epoch_end(ms.train.callback.RunContext(ms.train.callback.CallbackParam(
            cur_epoch_num=epoch + 1,
            train_network=model.train_network.network.network
        )))

    # 计算总训练时间
    end_time = time.time()
    total_time = end_time - start_time
    print(f"训练完成，总耗时: {total_time:.2f}秒，平均每个epoch耗时: {total_time / args.epochs:.2f}秒")

    # 最终评估
    print("在测试集上进行最终评估...")
    final_metrics = model.eval(eval_dataset, dataset_sink_mode=False)
    print("最终评估结果:")
    for name, value in final_metrics.items():
        print(f"{name}: {value:.4f}")

    # 绘制训练曲线
    plot_training_curves(
        train_acc_list,
        callbacks[2].eval_acc_list,
        train_loss_list,
        callbacks[2].eval_loss_list,
        save_path=os.path.join(args.log_dir, "training_curves.png")
    )

    return final_metrics


def plot_training_curves(train_acc, eval_acc, train_loss, eval_loss, save_path=None):
    """绘制训练和验证的准确率与损失曲线"""
    epochs = range(1, len(train_acc) + 1)

    plt.figure(figsize=(12, 5))

    # 准确率曲线
    plt.subplot(1, 2, 1)
    plt.plot(epochs, train_acc, 'b-', label='训练准确率')
    plt.plot(epochs, eval_acc, 'r-', label='验证准确率')
    plt.title('训练和验证准确率')
    plt.xlabel('Epoch')
    plt.ylabel('准确率')
    plt.legend()

    # 损失曲线
    plt.subplot(1, 2, 2)
    plt.plot(epochs, train_loss, 'b-', label='训练损失')
    plt.plot(epochs, eval_loss, 'r-', label='验证损失')
    plt.title('训练和验证损失')
    plt.xlabel('Epoch')
    plt.ylabel('损失')
    plt.legend()

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path)
        print(f"训练曲线已保存至 {save_path}")
    else:
        plt.show()


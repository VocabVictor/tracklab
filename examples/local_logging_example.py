#!/usr/bin/env python3
"""
TrackLab 本地日志系统使用示例

这个示例展示了如何使用简化的本地日志系统来记录机器学习实验。
"""

import sys
import time
import random
from pathlib import Path

# 添加 tracklab 到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from tracklab.sdk.local_logger import init, log_metric, log_metrics, log_config, log_summary, save_artifact, finish


def simulate_training():
    """模拟机器学习训练过程"""
    
    # 1. 初始化 TrackLab
    print("🚀 初始化 TrackLab 本地日志系统...")
    logger = init(log_dir="./tracklab_logs")
    print(f"✅ 创建新的运行: {logger.run_id}")
    
    # 2. 记录配置
    config = {
        "learning_rate": 0.01,
        "batch_size": 32,
        "epochs": 10,
        "model_type": "ResNet18",
        "optimizer": "Adam",
        "dataset": "CIFAR-10"
    }
    
    print("📝 记录实验配置...")
    log_config(config)
    
    # 3. 模拟训练过程
    print("🎯 开始模拟训练...")
    
    best_accuracy = 0
    for epoch in range(config["epochs"]):
        # 模拟每个 epoch 的训练
        epoch_loss = 1.0 - (epoch * 0.08) + random.uniform(-0.05, 0.05)
        epoch_accuracy = 0.1 + (epoch * 0.08) + random.uniform(-0.02, 0.02)
        
        # 记录单个指标
        log_metric("loss", epoch_loss, step=epoch)
        log_metric("accuracy", epoch_accuracy, step=epoch)
        
        # 记录验证指标
        val_loss = epoch_loss + random.uniform(0, 0.1)
        val_accuracy = max(0, epoch_accuracy - random.uniform(0, 0.05))
        
        # 批量记录指标
        log_metrics({
            "val_loss": val_loss,
            "val_accuracy": val_accuracy,
            "learning_rate": config["learning_rate"] * (0.95 ** epoch)
        }, step=epoch)
        
        # 追踪最佳准确率
        if val_accuracy > best_accuracy:
            best_accuracy = val_accuracy
            
            # 保存最佳模型（模拟）
            model_path = Path("./temp_model.txt")
            with open(model_path, "w") as f:
                f.write(f"Best model at epoch {epoch}\n")
                f.write(f"Accuracy: {val_accuracy:.4f}\n")
                f.write(f"Loss: {val_loss:.4f}\n")
            
            save_artifact(str(model_path), "best_model.txt")
            model_path.unlink()  # 删除临时文件
            
            print(f"💾 保存最佳模型 (epoch {epoch}, accuracy: {val_accuracy:.4f})")
        
        print(f"Epoch {epoch+1}/{config['epochs']}: loss={epoch_loss:.4f}, acc={epoch_accuracy:.4f}, val_acc={val_accuracy:.4f}")
        time.sleep(0.1)  # 模拟训练时间
    
    # 4. 记录最终摘要
    summary = {
        "best_accuracy": best_accuracy,
        "final_loss": epoch_loss,
        "total_epochs": config["epochs"],
        "training_time": config["epochs"] * 0.1,
        "model_size": "11.2M parameters",
        "dataset_size": "50k samples"
    }
    
    print("📊 记录最终摘要...")
    log_summary(summary)
    
    # 5. 保存更多构件
    print("💾 保存训练日志...")
    
    # 创建训练日志
    log_path = Path("./training.log")
    with open(log_path, "w") as f:
        f.write("TrackLab Training Log\n")
        f.write("====================\n\n")
        f.write(f"Configuration: {config}\n")
        f.write(f"Best Accuracy: {best_accuracy:.4f}\n")
        f.write(f"Training completed successfully!\n")
    
    save_artifact(str(log_path), "training.log")
    log_path.unlink()
    
    # 6. 完成实验
    print("🏁 完成实验...")
    finish()
    
    print(f"\n✅ 实验完成！日志保存在: {logger.run_dir}")
    print(f"📁 运行ID: {logger.run_id}")


def demonstrate_features():
    """演示各种功能"""
    
    print("\n" + "="*50)
    print("🧪 演示 TrackLab 本地日志系统功能")
    print("="*50)
    
    # 运行模拟训练
    simulate_training()
    
    print("\n" + "="*50)
    print("📋 功能总结:")
    print("✅ 本地文件存储 (无网络依赖)")
    print("✅ 配置管理 (config.yaml)")
    print("✅ 指标记录 (history.jsonl)")
    print("✅ 摘要统计 (summary.json)")
    print("✅ 构件保存 (artifacts/)")
    print("✅ 元数据跟踪 (metadata.json)")
    print("✅ 缓冲写入 (性能优化)")
    print("✅ 简单 API (易于使用)")
    print("="*50)


if __name__ == "__main__":
    demonstrate_features()
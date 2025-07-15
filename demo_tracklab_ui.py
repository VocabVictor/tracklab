#!/usr/bin/env python3
"""
TrackLab UI Demo - 展示完整的TrackLab UI功能
"""

import tracklab
import random
import time
import math

def demo_experiments():
    """演示实验记录"""
    print("🧪 Running TrackLab UI Demo...")
    print("=" * 50)
    
    # 模拟多个实验
    experiments = [
        {
            "name": "cnn-baseline",
            "config": {
                "model": "CNN",
                "learning_rate": 0.001,
                "batch_size": 32,
                "epochs": 10,
                "optimizer": "Adam"
            }
        },
        {
            "name": "resnet-experiment",
            "config": {
                "model": "ResNet50",
                "learning_rate": 0.0001,
                "batch_size": 16,
                "epochs": 20,
                "optimizer": "AdamW"
            }
        },
        {
            "name": "transformer-test",
            "config": {
                "model": "Transformer",
                "learning_rate": 0.0005,
                "batch_size": 8,
                "epochs": 15,
                "optimizer": "SGD"
            }
        }
    ]
    
    for i, exp in enumerate(experiments):
        print(f"\n🔬 Running experiment {i+1}/{len(experiments)}: {exp['name']}")
        
        # 初始化实验
        run = tracklab.init(
            project="demo-project",
            name=exp["name"],
            config=exp["config"],
            tags=["demo", "ui-test", exp["config"]["model"].lower()],
            notes=f"Demo experiment for {exp['config']['model']} model"
        )
        
        # 模拟训练过程
        epochs = exp["config"]["epochs"]
        for epoch in range(epochs):
            # 模拟训练指标
            base_loss = 2.0
            base_acc = 0.3
            
            # 添加一些随机性和趋势
            progress = epoch / epochs
            loss = base_loss * (1 - progress * 0.8) + random.uniform(-0.1, 0.1)
            accuracy = base_acc + progress * 0.6 + random.uniform(-0.05, 0.05)
            
            # 模拟验证指标
            val_loss = loss + random.uniform(0, 0.3)
            val_accuracy = accuracy - random.uniform(0, 0.1)
            
            # 记录指标
            tracklab.log({
                "epoch": epoch,
                "train_loss": loss,
                "train_accuracy": accuracy,
                "val_loss": val_loss,
                "val_accuracy": val_accuracy,
                "learning_rate": exp["config"]["learning_rate"] * (0.95 ** epoch),
                "batch_size": exp["config"]["batch_size"],
                "gpu_memory": random.uniform(60, 90),
                "training_time": epoch * random.uniform(45, 75)
            })
            
            # 模拟进度
            if epoch % 5 == 0:
                print(f"  Epoch {epoch}: loss={loss:.4f}, acc={accuracy:.4f}")
        
        # 保存模型文件
        model_path = f"model_{exp['name']}.pth"
        with open(model_path, "w") as f:
            f.write(f"# Mock model file for {exp['name']}\n")
            f.write(f"# Config: {exp['config']}\n")
            f.write(f"# Final accuracy: {accuracy:.4f}\n")
        
        tracklab.save(model_path)
        
        # 完成实验
        tracklab.finish()
        
        print(f"  ✅ Completed {exp['name']}")
        time.sleep(0.5)  # 短暂延迟
    
    print("\n🎉 All experiments completed!")
    print("\n📋 Next Steps:")
    print("  1. Build UI: python -m tracklab.cli.cli ui build")  
    print("  2. Start server: python -m tracklab.cli.cli ui start")
    print("  3. Open browser: http://localhost:8000")
    print("  4. Explore your experiments in the TrackLab UI!")

if __name__ == "__main__":
    demo_experiments()
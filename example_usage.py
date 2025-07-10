#!/usr/bin/env python3
"""
Example usage of TrackLab - wandb compatible local experiment tracking
"""

import numpy as np
import time

# Import TrackLab as wandb for compatibility
import tracklab as wandb

def train_model():
    """Simulate training a machine learning model"""
    
    # Initialize experiment
    run = wandb.init(
        project="mnist-classification",
        name="cnn-experiment",
        config={
            "learning_rate": 0.001,
            "batch_size": 32,
            "epochs": 10,
            "model_type": "CNN",
            "optimizer": "adam"
        },
        tags=["deep-learning", "computer-vision", "cnn"],
        notes="Training a CNN on MNIST dataset"
    )
    
    print(f"🚀 Started experiment: {run.name}")
    print(f"📊 Project: {run.project}")
    print(f"🔧 Config: {dict(wandb.config)}")
    
    # Simulate training loop
    for epoch in range(wandb.config["epochs"]):
        print(f"\n📈 Epoch {epoch + 1}/{wandb.config['epochs']}")
        
        # Simulate training metrics
        train_loss = 2.0 * np.exp(-epoch * 0.3) + 0.1 * np.random.random()
        train_acc = 1 - np.exp(-epoch * 0.4) + 0.05 * np.random.random()
        
        # Simulate validation metrics
        val_loss = train_loss + 0.1 * np.random.random()
        val_acc = train_acc - 0.05 * np.random.random()
        
        # Log metrics
        wandb.log({
            "epoch": epoch + 1,
            "train/loss": train_loss,
            "train/accuracy": train_acc,
            "val/loss": val_loss,
            "val/accuracy": val_acc,
            "learning_rate": wandb.config["learning_rate"] * (0.95 ** epoch)
        }, step=epoch)
        
        print(f"   Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.4f}")
        print(f"   Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.4f}")
        
        # Simulate training time
        time.sleep(0.1)
    
    # Create some visualizations
    print("\n📊 Creating visualizations...")
    
    # Example confusion matrix (simulated)
    confusion_matrix = np.random.randint(0, 50, (10, 10))
    cm_table = wandb.Table(
        data=confusion_matrix.tolist(),
        columns=[f"Pred_{i}" for i in range(10)]
    )
    
    # Example prediction samples
    sample_predictions = [
        {"image_id": i, "true_label": np.random.randint(0, 10), 
         "predicted_label": np.random.randint(0, 10), 
         "confidence": np.random.random()}
        for i in range(20)
    ]
    
    predictions_table = wandb.Table(data=sample_predictions)
    
    # Example training curve
    epochs = list(range(1, wandb.config["epochs"] + 1))
    train_losses = [2.0 * np.exp(-e * 0.3) + 0.1 * np.random.random() for e in epochs]
    
    curve_data = [[e, loss] for e, loss in zip(epochs, train_losses)]
    curve_table = wandb.Table(data=curve_data, columns=["epoch", "loss"])
    
    # Log tables
    wandb.log({
        "confusion_matrix": cm_table,
        "predictions": predictions_table,
        "training_curve": curve_table
    })
    
    # Example histogram
    final_weights = np.random.normal(0, 0.1, 1000)
    wandb.log({"final_weights_distribution": wandb.Histogram(final_weights)})
    
    # Example HTML report
    html_report = f"""
    <h2>Training Report</h2>
    <p><strong>Model:</strong> {wandb.config['model_type']}</p>
    <p><strong>Final Training Accuracy:</strong> {train_acc:.4f}</p>
    <p><strong>Final Validation Accuracy:</strong> {val_acc:.4f}</p>
    <p><strong>Training completed successfully!</strong></p>
    """
    
    wandb.log({"training_report": wandb.Html(html_report)})
    
    # Update summary with final results
    wandb.summary["final_train_accuracy"] = train_acc
    wandb.summary["final_val_accuracy"] = val_acc
    wandb.summary["final_train_loss"] = train_loss
    wandb.summary["final_val_loss"] = val_loss
    wandb.summary["total_parameters"] = 1247648
    wandb.summary["best_epoch"] = epoch + 1
    
    # Create and log an artifact
    print("\n📦 Creating artifact...")
    artifact = wandb.Artifact("model-checkpoint", type="model")
    
    # In a real scenario, you would save your model and add it to the artifact
    # artifact.add_file("model.pkl")
    # artifact.add_file("model_config.json")
    
    # For demo, we'll just add some metadata
    artifact.metadata["model_type"] = wandb.config["model_type"]
    artifact.metadata["final_accuracy"] = float(val_acc)
    artifact.metadata["training_time"] = "5 minutes"
    
    # Log the artifact
    wandb.log_artifact(artifact)
    
    print(f"\n✅ Training completed!")
    print(f"📊 Final Results:")
    print(f"   Training Accuracy: {train_acc:.4f}")
    print(f"   Validation Accuracy: {val_acc:.4f}")
    print(f"   Total Parameters: {wandb.summary['total_parameters']:,}")
    
    # Finish the run
    wandb.finish()

def hyperparameter_sweep():
    """Demonstrate hyperparameter sweeps"""
    
    print("\n🔍 Running Hyperparameter Sweep")
    print("=" * 40)
    
    # Define sweep configuration
    sweep_config = {
        "method": "random",
        "metric": {"name": "val_accuracy", "goal": "maximize"},
        "parameters": {
            "learning_rate": {"values": [0.001, 0.01, 0.1]},
            "batch_size": {"values": [16, 32, 64]},
            "dropout": {"min": 0.1, "max": 0.5}
        }
    }
    
    # Create sweep
    sweep_id = wandb.sweep(sweep_config, project="hyperparameter-tuning")
    
    def train_with_config():
        """Training function for sweep"""
        
        # Initialize with sweep config
        wandb.init(project="hyperparameter-tuning")
        
        # Get config from sweep
        config = wandb.config
        
        print(f"🔧 Testing config: lr={config['learning_rate']}, batch_size={config['batch_size']}")
        
        # Simulate training with this config
        epochs = 5
        best_val_acc = 0
        
        for epoch in range(epochs):
            # Simulate metrics based on config
            train_loss = 2.0 * np.exp(-epoch * config["learning_rate"]) + 0.1 * np.random.random()
            val_acc = min(0.95, (1 - np.exp(-epoch * config["learning_rate"] * 2)) + 0.05 * np.random.random())
            
            if val_acc > best_val_acc:
                best_val_acc = val_acc
            
            wandb.log({
                "train_loss": train_loss,
                "val_accuracy": val_acc,
                "epoch": epoch
            })
        
        wandb.summary["best_val_accuracy"] = best_val_acc
        wandb.finish()
    
    # Run sweep agent
    wandb.agent(sweep_id, function=train_with_config, count=3)
    
    print("✅ Hyperparameter sweep completed!")

def main():
    """Main example function"""
    
    print("🚀 TrackLab Example - wandb Compatible Local Experiment Tracking")
    print("=" * 70)
    
    # Example 1: Basic training
    print("\n1. Running basic training example...")
    train_model()
    
    # Example 2: Hyperparameter sweep
    print("\n2. Running hyperparameter sweep example...")
    hyperparameter_sweep()
    
    print("\n" + "=" * 70)
    print("🎉 All examples completed successfully!")
    print()
    print("💡 Next steps:")
    print("1. Start the TrackLab server: tracklab server start")
    print("2. Open the dashboard: http://localhost:8080/dashboard")
    print("3. Explore your experiments in the web interface")
    print("4. Use 'tracklab runs list' to see all runs")
    print("5. Use 'tracklab projects list' to see all projects")

if __name__ == "__main__":
    main()
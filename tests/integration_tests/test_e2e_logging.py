"""端到端日志记录测试"""

import pytest
import unittest.mock
import json
from pathlib import Path


def test_complete_logging_workflow():
    """测试完整的日志记录工作流"""
    import tracklab
    
    # 创建一个临时目录用于测试
    with unittest.mock.patch("tracklab.backend.server.get_data_dir") as mock_data_dir:
        mock_data_dir.return_value = Path("test_data")
        
        # 初始化 TrackLab
        run = tracklab.init(
            project="integration-test",
            name="e2e-logging-test",
            config={"learning_rate": 0.001, "batch_size": 32}
        )
        
        # 记录各种类型的数据
        run.log({"loss": 0.5, "accuracy": 0.85})
        run.log({"loss": 0.3, "accuracy": 0.90})
        run.log({"loss": 0.1, "accuracy": 0.95})
        
        # 更新配置
        run.config.update({"epochs": 10})
        
        # 更新摘要
        run.summary["best_accuracy"] = 0.95
        run.summary["final_loss"] = 0.1
        
        # 保存文件
        test_file = Path("test_model.txt")
        test_file.write_text("model weights")
        run.save(str(test_file))
        
        # 结束运行
        run.finish()
        
        # 验证数据是否正确保存
        assert run.state == "finished"
        assert run.config.epochs == 10
        assert run.summary["best_accuracy"] == 0.95


def test_multiple_runs_same_project():
    """测试同一项目中的多个运行"""
    import tracklab
    
    with unittest.mock.patch("tracklab.backend.server.get_data_dir") as mock_data_dir:
        mock_data_dir.return_value = Path("test_data")
        
        # 创建第一个运行
        run1 = tracklab.init(project="multi-run-test", name="run-1")
        run1.log({"metric": 1.0})
        run1.finish()
        
        # 创建第二个运行
        run2 = tracklab.init(project="multi-run-test", name="run-2")
        run2.log({"metric": 2.0})
        run2.finish()
        
        # 验证两个运行是独立的
        assert run1.id != run2.id
        assert run1.name == "run-1"
        assert run2.name == "run-2"


def test_resume_run_workflow():
    """测试恢复运行的工作流"""
    import tracklab
    
    with unittest.mock.patch("tracklab.backend.server.get_data_dir") as mock_data_dir:
        mock_data_dir.return_value = Path("test_data")
        
        # 创建初始运行
        run1 = tracklab.init(
            project="resume-test",
            name="resumable-run",
            id="fixed-run-id"
        )
        run1.log({"step": 1, "loss": 0.5})
        run1.finish()
        
        # 恢复运行
        run2 = tracklab.init(
            project="resume-test",
            id="fixed-run-id",
            resume="must"
        )
        run2.log({"step": 2, "loss": 0.3})
        run2.finish()
        
        # 验证恢复的运行
        assert run2.id == "fixed-run-id"
        assert run2.name == "resumable-run"


def test_offline_mode_workflow():
    """测试离线模式的工作流"""
    import tracklab
    
    with unittest.mock.patch("tracklab.backend.server.get_data_dir") as mock_data_dir:
        mock_data_dir.return_value = Path("test_data")
        
        # 以离线模式初始化
        run = tracklab.init(
            project="offline-test",
            mode="offline"
        )
        
        # 记录数据
        run.log({"offline_metric": 0.8})
        run.summary["offline_result"] = "success"
        
        # 结束运行
        run.finish()
        
        # 验证离线模式
        assert run.settings.mode == "offline"
        assert run.state == "finished"


def test_concurrent_logging():
    """测试并发日志记录"""
    import tracklab
    import threading
    import time
    
    with unittest.mock.patch("tracklab.backend.server.get_data_dir") as mock_data_dir:
        mock_data_dir.return_value = Path("test_data")
        
        run = tracklab.init(project="concurrent-test")
        
        def log_metrics(thread_id):
            for i in range(10):
                run.log({f"metric_{thread_id}": i})
                time.sleep(0.01)
        
        # 创建多个线程进行并发日志记录
        threads = []
        for i in range(3):
            thread = threading.Thread(target=log_metrics, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        run.finish()
        
        # 验证所有数据都被记录
        assert run.state == "finished"


def test_error_handling_in_workflow():
    """测试工作流中的错误处理"""
    import tracklab
    from tracklab.errors import TrackLabError
    
    with unittest.mock.patch("tracklab.backend.server.get_data_dir") as mock_data_dir:
        mock_data_dir.return_value = Path("test_data")
        
        run = tracklab.init(project="error-test")
        
        # 测试记录无效数据的错误处理
        with pytest.raises(TrackLabError):
            run.log("invalid_data")
        
        # 测试正常数据仍然可以记录
        run.log({"valid_metric": 0.9})
        
        # 测试重复结束运行的错误处理
        run.finish()
        with pytest.raises(TrackLabError):
            run.finish()


def test_large_data_logging():
    """测试大数据量的日志记录"""
    import tracklab
    import numpy as np
    
    with unittest.mock.patch("tracklab.backend.server.get_data_dir") as mock_data_dir:
        mock_data_dir.return_value = Path("test_data")
        
        run = tracklab.init(project="large-data-test")
        
        # 记录大量数据
        for i in range(1000):
            run.log({
                "step": i,
                "loss": np.random.random(),
                "accuracy": np.random.random(),
                "precision": np.random.random(),
                "recall": np.random.random()
            })
        
        run.finish()
        
        # 验证大数据量处理
        assert run.state == "finished"


def test_config_and_summary_persistence():
    """测试配置和摘要的持久化"""
    import tracklab
    
    with unittest.mock.patch("tracklab.backend.server.get_data_dir") as mock_data_dir:
        mock_data_dir.return_value = Path("test_data")
        
        # 初始化运行
        run = tracklab.init(
            project="persistence-test",
            config={"initial_param": 1.0}
        )
        
        # 更新配置
        run.config.update({
            "learning_rate": 0.001,
            "batch_size": 32,
            "epochs": 100
        })
        
        # 设置摘要
        run.summary.update({
            "best_loss": 0.05,
            "best_accuracy": 0.98,
            "training_time": 3600
        })
        
        # 结束运行
        run.finish()
        
        # 验证配置和摘要的持久化
        assert run.config.initial_param == 1.0
        assert run.config.learning_rate == 0.001
        assert run.summary["best_loss"] == 0.05
        assert run.summary["best_accuracy"] == 0.98
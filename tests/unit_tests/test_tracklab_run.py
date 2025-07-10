"""测试 TrackLab Run 类功能"""

import pytest
import unittest.mock
from tracklab.errors import TrackLabError


def test_run_creation():
    """测试 Run 对象的创建"""
    from tracklab.sdk.tracklab_run import Run
    from tracklab.sdk.tracklab_settings import Settings
    
    settings = Settings(project="test-project")
    
    with unittest.mock.patch("tracklab.sdk.tracklab_run.create_local_backend") as mock_backend:
        mock_backend.return_value = unittest.mock.MagicMock()
        
        run = Run(settings=settings)
        
        assert run.project == "test-project"
        assert run.settings is settings
        assert run.backend is not None


def test_run_log_metrics():
    """测试记录指标功能"""
    from tracklab.sdk.tracklab_run import Run
    from tracklab.sdk.tracklab_settings import Settings
    
    settings = Settings(project="test-project")
    mock_backend = unittest.mock.MagicMock()
    
    with unittest.mock.patch("tracklab.sdk.tracklab_run.create_local_backend", return_value=mock_backend):
        run = Run(settings=settings)
        
        # 测试记录单个指标
        run.log({"accuracy": 0.95})
        mock_backend.log.assert_called_with({"accuracy": 0.95})
        
        # 测试记录多个指标
        run.log({"loss": 0.05, "accuracy": 0.97})
        mock_backend.log.assert_called_with({"loss": 0.05, "accuracy": 0.97})


def test_run_log_invalid_data():
    """测试记录无效数据"""
    from tracklab.sdk.tracklab_run import Run
    from tracklab.sdk.tracklab_settings import Settings
    
    settings = Settings(project="test-project")
    mock_backend = unittest.mock.MagicMock()
    
    with unittest.mock.patch("tracklab.sdk.tracklab_run.create_local_backend", return_value=mock_backend):
        run = Run(settings=settings)
        
        # 测试记录无效数据类型
        with pytest.raises(TrackLabError, match="Invalid data type"):
            run.log("invalid_string")
        
        # 测试记录空数据
        with pytest.raises(TrackLabError, match="Cannot log empty data"):
            run.log({})


def test_run_save_file():
    """测试保存文件功能"""
    from tracklab.sdk.tracklab_run import Run
    from tracklab.sdk.tracklab_settings import Settings
    
    settings = Settings(project="test-project")
    mock_backend = unittest.mock.MagicMock()
    
    with unittest.mock.patch("tracklab.sdk.tracklab_run.create_local_backend", return_value=mock_backend):
        run = Run(settings=settings)
        
        # 测试保存文件
        run.save("test_file.txt")
        mock_backend.save.assert_called_with("test_file.txt")


def test_run_finish():
    """测试结束运行功能"""
    from tracklab.sdk.tracklab_run import Run
    from tracklab.sdk.tracklab_settings import Settings
    
    settings = Settings(project="test-project")
    mock_backend = unittest.mock.MagicMock()
    
    with unittest.mock.patch("tracklab.sdk.tracklab_run.create_local_backend", return_value=mock_backend):
        run = Run(settings=settings)
        
        # 测试结束运行
        run.finish()
        mock_backend.finish.assert_called_once()
        
        # 测试重复结束运行
        with pytest.raises(TrackLabError, match="Run already finished"):
            run.finish()


def test_run_config_access():
    """测试配置访问"""
    from tracklab.sdk.tracklab_run import Run
    from tracklab.sdk.tracklab_settings import Settings
    
    settings = Settings(project="test-project")
    mock_backend = unittest.mock.MagicMock()
    
    with unittest.mock.patch("tracklab.sdk.tracklab_run.create_local_backend", return_value=mock_backend):
        run = Run(settings=settings, config={"lr": 0.001, "batch_size": 32})
        
        # 测试访问配置
        assert run.config.lr == 0.001
        assert run.config.batch_size == 32
        
        # 测试更新配置
        run.config.update({"epochs": 10})
        assert run.config.epochs == 10


def test_run_summary_access():
    """测试摘要访问"""
    from tracklab.sdk.tracklab_run import Run
    from tracklab.sdk.tracklab_settings import Settings
    
    settings = Settings(project="test-project")
    mock_backend = unittest.mock.MagicMock()
    
    with unittest.mock.patch("tracklab.sdk.tracklab_run.create_local_backend", return_value=mock_backend):
        run = Run(settings=settings)
        
        # 测试设置摘要
        run.summary["best_accuracy"] = 0.98
        run.summary["final_loss"] = 0.02
        
        assert run.summary["best_accuracy"] == 0.98
        assert run.summary["final_loss"] == 0.02


def test_run_watch_model():
    """测试监控模型功能"""
    from tracklab.sdk.tracklab_run import Run
    from tracklab.sdk.tracklab_settings import Settings
    
    settings = Settings(project="test-project")
    mock_backend = unittest.mock.MagicMock()
    
    with unittest.mock.patch("tracklab.sdk.tracklab_run.create_local_backend", return_value=mock_backend):
        run = Run(settings=settings)
        
        # 创建一个模拟的模型对象
        mock_model = unittest.mock.MagicMock()
        
        # 测试监控模型
        run.watch(mock_model)
        # 这里应该验证模型监控的具体行为
        # 具体实现取决于 watch 功能的设计


def test_run_properties():
    """测试 Run 对象的属性"""
    from tracklab.sdk.tracklab_run import Run
    from tracklab.sdk.tracklab_settings import Settings
    
    settings = Settings(project="test-project", name="test-run")
    mock_backend = unittest.mock.MagicMock()
    
    with unittest.mock.patch("tracklab.sdk.tracklab_run.create_local_backend", return_value=mock_backend):
        run = Run(settings=settings)
        
        # 测试基本属性
        assert run.project == "test-project"
        assert run.name == "test-run"
        assert run.id is not None
        assert run.url is not None
        assert run.state == "running"


def test_run_context_manager():
    """测试 Run 作为上下文管理器的使用"""
    from tracklab.sdk.tracklab_run import Run
    from tracklab.sdk.tracklab_settings import Settings
    
    settings = Settings(project="test-project")
    mock_backend = unittest.mock.MagicMock()
    
    with unittest.mock.patch("tracklab.sdk.tracklab_run.create_local_backend", return_value=mock_backend):
        # 测试上下文管理器
        with Run(settings=settings) as run:
            run.log({"test": 1})
            assert run.state == "running"
        
        # 退出上下文后应该自动结束
        assert run.state == "finished"
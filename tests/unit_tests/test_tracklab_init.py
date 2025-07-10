"""测试 TrackLab 初始化功能"""

import pytest
import unittest.mock
from tracklab.errors import TrackLabError


def test_init_before_import():
    """测试在导入前调用 init 应该抛出错误"""
    # 这里测试预初始化对象的行为
    import tracklab
    
    # 在 init 之前访问 run 应该抛出错误
    with pytest.raises(TrackLabError, match="You must call tracklab.init"):
        _ = tracklab.run.id


def test_init_with_basic_params():
    """测试基本参数的初始化"""
    import tracklab
    
    # Mock 后端接口
    with unittest.mock.patch("tracklab.sdk.tracklab_init.create_local_backend") as mock_backend:
        mock_backend.return_value = unittest.mock.MagicMock()
        
        run = tracklab.init(
            project="test-project",
            name="test-run",
            config={"lr": 0.001}
        )
        
        assert run is not None
        assert run.project == "test-project"
        assert run.name == "test-run"
        assert run.config.lr == 0.001


def test_init_with_settings():
    """测试使用 Settings 对象初始化"""
    import tracklab
    
    settings = tracklab.Settings(
        project="test-project",
        mode="test",
        console="off"
    )
    
    with unittest.mock.patch("tracklab.sdk.tracklab_init.create_local_backend") as mock_backend:
        mock_backend.return_value = unittest.mock.MagicMock()
        
        run = tracklab.init(settings=settings)
        
        assert run is not None
        assert run.settings.project == "test-project"
        assert run.settings.mode == "test"


def test_init_multiple_times():
    """测试多次初始化的行为"""
    import tracklab
    
    with unittest.mock.patch("tracklab.sdk.tracklab_init.create_local_backend") as mock_backend:
        mock_backend.return_value = unittest.mock.MagicMock()
        
        # 第一次初始化
        run1 = tracklab.init(project="test1")
        
        # 第二次初始化应该创建新的 run
        run2 = tracklab.init(project="test2")
        
        assert run1 is not run2
        assert run1.project == "test1"
        assert run2.project == "test2"


def test_init_with_invalid_params():
    """测试无效参数的初始化"""
    import tracklab
    
    with pytest.raises(TrackLabError, match="Invalid project name"):
        tracklab.init(project="")
    
    with pytest.raises(TrackLabError, match="Invalid config"):
        tracklab.init(project="test", config="invalid")


def test_init_offline_mode():
    """测试离线模式初始化"""
    import tracklab
    
    with unittest.mock.patch("tracklab.sdk.tracklab_init.create_local_backend") as mock_backend:
        mock_backend.return_value = unittest.mock.MagicMock()
        
        run = tracklab.init(
            project="test-project",
            mode="offline"
        )
        
        assert run is not None
        assert run.settings.mode == "offline"


def test_init_with_resume():
    """测试恢复运行的初始化"""
    import tracklab
    
    with unittest.mock.patch("tracklab.sdk.tracklab_init.create_local_backend") as mock_backend:
        mock_backend.return_value = unittest.mock.MagicMock()
        
        # 创建一个运行
        run1 = tracklab.init(project="test", id="test-run-id")
        run1.finish()
        
        # 恢复运行
        run2 = tracklab.init(project="test", id="test-run-id", resume="must")
        
        assert run2.id == "test-run-id"


def test_init_global_state():
    """测试初始化后的全局状态"""
    import tracklab
    
    with unittest.mock.patch("tracklab.sdk.tracklab_init.create_local_backend") as mock_backend:
        mock_backend.return_value = unittest.mock.MagicMock()
        
        run = tracklab.init(project="test")
        
        # 检查全局状态是否正确设置
        assert tracklab.run is run
        assert tracklab.config is run.config
        assert tracklab.summary is run.summary
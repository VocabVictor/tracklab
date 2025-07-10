"""单元测试专用配置"""

import pytest
import unittest.mock


@pytest.fixture
def mock_backend():
    """Mock 后端接口"""
    backend = unittest.mock.MagicMock()
    backend.log = unittest.mock.MagicMock()
    backend.save = unittest.mock.MagicMock()
    backend.finish = unittest.mock.MagicMock()
    return backend


@pytest.fixture
def mock_settings():
    """Mock 设置对象"""
    settings = unittest.mock.MagicMock()
    settings.mode = "test"
    settings.console = "off"
    settings.save_code = False
    return settings
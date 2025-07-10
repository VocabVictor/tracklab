"""TrackLab 测试配置文件

基于 wandb 的测试结构，提供全局 fixtures 和测试配置。
"""
from __future__ import annotations

import logging
import os
import pathlib
import platform
import shutil
import sys
import time
import unittest.mock
from itertools import takewhile
from pathlib import Path
from queue import Queue
from typing import Any, Callable, Generator, Iterable, Iterator

import pytest
from pytest_mock import MockerFixture

# 禁用 TrackLab 的错误报告
os.environ["TRACKLAB_ERROR_REPORTING"] = "false"

# 导入 TrackLab 模块
import tracklab
from tracklab.errors import TrackLabError
from tracklab.sdk.lib import filesystem, module, runid


# --------------------------------
# 全局 pytest 配置
# --------------------------------

@pytest.fixture(autouse=True)
def setup_tracklab_env_variables(monkeypatch: pytest.MonkeyPatch) -> None:
    """配置 TrackLab 环境变量为适合测试的默认值"""
    # 设置网络缓冲区大小
    monkeypatch.setenv("TRACKLAB_X_NETWORK_BUFFER", "1000")
    # 设置为测试模式
    monkeypatch.setenv("TRACKLAB_MODE", "test")


# --------------------------------
# 资源管理 Fixtures
# --------------------------------

@pytest.fixture(scope="session")
def assets_path() -> Generator[Callable[[str], Path], None, None]:
    """返回测试资源文件路径的函数"""
    assets_dir = Path(__file__).resolve().parent / "assets"
    
    def assets_path_fn(path: str) -> Path:
        return assets_dir / path
    
    yield assets_path_fn


@pytest.fixture
def copy_asset(assets_path) -> Generator[Callable[[str, str | None], Path], None, None]:
    """复制测试资源文件的函数"""
    def copy_asset_fn(path: str, dst: str | None = None) -> Path:
        src = assets_path(path)
        if src.is_file():
            return shutil.copy(src, dst or path)
        return shutil.copytree(src, dst or path)
    
    yield copy_asset_fn


# --------------------------------
# 日志和输出 Fixtures
# --------------------------------

@pytest.fixture()
def tracklab_caplog(caplog: pytest.LogCaptureFixture) -> Iterator[pytest.LogCaptureFixture]:
    """修改的 caplog fixture，用于捕获 TrackLab 日志消息"""
    logger = logging.getLogger("tracklab")
    
    logger.addHandler(caplog.handler)
    try:
        yield caplog
    finally:
        logger.removeHandler(caplog.handler)


@pytest.fixture(autouse=True)
def reset_logger():
    """重置日志记录器"""
    # 重置 TrackLab 日志设置
    logging.getLogger("tracklab").handlers.clear()
    logging.getLogger("tracklab").setLevel(logging.INFO)


class MockTrackLabTerm:
    """用于测试 TrackLab 终端输出的辅助类"""
    
    def __init__(
        self,
        termlog: unittest.mock.MagicMock,
        termwarn: unittest.mock.MagicMock,
        termerror: unittest.mock.MagicMock,
    ):
        self._termlog = termlog
        self._termwarn = termwarn
        self._termerror = termerror
    
    def logged(self, msg: str) -> bool:
        """返回消息是否被记录到日志"""
        return self._logged(self._termlog, msg)
    
    def warned(self, msg: str) -> bool:
        """返回消息是否被记录为警告"""
        return self._logged(self._termwarn, msg)
    
    def errored(self, msg: str) -> bool:
        """返回消息是否被记录为错误"""
        return self._logged(self._termerror, msg)
    
    def _logged(self, termfunc: unittest.mock.MagicMock, msg: str) -> bool:
        return any(msg in logged for logged in self._logs(termfunc))
    
    def _logs(self, termfunc: unittest.mock.MagicMock) -> Iterable[str]:
        for call in termfunc.call_args_list:
            if "string" in call.kwargs:
                yield call.kwargs["string"]
            else:
                yield call.args[0]


@pytest.fixture()
def mock_tracklab_term() -> Generator[MockTrackLabTerm, None, None]:
    """Mock TrackLab 终端方法用于测试"""
    with unittest.mock.patch.multiple(
        "tracklab",
        termlog=unittest.mock.DEFAULT,
        termwarn=unittest.mock.DEFAULT,
        termerror=unittest.mock.DEFAULT,
    ) as patched:
        yield MockTrackLabTerm(
            patched["termlog"],
            patched["termwarn"],
            patched["termerror"],
        )


# --------------------------------
# 文件系统隔离 Fixtures
# --------------------------------

@pytest.fixture(scope="function", autouse=True)
def filesystem_isolate(tmp_path, monkeypatch):
    """隔离的文件系统环境"""
    # 设置覆盖率文件路径
    if covfile := os.getenv("COVERAGE_FILE"):
        new_covfile = str(pathlib.Path(covfile).absolute())
    else:
        new_covfile = str(pathlib.Path(os.getcwd()) / ".coverage")
    
    monkeypatch.setenv("COVERAGE_FILE", new_covfile)
    
    # 创建临时目录并切换到该目录
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        yield
    finally:
        os.chdir(original_cwd)


@pytest.fixture(scope="function", autouse=False)
def local_settings(filesystem_isolate):
    """将全局设置放在隔离目录中"""
    config_path = os.path.join(os.getcwd(), ".config", "tracklab", "settings")
    filesystem.mkdir_exists_ok(os.path.join(".config", "tracklab"))
    
    with unittest.mock.patch.object(
        tracklab.Settings,
        "_global_path",
        return_value=config_path,
    ):
        yield


# --------------------------------
# TrackLab 核心 Fixtures
# --------------------------------

@pytest.fixture(scope="function")
def test_settings():
    """创建测试用的设置对象"""
    def update_test_settings(
        extra_settings: dict | tracklab.Settings | None = None,
    ):
        if not extra_settings:
            extra_settings = dict()
        
        settings = tracklab.Settings(
            console="off",
            save_code=False,
            mode="test",
        )
        if isinstance(extra_settings, dict):
            settings.update_from_dict(extra_settings)
        elif isinstance(extra_settings, tracklab.Settings):
            settings.update_from_settings(extra_settings)
        settings.x_start_time = time.time()
        return settings
    
    yield update_test_settings


@pytest.fixture()
def record_q() -> Queue:
    """消息队列用于测试"""
    return Queue()


@pytest.fixture()
def local_backend(record_q: Queue):
    """本地化的后端接口"""
    class MockedLocalBackend:
        def __init__(self) -> None:
            self.record_q = record_q
        
        def log(self, data: dict) -> None:
            self.record_q.put(data)
        
        def save(self, filename: str) -> None:
            self.record_q.put({"type": "save", "filename": filename})
        
        def finish(self) -> None:
            self.record_q.put({"type": "finish"})
    
    yield MockedLocalBackend()


@pytest.fixture(scope="function")
def mock_run(test_settings, local_backend) -> Generator[Callable, None, None]:
    """创建带有 mocked backend 的 Run 对象"""
    
    def mock_run_fn(use_magic_mock=False, **kwargs: Any):
        kwargs_settings = kwargs.pop("settings", dict())
        kwargs_settings = {
            "run_id": runid.generate_id(),
            **dict(kwargs_settings),
        }
        
        # 创建 Run 对象（暂时使用 mock，后续实现真实的 Run 类）
        run = unittest.mock.MagicMock()
        run.settings = test_settings(kwargs_settings)
        run.backend = unittest.mock.MagicMock() if use_magic_mock else local_backend
        
        # 设置全局变量
        module.set_global(
            run=run,
            config=run.config,
            log=run.log,
            summary=run.summary,
            save=run.save,
            use_artifact=run.use_artifact,
            log_artifact=run.log_artifact,
            define_metric=run.define_metric,
            alert=run.alert,
            watch=run.watch,
            unwatch=run.unwatch,
        )
        
        return run
    
    yield mock_run_fn
    module.unset_globals()


# --------------------------------
# 测试数据 Fixtures
# --------------------------------

@pytest.fixture
def example_file(tmp_path: Path) -> Path:
    """创建示例文件"""
    new_file = tmp_path / "test.txt"
    new_file.write_text("hello")
    return new_file


@pytest.fixture
def example_files(tmp_path: Path) -> Path:
    """创建示例文件目录"""
    files_dir = tmp_path / "files"
    files_dir.mkdir(parents=True, exist_ok=True)
    for i in range(3):
        (files_dir / f"file_{i}.txt").write_text(f"content-{i}")
    return files_dir


@pytest.fixture
def dummy_api_key() -> str:
    """虚拟的 API 密钥"""
    return "test_api_key_1234567890abcdef"


# --------------------------------
# 清理 Fixtures
# --------------------------------

@pytest.fixture(scope="function", autouse=True)
def unset_global_objects():
    """清理全局对象"""
    from tracklab.sdk.lib.module import unset_globals
    
    yield
    unset_globals()


@pytest.fixture(scope="function", autouse=True)
def clean_up():
    """清理测试环境"""
    yield
    # 清理 TrackLab 相关的全局状态
    if hasattr(tracklab, "teardown"):
        tracklab.teardown()
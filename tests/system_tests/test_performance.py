"""系统性能测试"""

import pytest
import time
import threading
import unittest.mock
import numpy as np
from pathlib import Path


def test_high_frequency_logging_performance():
    """测试高频率日志记录的性能"""
    import tracklab
    
    with unittest.mock.patch("tracklab.backend.server.get_data_dir") as mock_data_dir:
        mock_data_dir.return_value = Path("test_data")
        
        run = tracklab.init(project="performance-test")
        
        # 记录开始时间
        start_time = time.time()
        
        # 高频率记录大量数据
        num_logs = 10000
        for i in range(num_logs):
            run.log({
                "step": i,
                "metric1": np.random.random(),
                "metric2": np.random.random(),
                "metric3": np.random.random()
            })
        
        # 记录结束时间
        end_time = time.time()
        duration = end_time - start_time
        
        run.finish()
        
        # 验证性能指标
        logs_per_second = num_logs / duration
        assert logs_per_second > 100, f"日志记录速度过慢: {logs_per_second:.2f} logs/sec"
        
        # 验证内存使用情况
        import psutil
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        assert memory_mb < 500, f"内存使用过多: {memory_mb:.2f} MB"


def test_concurrent_runs_performance():
    """测试并发运行的性能"""
    import tracklab
    
    with unittest.mock.patch("tracklab.backend.server.get_data_dir") as mock_data_dir:
        mock_data_dir.return_value = Path("test_data")
        
        def run_experiment(run_id):
            run = tracklab.init(project="concurrent-performance-test", name=f"run-{run_id}")
            
            # 每个运行记录一些数据
            for i in range(1000):
                run.log({
                    "step": i,
                    "loss": np.random.random(),
                    "accuracy": np.random.random()
                })
            
            run.finish()
            return run
        
        # 记录开始时间
        start_time = time.time()
        
        # 创建多个并发运行
        threads = []
        num_runs = 5
        
        for i in range(num_runs):
            thread = threading.Thread(target=run_experiment, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 记录结束时间
        end_time = time.time()
        duration = end_time - start_time
        
        # 验证并发性能
        assert duration < 60, f"并发运行时间过长: {duration:.2f} seconds"


def test_large_config_performance():
    """测试大配置对象的性能"""
    import tracklab
    
    with unittest.mock.patch("tracklab.backend.server.get_data_dir") as mock_data_dir:
        mock_data_dir.return_value = Path("test_data")
        
        # 创建大配置对象
        large_config = {}
        for i in range(10000):
            large_config[f"param_{i}"] = np.random.random()
        
        # 记录开始时间
        start_time = time.time()
        
        run = tracklab.init(project="large-config-test", config=large_config)
        
        # 更新配置
        run.config.update({"additional_param": "value"})
        
        # 记录结束时间
        init_time = time.time() - start_time
        
        run.finish()
        
        # 验证配置处理性能
        assert init_time < 5, f"大配置初始化时间过长: {init_time:.2f} seconds"
        assert len(run.config) == 10001  # 10000 + 1 additional


def test_memory_usage_stability():
    """测试内存使用的稳定性"""
    import tracklab
    import psutil
    
    with unittest.mock.patch("tracklab.backend.server.get_data_dir") as mock_data_dir:
        mock_data_dir.return_value = Path("test_data")
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024
        
        # 创建多个运行来测试内存泄漏
        for run_id in range(10):
            run = tracklab.init(project="memory-test", name=f"run-{run_id}")
            
            # 记录大量数据
            for i in range(1000):
                run.log({
                    "step": i,
                    "data": np.random.random(100).tolist()  # 较大的数据
                })
            
            run.finish()
            
            # 检查内存使用
            current_memory = process.memory_info().rss / 1024 / 1024
            memory_increase = current_memory - initial_memory
            
            # 内存增长不应超过 100MB
            assert memory_increase < 100, f"内存泄漏检测: {memory_increase:.2f} MB"


def test_large_file_handling_performance():
    """测试大文件处理的性能"""
    import tracklab
    from pathlib import Path
    
    with unittest.mock.patch("tracklab.backend.server.get_data_dir") as mock_data_dir:
        mock_data_dir.return_value = Path("test_data")
        
        run = tracklab.init(project="large-file-test")
        
        # 创建大文件
        large_file = Path("large_test_file.txt")
        large_content = "A" * (10 * 1024 * 1024)  # 10MB 文件
        large_file.write_text(large_content)
        
        # 记录开始时间
        start_time = time.time()
        
        # 保存大文件
        run.save(str(large_file))
        
        # 记录结束时间
        save_time = time.time() - start_time
        
        run.finish()
        
        # 验证文件处理性能
        assert save_time < 10, f"大文件保存时间过长: {save_time:.2f} seconds"
        
        # 清理测试文件
        large_file.unlink()


def test_database_performance():
    """测试数据库操作的性能"""
    import tracklab
    
    with unittest.mock.patch("tracklab.backend.server.get_data_dir") as mock_data_dir:
        mock_data_dir.return_value = Path("test_data")
        
        # 创建运行
        run = tracklab.init(project="database-performance-test")
        
        # 记录开始时间
        start_time = time.time()
        
        # 批量写入数据
        for batch in range(100):
            batch_data = []
            for i in range(100):
                batch_data.append({
                    "step": batch * 100 + i,
                    "metric1": np.random.random(),
                    "metric2": np.random.random(),
                    "metric3": np.random.random()
                })
            
            # 批量记录
            for data in batch_data:
                run.log(data)
        
        # 记录结束时间
        write_time = time.time() - start_time
        
        run.finish()
        
        # 验证数据库性能
        total_records = 100 * 100
        records_per_second = total_records / write_time
        assert records_per_second > 500, f"数据库写入速度过慢: {records_per_second:.2f} records/sec"


def test_server_startup_performance():
    """测试服务器启动性能"""
    import tracklab
    
    with unittest.mock.patch("tracklab.backend.server.get_data_dir") as mock_data_dir:
        mock_data_dir.return_value = Path("test_data")
        
        # 记录开始时间
        start_time = time.time()
        
        # 初始化 TrackLab（会启动服务器）
        run = tracklab.init(project="server-startup-test")
        
        # 记录服务器启动时间
        startup_time = time.time() - start_time
        
        run.finish()
        
        # 验证服务器启动性能
        assert startup_time < 5, f"服务器启动时间过长: {startup_time:.2f} seconds"


def test_ui_responsiveness():
    """测试 UI 响应性能"""
    import tracklab
    
    with unittest.mock.patch("tracklab.backend.server.get_data_dir") as mock_data_dir:
        mock_data_dir.return_value = Path("test_data")
        
        run = tracklab.init(project="ui-responsiveness-test")
        
        # 记录大量数据以测试 UI 响应
        for i in range(5000):
            run.log({
                "step": i,
                "loss": np.random.random(),
                "accuracy": np.random.random(),
                "precision": np.random.random(),
                "recall": np.random.random(),
                "f1_score": np.random.random()
            })
        
        # 模拟用户访问 UI
        # 这里可以添加实际的 HTTP 请求测试
        # 或者模拟 UI 数据获取的性能测试
        
        run.finish()
        
        # 验证 UI 数据查询性能
        assert run.state == "finished"


@pytest.mark.slow
def test_long_running_stability():
    """测试长时间运行的稳定性"""
    import tracklab
    
    with unittest.mock.patch("tracklab.backend.server.get_data_dir") as mock_data_dir:
        mock_data_dir.return_value = Path("test_data")
        
        run = tracklab.init(project="long-running-test")
        
        # 模拟长时间运行的实验
        for hour in range(24):  # 模拟 24 小时
            for minute in range(60):  # 每小时 60 次记录
                run.log({
                    "hour": hour,
                    "minute": minute,
                    "metric": np.random.random()
                })
                
                # 短暂暂停以模拟真实训练间隔
                time.sleep(0.001)
        
        run.finish()
        
        # 验证长时间运行的稳定性
        assert run.state == "finished"
        
        # 检查内存使用
        import psutil
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        assert memory_mb < 1000, f"长时间运行后内存使用过多: {memory_mb:.2f} MB"
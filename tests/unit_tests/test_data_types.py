"""测试 TrackLab 数据类型功能"""

import pytest
import numpy as np
from pathlib import Path


def test_image_data_type():
    """测试图像数据类型"""
    from tracklab.data_types import Image
    
    # 测试从 numpy 数组创建图像
    img_array = np.random.rand(100, 100, 3)
    image = Image(img_array)
    
    assert image.data.shape == (100, 100, 3)
    assert image.format == "numpy"
    
    # 测试从文件路径创建图像
    image_from_path = Image("test.png")
    assert image_from_path.path == "test.png"
    assert image_from_path.format == "path"


def test_table_data_type():
    """测试表格数据类型"""
    from tracklab.data_types import Table
    
    # 测试从列表创建表格
    data = [["a", "b", "c"], [1, 2, 3], [4, 5, 6]]
    columns = ["col1", "col2", "col3"]
    
    table = Table(data=data, columns=columns)
    
    assert table.data == data
    assert table.columns == columns
    assert table.rows == 3
    assert table.cols == 3


def test_histogram_data_type():
    """测试直方图数据类型"""
    from tracklab.data_types import Histogram
    
    # 测试从数据创建直方图
    values = np.random.randn(1000)
    histogram = Histogram(values)
    
    assert histogram.values is not None
    assert histogram.bins is not None
    assert len(histogram.values) == len(histogram.bins) - 1


def test_audio_data_type():
    """测试音频数据类型"""
    from tracklab.data_types import Audio
    
    # 测试从数组创建音频
    audio_data = np.random.rand(44100)  # 1 秒的音频
    audio = Audio(audio_data, sample_rate=44100)
    
    assert audio.data.shape == (44100,)
    assert audio.sample_rate == 44100
    assert audio.duration == 1.0


def test_video_data_type():
    """测试视频数据类型"""
    from tracklab.data_types import Video
    
    # 测试从文件路径创建视频
    video = Video("test_video.mp4")
    
    assert video.path == "test_video.mp4"
    assert video.format == "mp4"


def test_object3d_data_type():
    """测试 3D 对象数据类型"""
    from tracklab.data_types import Object3D
    
    # 测试从点云数据创建 3D 对象
    points = np.random.rand(1000, 3)
    obj3d = Object3D(points)
    
    assert obj3d.points.shape == (1000, 3)
    assert obj3d.type == "point_cloud"


def test_plotly_data_type():
    """测试 Plotly 数据类型"""
    from tracklab.data_types import Plotly
    
    # 测试从 Plotly 图创建
    fig_data = {
        "data": [{"x": [1, 2, 3], "y": [4, 5, 6], "type": "scatter"}],
        "layout": {"title": "Test Plot"}
    }
    
    plotly_obj = Plotly(fig_data)
    
    assert plotly_obj.data == fig_data
    assert plotly_obj.layout["title"] == "Test Plot"


def test_html_data_type():
    """测试 HTML 数据类型"""
    from tracklab.data_types import Html
    
    # 测试从 HTML 字符串创建
    html_string = "<h1>Test HTML</h1><p>This is a test.</p>"
    html = Html(html_string)
    
    assert html.html == html_string
    assert "Test HTML" in html.html


def test_data_type_serialization():
    """测试数据类型的序列化"""
    from tracklab.data_types import Image, Table
    
    # 测试图像序列化
    img_array = np.random.rand(50, 50, 3)
    image = Image(img_array)
    
    serialized = image.to_json()
    assert "data" in serialized
    assert "format" in serialized
    
    # 测试表格序列化
    data = [["a", "b"], [1, 2], [3, 4]]
    columns = ["col1", "col2"]
    table = Table(data=data, columns=columns)
    
    serialized = table.to_json()
    assert "data" in serialized
    assert "columns" in serialized


def test_data_type_validation():
    """测试数据类型的验证"""
    from tracklab.data_types import Image, Table
    from tracklab.errors import TrackLabError
    
    # 测试图像验证
    with pytest.raises(TrackLabError, match="Invalid image data"):
        Image("invalid_data")
    
    # 测试表格验证
    with pytest.raises(TrackLabError, match="Invalid table data"):
        Table(data="invalid", columns=["col1"])
    
    with pytest.raises(TrackLabError, match="Columns and data mismatch"):
        Table(data=[[1, 2, 3]], columns=["col1", "col2"])


def test_data_type_conversion():
    """测试数据类型转换"""
    from tracklab.data_types import Image, Table
    
    # 测试图像转换
    img_array = np.random.rand(30, 30, 3)
    image = Image(img_array)
    
    # 转换为 PIL 图像
    pil_image = image.to_pil()
    assert pil_image.size == (30, 30)
    
    # 测试表格转换
    data = [["a", "b"], [1, 2], [3, 4]]
    columns = ["col1", "col2"]
    table = Table(data=data, columns=columns)
    
    # 转换为 pandas DataFrame
    df = table.to_dataframe()
    assert df.shape == (2, 2)
    assert list(df.columns) == columns


def test_data_type_with_metadata():
    """测试带有元数据的数据类型"""
    from tracklab.data_types import Image
    
    img_array = np.random.rand(40, 40, 3)
    image = Image(img_array, caption="Test Image", grouping="validation")
    
    assert image.caption == "Test Image"
    assert image.grouping == "validation"
    
    # 测试序列化包含元数据
    serialized = image.to_json()
    assert "caption" in serialized
    assert "grouping" in serialized
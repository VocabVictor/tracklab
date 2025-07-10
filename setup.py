from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="tracklab",
    version="0.1.0",
    author="TrackLab Team",
    author_email="tracklab@example.com",
    description="Local experiment tracking for machine learning - wandb compatible",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tracklab/tracklab",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: System :: Monitoring",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.7",
    install_requires=[
        "fastapi>=0.68.0",
        "uvicorn[standard]>=0.15.0",
        "sqlalchemy>=1.4.0",
        "pydantic>=1.8.0",
        "psutil>=5.8.0",
        "pillow>=8.0.0",
        "numpy>=1.21.0",
        "pandas>=1.3.0",
        "aiofiles>=0.7.0",
        "python-multipart>=0.0.5",
        "websockets>=10.0",
        "requests>=2.25.0",
        "click>=8.0.0",
        "plotly>=5.0.0",
        "matplotlib>=3.3.0",
        "seaborn>=0.11.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "pytest-asyncio>=0.15.0",
            "black>=21.0.0",
            "flake8>=3.9.0",
            "mypy>=0.910",
            "isort>=5.9.0",
            "pre-commit>=2.15.0",
        ],
        "test": [
            "pytest>=6.0.0",
            "pytest-asyncio>=0.15.0",
            "pytest-cov>=2.12.0",
            "httpx>=0.24.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "tracklab=tracklab.cli.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "tracklab": [
            "server/static/**/*",
            "server/templates/**/*",
        ],
    },
    keywords="machine learning, experiment tracking, wandb, local, visualization",
    project_urls={
        "Bug Reports": "https://github.com/tracklab/tracklab/issues",
        "Source": "https://github.com/tracklab/tracklab",
        "Documentation": "https://tracklab.readthedocs.io/",
    },
)
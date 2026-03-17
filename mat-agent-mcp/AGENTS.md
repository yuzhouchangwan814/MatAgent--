# MatAgent 开发指南

本项目是 **MatAgent** - 一个面向材料科学的 MCP (Model Context Protocol) 服务器，提供材料查询、结构建模、VASP 计算任务管理、机器学习预测等功能。

## 项目架构

```
mat-agent-mcp/
├── mpmcp.py              # 主 MCP 服务器入口，定义所有工具函数
├── mcp_skill.py          # MCP Agent Skill 封装，供外部 Agent 调用
├── main.py               # 项目入口（当前为占位）
├── loadenv.py            # 环境变量加载与配置管理
├── tryssh.py             # SSH 远程连接与 VASP 任务管理
├── databasemanage.py     # SQLite 数据库管理
├── flask_builder.py      # 晶体结构可视化 Web 服务
├── flask_plot.py         # 绘图相关 Flask 服务
├── requirements.txt      # 依赖列表
├── pyproject.toml        # 项目配置
├── myml/                 # 机器学习模块
│   ├── bandgap_predict.py    # 带隙预测模型 (XGBoost)
│   ├── ion_conductivity.py   # 离子电导率预测
│   ├── featurizer.py         # 特征工程
│   ├── atomic_orbital_calc.py # 原子轨道计算
│   ├── element_features*.csv  # 元素特征数据
│   └── *.json               # 训练好的模型文件
└── .vscode/
    └── settings.json
```

## 环境要求

- **Python**: 3.13.4
- **包管理器**: uv (配置见 `uv.toml`，使用阿里云镜像)
- **主要依赖**: fastmcp, pymatgen, mp-api, flask, xgboost, paramiko, duckdb

## 运行命令

### 1. 安装依赖

```bash
# 使用 uv 安装
uv sync

# 或使用 pip
pip install -r requirements.txt
```

### 2. 启动 MCP 服务器

```bash
# 启动 MatAgent MCP 服务（默认端口 8000）
python mpmcp.py

# 或使用 uv 运行
uv run python mpmcp.py
```

### 3. 环境变量配置

需要在 `.env` 文件中配置以下变量：

```
mp_API_KEY=<Materials Project API Key>
local_HOST=<本地IP地址>
HOST=<远程服务器地址>
PORT=<SSH端口>
USERNAME=<SSH用户名>
PASSWORD=<SSH密码>
base_dir=<远程任务根目录>
```

### 4. 测试

```bash
# 运行单个测试文件
python -m pytest tests/test_mpmcp.py -v

# 运行单个测试函数
python -m pytest tests/test_mpmcp.py::test_get_time -v

# 运行所有测试
python -m pytest
```

### 5. Lint/Type Check（项目当前未配置）

项目当前没有配置 lint 或 type check 工具。如需添加，推荐：

```bash
# 安装 ruff（Python linter）
pip install ruff

# 运行 lint
ruff check .

# 安装 mypy（类型检查）
pip install mypy

# 运行类型检查
mypy .
```

## 代码风格指南

### 1. 导入规范

- **标准库导入** → **第三方库导入** → **本地模块导入**（按字母顺序排列）
- 每组之间用一个空行分隔
- 使用绝对导入

```python
# 正确示例
import os
import re
from datetime import datetime

import pandas as pd
from pymatgen.core import Structure
from fastmcp import FastMCP

import databasemanage
import loadenv
import tryssh
```

### 2. 类型注解

- **函数参数和返回值**应使用类型注解
- 使用 `typing` 模块中的 `Optional`, `List`, `Dict`, `Union` 等
- 推荐使用 Python 3.10+ 的内置类型注解语法

```python
# 正确示例
def get_band_gap(material_id: str) -> dict | None:
    ...

def search_materials(
    elements: list[str] | None = None,
    band_gap: tuple[float, float] | None = None,
) -> list[dict]:
    ...
```

### 3. 命名规范

- **函数/方法**: `snake_case` (如 `get_band_gap`, `create_task`)
- **类名**: `PascalCase` (如 `DatabaseManager`, `VaspTaskInitializer`)
- **常量**: `UPPER_SNAKE_CASE` (如 `MAX_STRUCTURES`)
- **私有变量/函数**: 单下划线前缀 (如 `_cleanup_child_processes`)
- **模块文件名**: `snake_case` (如 `flask_builder.py`)

### 4. 文档字符串

- 所有公开函数应包含 docstring
- 使用中文或英文保持一致（项目主要使用中文）
- 格式示例：

```python
@mcp.tool()
async def get_time() -> str:
    """
    获取当前时间
    Returns:
        当前时间字符串，格式为 YYYY-MM-DD HH:MM:SS
    """
    return pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
```

### 5. 错误处理

- 使用 try-except 捕获具体异常，避免 bare except
- 返回错误信息字典而非直接抛出异常（MCP 工具规范）
- 日志记录使用 print 或项目指定的日志模块

```python
# 正确示例
try:
    result = self.conn.execute(...)
    return result
except sqlite3.IntegrityError:
    # 处理唯一约束冲突
    ...
except Exception as e:
    return {"error": str(e), "message": "操作失败"}
```

### 6. 异步处理

- MCP 工具函数使用 `@mcp.tool()` 装饰器
- 推荐使用 async/await 模式
- 异步函数需使用 `async def`

```python
@mcp.tool()
async def get_material_project_page(material_id: str) -> dict:
    ...
```

### 7. 常量定义

- 模块级常量放在文件顶部
- 配置类使用 `Config` 后缀
- Magic numbers 应提取为常量

```python
# 配置常量
MAX_STRUCTURES = 10
STRUCTURE_QUEUE = deque(maxlen=MAX_STRUCTURES)
```

### 8. 线程与进程管理

- 子进程需注册清理函数
- 使用 `atexit.register` 和 signal handler 处理优雅退出

```python
child_processes: list[tuple[multiprocessing.Process, str]] = []

atexit.register(cleanup_child_processes)
signal.signal(signal.SIGTERM, _handle_exit)
```

## 核心功能模块

### 1. MCP 工具 (mpmcp.py)

| 工具名称 | 功能 |
|---------|------|
| `get_time` | 获取当前时间 |
| `get_material_project_page` | 生成 MP 页面链接 |
| `search_materials` | 搜索材料 |
| `get_band_gap` | 获取带隙 |
| `get_material_structure` | 获取晶体结构 |
| `build_structure` | 构建晶体结构 |
| `get_structure_plot` | 生成结构图片 |
| `visualize_structure` | 3D 可视化 |
| `predict_band_gap` | ML 预测带隙 |
| `set_task_progress` | 项目进度管理 |
| SSH 相关工具 | 远程 VASP 任务管理 |

### 2. 数据库 (databasemanage.py)

- 使用 SQLite 存储材料数据
- 支持材料 ID、公式、结构、带隙等字段
- 使用 pickle 序列化 pymatgen Structure 对象

### 3. 远程计算 (tryssh.py)

- SSH/SFTP 连接管理（支持密码或密钥）
- VASP 任务创建、提交、结果提取
- 支持结构优化、自洽计算、能带计算、态密度计算

### 4. 可视化 (flask_builder.py, flask_plot.py)

- Flask 后台服务显示晶体结构
- 3D 交互式 HTML 可视化（ASE）
- 结构图片生成（matplotlib/plotly）

### 5. 机器学习 (myml/)

- **bandgap_predict.py**: XGBoost 带隙预测模型
- **ion_conductivity.py**: 离子电导率预测
- **featurizer.py**: 基于元素特征的材料特征工程
- **atomic_orbital_calc.py**: 原子轨道相关计算

## 常见工作流

### 材料查询 → 构建 → 计算

1. `search_materials()` 查询候选材料
2. `get_material_structure()` 获取结构
3. `build_structure()` 自定义修改
4. SSH 工具提交 VASP 计算
5. `extract_opt_info()` / `extract_scf_info()` 提取结果

### 带隙预测

```python
from myml.bandgap_predict import predict_band_gap
result = predict_band_gap("LiFePO4")
```

## 注意事项

1. **环境变量**: 启动前必须配置 `.env` 文件
2. **MP_API_KEY**: 需要从 Materials Project 官网申请
3. **SSH 连接**: 确保远程服务器可访问，SSH 端口开放
4. **临时文件**: 结构可视化生成的临时文件会定期清理
5. **并发安全**: 数据库操作使用 sqlite3，默认不开启 WAL 模式

## 推荐开发工具

- **IDE**: VS Code (配置见 `.vscode/settings.json`)
- **Python 环境**: 使用 `uv` 管理虚拟环境
- **调试**: 使用 `print()` 或 VS Code 调试器
- **代码格式**: 推荐使用 `ruff format`

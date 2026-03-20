# MatAgent 开发指南

本项目是 **MatAgent** - 一个面向材料科学的 MCP (Model Context Protocol) 服务器，提供材料查询、结构建模、VASP 计算任务管理、机器学习预测等功能。

## 项目定位

MatAgent 是一个专注于材料科学领域的智能计算平台，其核心目标是：

1. **材料数据检索**：整合 Materials Project 数据库，提供高效的晶体结构、电子性质查询
2. **计算任务自动化**：通过 SSH 远程管理 VASP 计算任务，实现结构优化、自洽计算、能带计算全流程自动化
3. **机器学习预测**：基于 XGBoost 的带隙预测模型，实现快速材料性质筛选
4. **智能交互**：通过自然语言处理技术，让用户以对话方式完成复杂的材料计算工作流

**典型应用场景：**
- 新能源材料研发（如锂离子电池正极材料）
- 光伏材料筛选（如钙钛矿太阳能电池）
- 催化材料设计（如 HER/ORR 催化剂）
- 电子材料探索（如高介电常数材料）

---

## 项目架构

```
mat-agent-mcp/
├── mpmcp.py                   # 主 MCP 服务器入口，定义所有工具函数
├── mcp_skill.py               # MCP Agent Skill 封装，供外部 Agent 调用
├── main.py                    # 项目入口（当前为占位）
├── loadenv.py                 # 环境变量加载与配置管理
├── tryssh.py                  # SSH 远程连接与 VASP 任务管理
├── databasemanage.py          # SQLite 数据库管理
├── flask_builder.py           # 晶体结构可视化 Web 服务
├── flask_plot.py              # 绘图相关 Flask 服务
├── web_app.py                 # Streamlit Web 界面
├── requirements.txt           # 依赖列表
├── pyproject.toml             # 项目配置
├── material_workflow.json     # 项目进度存储
├── agent/                     # Agent 核心模块
│   ├── __init__.py
│   ├── agent.py               # MaterialAgent 智能助手实现
│   ├── tool_registry.py       # 工具注册与管理
│   ├── llm_client.py          # DeepSeek LLM 客户端
│   └── prompt_templates.py    # 提示词模板
├── myml/                      # 机器学习模块
│   ├── bandgap_predict.py     # 带隙预测模型 (XGBoost)
│   ├── ion_conductivity.py    # 离子电导率预测
│   ├── featurizer.py          # 特征工程
│   ├── atomic_orbital_calc.py # 原子轨道计算
│   ├── element_features_bandgap.csv  # 带隙预测特征数据
│   └── xgb_model.json         # 训练好的模型文件
├── cifs/                      # CIF 文件存储目录
├── custom_structures/         # 自定义结构存储
├── calculation_output/        # VASP 计算结果输出
├── .env                      # 环境变量配置
└── .vscode/
    └── settings.json
```

---

## 环境要求

- **Python**: 3.13.4
- **包管理器**: uv (配置见 `uv.toml`，使用阿里云镜像)
- **主要依赖**: fastmcp, pymatgen, mp-api, flask, xgboost, paramiko, duckdb, streamlit, openai

---

## 运行命令

### 1. 安装依赖

```bash
# 使用 uv 安装
uv sync

# 或使用 pip
pip install -r requirements.txt
```

### 2. 配置环境变量

在项目根目录创建 `.env` 文件：

```bash
cp .env.example .env
```

编辑 `.env` 文件，配置以下变量：

| 变量名 | 说明 | 示例值 |
|--------|------|--------|
| `mp_API_KEY` | Materials Project API Key | `xxxxx` |
| `local_HOST` | 本地 IP 地址 | `192.168.1.100` |
| `HOST` | 远程 VASP 服务器地址 | `server.example.com` |
| `PORT` | SSH 端口 | `22` |
| `USERNAME` | SSH 用户名 | `vaspuser` |
| `PASSWORD` | SSH 密码 | `xxxxx` |
| `base_dir` | 远程任务根目录 | `/home/vaspuser/vasp_tasks` |
| `DEEPSEEK_API_KEY` | DeepSeek API Key（用于 Agent 对话） | `sk-xxxxx` |
| `MCP_URL` | MCP 服务地址 | `http://127.0.0.1:8000/sse` |

### 3. 启动 MCP 服务器

```bash
# 启动 MatAgent MCP 服务（默认端口 8000）
python mpmcp.py

# 或使用 uv 运行
uv run python mpmcp.py
```

### 4. 启动 Web 界面（可选）

```bash
streamlit run web_app.py
```

访问 `http://localhost:8501` 使用图形界面。

### 5. 测试

```bash
# 运行单个测试文件
python -m pytest tests/test_mpmcp.py -v

# 运行单个测试函数
python -m pytest tests/test_mpmcp.py::test_get_time -v

# 运行所有测试
python -m pytest
```

---

## 核心功能模块

### 1. MCP 工具 (mpmcp.py)

MatAgent MCP 服务器使用 **FastMCP** 框架构建，提供以下工具函数：

#### 1.1 基础辅助工具

| 工具名称 | 功能 | 参数 |
|---------|------|------|
| `get_time` | 获取当前系统时间 | 无 |
| `get_material_project_page` | 生成 Materials Project 页面链接 | `material_id: str` |

#### 1.2 材料查询与信息获取

| 工具名称 | 功能 | 参数 |
|---------|------|------|
| `search_materials` | 从 Materials Project 搜索材料 | `elements`, `exclude_elements`, `chemsys`, `band_gap`, `num_elements`, `formula`, `chunk_size` |
| `get_band_gap` | 获取材料带隙值 | `material_id: str` |
| `get_material_structure` | 获取晶体结构信息 | `material_id`, `get_sites`, `get_plot`, `download` |
| `get_material_all_infomation_by_id` | 获取材料完整信息 | `material_id: str` |

**search_materials 详细参数：**
- `elements`: 包含的元素列表，如 `["Li", "O"]`
- `exclude_elements`: 排除的元素列表，如 `["H"]`
- `chemsys`: 化学系统，如 `"Li-Fe-O"` 或 `["Li-O", "Fe-P"]`
- `band_gap`: 带隙范围元组，如 `(0.0, 2.0)`
- `num_elements`: 元素个数范围，如 `(1, 5)`
- `formula`: 化学式或通配公式，如 `"Li*Cl*"`
- `chunk_size`: 返回结果数量，默认 25，最大 1000

#### 1.3 自定义结构建模

| 工具名称 | 功能 | 参数 |
|---------|------|------|
| `build_structure` | 根据晶格参数和坐标构建晶体结构 | `a`, `b`, `c`, `alpha`, `beta`, `gamma`, `elements`, `frac_coord`, `scaling_matrix`, `save_to_cif`, `add_to_database` |

**build_structure 详细参数：**
- `a`, `b`, `c`: 晶格常数（埃）
- `alpha`, `beta`, `gamma`: 晶格角度（度）
- `elements`: 元素符号列表，如 `["Si", "O", "O"]`
- `frac_coord`: 分数坐标列表，如 `[[0, 0, 0], [0.25, 0.25, 0.25]]`
- `scaling_matrix`: 超胞扩展因子，整数或 `[x, y, z]` 列表
- `save_to_cif`: 是否保存 CIF 文件
- `add_to_database`: 数据库路径，可选

#### 1.4 VASP 远程计算任务管理

| 工具名称 | 功能 | 参数 |
|---------|------|------|
| `create_task` | 创建任务目录并上传 CIF | `formula: str`, `cif_path: str` |
| `list_task_directories` | 列出远程任务目录 | 无 |
| `check_squeue` | 检查 Slurm 任务队列 | 无 |
| `submit_opt_mission` | 提交结构优化任务 | `task_directory: str` |
| `extract_opt_info` | 提取结构优化结果 | `task_directory`, `get_plot`, `visualize` |
| `submit_scf_mission` | 提交自洽计算任务 | `task_directory: str`, `custom_incar` |
| `extract_scf_info` | 提取自洽计算结果 | `task_directory: str` |
| `submit_band_mission` | 提交能带计算任务 | `task_directory: str` |
| `extract_band_info` | 提取能带计算结果 | `task_directory`, `plot_band` |
| `excute_command` | 执行远程 Linux 命令 | `command: str` |

**VASP 计算默认 INCAR 参数：**
- `ENCUT`: 520 eV（平面波截断能量）
- `ISMEAR`: 0（高斯展宽）
- `SIGMA`: 0.05 eV（展宽宽度）
- `EDIFF`: 1E-6（电子步收敛精度）
- `LWAVE`: True（输出 WAVECAR）
- `LCHARG`: True（输出 CHGCAR）
- `NELM`: 100（最大电子步数）

#### 1.5 机器学习预测

| 工具名称 | 功能 | 参数 |
|---------|------|------|
| `predict_band_gap` | 使用 XGBoost 模型预测带隙 | `formula: str | list[str]` |

#### 1.6 项目管理

| 工具名称 | 功能 | 参数 |
|---------|------|------|
| `set_task_progress` | 记录项目进度 | `project_name`, `description`, `step_name`, `status` |
| `list_all_projects` | 列出所有项目 | 无 |
| `get_project_workflow` | 查看项目详情 | `project_name: str` |

**项目状态枚举：**
- `Pending`: 等待中
- `Running`: 运行中
- `Completed`: 已完成
- `Failed`: 失败

#### 1.7 文件管理

| 工具名称 | 功能 | 参数 |
|---------|------|------|
| `read_file` | 读取服务器文件内容 | `file_path: str` |

---

### 2. Agent 模块 (agent/)

#### 2.1 MaterialAgent 智能助手

`agent/agent.py` 中的 `MaterialAgent` 类是核心智能助手，实现基于 LLM 的材料科学问答：

```python
from agent import create_agent
from mcp_skill import MCPAgentSkill

# 初始化
skill = MCPAgentSkill(mcp_url="http://127.0.0.1:8000")
agent = create_agent(mcp_skill=skill)

# 对话交互
response = agent.chat("帮我搜索带隙在 1-2 eV 的锂离子电池材料")
```

**核心特性：**
- **LLM 集成**：使用 DeepSeek API 进行自然语言理解
- **工具自动选择**：根据用户意图自动调用合适的 MCP 工具
- **结果格式化**：自动将工具返回结果转换为易读的 Markdown 格式
- **对话历史管理**：维护完整的对话上下文
- **多轮对话支持**：支持复杂的多步骤材料计算工作流

**系统提示词 (SYSTEM_PROMPT)：**
```
你是一个专业的材料科学智能助手，专门帮助用户进行材料设计与计算。

## 你的能力

1. **材料查询**: 从 Materials Project 数据库搜索材料，查询带隙、结构等信息
2. **结构建模**: 根据晶格参数和原子坐标构建自定义晶体结构
3. **ML 预测**: 使用机器学习模型预测材料的带隙
4. **VASP 计算**: 管理远程服务器的 VASP 计算任务（结构优化、自洽、能带等）
5. **项目管理**: 跟踪材料研发项目的进度
```

#### 2.2 ToolRegistry 工具注册

`agent/tool_registry.py` 负责将 MCP 工具注册为 OpenAI Function Calling 格式：

```python
from agent.tool_registry import create_tool_registry

registry = create_tool_registry(mcp_skill=skill)
functions = registry.get_openai_functions()  # 获取 OpenAI 函数定义列表

# 函数定义示例
{
    "type": "function",
    "function": {
        "name": "search_materials",
        "description": "从Materials Project数据库搜索材料...",
        "parameters": {
            "type": "object",
            "properties": {
                "elements": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "包含的元素列表"
                },
                ...
            }
        }
    }
}
```

#### 2.3 LLM 客户端

`agent/llm_client.py` 封装 DeepSeek API 调用：

```python
from agent.llm_client import DeepSeekClient

client = DeepSeekClient(api_key="sk-xxxxx")

# 基础对话
response = client.chat(messages=[...], temperature=0.7)

# 函数调用对话
result = client.chat_with_functions(
    messages=[...],
    functions=[...],
    function_call="auto"
)
```

---

### 3. MCP Skill 封装 (mcp_skill.py)

`MCPAgentSkill` 类提供同步/异步接口供外部系统调用：

```python
from mcp_skill import MCPAgentSkill

skill = MCPAgentSkill(mcp_url="http://127.0.0.1:8000")

# 列出可用工具
print(skill.list_tools())

# 调用工具示例
result = skill.get_band_gap("mp-149")
result = skill.search_materials(elements=["Li", "O"], band_gap=(0, 2))
result = skill.predict_band_gap("LiFePO4")
result = skill.submit_opt_mission("/path/to/task")
result = skill.extract_band_info("/path/to/task", plot_band=True)
```

---

### 4. 远程计算 (tryssh.py)

#### 4.1 VaspTaskInitializer

`tryssh.py` 中的 `VaspTaskInitializer` 类管理 SSH/SFTP 连接和 VASP 任务：

```python
import tryssh

with tryssh.VaspTaskInitializer(host, username, password, port) as vasp_task:
    # 创建任务目录
    task_dir = vasp_task.create_task("SiO2", "cifs/SiO2.cif", "/base/dir")
    
    # 提交各类计算
    vasp_task.opt(task_dir)           # 结构优化
    vasp_task.scf(task_dir)           # 自洽计算
    vasp_task.band_calc(task_dir)     # 能带计算
    
    # 提取计算结果
    opt_result = vasp_task.extract_opt_info(task_dir)
    scf_result = vasp_task.extract_scf_info(task_dir)
    band_result = vasp_task.extract_band_info(task_dir)
```

**核心方法：**

| 方法 | 功能 | 返回信息 |
|------|------|----------|
| `create_task()` | 创建任务目录、上传 CIF | 任务目录路径 |
| `opt()` | 提交结构优化 | 执行状态 |
| `scf()` | 提交自洽计算 | 执行状态 |
| `band_calc()` | 提交能带计算 | 执行状态 |
| `extract_opt_info()` | 提取结构优化结果 | 能量、力、应力、结构 |
| `extract_scf_info()` | 提取自洽结果 | 能量、带隙、费米能级 |
| `extract_band_info()` | 提取能带结果 | 带隙、VBM、CBM、能带图 |
| `excute_command()` | 执行远程命令 | stdout/stderr |

**安全机制：**
- `excute_command()` 内置危险命令检测
- 拒绝 `rm -rf`, `shutdown`, `mkfs` 等操作
- 支持 Python 代码执行的白名单模式

---

### 5. 数据库 (databasemanage.py)

使用 SQLite 存储材料数据，支持 pickle 序列化 pymatgen Structure 对象：

```python
import databasemanage
from pymatgen.core import Structure

db = databasemanage.DatabaseManager("materials.db")

# 添加材料
struct = Structure.from_file("cifs/SiO2.cif")
db.add_material("SiO2", struct, 1.5, "mp-123")

# 查询材料
material = db.get_material_by_material_id("mp-123")
materials = db.get_material_by_elements("Li", page=1, page_size=10)
all_materials = db.list_all_materials_by_pages(page=1, page_size=10)

# 更新与删除
db.update_material(material['ID'], band_gap=2.0)
db.remove_material(material['ID'])

db.close()
```

**数据库表结构：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `ID` | INTEGER | 自增主键 |
| `add_time` | TIMESTAMP | 添加时间 |
| `material_id` | VARCHAR | Materials Project ID |
| `formula` | VARCHAR | 化学式 |
| `structure` | BLOB | pymatgen Structure (pickle) |
| `band_gap` | FLOAT | 带隙值 |

---

### 6. 可视化模块

#### 6.1 Flask 3D 可视化 (flask_builder.py)

```python
from flask_builder import CrystalManager
from pymatgen.core import Structure

struct = Structure.from_file("cifs/SiO2.cif")
manager = CrystalManager()
url = manager.show(struct, "path/to/3d.html")
# 返回访问链接：http://local_ip:6750/view/uuid
```

**特性：**
- 基于 ASE 的 3D 交互式 HTML 可视化
- 自动生成晶格参数、原子位点信息面板
- 支持 CIF 文件下载
- 最多缓存 10 个结构，自动清理旧结构

#### 6.2 结构图生成 (flask_plot.py)

提供内存图像服务器，将 matplotlib 图表转换为 URL：

```python
from flask_plot import MemoryImageServer
import matplotlib.pyplot as plt
import io

server = MemoryImageServer(port=6760)

fig, ax = plt.subplots()
ax.plot([1, 2, 3], [1, 4, 9])
plt.savefig(buf := io.BytesIO(), format='png')
url = server.add_image(buf)
```

**能带图绘制特性：**
- 使用 VASPKIT 导出格式化数据
- 自动识别高对称点路径
- 费米能级参考线
- 支持金属/半导体判别

---

### 7. 机器学习模块 (myml/)

#### 7.1 带隙预测 (bandgap_predict.py)

基于 XGBoost 的带隙预测模型：

```python
from myml.bandgap_predict import predict_bandgap

# 单个材料
result = predict_bandgap("LiFePO4")
# 返回: [1.23]

# 批量预测
result = predict_bandgap(["LiFePO4", "LiCoO2", "LiMn2O4"])
# 返回: [1.23, 2.56, 1.89]
```

**特征工程：**
- 从 80+ 元素特征计算统计量
- 支持括号和小数系数的化学式解析（如 `Ag(W3Br7)2`, `Ag0.5Ge1Pb1.75S4`）
- 特征类型：max, min, avg, range, std

---

### 8. Web 界面 (web_app.py)

Streamlit 图形界面提供以下功能面板：

| 面板 | 功能 |
|------|------|
| AI 对话 | 自然语言交互 |
| 材料查询 | 按元素、带隙等条件搜索 MP 数据库 |
| 结构建模 | 可视化构建晶体结构 |
| ML 预测 | 带隙预测 |
| VASP 任务 | 远程任务提交与管理 |
| 项目管理 | 项目进度跟踪 |
| 文件管理 | 读取服务器文件 |

---

## 技术架构

### 1. MCP 服务端架构

```
                    ┌─────────────────┐
                    │   MCP Client    │
                    │  (Agent/App)    │
                    └────────┬────────┘
                             │ SSE/HTTP
                             ▼
┌──────────────────────────────────────────────────────┐
│                    MCP Server                         │
│  ┌─────────────────────────────────────────────────┐ │
│  │           FastMCP @mcp.tool()                  │ │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────────────┐  │ │
│  │  │ 材料查询 │ │结构建模 │ │ VASP任务管理    │  │ │
│  │  │ 工具集   │ │ 工具集  │ │    工具集       │  │ │
│  │  └─────────┘ └─────────┘ └─────────────────┘  │ │
│  └─────────────────────────────────────────────────┘ │
│                         │                             │
│          ┌──────────────┼──────────────┐             │
│          ▼              ▼              ▼             │
│   ┌────────────┐ ┌────────────┐ ┌────────────┐      │
│   │ Materials  │ │  Database  │ │   Remote   │      │
│   │  Project   │ │  SQLite   │ │   Server   │      │
│   │    API     │ │           │ │   (SSH)    │      │
│   └────────────┘ └────────────┘ └────────────┘      │
└──────────────────────────────────────────────────────┘
```

### 2. Agent 工作流

```
用户输入 ──► MaterialAgent.chat()
                 │
                 ▼
         ┌──────────────┐
         │  DeepSeek    │
         │    LLM       │
         │  (Function   │
         │   Calling)   │
         └──────┬───────┘
                │
                ▼ (tool_calls)
         ┌──────────────┐
         │ ToolRegistry  │
         │   execute()   │
         └──────┬───────┘
                │
                ▼
         ┌──────────────┐
         │ MCPAgentSkill│
         │  call_tool() │
         └──────┬───────┘
                │
                ▼
         ┌──────────────┐
         │   MCP Server  │
         │   (mpmcp.py) │
         └──────────────┘
```

---

## 使用指南

### 典型工作流

#### 1. 材料查询 → 结构获取

```python
# 搜索材料
results = skill.search_materials(
    elements=["Li", "Co", "O"],
    band_gap=(0, 3),
    chunk_size=10
)

# 获取结构
structure = skill.get_material_structure(
    material_id="mp-1234",
    get_plot=True,
    download=True
)
```

#### 2. 自定义结构建模

```python
# 构建 NaCl 结构 (岩盐结构)
skill.build_structure(
    a=5.64, b=5.64, c=5.64,
    alpha=90, beta=90, gamma=90,
    elements=["Na", "Cl", "Na", "Cl"],
    frac_coord=[
        [0, 0, 0],
        [0.5, 0.5, 0.5],
        [0.5, 0.5, 0],
        [0, 0, 0.5]
    ],
    save_to_cif=True
)
```

#### 3. VASP 计算流程

```python
# 1. 创建任务
task_dir = skill.create_task("SiO2", "cifs/SiO2.cif")

# 2. 提交结构优化
skill.submit_opt_mission(task_dir)

# 3. 检查任务状态
skill.check_squeue()

# 4. 提取优化结果
opt_result = skill.extract_opt_info(task_dir, get_plot=True)

# 5. 提交自洽计算
skill.submit_scf_mission(task_dir)

# 6. 提取自洽结果
scf_result = skill.extract_scf_info(task_dir)

# 7. 提交能带计算
skill.submit_band_mission(task_dir)

# 8. 提取能带结果并绘图
band_result = skill.extract_band_info(task_dir, plot_band=True)
```

#### 4. 带隙预测

```python
# 单个材料
result = skill.predict_band_gap("LiFePO4")

# 批量预测
result = skill.predict_band_gap(["LiFePO4", "LiCoO2", "LiMn2O4"])
```

#### 5. 项目管理

```python
# 创建项目
skill.set_task_progress(
    project_name="LiFePO4_Bandgap_Study",
    description="研究 LiFePO4 的带隙性质",
    step_name="Init",
    status="Pending"
)

# 更新进度
skill.set_task_progress(
    project_name="LiFePO4_Bandgap_Study",
    step_name="Structure_Optimization",
    status="Running"
)

# 查看项目
workflow = skill.get_project_workflow("LiFePO4_Bandgap_Study")
```

---

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

---

## 注意事项

1. **环境变量**: 启动前必须配置 `.env` 文件
2. **MP_API_KEY**: 需要从 [Materials Project](https://next-gen.materialsproject.org/) 官网申请
3. **SSH 连接**: 确保远程服务器可访问，SSH 端口开放
4. **临时文件**: 结构可视化生成的临时文件会定期清理
5. **并发安全**: 数据库操作使用 sqlite3，默认不开启 WAL 模式

---

## 推荐开发工具

- **IDE**: VS Code (配置见 `.vscode/settings.json`)
- **Python 环境**: 使用 `uv` 管理虚拟环境
- **调试**: 使用 `print()` 或 VS Code 调试器
- **代码格式**: 推荐使用 `ruff format`

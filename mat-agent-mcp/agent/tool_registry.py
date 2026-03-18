from typing import Any, Callable, Optional, Dict, List
import json


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Dict] = {}
        self._mcp_skill: Optional[Any] = None

    def register(self, name: str, func: Callable, description: str, parameters: dict):
        self._tools[name] = {
            "func": func,
            "description": description,
            "parameters": parameters,
        }

    def set_mcp_skill(self, mcp_skill):
        self._mcp_skill = mcp_skill

    def get_tool(self, name: str) -> Optional[dict]:
        return self._tools.get(name)

    def get_all_tools(self) -> dict:
        return self._tools

    def get_openai_functions(self) -> List[dict]:
        functions = []
        for name, tool in self._tools.items():
            functions.append(
                {
                    "type": "function",
                    "function": {
                        "name": name,
                        "description": tool["description"],
                        "parameters": tool["parameters"],
                    },
                }
            )
        return functions

    def execute(self, name: str, arguments: dict) -> Any:
        tool = self._tools.get(name)
        if not tool:
            return {"error": f"Tool {name} not found"}

        try:
            func = tool["func"]
            if self._mcp_skill and func is None:
                method = getattr(self._mcp_skill, name, None)
                if method:
                    result = method(**arguments)
                    return result
            elif func:
                result = func(**arguments)
                return result
            else:
                return {"error": f"无法执行工具 {name}: 未连接到 MCP"}
        except Exception as e:
            return {"error": str(e)}

    def execute_from_string(self, name: str, arguments_json: str) -> Any:
        try:
            arguments = json.loads(arguments_json)
        except json.JSONDecodeError:
            return {"error": f"Invalid JSON arguments: {arguments_json}"}
        return self.execute(name, arguments)


def create_tool_registry(mcp_skill=None) -> ToolRegistry:
    registry = ToolRegistry()
    registry.set_mcp_skill(mcp_skill)

    registry.register(
        "get_time",
        None,
        "获取当前系统时间，返回当前日期和时间",
        {"type": "object", "properties": {}, "required": []},
    )

    registry.register(
        "get_material_project_page",
        None,
        "获取指定材料的Materials Project页面链接",
        {
            "type": "object",
            "properties": {
                "material_id": {"type": "string", "description": "材料ID，如 mp-1234"}
            },
            "required": ["material_id"],
        },
    )

    registry.register(
        "search_materials",
        None,
        "从Materials Project数据库搜索材料，支持按元素、带隙范围、化学系统、公式等条件筛选，返回材料的基本信息",
        {
            "type": "object",
            "properties": {
                "elements": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "包含的元素列表，如 ['Li', 'O']",
                },
                "exclude_elements": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "排除的元素列表，如 ['H']",
                },
                "chemsys": {"type": "string", "description": "化学系统，如 'Li-Fe-O'"},
                "band_gap": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "带隙范围 [最小值, 最大值]，单位 eV",
                },
                "num_elements": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "元素个数范围 [最小, 最大]",
                },
                "formula": {
                    "type": "string",
                    "description": "化学式，支持通配符，如 'Li*Cl*'",
                },
                "chunk_size": {
                    "type": "integer",
                    "description": "返回结果数量，默认25，最大1000",
                },
            },
            "required": [],
        },
    )

    registry.register(
        "get_band_gap",
        None,
        "获取指定材料的带隙值（电子伏特）",
        {
            "type": "object",
            "properties": {
                "material_id": {"type": "string", "description": "材料ID，如 mp-1234"}
            },
            "required": ["material_id"],
        },
    )

    registry.register(
        "get_material_structure",
        None,
        "获取指定材料的晶体结构信息，包括空间群、晶格参数、原子位置等，可生成结构图和3D可视化",
        {
            "type": "object",
            "properties": {
                "material_id": {"type": "string", "description": "材料ID"},
                "get_sites": {"type": "boolean", "description": "是否获取原子位点信息"},
                "get_plot": {"type": "boolean", "description": "是否生成结构图"},
                "download": {"type": "boolean", "description": "是否下载CIF文件"},
            },
            "required": ["material_id"],
        },
    )

    registry.register(
        "build_structure",
        None,
        "根据晶格参数和原子坐标自定义构建晶体结构，可设置超胞，生成结构图和3D可视化",
        {
            "type": "object",
            "properties": {
                "a": {"type": "number", "description": "晶格参数 a (埃)"},
                "b": {"type": "number", "description": "晶格参数 b (埃)"},
                "c": {"type": "number", "description": "晶格参数 c (埃)"},
                "alpha": {"type": "number", "description": "晶格角 alpha (度)"},
                "beta": {"type": "number", "description": "晶格角 beta (度)"},
                "gamma": {"type": "number", "description": "晶格角 gamma (度)"},
                "elements": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "元素符号列表，如 ['Si', 'O', 'O']",
                },
                "frac_coord": {
                    "type": "array",
                    "items": {"type": "array", "items": {"type": "number"}},
                    "description": "分数坐标列表，与元素对应",
                },
                "scaling_matrix": {
                    "oneOf": [{"type": "integer"}, {"type": "array"}],
                    "description": "超胞扩展因子，整数或 [x,y,z] 列表",
                },
                "save_to_cif": {"type": "boolean", "description": "是否保存CIF文件"},
                "add_to_database": {
                    "type": "string",
                    "description": "数据库路径，可选",
                },
            },
            "required": [
                "a",
                "b",
                "c",
                "alpha",
                "beta",
                "gamma",
                "elements",
                "frac_coord",
            ],
        },
    )

    registry.register(
        "predict_band_gap",
        None,
        "使用机器学习模型预测材料的带隙值",
        {
            "type": "object",
            "properties": {
                "formula": {
                    "oneOf": [{"type": "string"}, {"type": "array"}],
                    "description": "化学式字符串或列表，如 'LiFePO4'",
                }
            },
            "required": ["formula"],
        },
    )

    registry.register(
        "create_task",
        None,
        "在远程VASP服务器上创建任务目录并上传CIF文件",
        {
            "type": "object",
            "properties": {
                "formula": {"type": "string", "description": "化学式"},
                "cif_path": {"type": "string", "description": "本地CIF文件路径"},
            },
            "required": ["formula", "cif_path"],
        },
    )

    registry.register(
        "list_task_directories",
        None,
        "列出远程VASP服务器上的所有任务目录",
        {"type": "object", "properties": {}, "required": []},
    )

    registry.register(
        "check_squeue",
        None,
        "检查远程服务器上的Slurm任务队列状态",
        {"type": "object", "properties": {}, "required": []},
    )

    registry.register(
        "submit_opt_mission",
        None,
        "提交结构优化任务到远程VASP服务器",
        {
            "type": "object",
            "properties": {
                "task_directory": {"type": "string", "description": "任务目录路径"}
            },
            "required": ["task_directory"],
        },
    )

    registry.register(
        "extract_opt_info",
        None,
        "提取结构优化任务的结果信息",
        {
            "type": "object",
            "properties": {
                "task_directory": {"type": "string", "description": "任务目录路径"},
                "get_plot": {"type": "boolean", "description": "是否生成结构图"},
                "visualize": {"type": "boolean", "description": "是否生成3D可视化"},
            },
            "required": ["task_directory"],
        },
    )

    registry.register(
        "submit_scf_mission",
        None,
        "提交自洽计算任务到远程VASP服务器",
        {
            "type": "object",
            "properties": {
                "task_directory": {"type": "string", "description": "任务目录路径"},
                "custom_incar": {"type": "object", "description": "自定义INCAR参数"},
            },
            "required": ["task_directory"],
        },
    )

    registry.register(
        "extract_scf_info",
        None,
        "提取自洽计算任务的结果信息",
        {
            "type": "object",
            "properties": {
                "task_directory": {"type": "string", "description": "任务目录路径"}
            },
            "required": ["task_directory"],
        },
    )

    registry.register(
        "submit_band_mission",
        None,
        "提交能带计算任务到远程VASP服务器",
        {
            "type": "object",
            "properties": {
                "task_directory": {"type": "string", "description": "任务目录路径"}
            },
            "required": ["task_directory"],
        },
    )

    registry.register(
        "extract_band_info",
        None,
        "提取能带计算任务的结果信息，可绘制能带图",
        {
            "type": "object",
            "properties": {
                "task_directory": {"type": "string", "description": "任务目录路径"},
                "plot_band": {"type": "boolean", "description": "是否绘制能带图"},
            },
            "required": ["task_directory"],
        },
    )

    registry.register(
        "excute_command",
        None,
        "在远程VASP服务器上执行Linux命令",
        {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "要执行的命令"}
            },
            "required": ["command"],
        },
    )

    registry.register(
        "set_task_progress",
        None,
        "记录或更新材料研发项目的进度",
        {
            "type": "object",
            "properties": {
                "project_name": {"type": "string", "description": "项目名称"},
                "description": {"type": "string", "description": "项目描述"},
                "step_name": {"type": "string", "description": "步骤名称"},
                "status": {
                    "type": "string",
                    "description": "状态：Pending/Running/Completed/Failed",
                },
            },
            "required": ["project_name"],
        },
    )

    registry.register(
        "list_all_projects",
        None,
        "列出当前所有材料研发项目名称",
        {"type": "object", "properties": {}, "required": []},
    )

    registry.register(
        "get_project_workflow",
        None,
        "查看指定项目的详细任务清单和进度",
        {
            "type": "object",
            "properties": {
                "project_name": {"type": "string", "description": "项目名称"}
            },
            "required": ["project_name"],
        },
    )

    registry.register(
        "read_file",
        None,
        "读取MCP服务器上的文件内容",
        {
            "type": "object",
            "properties": {"file_path": {"type": "string", "description": "文件路径"}},
            "required": ["file_path"],
        },
    )

    registry.register(
        "get_material_all_infomation_by_id",
        None,
        "获取指定材料的完整Materials Project数据",
        {
            "type": "object",
            "properties": {"material_id": {"type": "string", "description": "材料ID"}},
            "required": ["material_id"],
        },
    )

    return registry


TOOL_REGISTRY = create_tool_registry()


def get_tool_schemas() -> list:
    return TOOL_REGISTRY.get_openai_functions()


def get_tool_registry() -> ToolRegistry:
    return TOOL_REGISTRY

"""MCP Agent Skill

这个文件定义了一个可被 agent 直接调用的 skill 类：
- 连接你的 mpmcp 服务（默认 http://127.0.0.1:8000）
- 列出工具、调用工具
- 常用材料和计算任务接口封装

使用方式：
    from mcp_skill import MCPAgentSkill
    skill = MCPAgentSkill(mcp_url="http://127.0.0.1:8000")
    result = skill.get_band_gap("mp-149")
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

from fastmcp.client import Client


class MCPAgentSkill:
    """Agent Skill wrapper for your mcp service."""

    def __init__(self, mcp_url: str = "http://127.0.0.1:8000"):
        self.mcp_url = mcp_url
        self.client = Client(mcp_url)

    def _convert_result(self, result):
        """将MCP返回的结果转换为Python字典"""
        import json

        if result is None:
            return None

        # 处理 CallToolResult 对象（FastMCP 返回的对象）
        if hasattr(result, "content"):
            # 这是一个 CallToolResult 对象
            content = result.content
            if isinstance(content, list) and len(content) > 0:
                # 取第一个 content item
                first_content = content[0]
                if hasattr(first_content, "text"):
                    try:
                        return json.loads(first_content.text)
                    except (json.JSONDecodeError, AttributeError):
                        return {"result": first_content.text}
                elif hasattr(first_content, "structured_content"):
                    # structured_content 已经是字典
                    return first_content.structured_content
                elif isinstance(first_content, dict):
                    return first_content
            # 如果没有 content，返回原始对象的字符串形式
            return {"result": str(result)}

        if isinstance(result, dict):
            return result

        if isinstance(result, list):
            return [self._convert_result(item) for item in result]

        if hasattr(result, "text"):
            try:
                return json.loads(result.text)
            except (json.JSONDecodeError, AttributeError):
                return {"result": result.text}

        if hasattr(result, "json"):
            return result.json

        return {"result": str(result)}

    async def _call_tool_async(
        self, tool_name: str, arguments: Optional[Dict[str, Any]] = None
    ) -> Any:
        arguments = arguments or {}
        async with self.client as c:
            result = await c.call_tool(tool_name, arguments)
        # 转换 MCP 结果为 Python 字典
        if isinstance(result, list) and len(result) == 1:
            return self._convert_result(result[0])
        elif isinstance(result, list):
            return self._convert_result(result)
        return self._convert_result(result)

    async def _list_tools_async(self) -> List[str]:
        async with self.client as c:
            tools = await c.list_tools()
        # 如果返回对象含 name 字段，则提取
        if isinstance(tools, list):
            return [t.name if hasattr(t, "name") else str(t) for t in tools]
        return [str(tools)]

    def _run_async(self, coro):
        return asyncio.run(coro)

    def list_tools(self) -> List[str]:
        """列出当前 mcp 服务中的可用工具名称。"""
        return self._run_async(self._list_tools_async())

    def call_tool(
        self, tool_name: str, arguments: Optional[Dict[str, Any]] = None
    ) -> Any:
        """通用调用任意 MCP 工具。"""
        # 过滤掉 None 和空字符串参数
        if arguments:
            arguments = {
                k: v for k, v in arguments.items() if v is not None and v != ""
            }
        return self._run_async(self._call_tool_async(tool_name, arguments))

    def get_time(self) -> str:
        return self.call_tool("get_time")

    def get_material_project_page(self, material_id: str) -> dict:
        return self.call_tool("get_material_project_page", {"material_id": material_id})

    def search_materials(
        self,
        elements: Optional[List[str]] = None,
        exclude_elements: Optional[List[str]] = None,
        chemsys: Optional[str | List[str]] = None,
        band_gap: Optional[tuple[float, float]] = None,
        num_elements: Optional[tuple[int, int]] = None,
        formula: Optional[str | List[str]] = None,
        chunk_size: Optional[int] = 25,
    ) -> Any:
        args = {
            "elements": elements,
            "exclude_elements": exclude_elements,
            "chemsys": chemsys,
            "band_gap": band_gap,
            "num_elements": num_elements,
            "formula": formula,
            "chunk_size": chunk_size,
        }
        # 移除 None 参数
        args = {k: v for k, v in args.items() if v is not None}
        return self.call_tool("search_materials", args)

    def get_band_gap(self, material_id: str) -> Any:
        return self.call_tool("get_band_gap", {"material_id": material_id})

    def get_material_structure(
        self,
        material_id: str,
        get_sites: bool = False,
        get_plot: bool = False,
        download: bool = False,
    ) -> Any:
        return self.call_tool(
            "get_material_structure",
            {
                "material_id": material_id,
                "get_sites": get_sites,
                "get_plot": get_plot,
                "download": download,
            },
        )

    def build_structure(
        self,
        a: float,
        b: float,
        c: float,
        alpha: float,
        beta: float,
        gamma: float,
        elements: List[str],
        frac_coord: List[List[float]],
        scaling_matrix: int | List[int] = 1,
        save_to_cif: bool = False,
        add_to_database: Optional[str] = None,
    ) -> Any:
        return self.call_tool(
            "build_structure",
            {
                "a": a,
                "b": b,
                "c": c,
                "alpha": alpha,
                "beta": beta,
                "gamma": gamma,
                "elements": elements,
                "frac_coord": frac_coord,
                "scaling_matrix": scaling_matrix,
                "save_to_cif": save_to_cif,
                "add_to_database": add_to_database,
            },
        )

    def create_task(self, formula: str, cif_path: str) -> Any:
        return self.call_tool("create_task", {"formula": formula, "cif_path": cif_path})

    def list_task_directories(self) -> Any:
        return self.call_tool("list_task_directories")

    def check_squeue(self) -> Any:
        return self.call_tool("check_squeue")

    def submit_opt_mission(self, task_directory: str) -> Any:
        return self.call_tool("submit_opt_mission", {"task_directory": task_directory})

    def extract_opt_info(
        self, task_directory: str, get_plot: bool = True, visualize: bool = False
    ) -> Any:
        return self.call_tool(
            "extract_opt_info",
            {
                "task_directory": task_directory,
                "get_plot": get_plot,
                "visualize": visualize,
            },
        )

    def submit_scf_mission(
        self, task_directory: str, custom_incar: Optional[Dict[str, Any]] = None
    ) -> Any:
        return self.call_tool(
            "submit_scf_mission",
            {
                "task_directory": task_directory,
                "custom_incar": custom_incar,
            },
        )

    def extract_scf_info(self, task_directory: str) -> Any:
        return self.call_tool("extract_scf_info", {"task_directory": task_directory})

    def submit_band_mission(self, task_directory: str) -> Any:
        return self.call_tool("submit_band_mission", {"task_directory": task_directory})

    def extract_band_info(self, task_directory: str, plot_band: bool = True) -> Any:
        return self.call_tool(
            "extract_band_info",
            {"task_directory": task_directory, "plot_band": plot_band},
        )

    def excute_command(self, command: str) -> Any:
        return self.call_tool("excute_command", {"command": command})

    def predict_band_gap(self, formula: str | list[str]) -> Any:
        return self.call_tool("predict_band_gap", {"formula": formula})

    def set_task_progress(
        self,
        project_name: str,
        description: str = "",
        step_name: str = "",
        status: str = "",
    ) -> Any:
        return self.call_tool(
            "set_task_progress",
            {
                "project_name": project_name,
                "description": description,
                "step_name": step_name,
                "status": status,
            },
        )

    def list_all_projects(self) -> Any:
        return self.call_tool("list_all_projects")

    def get_project_workflow(self, project_name: str) -> Any:
        return self.call_tool("get_project_workflow", {"project_name": project_name})

    def read_file(self, file_path: str) -> Any:
        return self.call_tool("read_file", {"file_path": file_path})

    def get_material_all_infomation_by_id(self, material_id: str) -> Any:
        return self.call_tool(
            "get_material_all_infomation_by_id", {"material_id": material_id}
        )


if __name__ == "__main__":
    skill = MCPAgentSkill()
    print("[MCP Skill] 已连接到", skill.mcp_url)
    print("[MCP Skill] 可用工具：", skill.list_tools())
    print("[示例] get_time ->", skill.get_time())

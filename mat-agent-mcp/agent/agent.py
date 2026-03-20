import json
from typing import Any, Optional
from .llm_client import DeepSeekClient
from .tool_registry import ToolRegistry


SYSTEM_PROMPT = """你是一个专业的材料科学智能助手，专门帮助用户进行材料设计与计算。

## 你的能力

1. **材料查询**: 从 Materials Project 数据库搜索材料，查询带隙、结构等信息
2. **结构建模**: 根据晶格参数和原子坐标构建自定义晶体结构
3. **ML 预测**: 使用机器学习模型预测材料的带隙
4. **VASP 计算**: 管理远程服务器的 VASP 计算任务（结构优化、自洽、能带等）
5. **项目管理**: 跟踪材料研发项目的进度

## 响应规则

1. 始终使用中文回复（除非用户使用英文）
2. 当需要调用工具时，LLM会自动选择合适的工具并提取参数
3. 返回结果后，适当解释结果含义
4. 如果工具返回错误，指出可能的原因并建议解决方案
5. 对于复杂任务，按步骤进行

## 重要提示

- 用户可能不熟悉材料科学术语，解释时要注意易懂
- VASP 计算需要时间，提交任务后提醒用户等待
- 如果需要用户确认某一步骤，先询问用户
"""


class MaterialAgent:
    def __init__(
        self,
        llm_client: DeepSeekClient,
        tool_registry: ToolRegistry,
        mcp_skill: Optional[Any] = None,
    ):
        self.llm = llm_client
        self.registry = tool_registry
        self.mcp_skill = mcp_skill
        self.messages = []
        self._init_system_message()

    def _init_system_message(self):
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    def reset(self):
        self._init_system_message()

    def _execute_tool(self, tool_name: str, arguments: dict) -> Any:
        if not self.mcp_skill:
            return {"error": "MCP Skill 未连接，无法执行工具"}

        try:
            func = getattr(self.mcp_skill, tool_name, None)
            if not func:
                available_tools = [
                    "get_material_structure",
                    "get_band_gap",
                    "search_materials",
                    "get_material_all_infomation_by_id",
                    "predict_band_gap",
                    "build_structure",
                ]
                return {
                    "error": f"工具 {tool_name} 不存在。正确工具名包括: {', '.join(available_tools)}"
                }

            clean_args = {}
            for k, v in arguments.items():
                if v is not None and v != "":
                    clean_args[k] = v

            result = func(**clean_args)
            return result
        except Exception as e:
            import traceback

            error_msg = str(e)
            # 如果是工具调用错误，给出更清晰的提示
            if (
                "does not exist" in error_msg.lower()
                or "not found" in error_msg.lower()
            ):
                return {"error": f"工具调用失败：{error_msg}"}
            return {"error": f"执行工具时出错: {error_msg}"}

    def _format_result(self, tool_name: str, result: Any) -> str:
        if isinstance(result, dict):
            if "error" in result:
                return f"❌ 错误: {result.get('error', 'Unknown error')}\n\n请检查参数是否正确，或稍后重试。"

            if tool_name == "search_materials":
                if isinstance(result, list) and result:
                    lines = [f"找到 {len(result)} 种材料:\n"]
                    for i, r in enumerate(result[:10], 1):
                        formula = r.get("formula_pretty", "Unknown")
                        material_id = r.get("material_id", "N/A")
                        band_gap = r.get("band_gap", "N/A")
                        symmetry = r.get("symmetry", "N/A")
                        lines.append(f"{i}. **{formula}** ({material_id})")
                        lines.append(f"   带隙: {band_gap} eV | 对称性: {symmetry}")
                    if len(result) > 10:
                        lines.append(f"\n... 还有 {len(result) - 10} 种材料")
                    lines.append(
                        "\n您可以告诉我感兴趣的材料，我可以获取其详细信息或进行进一步计算。"
                    )
                    return "\n".join(lines)
                return "未找到符合条件的材料"

            elif tool_name == "get_band_gap":
                formula = result.get("formula", "Unknown")
                material_id = result.get("material_id", "N/A")
                band_gap = result.get("band_gap")

                if band_gap is None:
                    interpretation = "（数据不可用）"
                elif band_gap == 0:
                    interpretation = "这是金属材料，没有带隙"
                elif band_gap < 1:
                    interpretation = "窄带隙半导体"
                elif band_gap < 3:
                    interpretation = "中等带隙半导体"
                else:
                    interpretation = "宽带隙半导体"

                return f"""材料信息:
- 化学式: **{formula}**
- 材料ID: {material_id}
- 带隙: **{band_gap} eV** ({interpretation})"""

            elif tool_name == "get_material_structure":
                sdict = result.get("structure_dict", {})
                lattice = sdict.get("lattice_parameters", {})

                info = f"""晶体结构信息:
- 化学式: **{sdict.get("formula", "Unknown")}**
- 空间群: {sdict.get("space_group_symbol", "N/A")} (No. {sdict.get("space_group_number", "N/A")})
- 晶格参数:
  - a = {lattice.get("a", "N/A")} Å
  - b = {lattice.get("b", "N/A")} Å
  - c = {lattice.get("c", "N/A")} Å
  - α = {lattice.get("alpha", "N/A")}°
  - β = {lattice.get("beta", "N/A")}°
  - γ = {lattice.get("gamma", "N/A")}°
- 原子数: {sdict.get("number_of_sites", "N/A")}"""

                if "image_url" in result:
                    info += f"\n\n![结构图]({result['image_url']})"

                if "message" in result:
                    msg_list = result["message"]
                    for m in msg_list:
                        if isinstance(m, dict) and "3d_image_url" in m:
                            info += f"\n\n[查看3D结构]({m['3d_image_url']})"
                        elif isinstance(m, str) and "3d" in m.lower():
                            for item in msg_list:
                                if isinstance(item, str) and item.startswith("http"):
                                    info += f"\n\n[查看3D结构]({item})"
                                    break

                return info

            elif tool_name == "predict_band_gap":
                pred = result.get("predicted_band_gap", result.get("result"))
                formula = result.get("formula", "该材料")
                if isinstance(pred, dict):
                    return f"材料 **{formula}** 的预测带隙为 **{pred.get('predicted_gap', 'N/A')} eV**"
                return f"材料 **{formula}** 的预测带隙为 **{pred} eV**"

            elif tool_name in [
                "submit_opt_mission",
                "submit_scf_mission",
                "submit_band_mission",
            ]:
                task_type = {
                    "submit_opt_mission": "结构优化",
                    "submit_scf_mission": "自洽计算",
                    "submit_band_mission": "能带计算",
                }.get(tool_name, tool_name)

                msg = result.get("message", "")
                task_dir = result.get("task_directory", "")

                return f"""✅ **{task_type}任务已提交！**
- 任务目录: {task_dir or msg}
- 状态: 已提交

您可以:
- 使用「查看任务队列」了解计算进度
- 计算完成后使用「提取结果」获取输出"""

            elif tool_name == "check_squeue":
                sq = result.get("squeue", "")
                if sq and sq.strip():
                    return f"任务队列状态:\n{sq}"
                return "当前没有运行中的任务 ✓"

            elif tool_name == "list_task_directories":
                dirs = result.get("task_directories", [])
                if dirs:
                    return "任务目录列表:\n" + "\n".join([f"- {d}" for d in dirs])
                return "暂无任务目录"

            elif tool_name == "list_all_projects":
                if isinstance(result, list):
                    if result:
                        return "当前项目:\n" + "\n".join([f"- {p}" for p in result])
                    return "暂无项目"
                return str(result)

            elif tool_name == "get_project_workflow":
                proj = result.get("project", "N/A")
                workflow = result.get("workflow", {})

                info = f"项目: **{proj}**\n\n进度:"
                if "description" in workflow:
                    info += f"\n{workflow['description']}"

                for step, data in workflow.items():
                    if step != "description" and isinstance(data, dict):
                        status = data.get("status", "N/A")
                        time = data.get("time", "")
                        status_icon = {
                            "Pending": "⏳",
                            "Running": "🔄",
                            "Completed": "✅",
                            "Failed": "❌",
                        }.get(status, "○")
                        info += f"\n{status_icon} {step}: {status} {time}"

                return info

            else:
                return json.dumps(result, indent=2, ensure_ascii=False)

        elif isinstance(result, list):
            if not result:
                return "未找到结果"
            return f"找到 {len(result)} 个结果"

        else:
            return str(result)

    def process(self, user_message: str) -> str:
        self.messages.append({"role": "user", "content": user_message})

        functions = self.registry.get_openai_functions()

        response = self.llm.chat_with_functions(
            messages=self.messages, functions=functions, function_call="auto"
        )

        has_tool_call = response.get("tool_calls", [])

        if has_tool_call:
            tool_call = has_tool_call[0]
            tool_name = tool_call["function"]["name"]
            arguments_json = tool_call["function"]["arguments"]

            try:
                arguments = json.loads(arguments_json)
            except json.JSONDecodeError:
                arguments = {}

            result = self._execute_tool(tool_name, arguments)
            formatted_result = self._format_result(tool_name, result)

            self.messages.append(
                {
                    "role": "assistant",
                    "tool_calls": [
                        {
                            "id": tool_call["id"],
                            "type": "function",
                            "function": {
                                "name": tool_name,
                                "arguments": arguments_json,
                            },
                        }
                    ],
                }
            )
            self.messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": json.dumps(result, ensure_ascii=False),
                }
            )

            final_response = self.llm.chat_basic(
                messages=self.messages, temperature=0.7
            )

            self.messages.append({"role": "assistant", "content": final_response})
            return final_response

        else:
            content = response.get("content", "")
            self.messages.append({"role": "assistant", "content": content})
            return content

    def chat(self, user_message: str) -> str:
        return self.process(user_message)

    def get_conversation_history(self) -> list:
        return self.messages.copy()


def create_agent(mcp_skill=None, api_key: str = None) -> MaterialAgent:
    llm_client = DeepSeekClient(api_key)
    from .tool_registry import create_tool_registry

    registry = create_tool_registry(mcp_skill)
    return MaterialAgent(llm_client, registry, mcp_skill)

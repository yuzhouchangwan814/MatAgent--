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


RESPONSE_TEMPLATES = {
    "no_results": "未找到符合条件的材料",
    "error": "抱歉，处理您的请求时遇到错误: {error}",
    "tool_executed": "已执行工具: {tool_name}",
}


def format_search_results(results: list) -> str:
    if not results:
        return RESPONSE_TEMPLATES["no_results"]

    lines = [f"找到 {len(results)} 种材料:\n"]
    for i, r in enumerate(results, 1):
        formula = r.get("formula_pretty", "Unknown")
        material_id = r.get("material_id", "N/A")
        band_gap = r.get("band_gap", "N/A")
        lines.append(f"{i}. **{formula}** ({material_id}) - 带隙: {band_gap} eV")

    return "\n".join(lines)


def interpret_band_gap(band_gap: float) -> str:
    if band_gap is None or band_gap == "N/A":
        return "（数据不可用）"
    elif band_gap == 0:
        return "金属材料，无带隙"
    elif band_gap < 1:
        return "窄带隙半导体"
    elif band_gap < 3:
        return "中等带隙半导体"
    else:
        return "宽带隙半导体"

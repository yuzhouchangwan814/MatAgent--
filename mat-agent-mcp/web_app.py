import streamlit as st
import os
import sys
import asyncio

st.set_page_config(
    page_title="MatAgent 智能材料设计平台",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

if "messages" not in st.session_state:
    st.session_state.messages = []

if "agent" not in st.session_state:
    st.session_state.agent = None

if "mcp_skill" not in st.session_state:
    st.session_state.mcp_skill = None

if "mcp_connected" not in st.session_state:
    st.session_state.mcp_connected = False

if "selected_material" not in st.session_state:
    st.session_state.selected_material = None

st.markdown(
    """
<style>
    .main-header {
        font-size: 28px;
        font-weight: bold;
        color: #1E88E5;
        text-align: center;
        padding: 20px;
        background: linear-gradient(90deg, #1E88E5, #00ACC1);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .sidebar-title {
        font-size: 20px;
        font-weight: bold;
        color: #1E88E5;
    }
    .stButton>button {
        width: 100%;
    }
    .function-card {
        padding: 15px;
        border-radius: 10px;
        background-color: #f0f2f6;
        margin-bottom: 10px;
    }
    .result-card {
        padding: 20px;
        border-radius: 10px;
        background-color: #e8f5e9;
        margin: 10px 0;
    }
    .error-card {
        padding: 20px;
        border-radius: 10px;
        background-color: #ffebee;
        margin: 10px 0;
    }
</style>
""",
    unsafe_allow_html=True,
)


def init_mcp_connection():
    try:
        from mcp_skill import MCPAgentSkill

        mcp_url = os.getenv("MCP_URL", "http://127.0.0.1:8000/sse")
        skill = MCPAgentSkill(mcp_url=mcp_url)

        from agent import create_agent

        agent = create_agent(mcp_skill=skill)

        st.session_state.mcp_skill = skill
        st.session_state.agent = agent
        st.session_state.mcp_connected = True
        return True
    except Exception as e:
        st.error(f"MCP 连接失败: {e}")
        st.session_state.mcp_connected = False
        return False


def sidebar_functions():
    with st.sidebar:
        st.markdown('<p class="sidebar-title">📁 功能面板</p>', unsafe_allow_html=True)

        function_tabs = st.radio(
            "选择功能",
            [
                "💬 AI对话",
                "🔍 材料查询",
                "📊 结构建模",
                "🧪 ML预测",
                "💻 VASP任务",
                "📁 项目管理",
                "📂 文件管理",
            ],
            label_visibility="collapsed",
        )

        st.divider()

        if not st.session_state.mcp_connected:
            if st.button("🔗 连接 MCP 服务", type="primary"):
                with st.spinner("正在连接..."):
                    init_mcp_connection()
        else:
            st.success("✅ MCP 已连接")

            if st.button("🔄 重置对话"):
                if st.session_state.agent:
                    st.session_state.agent.reset()
                st.session_state.messages = []
                st.rerun()

        st.divider()

        st.markdown("**💡 使用提示**")
        st.info("""
        - 使用 AI 对话：用自然语言描述需求
        - 手动操作：选择对应功能面板
        - 支持材料搜索、结构建模、带隙预测、VASP任务管理
        """)

        return function_tabs


def chat_interface():
    st.markdown('<p class="main-header">💬 AI 对话</p>', unsafe_allow_html=True)

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("描述您的材料科学需求..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("AI 正在思考..."):
                if st.session_state.agent:
                    response = st.session_state.agent.chat(prompt)
                    st.markdown(response)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": response}
                    )
                else:
                    st.error("请先连接 MCP 服务")
                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": "请先在左侧点击「连接 MCP 服务」",
                        }
                    )


def material_search_panel():
    st.markdown("### 🔍 材料查询")

    col1, col2 = st.columns(2)

    with col1:
        elements_input = st.text_input("包含元素 (用逗号分隔)", placeholder="Li, Co, O")
        exclude_elements_input = st.text_input(
            "排除元素 (用逗号分隔)", placeholder="H, He"
        )
        chemsys = st.text_input("化学系统", placeholder="Li-Fe-O")

    with col2:
        band_gap_min = st.number_input("带隙最小值 (eV)", min_value=0.0, value=0.0)
        band_gap_max = st.number_input("带隙最大值 (eV)", min_value=0.0, value=5.0)
        chunk_size = st.slider("返回结果数量", 1, 100, 25)

    if st.button("🔍 搜索材料", type="primary"):
        if not st.session_state.mcp_connected:
            st.error("请先连接 MCP 服务")
            return

        with st.spinner("搜索中..."):
            try:
                elements = [e.strip() for e in elements_input.split(",") if e.strip()]
                exclude_elements = [
                    e.strip() for e in exclude_elements_input.split(",") if e.strip()
                ]

                result = st.session_state.mcp_skill.search_materials(
                    elements=elements if elements else None,
                    exclude_elements=exclude_elements if exclude_elements else None,
                    chemsys=chemsys if chemsys else None,
                    band_gap=(band_gap_min, band_gap_max)
                    if band_gap_min > 0 or band_gap_max > 0
                    else None,
                    chunk_size=chunk_size,
                )

                st.session_state.search_results = result

            except Exception as e:
                st.error(f"搜索失败: {e}")

    if "search_results" in st.session_state:
        results = st.session_state.search_results
        if isinstance(results, list) and results:
            st.markdown(f"**找到 {len(results)} 个材料:**")
            for r in results:
                with st.expander(
                    f"{r.get('formula_pretty', 'Unknown')} ({r.get('material_id', 'N/A')})"
                ):
                    col1, col2 = st.columns(2)
                    col1.markdown(f"**带隙:** {r.get('band_gap', 'N/A')} eV")
                    col1.markdown(f"**对称性:** {r.get('symmetry', 'N/A')}")
                    if col2.button("📊 查看结构", key=f"view_{r.get('material_id')}"):
                        st.session_state.selected_material = r.get("material_id")

        # 处理查看结构请求
        if (
            "selected_material" in st.session_state
            and st.session_state.selected_material
        ):
            st.divider()
            st.markdown(f"**查看材料: {st.session_state.selected_material}**")
            with st.spinner("获取结构信息..."):
                try:
                    structure_result = (
                        st.session_state.mcp_skill.get_material_structure(
                            material_id=st.session_state.selected_material,
                            get_plot=True,
                            get_sites=True,
                        )
                    )
                    st.write("调试信息:", structure_result)
                    if isinstance(structure_result, dict):
                        if "error" in structure_result:
                            st.error(
                                structure_result.get(
                                    "message", structure_result.get("error")
                                )
                            )
                        else:
                            # 显示结构信息
                            sdict = structure_result.get("structure_dict", {})
                            lattice = sdict.get("lattice_parameters", {})
                            st.markdown(f"""
                            **晶体结构信息:**
                            - 化学式: {sdict.get("formula", "N/A")}
                            - 空间群: {sdict.get("space_group_symbol", "N/A")} (No. {sdict.get("space_group_number", "N/A")})
                            - 晶格参数: a={lattice.get("a", "N/A")} Å, b={lattice.get("b", "N/A")} Å, c={lattice.get("c", "N/A")} Å
                            """)
                            # 显示图片
                            if "image_url" in structure_result:
                                st.image(
                                    structure_result["image_url"], caption="晶体结构图"
                                )
                            if "message" in structure_result:
                                for msg in structure_result["message"]:
                                    if isinstance(msg, dict) and "3d_image_url" in msg:
                                        st.markdown(
                                            f"[查看 3D 结构]({msg['3d_image_url']})"
                                        )
                    elif isinstance(structure_result, str):
                        st.text(structure_result)
                except Exception as e:
                    import traceback

                    st.error(f"获取结构失败: {e}")
                    with st.expander("查看详细错误"):
                        st.code(traceback.format_exc())

            # 添加清除选择按钮
            if st.button("❌ 清除选择"):
                st.session_state.selected_material = None
                st.rerun()
        elif isinstance(results, dict) and "error" in results:
            st.error(results.get("message", results.get("error")))


def structure_builder_panel():
    st.markdown("### 📊 结构建模")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**晶格参数**")
        a = st.number_input("a (Å)", value=5.0, step=0.1)
        b = st.number_input("b (Å)", value=5.0, step=0.1)
        c = st.number_input("c (Å)", value=5.0, step=0.1)
        alpha = st.number_input("α (°)", value=90.0, step=0.1)
        beta = st.number_input("β (°)", value=90.0, step=0.1)
        gamma = st.number_input("γ (°)", value=90.0, step=0.1)

    with col2:
        st.markdown("**原子信息**")
        elements_input = st.text_input("元素列表 (逗号分隔)", placeholder="Si, O, O")
        coords_input = st.text_area(
            "分数坐标 (每行一个坐标，用逗号分隔)",
            placeholder="0, 0, 0\n0.25, 0.25, 0.25\n0.5, 0.5, 0.5",
            height=120,
        )

    col3, col4 = st.columns(2)
    with col3:
        scaling = st.selectbox("超胞", ["1×1×1", "2×1×1", "1×2×1", "1×1×2", "2×2×2"])
    with col4:
        save_cif = st.checkbox("保存 CIF 文件")
        add_db = st.checkbox("添加到数据库")

    if st.button("🏗️ 构建结构", type="primary"):
        if not st.session_state.mcp_connected:
            st.error("请先连接 MCP 服务")
            return

        try:
            elements = [e.strip() for e in elements_input.split(",") if e.strip()]
            coords = []
            for line in coords_input.strip().split("\n"):
                if line.strip():
                    coords.append([float(x.strip()) for x in line.split(",")])

            scaling_matrix = 1
            if scaling == "2×1×1":
                scaling_matrix = [2, 1, 1]
            elif scaling == "1×2×1":
                scaling_matrix = [1, 2, 1]
            elif scaling == "1×1×2":
                scaling_matrix = [1, 1, 2]
            elif scaling == "2×2×2":
                scaling_matrix = 2

            db_path = "materials.db" if add_db else ""

            # 只在需要时传递参数
            kwargs = {
                "a": a,
                "b": b,
                "c": c,
                "alpha": alpha,
                "beta": beta,
                "gamma": gamma,
                "elements": elements,
                "frac_coord": coords,
                "scaling_matrix": scaling_matrix,
                "save_to_cif": save_cif,
            }
            if db_path:
                kwargs["add_to_database"] = db_path

            result = st.session_state.mcp_skill.build_structure(**kwargs)

            if isinstance(result, dict):
                if "error" in result:
                    st.error(f"构建失败: {result.get('message', result.get('error'))}")
                else:
                    st.success("结构构建成功!")
                    if "image" in result:
                        st.image(result["image"], caption="晶体结构")
                    if "3d_image_url" in result:
                        st.markdown(f"[查看 3D 结构]({result['3d_image_url']})")
            elif isinstance(result, str):
                st.success("结构构建成功!")
                st.text(result)
            else:
                st.success("结构构建成功!")
                st.json(result)
        except Exception as e:
            import traceback

            st.error(f"构建失败: {e}")
            with st.expander("查看详细错误"):
                st.code(traceback.format_exc())

        except Exception as e:
            st.error(f"构建失败: {e}")


def ml_prediction_panel():
    st.markdown("### 🧪 ML 预测")

    tab1, tab2 = st.tabs(["📈 带隙预测", "🔮 更多预测"])

    with tab1:
        formula_input = st.text_input("输入化学式", placeholder="LiFePO4")

        if st.button("🔮 预测带隙", type="primary"):
            if not st.session_state.mcp_connected:
                st.error("请先连接 MCP 服务")
                return

            if not formula_input:
                st.warning("请输入化学式")
                return

            with st.spinner("预测中..."):
                try:
                    result = st.session_state.mcp_skill.predict_band_gap(formula_input)

                    # 调试：打印原始结果
                    st.write(f"调试信息: {result}")

                    # 处理不同格式的结果
                    if isinstance(result, dict):
                        if "error" in result:
                            st.error(result.get("message", result.get("error")))
                        else:
                            # 处理 predicted_band_gap 可能是列表的情况
                            pred_gap = result.get(
                                "predicted_band_gap", result.get("result")
                            )
                            if isinstance(pred_gap, list):
                                pred_gap = pred_gap[0] if pred_gap else "N/A"
                            st.markdown(
                                f"""
                            <div class="result-card">
                                <h3>预测结果</h3>
                                <p>化学式: <b>{formula_input}</b></p>
                                <p>预测带隙: <b style="font-size: 24px; color: #1E88E5;">{pred_gap} eV</b></p>
                            </div>
                            """,
                                unsafe_allow_html=True,
                            )
                    elif isinstance(result, list):
                        # 处理列表格式的结果
                        pred_gap = result[0] if result else "N/A"
                        st.markdown(
                            f"""
                        <div class="result-card">
                            <h3>预测结果</h3>
                            <p>化学式: <b>{formula_input}</b></p>
                            <p>预测带隙: <b style="font-size: 24px; color: #1E88E5;">{pred_gap} eV</b></p>
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(f"**预测带隙: {result} eV**")

                except Exception as e:
                    import traceback

                    st.error(f"预测失败: {e}")
                    with st.expander("查看详细错误"):
                        st.code(traceback.format_exc())

    with tab2:
        st.info("更多 ML 预测功能开发中...")


def vasp_task_panel():
    st.markdown("### 💻 VASP 任务")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**📋 任务管理**")
        if st.button("🔄 刷新任务列表"):
            pass

        if st.button("📊 查看任务队列"):
            if st.session_state.mcp_connected:
                try:
                    result = st.session_state.mcp_skill.check_squeue()
                    if isinstance(result, dict):
                        if "error" in result:
                            st.error(result.get("message"))
                        else:
                            st.text(result.get("squeue", "无运行任务"))
                except Exception as e:
                    st.error(f"获取队列失败: {e}")
            else:
                st.error("请先连接 MCP 服务")

    with col2:
        st.markdown("**📤 提交任务**")
        task_type = st.selectbox("任务类型", ["结构优化", "自洽计算", "能带计算"])
        task_dir = st.text_input("任务目录", placeholder="/path/to/task")

        if st.button("📤 提交任务", type="primary"):
            if not st.session_state.mcp_connected:
                st.error("请先连接 MCP 服务")
                return

            if not task_dir:
                st.warning("请输入任务目录")
                return

            with st.spinner("提交中..."):
                try:
                    if task_type == "结构优化":
                        result = st.session_state.mcp_skill.submit_opt_mission(task_dir)
                    elif task_type == "自洽计算":
                        result = st.session_state.mcp_skill.submit_scf_mission(task_dir)
                    else:
                        result = st.session_state.mcp_skill.submit_band_mission(
                            task_dir
                        )

                    if isinstance(result, dict):
                        if "error" in result:
                            st.error(result.get("message"))
                        else:
                            st.success(f"任务提交成功!")
                            st.json(result)
                except Exception as e:
                    st.error(f"提交失败: {e}")

    st.divider()
    st.markdown("**📁 历史任务目录**")

    if st.button("📂 获取任务目录列表"):
        if st.session_state.mcp_connected:
            try:
                result = st.session_state.mcp_skill.list_task_directories()
                if isinstance(result, dict):
                    if "error" not in result:
                        dirs = result.get("task_directories", [])
                        if dirs:
                            for d in dirs:
                                st.text(d)
                        else:
                            st.info("暂无任务目录")
            except Exception as e:
                st.error(f"获取失败: {e}")


def project_management_panel():
    st.markdown("### 📁 项目管理")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**📋 项目列表**")
        if st.button("📜 查看所有项目"):
            if st.session_state.mcp_connected:
                try:
                    result = st.session_state.mcp_skill.list_all_projects()
                    if isinstance(result, list):
                        if result:
                            for p in result:
                                st.text(f"- {p}")
                        else:
                            st.info("暂无项目")
                    else:
                        st.text(str(result))
                except Exception as e:
                    st.error(f"获取失败: {e}")
            else:
                st.error("请先连接 MCP 服务")

    with col2:
        st.markdown("**➕ 新建项目**")
        new_project_name = st.text_input("项目名称")
        new_description = st.text_area("项目描述")

        if st.button("✅ 创建项目", type="primary"):
            if not st.session_state.mcp_connected:
                st.error("请先连接 MCP 服务")
                return

            if not new_project_name:
                st.warning("请输入项目名称")
                return

            try:
                result = st.session_state.mcp_skill.set_task_progress(
                    project_name=new_project_name,
                    description=new_description,
                    step_name="Init",
                    status="Pending",
                )
                st.success(f"项目创建成功!")
                st.text(result)
            except Exception as e:
                st.error(f"创建失败: {e}")

    st.divider()

    st.markdown("**🔧 项目进度**")
    view_project = st.text_input("查看项目进度")

    if st.button("📊 查看进度"):
        if st.session_state.mcp_connected and view_project:
            try:
                result = st.session_state.mcp_skill.get_project_workflow(view_project)
                if isinstance(result, dict):
                    if "error" in result:
                        st.error(result.get("error"))
                    else:
                        st.json(result)
            except Exception as e:
                st.error(f"获取失败: {e}")


def file_management_panel():
    st.markdown("### 📂 文件管理")

    file_path = st.text_input("文件路径", placeholder="/path/to/file")

    if st.button("📖 读取文件"):
        if not st.session_state.mcp_connected:
            st.error("请先连接 MCP 服务")
            return

        if not file_path:
            st.warning("请输入文件路径")
            return

        try:
            result = st.session_state.mcp_skill.read_file(file_path)
            if isinstance(result, dict):
                if result.get("success"):
                    st.success("文件读取成功")
                    st.text_area(
                        "文件内容", value=result.get("content", ""), height=400
                    )
                else:
                    st.error(result.get("error", "读取失败"))
        except Exception as e:
            st.error(f"读取失败: {e}")


def main():
    st.title("🔬 MatAgent 智能材料设计平台")

    function_tabs = sidebar_functions()

    if function_tabs == "💬 AI对话":
        chat_interface()
    elif function_tabs == "🔍 材料查询":
        material_search_panel()
    elif function_tabs == "📊 结构建模":
        structure_builder_panel()
    elif function_tabs == "🧪 ML预测":
        ml_prediction_panel()
    elif function_tabs == "💻 VASP任务":
        vasp_task_panel()
    elif function_tabs == "📁 项目管理":
        project_management_panel()
    elif function_tabs == "📂 文件管理":
        file_management_panel()


if __name__ == "__main__":
    main()

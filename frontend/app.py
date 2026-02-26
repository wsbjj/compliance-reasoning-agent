"""
Compliance Reasoning Agent — Streamlit 前端看板

启动命令:
    streamlit run frontend/app.py --server.port 8501
"""
import streamlit as st

# ---- 页面配置 ----
st.set_page_config(
    page_title="合规推理智能体",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---- 自定义样式 ----
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(120deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #6b7280;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        border-radius: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---- 侧边栏 ----
def render_sidebar():
    """渲染侧边栏"""
    with st.sidebar:
        st.image(
            "https://img.icons8.com/color/96/shield--v1.png",
            width=60,
        )
        st.title("🛡️ 合规推理智能体")
        st.markdown("---")

        # API 配置状态
        st.subheader("⚙️ 系统状态")

        api_base = st.text_input(
            "FastAPI 后端地址",
            value="http://localhost:8000",
            key="api_base",
        )

        # 连接测试
        if st.button("🔗 测试连接"):
            try:
                import httpx

                with httpx.Client(timeout=5.0) as client:
                    resp = client.get(f"{api_base}/health")
                    if resp.status_code == 200:
                        st.success("✅ 后端连接正常")
                    else:
                        st.error(f"❌ 连接异常: {resp.status_code}")
            except Exception as e:
                st.error(f"❌ 无法连接: {e}")

        st.markdown("---")
        st.markdown(
            """
            **功能模块:**
            - 📋 专利/商标排查
            - 📈 动态趋势看板
            - 🔍 窗口期预警简报
            """
        )

        st.markdown("---")
        st.caption("v0.1.0 | Powered by LangGraph + MCP")

    return api_base


# ---- 主页面 ----
def main():
    api_base = render_sidebar()

    # 标题
    st.markdown('<div class="main-header">合规推理智能体看板</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">专利排查 · 趋势分析 · 窗口期预警 — 一站式合规风控平台</div>',
        unsafe_allow_html=True,
    )

    # ---- 分析输入区 ----
    st.markdown("### 🚀 启动分析")

    col1, col2 = st.columns([2, 1])
    with col1:
        query = st.text_input(
            "产品核心关键词",
            placeholder="例如: Smart Ring, Wireless Earbuds, AI Camera",
            help="输入你想分析的产品或类目关键词",
        )
    with col2:
        extra_context = st.text_area(
            "额外上下文 (可选)",
            placeholder="例如: 近期 AI API 成本下降 80%，硬件成本持续降低...",
            height=68,
        )

    if st.button("🔍 开始合规分析", type="primary", use_container_width=True):
        if not query:
            st.warning("请输入产品关键词")
            return

        with st.spinner("🤖 智能体正在工作中..."):
            try:
                import httpx

                with httpx.Client(timeout=300.0) as client:
                    resp = client.post(
                        f"{api_base}/api/analysis/run",
                        json={
                            "query": query,
                            "extra_context": extra_context,
                            "user_id": "streamlit_user",
                        },
                    )
                    resp.raise_for_status()
                    result = resp.json()

                st.session_state["latest_result"] = result
                st.success("✅ 分析完成!")

            except Exception as e:
                st.error(f"❌ 分析失败: {e}")
                return

    # ---- 结果展示 ----
    if "latest_result" in st.session_state:
        result = st.session_state["latest_result"]

        # 指标卡片
        st.markdown("---")
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("📋 专利数量", result.get("patent_count", 0))
        with m2:
            st.metric("📈 趋势关键词", result.get("trend_keywords", 0))
        with m3:
            st.metric("🔄 迭代次数", result.get("iterations", 0))
        with m4:
            st.metric("✅ 状态", result.get("status", "unknown"))

        # Tab 页
        tab1, tab2, tab3, tab4 = st.tabs(
            ["📄 完整报告", "📋 专利分析", "📈 趋势分析", "📝 执行计划"]
        )

        with tab1:
            report = result.get("final_report", "暂无报告")
            st.markdown(report)

        with tab2:
            patent_analysis = result.get("patent_analysis", "暂无专利分析")
            st.markdown(patent_analysis)

        with tab3:
            trend_analysis = result.get("trend_analysis", "暂无趋势分析")
            st.markdown(trend_analysis)

            # 尝试展示趋势图
            _render_trend_chart(result)

        with tab4:
            plan = result.get("plan", "暂无执行计划")
            st.markdown(plan)

    # 历史记录
    st.markdown("---")
    st.markdown("### 📚 历史分析记录")
    try:
        import httpx

        with httpx.Client(timeout=10.0) as client:
            resp = client.get(f"{api_base}/api/analysis/")
            if resp.status_code == 200:
                history = resp.json()
                if history:
                    import pandas as pd

                    df = pd.DataFrame(history)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("暂无历史记录")
            else:
                st.info("无法获取历史记录")
    except Exception:
        st.info("请先启动后端服务 (uvicorn app.main:app)")


def _render_trend_chart(result: dict):
    """渲染趋势折线图"""
    try:
        import plotly.graph_objects as go
        import pandas as pd

        trend_analysis = result.get("trend_analysis", "")

        # 这里展示一个示例图表
        # 实际使用时应该从后端获取原始 trend data
        fig = go.Figure()

        fig.update_layout(
            title="关键词搜索趋势",
            xaxis_title="时间",
            yaxis_title="搜索指数",
            template="plotly_dark",
            height=400,
        )

        st.plotly_chart(fig, use_container_width=True)

    except ImportError:
        st.info("请安装 plotly: pip install plotly")


if __name__ == "__main__":
    main()

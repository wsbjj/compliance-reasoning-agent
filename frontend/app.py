"""
合规优化智能体 — Streamlit 主页看板

启动命令:
    streamlit run frontend/app.py --server.port 8501
"""
import sys
import os
import streamlit as st

# 确保 frontend 目录可以导入 styles
sys.path.insert(0, os.path.dirname(__file__))
from styles import inject_global_styles, page_title, section_header

# ---- 页面配置 ----
st.set_page_config(
    page_title="合规优化智能体",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---- 注入全局样式 ----
inject_global_styles()


# ---- 侧边栏 ----
def render_sidebar() -> str:
    """渲染侧边栏，返回 API 地址。"""
    with st.sidebar:
        # 品牌 Logo 区
        st.markdown(
            """
            <div style="display:flex; align-items:center; gap:12px; padding:8px 0 20px;">
                <div style="
                    width:42px; height:42px;
                    background: linear-gradient(135deg, #1E40AF, #3B82F6);
                    border-radius:10px;
                    display:flex; align-items:center; justify-content:center;
                    font-size:22px;
                ">🛡️</div>
                <div>
                    <div style="font-family:'Fira Code',monospace; font-weight:700; font-size:0.95rem; color:#E2E8F0;">合规优化智能体</div>
                    <div style="font-size:0.72rem; color:#64748B; margin-top:1px;">AI-Powered Compliance</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<hr style="border-color:rgba(59,130,246,0.15); margin:0 0 16px;">', unsafe_allow_html=True)

        # 系统状态
        section_header("系统配置")
        api_base = st.text_input(
            "后端服务地址",
            value="http://localhost:8000",
            key="api_base",
            help="FastAPI 后端的访问地址",
        )

        if st.button("检测连接", use_container_width=True):
            try:
                import httpx
                with httpx.Client(timeout=5.0) as client:
                    resp = client.get(f"{api_base}/health")
                    if resp.status_code == 200:
                        st.success("✅ 后端连接正常")
                    else:
                        st.error(f"⚠️ 异常状态码: {resp.status_code}")
            except Exception as e:
                st.error(f"❌ 连接失败: {e}")

        st.markdown('<hr style="border-color:rgba(59,130,246,0.15); margin:16px 0;">', unsafe_allow_html=True)

        # 功能导航
        section_header("功能模块")
        st.markdown(
            """
            <div class="sidebar-nav-item">
                <span>📊</span><span>分析看板</span>
            </div>
            <a href="/patent_matrix" style="text-decoration:none;">
                <div class="sidebar-nav-item">
                    <span>📋</span><span>专利矩阵</span>
                </div>
            </a>
            <a href="/trend_dashboard" style="text-decoration:none;">
                <div class="sidebar-nav-item">
                    <span>📈</span><span>趋势仪表盘</span>
                </div>
            </a>
            <a href="/report_viewer" style="text-decoration:none;">
                <div class="sidebar-nav-item">
                    <span>🔍</span><span>报告查看器</span>
                </div>
            </a>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<hr style="border-color:rgba(59,130,246,0.15); margin:16px 0;">', unsafe_allow_html=True)
        st.markdown(
            '<div style="color:#64748B; font-size:0.72rem; text-align:center;">v0.1.0 &nbsp;·&nbsp; LangGraph + MCP</div>',
            unsafe_allow_html=True,
        )

    return api_base


# ---- 主页面 ----
def main():
    api_base = render_sidebar()

    # 页面标题
    page_title(
        "合规优化智能体看板",
        "专利排查 · 趋势分析 · 窗口期预警 — 一站式合规风控平台",
    )

    # ---- 分析输入区 ----
    section_header("启动分析")

    col1, col2 = st.columns([2, 1])
    with col1:
        query = st.text_input(
            "产品核心关键词",
            placeholder="例如：Smart Ring、Wireless Earbuds、AI Camera",
            help="输入你想进行合规分析的产品或赛道关键词",
        )
    with col2:
        extra_context = st.text_area(
            "额外背景信息（可选）",
            placeholder="例如：近期 AI API 成本下降 80%，硬件成本持续下行...",
            height=72,
        )

    if st.button("开始合规分析", type="primary", use_container_width=True):
        if not query:
            st.warning("请先输入产品关键词")
            return

        with st.spinner("🤖 智能体正在规划任务、搜索专利、分析趋势，请稍候..."):
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
                st.success(f"✅ 分析完成！共检索到 {result.get('patent_count', 0)} 篇专利")

            except Exception as e:
                st.error(f"❌ 分析失败: {e}")
                return

    # ---- 结果展示 ----
    if "latest_result" in st.session_state:
        result = st.session_state["latest_result"]

        # 指标卡片行
        st.markdown("<br>", unsafe_allow_html=True)
        section_header("分析概览")

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("专利数量", result.get("patent_count", 0), help="搜索到的相关专利总数")
        with m2:
            st.metric("趋势关键词", result.get("trend_keywords", 0), help="分析的市场趋势词数量")
        with m3:
            st.metric("审核迭代次数", result.get("iterations", 0), help="AI 自我审核的循环次数")
        with m4:
            status_map = {"success": "✅ 已完成", "error": "❌ 失败", "running": "⏳ 进行中"}
            raw_status = result.get("status", "unknown")
            st.metric("分析状态", status_map.get(raw_status, raw_status))

        # 内容 Tab
        st.markdown("<br>", unsafe_allow_html=True)
        tab1, tab2, tab3, tab4 = st.tabs(
            ["📄  完整报告", "📋  专利分析", "📈  趋势分析", "📝  执行计划"]
        )

        with tab1:
            report = result.get("final_report", "")
            if report:
                st.markdown(report)
            else:
                st.info("暂无报告，请先运行分析")

        with tab2:
            patent_analysis = result.get("patent_analysis", "")
            if patent_analysis:
                st.markdown(patent_analysis)
            else:
                st.info("暂无专利分析数据")

        with tab3:
            trend_analysis = result.get("trend_analysis", "")
            if trend_analysis:
                st.markdown(trend_analysis)
            _render_trend_chart(result)

        with tab4:
            plan = result.get("plan", "")
            if plan:
                st.markdown(plan)
            else:
                st.info("暂无执行计划")

    # ---- 历史记录 ----
    st.markdown("<br>", unsafe_allow_html=True)
    section_header("历史分析记录")

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
                    st.info("暂无历史记录，运行分析后将在此展示")
            else:
                st.info("无法获取历史记录")
    except Exception:
        st.info("💡 请先启动后端服务: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`")


def _render_trend_chart(result: dict):
    """渲染趋势折线图（占位）"""
    try:
        import plotly.graph_objects as go

        fig = go.Figure()
        fig.update_layout(
            title="关键词搜索趋势分析",
            xaxis_title="时间",
            yaxis_title="搜索指数",
            template="plotly_dark",
            height=380,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(15,23,42,0.8)",
            font=dict(family="Fira Sans", color="#94A3B8"),
            title_font=dict(family="Fira Code", color="#E2E8F0", size=14),
            margin=dict(t=48, b=32, l=32, r=16),
        )
        st.plotly_chart(fig, use_container_width=True)

    except ImportError:
        st.caption("安装 plotly 后可查看趋势图: `pip install plotly`")


if __name__ == "__main__":
    main()

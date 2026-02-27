import streamlit as st

def render_sidebar():
    """渲染全站统一的侧边栏导航"""
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

        # 系统配置
        st.markdown('<div class="section-title">系统配置</div>', unsafe_allow_html=True)
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

        # 功能模块导航 - 采用 st.page_link 进行无刷新跳转
        st.markdown('<div class="section-title">功能模块</div>', unsafe_allow_html=True)
        st.page_link("app.py", label="分析看板", icon="📊")
        st.page_link("pages/patent_matrix.py", label="专利矩阵", icon="📋")
        st.page_link("pages/trend_dashboard.py", label="趋势仪表盘", icon="📈")
        st.page_link("pages/report_viewer.py", label="报告查看器", icon="🔍")

        st.markdown('<hr style="border-color:rgba(59,130,246,0.15); margin:16px 0;">', unsafe_allow_html=True)
        st.markdown(
            '<div style="color:#64748B; font-size:0.72rem; text-align:center;">v0.1.0 &nbsp;·&nbsp; LangGraph + MCP</div>',
            unsafe_allow_html=True,
        )

    return api_base

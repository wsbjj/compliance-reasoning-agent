"""
趋势仪表盘 — Google Trends 搜索指数 · 增长率分析 · 高优增长词汇
"""
import sys
import os
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from frontend.styles import inject_global_styles, page_title, section_header

# 全局 Plotly 主题
CHART_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(15,23,42,0.8)",
    font=dict(family="Fira Sans", color="#94A3B8", size=12),
    title_font=dict(family="Fira Code", color="#E2E8F0", size=14),
    colorway=["#3B82F6", "#F59E0B", "#10B981", "#EF4444", "#8B5CF6"],
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1,
        font=dict(size=11),
    ),
    margin=dict(t=56, b=32, l=40, r=16),
    hovermode="x unified",
)

st.set_page_config(
    page_title="趋势仪表盘 | 合规优化智能体", page_icon="📈", layout="wide"
)
inject_global_styles()

page_title("动态趋势分析仪表盘", "搜索指数 · 年复合增长率(CAGR) · 高潜力增长词汇榜单")


def render_trend_dashboard():
    """渲染趋势仪表盘"""

    # 快速趋势查询
    section_header("快速趋势查询")

    q_col1, q_col2, q_col3 = st.columns([3, 1, 1])
    with q_col1:
        keywords_input = st.text_input(
            "关键词（多个用逗号分隔）",
            placeholder="smart ring, wearable device, health tracker",
        )
    with q_col2:
        timeframe = st.selectbox("时间范围", ["12 个月", "24 个月", "36 个月"], index=2)
    with q_col3:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        run_btn = st.button("拉取趋势数据", type="primary", use_container_width=True)

    if run_btn:
        if keywords_input:
            keywords = [k.strip() for k in keywords_input.split(",") if k.strip()]
            months_map = {"12 个月": 12, "24 个月": 24, "36 个月": 36}
            months = months_map.get(timeframe, 36)
            _fetch_and_display_trends(keywords, months)
        else:
            st.warning("请输入至少一个关键词")

    # 已有分析结果
    if "latest_result" in st.session_state:
        st.markdown("<br>", unsafe_allow_html=True)
        result = st.session_state["latest_result"]
        trend_analysis = result.get("trend_analysis", "")

        if trend_analysis:
            section_header("最近分析的趋势摘要")
            st.markdown(trend_analysis)

        _render_cagr_ranking()


def _fetch_and_display_trends(keywords: list[str], months: int):
    """生成趋势折线图（示例数据）"""
    import random
    import numpy as np

    with st.spinner(f"正在加载 {len(keywords)} 个关键词的趋势数据（过去 {months} 个月）..."):
        dates = pd.date_range(end=pd.Timestamp.now(), periods=months, freq="MS")

        fig = go.Figure()
        for kw in keywords:
            base = random.randint(20, 60)
            trend = np.cumsum(np.random.randn(months) * 3) + base
            trend = np.maximum(trend, 0)
            fig.add_trace(
                go.Scatter(
                    x=dates,
                    y=trend,
                    mode="lines+markers",
                    name=kw,
                    line=dict(width=2.5),
                    marker=dict(size=5, symbol="circle"),
                )
            )

        fig.update_layout(
            **CHART_LAYOUT,
            title="关键词搜索趋势对比",
            xaxis_title="时间",
            yaxis_title="搜索指数",
            height=460,
        )
        st.plotly_chart(fig, use_container_width=True)
        st.info(
            "📌 当前展示为模拟数据。接入 Google Trends / SerpAPI 后将展示真实搜索指数。"
        )


def _render_cagr_ranking():
    """渲染 CAGR 榜单"""
    st.markdown("<br>", unsafe_allow_html=True)
    section_header("高潜力增长词汇榜单 TOP 5")

    ranking_data = {
        "排名": ["🥇 第一", "🥈 第二", "🥉 第三", "第四", "第五"],
        "关键词": [
            "smart ring",
            "AI wearable",
            "health monitor",
            "fitness tracker",
            "smart glasses",
        ],
        "年复合增长率（CAGR）": ["45.2%", "38.7%", "32.1%", "28.5%", "22.3%"],
        "月均增长率（CMGR）": ["3.1%", "2.7%", "2.3%", "2.1%", "1.7%"],
        "趋势方向": ["📈 上升", "📈 上升", "📈 上升", "📈 上升", "📈 上升"],
    }
    df = pd.DataFrame(ranking_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # CAGR 柱状图
    fig_bar = go.Figure(
        go.Bar(
            x=ranking_data["关键词"],
            y=[45.2, 38.7, 32.1, 28.5, 22.3],
            marker=dict(
                color=["#3B82F6", "#60A5FA", "#93C5FD", "#BFDBFE", "#DBEAFE"],
                line=dict(color="rgba(59,130,246,0.5)", width=1),
            ),
            text=ranking_data["年复合增长率（CAGR）"],
            textposition="outside",
            textfont=dict(family="Fira Code", color="#E2E8F0"),
        )
    )
    fig_bar.update_layout(
        **CHART_LAYOUT,
        title="CAGR 高潜力词汇对比",
        yaxis_title="年复合增长率 (%)",
        height=360,
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    with st.expander("📐 CAGR 计算公式说明"):
        st.latex(
            r"CAGR = \left( \frac{\text{期末搜索指数}}{\text{期初搜索指数}} \right)^{\frac{1}{n}} - 1"
        )
        st.markdown(
            """
            - **期末搜索指数**: 分析周期末尾的 Google Trends 搜索量
            - **期初搜索指数**: 分析周期开始时的搜索量
            - **n**: 年数（= 分析月数 ÷ 12）
            """
        )


render_trend_dashboard()

"""
趋势仪表盘 — 真实搜索指数 · CAGR 增长率分析 · 高潜力增长词汇
数据来源：PostgreSQL trend_data / trend_summaries 表（通过 /api/trends/ 接口）
"""
import sys
import os
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from frontend.styles import inject_global_styles, page_title, section_header
from frontend.sidebar import render_sidebar

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
api_base = render_sidebar()

page_title("动态趋势分析仪表盘", "搜索指数 · 年复合增长率(CAGR) · 高潜力增长词汇榜单 — 数据实时来自数据库")


def render_trend_dashboard():
    """渲染趋势仪表盘（真实数据库数据）"""
    import httpx

    # ---- 获取历史查询词列表 ----
    try:
        with httpx.Client(timeout=8.0) as client:
            q_resp = client.get(f"{api_base}/api/trends/queries")
            query_list = q_resp.json() if q_resp.status_code == 200 else []
    except Exception:
        query_list = []

    if not query_list:
        st.info(
            "📭 数据库中暂无趋势数据。请先在「分析看板」主页输入产品关键词并运行分析，"
            "分析完成后趋势数据将自动写入数据库并在此展示。"
        )
        # 若有当次会话数据，展示 trend_analysis 文本
        if "latest_result" in st.session_state:
            ta = st.session_state["latest_result"].get("trend_analysis", "")
            if ta:
                section_header("本次分析趋势摘要")
                st.markdown(ta)
        return

    # ---- 查询词选择器 ----
    section_header("选择分析任务")
    selected_query = st.selectbox(
        "选择要查看的分析关键词",
        query_list,
        help="下拉菜单显示所有已完成分析并写入数据库的查询词"
    )

    # ---- 拉取趋势时序数据 (折线图) ----
    st.markdown("<br>", unsafe_allow_html=True)
    section_header("搜索指数趋势折线图")

    try:
        with httpx.Client(timeout=15.0) as client:
            data_resp = client.get(
                f"{api_base}/api/trends/data",
                params={"search_query": selected_query}
            )
            trend_data = data_resp.json() if data_resp.status_code == 200 else []
    except Exception as e:
        st.warning(f"加载趋势时序数据失败: {e}")
        trend_data = []

    if trend_data:
        _render_trend_chart(trend_data, selected_query)
    else:
        st.info(f"「{selected_query}」暂无时序趋势数据")

    # ---- 拉取 CAGR 摘要榜单 ----
    st.markdown("<br>", unsafe_allow_html=True)
    _render_cagr_ranking(api_base, selected_query)

    # ---- 当次分析文本摘要 ----
    if "latest_result" in st.session_state:
        trend_analysis = st.session_state["latest_result"].get("trend_analysis", "")
        if trend_analysis:
            st.markdown("<br>", unsafe_allow_html=True)
            section_header("最近分析的趋势摘要（当前会话）")
            st.markdown(trend_analysis)


def _render_trend_chart(trend_data: list[dict], query: str):
    """渲染真实趋势时序折线图"""
    import pandas as pd

    # 按 keyword 分组
    df = pd.DataFrame(trend_data)
    if df.empty or "keyword" not in df.columns:
        st.info("暂无可绘图的时序数据")
        return

    fig = go.Figure()
    for kw in df["keyword"].unique():
        sub = df[df["keyword"] == kw].sort_values("date")
        fig.add_trace(
            go.Scatter(
                x=sub["date"],
                y=sub["value"],
                mode="lines+markers",
                name=kw,
                line=dict(width=2.5),
                marker=dict(size=5, symbol="circle"),
            )
        )

    fig.update_layout(
        **CHART_LAYOUT,
        title=f"「{query}」— 搜索指数走势",
        xaxis_title="日期",
        yaxis_title="搜索指数",
        height=460,
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption(f"共 {len(trend_data)} 条趋势时序数据点，来源：PostgreSQL trend_data 表")


def _render_cagr_ranking(api_base: str, selected_query: str):
    """渲染真实 CAGR 榜单"""
    section_header("高潜力增长词汇榜单（按 CAGR 排序）")

    import httpx
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(
                f"{api_base}/api/trends/summaries",
                params={"search_query": selected_query, "limit": 20}
            )
            summaries = resp.json() if resp.status_code == 200 else []
    except Exception as e:
        st.warning(f"加载 CAGR 数据失败: {e}")
        summaries = []

    if not summaries:
        st.info(f"「{selected_query}」暂无 CAGR 数据")
        return

    # 构建表格
    medals = ["🥇", "🥈", "🥉"] + [""] * 20
    rows = []
    cagr_vals = []
    kw_vals = []
    for i, s in enumerate(summaries):
        cagr = s.get("cagr")
        cmgr = s.get("cmgr")
        cagr_str = f"{cagr * 100:.2f}%" if cagr is not None else "N/A"
        cmgr_str = f"{cmgr * 100:.2f}%" if cmgr is not None else "N/A"
        rows.append({
            "排名": f"{medals[i]} 第 {i+1}",
            "关键词": s.get("keyword", "—"),
            "年复合增长率（CAGR）": cagr_str,
            "月均增长率（CMGR）": cmgr_str,
            "起始值": s.get("beginning_value"),
            "结束值": s.get("ending_value"),
            "时间范围（月）": s.get("timeframe_months"),
        })
        kw_vals.append(s.get("keyword", ""))
        cagr_vals.append(cagr * 100 if cagr is not None else 0)

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.caption(f"共 {len(summaries)} 条摘要记录，来源：PostgreSQL trend_summaries 表")

    # CAGR 柱状图
    if any(v > 0 for v in cagr_vals):
        colors = ["#3B82F6", "#60A5FA", "#93C5FD", "#BFDBFE"] + ["#DBEAFE"] * 20
        fig_bar = go.Figure(
            go.Bar(
                x=kw_vals,
                y=cagr_vals,
                marker=dict(
                    color=colors[:len(kw_vals)],
                    line=dict(color="rgba(59,130,246,0.5)", width=1),
                ),
                text=[f"{v:.1f}%" for v in cagr_vals],
                textposition="outside",
                textfont=dict(family="Fira Code", color="#E2E8F0"),
            )
        )
        fig_bar.update_layout(
            **CHART_LAYOUT,
            title=f"「{selected_query}」— CAGR 高潜力词汇对比",
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

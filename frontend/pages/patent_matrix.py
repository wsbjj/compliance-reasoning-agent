"""
专利矩阵看板 — 竞品专利布局矩阵（竞品 × 技术点）
数据来源：PostgreSQL patents 表（通过 /api/patents/ 接口）
"""
import sys
import os
import streamlit as st
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from frontend.styles import inject_global_styles, page_title, section_header
from frontend.sidebar import render_sidebar

st.set_page_config(page_title="专利矩阵 | 合规优化智能体", page_icon="📋", layout="wide")
inject_global_styles()
api_base = render_sidebar()

page_title("竞品专利布局矩阵", "按申请人 × 技术方向分类的竞争格局全景 — 数据实时来自数据库")


def render_patent_matrix():
    """渲染专利矩阵看板（真实数据库数据）"""
    import httpx

    # ---- 统计卡片 ----
    try:
        with httpx.Client(timeout=10.0) as client:
            stats_resp = client.get(f"{api_base}/api/patents/stats")
            stats = stats_resp.json() if stats_resp.status_code == 200 else {}
    except Exception:
        stats = {}

    if not stats.get("total"):
        st.info(
            "📭 数据库中暂无专利数据。请先在「分析看板」主页输入产品关键词并运行分析，"
            "分析完成后专利数据将自动写入数据库并在此展示。"
        )
        return

    # 顶部统计
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("数据库专利总量", stats.get("total", 0))
    with c2:
        st.metric("涉及申请人数", len(stats.get("assignees", [])))
    with c3:
        st.metric("已分析关键词数", len(stats.get("queries", [])))

    st.markdown("<br>", unsafe_allow_html=True)

    # ---- 筛选器 ----
    section_header("专利布局矩阵")

    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        # 查询词下拉（从已有数据中选）
        query_options = ["全部"] + stats.get("queries", [])
        selected_query = st.selectbox("按分析关键词筛选", query_options)
    with col2:
        filter_assignee = st.text_input("按申请人筛选", placeholder="输入公司/申请人名称...")
    with col3:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        search_btn = st.button("🔍 搜索", type="primary", use_container_width=True)

    # ---- 拉取数据 ----
    params: dict = {}
    if selected_query and selected_query != "全部":
        params["query"] = selected_query
    if filter_assignee:
        params["assignee"] = filter_assignee

    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(f"{api_base}/api/patents/", params=params)
            patents = resp.json() if resp.status_code == 200 else []
    except Exception as e:
        st.error(f"获取专利数据失败: {e}")
        return

    if not patents:
        st.warning("没有匹配当前筛选条件的专利数据")
        return

    # ---- 构建 DataFrame ----
    rows = []
    for p in patents:
        tech = ""
        if isinstance(p.get("tech_points"), dict):
            tech = "、".join(p["tech_points"].get("points", []))
        elif isinstance(p.get("tech_points"), list):
            tech = "、".join(str(x) for x in p["tech_points"][:3])

        rows.append({
            "专利标题": p.get("title", "—"),
            "申请人": p.get("assignee") or "未知",
            "专利号": p.get("patent_id") or "—",
            "申请日期": p.get("filing_date") or "—",
            "核心技术": tech or p.get("category") or "—",
            "数据来源": p.get("source", "—"),
            "所属查询": p.get("search_query", "—"),
        })

    df = pd.DataFrame(rows)

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "专利标题": st.column_config.TextColumn("专利标题", width="large"),
            "申请人": st.column_config.TextColumn("申请人", width="medium"),
            "数据来源": st.column_config.TextColumn("来源", width="small"),
        },
    )

    st.caption(f"共显示 {len(df)} 条专利记录（实时来自 PostgreSQL patents 表）")

    # ---- 分析摘要（如果有当次分析结果）----
    if "latest_result" in st.session_state:
        patent_analysis = st.session_state["latest_result"].get("patent_analysis", "")
        if patent_analysis:
            st.markdown("<br>", unsafe_allow_html=True)
            section_header("AI 专利格局分析")
            st.markdown(patent_analysis)


render_patent_matrix()

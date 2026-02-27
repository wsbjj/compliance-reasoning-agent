"""
专利矩阵看板 — 竞品专利布局矩阵（竞品 × 技术点）
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
render_sidebar()

page_title("竞品专利布局矩阵", "按申请人 × 技术方向分类的竞争格局全景")


def render_patent_matrix():
    """渲染专利矩阵看板"""

    if "latest_result" not in st.session_state:
        st.info("请先在主页「分析看板」中运行完整分析，结果将在此展示")
        _render_sample()
        return

    result = st.session_state.get("latest_result", {})
    patent_analysis = result.get("patent_analysis", "")

    if patent_analysis:
        section_header("AI 专利分析报告")
        with st.container():
            st.markdown(patent_analysis)
    else:
        st.warning("未发现专利分析数据，展示示例数据")

    st.markdown("<br>", unsafe_allow_html=True)
    _render_matrix_table(result)


def _render_sample():
    """展示示例矩阵（无分析数据时）"""
    st.markdown("<br>", unsafe_allow_html=True)
    section_header("示例数据预览")

    sample = _get_sample_df()
    st.dataframe(
        sample,
        use_container_width=True,
        hide_index=True,
        column_config={
            "风险等级": st.column_config.TextColumn("风险等级", width="small"),
            "申请日期": st.column_config.TextColumn("申请日期", width="medium"),
        },
    )


def _render_matrix_table(result: dict):
    """渲染专利矩阵 + 筛选器 + 统计"""
    section_header("专利布局矩阵")

    col1, col2 = st.columns(2)
    with col1:
        filter_assignee = st.text_input(
            "按申请人筛选", placeholder="输入申请人/公司名称..."
        )
    with col2:
        filter_tech = st.text_input(
            "按技术方向筛选", placeholder="输入技术方向关键词..."
        )

    df = _get_sample_df()

    if filter_assignee:
        df = df[df["申请人"].str.contains(filter_assignee, case=False, na=False)]
    if filter_tech:
        df = df[df["核心技术"].str.contains(filter_tech, case=False, na=False)]

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "风险等级": st.column_config.TextColumn("风险等级", width="small"),
        },
    )

    # 统计概览
    st.markdown("<br>", unsafe_allow_html=True)
    section_header("统计概览")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("专利总量", result.get("patent_count", len(df)))
    with c2:
        st.metric("涉及申请人", len(df["申请人"].unique()) if not df.empty else 0)
    with c3:
        st.metric("技术方向数", len(df["核心技术"].unique()) if not df.empty else 0)


def _get_sample_df() -> pd.DataFrame:
    """示例专利数据"""
    return pd.DataFrame(
        {
            "专利标题": [
                "基于 AI 的健康传感数据融合方法",
                "可穿戴生物信号处理系统",
                "低功耗温度传感器结构",
                "手势识别神经网络模型",
                "睡眠质量实时评估算法",
            ],
            "申请人": ["Apple Inc.", "Samsung", "Oura Ring", "Garmin", "Fitbit"],
            "核心技术": [
                "AI 数据融合",
                "生物信号处理",
                "温度传感器",
                "手势识别",
                "睡眠监测",
            ],
            "申请日期": [
                "2024-01-15",
                "2024-03-20",
                "2024-06-10",
                "2024-08-05",
                "2024-11-22",
            ],
            "风险等级": ["🔴 高", "🔴 高", "🟡 中", "🟡 中", "🟢 低"],
        }
    )


render_patent_matrix()

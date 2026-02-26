"""
专利矩阵看板页面

展示竞品专利布局矩阵（竞品 × 技术点）
"""
import streamlit as st
import pandas as pd

st.set_page_config(page_title="专利矩阵", page_icon="📋", layout="wide")

st.title("📋 竞品专利布局矩阵")
st.markdown("按申请人和技术方向分类的专利概览")


def render_patent_matrix():
    """渲染专利矩阵表格"""

    # 检查是否有分析结果
    if "latest_result" not in st.session_state:
        st.info("请先在主页运行分析任务")
        return

    result = st.session_state.get("latest_result", {})
    patent_analysis = result.get("patent_analysis", "")

    if not patent_analysis:
        st.warning("未找到专利分析数据")
        return

    # 展示原始分析
    st.markdown("### 专利分析报告")
    st.markdown(patent_analysis)

    # 示例矩阵表格（实际应从 patent 数据构建）
    st.markdown("---")
    st.markdown("### 专利布局矩阵")

    # 筛选器
    col1, col2 = st.columns(2)
    with col1:
        filter_assignee = st.text_input("按申请人筛选", placeholder="输入申请人名称...")
    with col2:
        filter_tech = st.text_input("按技术方向筛选", placeholder="输入技术关键词...")

    # 占位 DataFrame（实际应从后端获取数据）
    sample_data = {
        "专利标题": ["Patent A", "Patent B", "Patent C"],
        "申请人": ["Company X", "Company Y", "Company Z"],
        "核心技术": ["Sensor Tech", "AI Algorithm", "Battery Design"],
        "申请日期": ["2024-01-15", "2024-03-20", "2024-06-10"],
        "风险等级": ["🟢 低", "🟡 中", "🔴 高"],
    }

    df = pd.DataFrame(sample_data)

    if filter_assignee:
        df = df[df["申请人"].str.contains(filter_assignee, case=False, na=False)]
    if filter_tech:
        df = df[df["核心技术"].str.contains(filter_tech, case=False, na=False)]

    st.dataframe(
        df,
        use_container_width=True,
        column_config={
            "风险等级": st.column_config.TextColumn("风险等级", width="small"),
        },
    )

    # 统计
    st.markdown("### 统计概览")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("总专利数", result.get("patent_count", 0))
    with c2:
        st.metric("涉及申请人", len(df["申请人"].unique()) if not df.empty else 0)
    with c3:
        st.metric("技术方向", len(df["核心技术"].unique()) if not df.empty else 0)


render_patent_matrix()

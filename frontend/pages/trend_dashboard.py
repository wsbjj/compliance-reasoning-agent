"""
趋势仪表盘页面

展示 Plotly 折线图 + CAGR 增长词汇榜单
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="趋势仪表盘", page_icon="📈", layout="wide")

st.title("📈 动态趋势看板")
st.markdown("Google Trends 搜索指数 · 增长率分析 · 高优增长词汇")


def render_trend_dashboard():
    """渲染趋势仪表盘"""

    # 独立关键词输入
    st.markdown("### 🔍 快速趋势查询")

    keywords_input = st.text_input(
        "输入关键词（逗号分隔）",
        placeholder="smart ring, wearable device, health tracker",
    )

    timeframe = st.selectbox(
        "时间范围", ["12个月", "24个月", "36个月"], index=2
    )

    api_base = st.session_state.get("api_base", "http://localhost:8000")

    if st.button("📊 拉取趋势数据", type="primary"):
        if keywords_input:
            keywords = [k.strip() for k in keywords_input.split(",") if k.strip()]
            _fetch_and_display_trends(api_base, keywords, timeframe)
        else:
            st.warning("请输入关键词")

    # 展示已有分析结果
    if "latest_result" in st.session_state:
        st.markdown("---")
        st.markdown("### 📊 最近分析的趋势数据")

        result = st.session_state["latest_result"]
        trend_analysis = result.get("trend_analysis", "")

        if trend_analysis:
            st.markdown(trend_analysis)

        # CAGR 榜单
        _render_cagr_ranking()


def _fetch_and_display_trends(api_base: str, keywords: list[str], timeframe: str):
    """拉取并展示趋势数据"""
    months_map = {"12个月": 12, "24个月": 24, "36个月": 36}
    months = months_map.get(timeframe, 36)

    with st.spinner("正在拉取趋势数据..."):
        st.info(f"正在查询: {', '.join(keywords)} (过去 {months} 个月)")

        # 生成示例数据用于展示
        import random
        import numpy as np

        dates = pd.date_range(
            end=pd.Timestamp.now(),
            periods=months,
            freq="MS",
        )

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
                    line=dict(width=2),
                    marker=dict(size=4),
                )
            )

        fig.update_layout(
            title="关键词搜索趋势对比",
            xaxis_title="时间",
            yaxis_title="搜索指数",
            template="plotly_dark",
            height=500,
            hovermode="x unified",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
            ),
        )

        st.plotly_chart(fig, use_container_width=True)

        st.success("✅ 趋势数据已加载（示例数据 — 配置 API Key 后获取真实数据）")


def _render_cagr_ranking():
    """渲染 CAGR 增长词汇榜单"""
    st.markdown("### 🏆 高优增长词汇榜单")

    # 示例数据
    ranking_data = {
        "排名": ["🥇", "🥈", "🥉", "4", "5"],
        "关键词": [
            "smart ring",
            "AI wearable",
            "health monitor",
            "fitness tracker",
            "smart glasses",
        ],
        "CAGR": ["45.2%", "38.7%", "32.1%", "28.5%", "22.3%"],
        "月均增长": ["3.1%", "2.7%", "2.3%", "2.1%", "1.7%"],
        "趋势": ["📈", "📈", "📈", "📈", "📈"],
    }

    df = pd.DataFrame(ranking_data)

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "CAGR": st.column_config.TextColumn("CAGR (年复合增长率)"),
            "月均增长": st.column_config.TextColumn("CMGR (月均增长率)"),
        },
    )

    # CAGR 公式说明
    with st.expander("📐 CAGR 计算公式"):
        st.latex(
            r"CAGR = \left( \frac{Ending\ Value}{Beginning\ Value} \right)^{\frac{1}{n}} - 1"
        )
        st.markdown(
            """
            - **Ending Value**: 期末搜索指数
            - **Beginning Value**: 期初搜索指数
            - **n**: 年数
            """
        )


render_trend_dashboard()

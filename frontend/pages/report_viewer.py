"""
报告查看器 — 浏览和搜索历史 AI 报告
数据来源：PostgreSQL analysis_reports 表（通过 /api/analysis/ 接口）
"""
import sys
import os
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from frontend.styles import inject_global_styles, page_title, section_header
from frontend.sidebar import render_sidebar

st.set_page_config(
    page_title="报告查看器 | 合规优化智能体", page_icon="🔍", layout="wide"
)
inject_global_styles()
api_base = render_sidebar()

page_title("窗口期预警简报", "AI 深度分析报告 — 专利壁垒 × 市场趋势 × 进入时机研判")


def render_report_viewer():
    """渲染报告查看器（真实数据库数据）"""
    import httpx

    # ---- 拉取历史报告列表 ----
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(f"{api_base}/api/analysis/")
            history = resp.json() if resp.status_code == 200 else []
    except Exception:
        history = []

    # ---- 无数据时的提示 ----
    if not history:
        st.info(
            "📭 数据库中暂无分析报告。请先前往「分析看板」主页，"
            "输入产品关键词并启动分析，报告完成后将自动保存到数据库并在此展示。"
        )
        # 如果当前会话有最新结果，也可以展示
        if "latest_result" in st.session_state:
            result = st.session_state["latest_result"]
            r = result.get("final_report", "")
            if r:
                st.markdown("<br>", unsafe_allow_html=True)
                section_header("当前会话最新报告")
                _render_report_detail(result)
        return

    # ---- 左侧报告列表 + 右侧报告正文 ----
    STATUS_BADGE = {
        "completed": "✅",
        "running":   "⏳",
        "failed":    "❌",
        "pending":   "🕐",
    }

    # 顶部统计
    completed = sum(1 for h in history if h.get("status") == "completed")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("历史报告总数", len(history))
    with c2:
        st.metric("已完成报告", completed)
    with c3:
        st.metric("数据来源", "PostgreSQL")

    st.markdown("<br>", unsafe_allow_html=True)
    section_header("历史报告列表")

    # 搜索过滤
    search_kw = st.text_input("🔍 按关键词搜索报告", placeholder="例如：Smart Ring")
    if search_kw:
        history = [h for h in history if search_kw.lower() in h.get("query", "").lower()]

    if not history:
        st.warning("没有匹配的报告")
        return

    # 报告列表
    for item in history:
        badge = STATUS_BADGE.get(item.get("status", ""), "❓")
        created = item.get("created_at", "")[:19].replace("T", " ")
        label = f"{badge} **{item.get('query', '未知关键词')}** — {created}"

        with st.expander(label, expanded=False):
            report_id = item.get("report_id", "")

            col_meta, col_btn = st.columns([3, 1])
            with col_meta:
                st.caption(f"报告 ID：{report_id}")
                st.caption(f"状态：{item.get('status', '—')}")

            with col_btn:
                if item.get("status") == "completed" and st.button(
                    "📄 展开完整报告", key=f"open_{report_id}", use_container_width=True
                ):
                    st.session_state[f"show_report_{report_id}"] = True

            # 专利摘要预览
            patent_sum = item.get("patent_summary") or ""
            if patent_sum:
                with st.container():
                    st.caption("📋 专利分析摘要（前 300 字）")
                    st.markdown(
                        patent_sum[:300] + "…" if len(patent_sum) > 300 else patent_sum
                    )

            # 完整报告展示（点击按钮触发）
            if st.session_state.get(f"show_report_{report_id}"):
                _load_and_render_full_report(api_base, report_id, item.get("query", ""))


def _load_and_render_full_report(api_base: str, report_id: str, query: str):
    """从 API 拉取并渲染完整报告"""
    import httpx
    try:
        with httpx.Client(timeout=20.0) as client:
            resp = client.get(f"{api_base}/api/analysis/{report_id}")
            if resp.status_code != 200:
                st.error("无法获取报告内容")
                return
            detail = resp.json()
    except Exception as e:
        st.error(f"加载报告失败: {e}")
        return

    full_report = detail.get("final_report", "")
    if not full_report:
        st.warning("报告内容为空，可能仍在生成中")
        return

    st.markdown("---")
    section_header("报告正文")

    # 元信息行
    mi1, mi2, mi3 = st.columns(3)
    with mi1:
        st.metric("分析关键词", query)
    with mi2:
        st.metric("专利数量", detail.get("patent_count", "—"))
    with mi3:
        st.metric("AI 审核迭代次数", detail.get("iterations", "—"))

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(full_report)

    # 下载区
    st.markdown("<br>", unsafe_allow_html=True)
    section_header("导出报告")
    dl1, dl2 = st.columns(2)
    with dl1:
        st.download_button(
            label="⬇️ 下载 Markdown 报告",
            data=full_report,
            file_name=f"合规分析报告_{query}.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with dl2:
        import json
        st.download_button(
            label="⬇️ 下载完整数据（JSON）",
            data=json.dumps(detail, ensure_ascii=False, indent=2),
            file_name=f"合规分析数据_{query}.json",
            mime="application/json",
            use_container_width=True,
        )


def _render_report_detail(result: dict):
    """渲染当前会话报告详情"""
    report = result.get("final_report", "")
    if not report:
        return

    mi1, mi2, mi3 = st.columns(3)
    with mi1:
        st.metric("分析关键词", result.get("query", "—"))
    with mi2:
        status_map = {"completed": "✅ 已完成", "failed": "❌ 失败", "running": "⏳ 进行中"}
        st.metric("分析状态", status_map.get(result.get("status", ""), result.get("status", "—")))
    with mi3:
        st.metric("AI 审核迭代次数", result.get("iterations", 0))

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(report)


render_report_viewer()

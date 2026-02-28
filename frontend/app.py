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


from sidebar import render_sidebar


# ---- 主页面 ----
def main():
    api_base = render_sidebar()

    # ---- 任务节流初始化 ----
    if "is_running" not in st.session_state:
        st.session_state["is_running"] = False

    # 页面标题
    page_title(
        "合规优化智能体看板",
        "专利排查 · 趋势分析 · 窗口期预警 — 一站式合规风控平台",
    )

    # ---- 分析输入区 ----
    section_header("启动分析")

    col1, col2, col3 = st.columns([5, 3, 2])
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
    with col3:
        # ---- 国家筛选 ----
        _ALL_LABEL = "全部国家"
        COUNTRY_OPTIONS: dict[str, str] = {
            "US": "美国 (US)",
            "CN": "中国 (CN)",
            "EP": "欧洲 (EP)",
            "WO": "WIPO/PCT (WO)",
            "JP": "日本 (JP)",
            "KR": "韩国 (KR)",
            "DE": "德国 (DE)",
            "GB": "英国 (GB)",
            "FR": "法国 (FR)",
            "CA": "加拿大 (CA)",
            "AU": "澳大利亚 (AU)",
            "IN": "印度 (IN)",
            "TW": "中国台湾 (TW)",
            "MX": "墨西哥 (MX)",
        }
        all_country_labels = list(COUNTRY_OPTIONS.values())
        # "全部国家" 置顶
        dropdown_options = [_ALL_LABEL] + all_country_labels

        selected_labels = st.multiselect(
            "专利检索国家/地区",
            options=dropdown_options,
            default=[],
            placeholder="不选择则检索全部",
            help="选择要分析的专利所属国家/地区，留空或选择「全部国家」表示不限",
        )

    # 将显示标签映射回国家代码；选了 "全部国家" 或空 → 传空列表（后端不限）
    label_to_code = {v: k for k, v in COUNTRY_OPTIONS.items()}
    if _ALL_LABEL in selected_labels or not selected_labels:
        selected_countries: list[str] = []
    else:
        selected_countries = [
            label_to_code[lb] for lb in selected_labels if lb in label_to_code
        ]

    # ---- 任务节流：运行中禁止重复提交 ----
    if st.session_state["is_running"] and "pending_query" not in st.session_state:
        st.warning("⏳ 分析任务正在运行中，请耐心等待完成后再提交新任务…")

    btn_clicked = st.button(
        "开始合规分析",
        type="primary",
        use_container_width=True,
        disabled=st.session_state["is_running"],
    )

    if btn_clicked:
        if not query:
            st.warning("请先输入产品关键词")
        else:
            # 缓存待运行的 query，置为运行中后强制刷新
            st.session_state["is_running"] = True
            st.session_state["pending_query"] = query
            st.session_state["pending_context"] = extra_context
            st.session_state["pending_countries"] = selected_countries
            st.rerun()

    # ---- 实际执行分析（is_running=True 时在下一轮 render 中触发）----
    if st.session_state["is_running"] and "pending_query" in st.session_state:
        pending_q = st.session_state.pop("pending_query")
        pending_ctx = st.session_state.pop("pending_context", "")
        pending_countries = st.session_state.pop("pending_countries", [])

        # ---- 链式进度显示（实时展示后端操作）----
        progress_placeholder = st.empty()

        # 有效完成节点（处理重试后重置）
        effective_completed: dict[str, dict] = {}
        retry_count = 0
        result = None
        error_msg = None

        try:
            import httpx
            import json

            with httpx.Client(timeout=300.0) as client:
                with client.stream(
                    "POST",
                    f"{api_base}/api/analysis/run_stream",
                    json={
                        "query": pending_q,
                        "extra_context": pending_ctx,
                        "user_id": "streamlit_user",
                        "countries": pending_countries,
                    },
                ) as response:
                    response.raise_for_status()
                    for line in response.iter_lines():
                        if not line or not line.startswith("data: "):
                            continue
                        event = json.loads(line[6:])

                        if event.get("type") == "node_complete":
                            node = event["node"]
                            # 审核未通过时重置 synthesize/review 状态
                            if node == "review" and "RETRY" in event.get("summary", ""):
                                retry_count += 1
                                effective_completed.pop("synthesize", None)
                                effective_completed.pop("review", None)
                            else:
                                effective_completed[node] = event
                            _render_progress_chain(
                                progress_placeholder, effective_completed, retry_count
                            )

                        elif event.get("type") == "result":
                            result = event["data"]

                        elif event.get("type") == "error":
                            error_msg = event.get("message", "Unknown error")

            if result:
                # 最终渲染全部完成状态
                _render_progress_chain(
                    progress_placeholder, effective_completed, retry_count, done=True
                )
                st.session_state["latest_result"] = result
                st.session_state["_analysis_msg"] = (
                    "success",
                    f"分析完成！共检索到 {result.get('patent_count', 0)} 篇专利",
                )
            elif error_msg:
                st.session_state["_analysis_msg"] = ("error", f"分析失败: {error_msg}")

        except Exception as e:
            st.session_state["_analysis_msg"] = ("error", f"分析失败: {e}")
        finally:
            # 无论成功失败，解除节流锁并刷新页面以清除过时 UI
            st.session_state["is_running"] = False
            st.rerun()

    # ---- 显示上一次分析的完成/错误提示 ----
    if "_analysis_msg" in st.session_state:
        msg_type, msg_text = st.session_state.pop("_analysis_msg")
        if msg_type == "success":
            st.success(msg_text)
        else:
            st.error(msg_text)

    # ---- 结果展示 ----
    if "latest_result" in st.session_state:
        result = st.session_state["latest_result"]

        # 指标卡片行
        st.markdown("<br>", unsafe_allow_html=True)
        section_header("分析概览")

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric(
                "专利数量", result.get("patent_count", 0), help="搜索到的相关专利总数"
            )
        with m2:
            st.metric(
                "趋势关键词",
                result.get("trend_keywords", 0),
                help="分析的市场趋势词数量",
            )
        with m3:
            st.metric(
                "审核迭代次数",
                result.get("iterations", 0),
                help="AI 自我审核的循环次数",
            )
        with m4:
            status_map = {
                "success": "✅ 已完成",
                "error": "❌ 失败",
                "running": "⏳ 进行中",
            }
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

    col_refresh, _ = st.columns([1, 5])
    with col_refresh:
        refresh = st.button("🔄 刷新记录", use_container_width=True)

    _render_history(api_base)


def _render_progress_chain(
    placeholder,
    effective_completed: dict[str, dict],
    retry_count: int = 0,
    done: bool = False,
) -> None:
    """
    渲染链式任务进度 — 实时展示后端各节点的执行状态

    effective_completed: {node_id: event_dict} — 当前有效的已完成节点
    retry_count: 审核重试次数
    done: 全部流程是否结束
    """
    # 节点定义（与后端 graph 一致）
    CHAIN_NODES = [
        ("plan", "任务规划", "🧠"),
        ("patents", "专利搜索 + DB写入", "🔍"),
        ("trends", "趋势分析 + DB写入", "📈"),
        ("synthesize", "报告生成", "📝"),
        ("review", "质量审核", "🔎"),
        ("memory", "记忆更新 + 持久化", "💾"),
    ]
    # 前驱关系（用于推断 "正在运行" 状态）
    PREDS: dict[str, list[str]] = {
        "plan": [],
        "patents": ["plan"],
        "trends": ["plan"],
        "synthesize": ["patents", "trends"],
        "review": ["synthesize"],
        "memory": ["review"],
    }

    done_set = set(effective_completed.keys())

    def _is_running(nid: str) -> bool:
        if nid in done_set:
            return False
        return all(p in done_set for p in PREDS.get(nid, []))

    # ---- 构建 HTML ----
    parts: list[str] = [
        "<style>"
        "@keyframes agent-pulse{0%,100%{opacity:1}50%{opacity:.45}}"
        "</style>"
        "<div style=\"font-family:'Fira Code',monospace;font-size:13px;"
        'line-height:1.5;padding:12px 0;">'
    ]

    for idx, (nid, label, icon) in enumerate(CHAIN_NODES):
        is_parallel = nid in ("patents", "trends")
        # 并行节点前缀
        prefix = "├─" if is_parallel else "▶"

        if nid in effective_completed:
            info = effective_completed[nid]
            elapsed = info.get("elapsed", 0)
            summary = info.get("summary", "")
            summary_html = (
                f'<span style="color:#64748b;font-weight:400"> — {summary}</span>'
                if summary
                else ""
            )
            parts.append(
                f'<div style="display:flex;align-items:center;gap:8px;'
                f"padding:6px 14px;margin:3px 0;"
                f"background:rgba(34,197,94,.08);border-left:3px solid #22c55e;"
                f'border-radius:0 8px 8px 0;">'
                f"<span>{prefix}</span>"
                f'<span style="color:#22c55e;font-weight:700;">✅</span>'
                f'<span style="color:#e2e8f0;font-weight:600;">{icon} {label}</span>'
                f'<span style="color:#94a3b8;">({elapsed}s)</span>'
                f"{summary_html}"
                f"</div>"
            )

        elif _is_running(nid) and not done:
            retry_hint = ""
            if nid == "synthesize" and retry_count > 0:
                retry_hint = (
                    f'<span style="color:#94a3b8;margin-left:6px;">'
                    f"(第 {retry_count + 1} 次)</span>"
                )
            parts.append(
                f'<div style="display:flex;align-items:center;gap:8px;'
                f"padding:6px 14px;margin:3px 0;"
                f"background:rgba(59,130,246,.10);border-left:3px solid #3b82f6;"
                f"border-radius:0 8px 8px 0;"
                f'animation:agent-pulse 1.5s ease-in-out infinite;">'
                f"<span>{prefix}</span>"
                f'<span style="color:#3b82f6;font-weight:700;">⏳</span>'
                f'<span style="color:#e2e8f0;font-weight:600;">{icon} {label}</span>'
                f'<span style="color:#3b82f6;">正在运行...</span>'
                f"{retry_hint}"
                f"</div>"
            )

        else:
            parts.append(
                f'<div style="display:flex;align-items:center;gap:8px;'
                f"padding:6px 14px;margin:3px 0;"
                f"border-left:3px solid #334155;border-radius:0 8px 8px 0;"
                f'opacity:.4;">'
                f"<span>{prefix}</span>"
                f'<span style="color:#475569;">○</span>'
                f'<span style="color:#64748b;">{icon} {label}</span>'
                f"</div>"
            )

        # 连接线（并行节点之间不画线）
        if idx < len(CHAIN_NODES) - 1:
            next_nid = CHAIN_NODES[idx + 1][0]
            if not (is_parallel and next_nid in ("patents", "trends")):
                c_color = "#22c55e" if nid in done_set else "#334155"
                parts.append(
                    f'<div style="color:{c_color};padding:0 0 0 20px;'
                    f'line-height:1;font-size:12px;">│</div>'
                )

    parts.append("</div>")

    with placeholder.container():
        st.markdown("".join(parts), unsafe_allow_html=True)


def _render_history(api_base: str) -> None:
    """渲染历史分析记录列表"""
    STATUS_BADGE = {
        "completed": "✅ 完成",
        "running": "⏳ 运行中",
        "failed": "❌ 失败",
        "pending": "🕐 等待中",
    }

    try:
        import httpx

        with httpx.Client(timeout=10.0) as client:
            resp = client.get(f"{api_base}/api/analysis/")
            if resp.status_code != 200:
                st.info("无法获取历史记录，请确认后端已启动")
                return
            history = resp.json()

        if not history:
            st.info("暂无历史记录，运行分析后将在此展示")
            return

        # 逐条渲染
        for item in history:
            status_raw = item.get("status", "unknown")
            badge = STATUS_BADGE.get(status_raw, f"❓ {status_raw}")
            created_at = item.get("created_at", "")[:19].replace("T", " ")
            query_text = item.get("query", "—")
            report_id = item.get("report_id", "")

            with st.expander(
                f"{badge}  **{query_text}**  —  {created_at}",
                expanded=False,
            ):
                col_a, col_b = st.columns([1, 3])
                with col_a:
                    st.caption("报告 ID")
                    st.code(report_id, language=None)
                with col_b:
                    # 点击"查看完整报告"时，从 API 拉取详情
                    if st.button("📄 查看完整报告", key=f"view_{report_id}"):
                        try:
                            with httpx.Client(timeout=15.0) as c:
                                detail = c.get(
                                    f"{api_base}/api/analysis/{report_id}"
                                ).json()
                            full = detail.get("final_report", "")
                            if full:
                                st.markdown(full)
                            else:
                                st.warning("报告内容为空，可能仍在生成中")
                        except Exception as e:
                            st.error(f"获取报告失败: {e}")

                # 摘要预览
                patent_sum = item.get("patent_summary") or ""
                if patent_sum:
                    st.caption("📋 专利分析摘要")
                    st.markdown(
                        patent_sum[:400] + "…" if len(patent_sum) > 400 else patent_sum
                    )

    except Exception:
        st.info(
            "💡 请先启动后端服务: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`"
        )


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

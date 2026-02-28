"""
专利矩阵看板 — 竞品专利布局（卡片式详情展示）
功能：
  - 数据库历史专利展示（带图片/PDF/全字段）
  - 实时 SerpApi 搜索（含国家筛选，自动写库）
"""
import sys
import os
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from frontend.styles import inject_global_styles, page_title, section_header
from frontend.sidebar import render_sidebar

st.set_page_config(page_title="专利矩阵 | 合规优化智能体", page_icon="📋", layout="wide")
inject_global_styles()
api_base = render_sidebar()

page_title("竞品专利布局矩阵", "数据库历史专利 · 实时搜索 · 国家筛选 · 图文详情")

# ================================================================
# 国家映射表（中文 → ISO 代码）
# ================================================================
COUNTRY_OPTIONS = {
    "🇺🇸 美国": "US",
    "🇨🇳 中国": "CN",
    "🇪🇺 欧洲": "EP",
    "🇯🇵 日本": "JP",
    "🇰🇷 韩国": "KR",
    "🇨🇦 加拿大": "CA",
    "🇬🇧 英国": "GB",
    "🇩🇪 德国": "DE",
    "🇫🇷 法国": "FR",
    "🇦🇺 澳大利亚": "AU",
    "🇮🇳 印度": "IN",
    "🇧🇷 巴西": "BR",
    "🇲🇽 墨西哥": "MX",
}


def _country_status_badge(status_dict: dict) -> str:
    """从 country_status 中生成状态徽章文字"""
    if not status_dict or not isinstance(status_dict, dict):
        return ""
    parts = []
    for country, status in list(status_dict.items())[:4]:
        icon = "✅" if status == "ACTIVE" else "❌"
        parts.append(f"{icon} {country}")
    return "  ".join(parts)


def _render_patent_card(p: dict, idx: int):
    """渲染单张专利卡片（Expander）"""
    patent_id = p.get("patent_id") or p.get("publication_number") or f"#{idx+1}"
    title = p.get("title") or "（无标题）"
    assignee = p.get("assignee") or "—"
    country_badge = _country_status_badge(p.get("country_status", {}))

    expander_label = f"**{title}**  ·  {assignee}  ·  `{patent_id}`"
    if country_badge:
        expander_label += f"  {country_badge}"

    with st.expander(expander_label, expanded=False):
        left, right = st.columns([2, 1])

        with left:
            # 缩略图
            thumbnail = p.get("thumbnail_url") or p.get("thumbnail") or ""
            if thumbnail:
                st.image(thumbnail, caption="专利首页示意图", width=220)
            else:
                st.caption("（无缩略图）")

            # figures 图表列表
            figures = p.get("figures") or []
            if figures:
                st.caption(f"📐 专利图表（共 {len(figures)} 张）")
                cols = st.columns(min(len(figures), 4))
                for fi, fig_url in enumerate(figures[:4]):
                    with cols[fi]:
                        try:
                            st.image(fig_url, use_container_width=True)
                        except Exception:
                            st.caption(f"图 {fi+1}")

        with right:
            st.markdown("#### 📋 基本信息")
            info_rows = [
                ("专利号", patent_id),
                ("公开号", p.get("publication_number") or "—"),
                ("申请人", assignee),
                ("发明人", p.get("inventor") or "—"),
                ("优先权日", p.get("priority_date") or "—"),
                ("申请日", p.get("filing_date") or "—"),
                ("公开日", p.get("publication_date") or "—"),
                ("数据来源", p.get("source") or "serpapi"),
            ]
            for label, val in info_rows:
                st.markdown(f"**{label}**：{val}")

            # PDF 链接
            pdf_url = p.get("pdf_url") or p.get("pdf") or ""
            if pdf_url:
                st.link_button("📄 查看专利原文 PDF", pdf_url, use_container_width=True)

            # 各国有效性
            cs = p.get("country_status", {})
            if cs and isinstance(cs, dict):
                st.markdown("**专利有效性：**")
                for country, status in cs.items():
                    icon = "✅" if status == "ACTIVE" else "❌"
                    st.markdown(f"{icon} {country}: {status}")

        # 摘要
        abstract = p.get("abstract") or p.get("snippet") or ""
        if abstract:
            st.markdown("---")
            st.markdown(f"**摘要：** {abstract}")

        sq = p.get("search_query") or ""
        ca = p.get("created_at") or ""
        if sq or ca:
            st.caption(f"查询词：{sq}  |  录入时间：{ca[:10] if ca else '—'}")


# ================================================================
# 模块一：数据库历史专利矩阵
# ================================================================
def render_db_patent_matrix():
    """展示数据库中的历史分析专利"""
    import httpx

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
            "\n\n也可在「🌐 实时专利搜索」Tab 中直接搜索，结果同步写入数据库。"
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
    col1, col2 = st.columns([2, 2])
    with col1:
        query_options = ["全部"] + stats.get("queries", [])
        selected_query = st.selectbox("按分析关键词筛选", query_options, key="db_query_filter")
    with col2:
        filter_assignee = st.text_input(
            "按申请人筛选", placeholder="输入公司/申请人名称...", key="db_assignee_filter"
        )

    st.button("🔍 搜索", type="primary", key="db_search_btn")

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

    st.caption(f"共找到 **{len(patents)}** 条专利记录（来自 PostgreSQL patents 表）")
    st.markdown("<br>", unsafe_allow_html=True)

    for idx, p in enumerate(patents):
        _render_patent_card(p, idx)

    # AI 分析摘要
    if "latest_result" in st.session_state:
        patent_analysis = st.session_state["latest_result"].get("patent_analysis", "")
        if patent_analysis:
            st.markdown("<br>", unsafe_allow_html=True)
            section_header("AI 专利格局分析")
            st.markdown(patent_analysis)


# ================================================================
# 模块二：实时 SerpApi 专利搜索
# ================================================================
def render_live_search():
    """实时调用 SerpApi 搜索专利（结果同步写库）"""
    import httpx

    section_header("🔍 实时专利搜索")
    st.caption("直接调用 SerpApi Google Patents，搜索结果自动写入数据库")

    col1, col2 = st.columns([2, 2])
    with col1:
        live_query = st.text_input(
            "搜索关键词",
            placeholder="例如：smart yoga mat、wireless earbuds",
            key="live_query",
        )
    with col2:
        selected_countries_zh = st.multiselect(
            "国家/地区筛选（可多选，不选则搜索全球）",
            options=list(COUNTRY_OPTIONS.keys()),
            default=["🇺🇸 美国", "🇨🇳 中国"],
            key="live_countries",
        )

    search_btn = st.button("🌐 搜索专利", type="primary", key="live_search_btn")

    if search_btn:
        if not live_query:
            st.warning("请输入搜索关键词")
            return

        country_codes = [COUNTRY_OPTIONS[zh] for zh in selected_countries_zh]
        countries_param = ",".join(country_codes) if country_codes else None

        # 展示实际 query 格式
        if country_codes:
            q_display = f"{live_query} ({' OR '.join(f'country:{c}' for c in country_codes)})"
        else:
            q_display = live_query
        st.caption(f"🔎 实际搜索 Query：`{q_display}`")

        with st.spinner("正在调用 SerpApi 搜索，并将结果写入数据库..."):
            try:
                params = {"q": live_query}
                if countries_param:
                    params["countries"] = countries_param

                with httpx.Client(timeout=60.0) as client:
                    resp = client.get(f"{api_base}/api/patents/search", params=params)
                    resp.raise_for_status()
                    results = resp.json()

                if not results:
                    st.info("未找到匹配的专利结果，请尝试调整关键词或国家筛选")
                    return

                st.success(f"✅ 共找到 **{len(results)}** 条专利结果，已写入数据库")
                st.markdown("<br>", unsafe_allow_html=True)

                for idx, p in enumerate(results):
                    _render_patent_card(p, idx)

            except Exception as e:
                st.error(f"❌ 搜索失败: {e}")


# ================================================================
# 主渲染入口
# ================================================================
tab_db, tab_live = st.tabs(["📚 历史专利（数据库）", "🌐 实时专利搜索"])

with tab_db:
    render_db_patent_matrix()

with tab_live:
    render_live_search()

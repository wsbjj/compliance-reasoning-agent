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

st.set_page_config(
    page_title="专利矩阵 | 合规优化智能体", page_icon="📋", layout="wide"
)
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

_ALL_OPTION = "🌍 全部（不过滤）"
LIVE_COUNTRY_OPTIONS = {_ALL_OPTION: None, **COUNTRY_OPTIONS}

# 专利有效性筛选选项映射
_VALIDITY_OPTIONS = {
    "不筛选": None,
    "✅ ACTIVE（有效）": "ACTIVE",
    "❌ NOT_ACTIVE（无效）": "NOT_ACTIVE",
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
    patent_id = p.get("patent_id") or p.get("publication_number") or f"#{idx + 1}"
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
                            st.caption(f"图 {fi + 1}")

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
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        query_options = ["全部"] + stats.get("queries", [])
        selected_query = st.selectbox(
            "按分析关键词筛选", query_options, key="db_query_filter"
        )
    with col2:
        filter_assignee = st.text_input(
            "按申请人筛选",
            placeholder="输入公司/申请人名称...",
            key="db_assignee_filter",
        )
    with col3:
        validity_label = st.selectbox(
            "专利有效性",
            options=list(_VALIDITY_OPTIONS.keys()),
            key="db_validity_filter",
            help="ACTIVE=至少一个国家有效；NOT_ACTIVE=至少一个国家无效",
        )

    st.button("🔍 搜索", type="primary", key="db_search_btn")

    # ---- 拉取数据 ----
    params: dict = {}
    if selected_query and selected_query != "全部":
        params["query"] = selected_query
    if filter_assignee:
        params["assignee"] = filter_assignee
    validity_value = _VALIDITY_OPTIONS[validity_label]
    if validity_value:
        params["validity"] = validity_value

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

# 高级筛选选项映射
_STATUS_OPTIONS = {
    "全部": None,
    "✅ 已授权 (GRANT)": "GRANT",
    "📋 申请中 (APPLICATION)": "APPLICATION",
}
_SORT_OPTIONS = {
    "默认（相关度）": None,
    "最新优先 (new)": "new",
    "最旧优先 (old)": "old",
}
_DUPS_OPTIONS = {
    "同族去重（默认）": None,  # Family：同一技术族只显示一条
    "显示全部公开文本 (language)": "language",  # Publication：每个国家公开文本都显示
}
_TYPE_OPTIONS = {
    "全部": None,
    "发明专利 (PATENT)": "PATENT",
    "外观设计 (DESIGN)": "DESIGN",
}


def render_live_search():
    """实时调用 SerpApi 搜索专利（结果同步写库）"""
    import httpx

    section_header("🔍 实时专利搜索")
    st.caption("直接调用 SerpApi Google Patents，搜索结果自动写入数据库")

    # ── 主搜索行 ──────────────────────────────────────────────────
    col1, col2 = st.columns([2, 2])
    with col1:
        live_query = st.text_input(
            "搜索关键词",
            placeholder="例如：smart yoga mat、(Coffee) OR (Tea)",
            key="live_query",
        )
    with col2:
        selected_countries_zh = st.multiselect(
            "国家/地区筛选（可多选，不选则搜索全球）",
            options=list(LIVE_COUNTRY_OPTIONS.keys()),
            default=[_ALL_OPTION],
            key="live_countries",
        )

    # ── 操作行：搜索按钮 + 有效性筛选 + 获取条数 ──────────────────
    col_btn, col_validity, col_title_only, col_num = st.columns([2, 1, 1, 1])
    with col_btn:
        search_btn = st.button("🌐 搜索专利", type="primary", key="live_search_btn")
    with col_validity:
        live_validity_label = st.selectbox(
            "专利有效性",
            options=list(_VALIDITY_OPTIONS.keys()),
            key="live_validity",
            help="基于 country_status 字段后过滤：ACTIVE=至少一个国家有效；NOT_ACTIVE=至少一个国家无效（SerpApi 不支持该参数，结果获取后本地过滤）",
        )
    with col_title_only:
        title_only = st.checkbox(
            "只匹配标题",
            value=True,
            key="live_title_only",
            help="勾选后仅保留标题中包含关键词的专利结果",
        )
    with col_num:
        max_results = st.selectbox(
            "获取条数",
            options=[10, 20, 50, 100],
            index=1,
            key="live_max_results",
            help="单次最多 100 条，设为 100 时只需 1 次 SerpApi 请求",
        )

    # ── 高级筛选（折叠） ─────────────────────────────────────────
    with st.expander("🔧 高级筛选（可选）"):
        adv1, adv2, adv3, adv4_dups = st.columns(4)
        with adv1:
            status_label = st.selectbox(
                "法律状态",
                options=list(_STATUS_OPTIONS.keys()),
                key="live_status",
                help="GRANT=已授权专利；APPLICATION=申请中专利",
            )
        with adv2:
            sort_label = st.selectbox(
                "排序方式",
                options=list(_SORT_OPTIONS.keys()),
                key="live_sort",
                help="new=最新优先；old=最旧优先；默认=相关度",
            )
        with adv3:
            type_label = st.selectbox(
                "专利类型",
                options=list(_TYPE_OPTIONS.keys()),
                key="live_type",
            )
        with adv4_dups:
            dups_label = st.selectbox(
                "结果分组",
                options=list(_DUPS_OPTIONS.keys()),
                key="live_dups",
                help="同族去重：每个专利族只显示一条；显示全部：每个国家公开文本都显示",
            )

        adv4, adv5 = st.columns(2)
        with adv4:
            date_after = st.text_input(
                "日期下限（after）",
                placeholder="filing:20200101",
                key="live_after",
                help="格式：type:YYYYMMDD，type 可选 priority / filing / publication",
            )
        with adv5:
            date_before = st.text_input(
                "日期上限（before）",
                placeholder="publication:20240101",
                key="live_before",
                help="格式：type:YYYYMMDD",
            )

    # ── 触发搜索 ─────────────────────────────────────────────────
    if search_btn:
        if not live_query:
            st.warning("请输入搜索关键词")
            return

        country_codes = [
            COUNTRY_OPTIONS[zh]
            for zh in selected_countries_zh
            if zh in COUNTRY_OPTIONS  # 排除"全部"选项
        ]
        countries_param = ",".join(country_codes) if country_codes else None

        # 高级筛选值
        status_param = _STATUS_OPTIONS[status_label]
        sort_param = _SORT_OPTIONS[sort_label]
        type_param = _TYPE_OPTIONS[type_label]
        dups_param = _DUPS_OPTIONS[dups_label]
        after_param = date_after.strip() or None
        before_param = date_before.strip() or None

        # 构建展示信息
        filter_tags = []
        if country_codes:
            filter_tags.append(f"国家: {', '.join(country_codes)}")
        if status_param:
            filter_tags.append(f"状态: {status_param}")
        if sort_param:
            filter_tags.append(f"排序: {sort_param}")
        if dups_param:
            filter_tags.append(f"分组: {dups_param}")
        if type_param:
            filter_tags.append(f"类型: {type_param}")
        if after_param:
            filter_tags.append(f"after: {after_param}")
        if before_param:
            filter_tags.append(f"before: {before_param}")

        # 专利有效性筛选值
        live_validity_value = _VALIDITY_OPTIONS[live_validity_label]
        if live_validity_value:
            filter_tags.append(f"有效性: {live_validity_value}")
        if title_only:
            filter_tags.append("只匹配标题")

        st.caption(
            f"🔎 搜索词：`{live_query}`"
            + (f"　　筛选：{' | '.join(filter_tags)}" if filter_tags else "")
        )

        with st.spinner(
            f"正在调用 SerpApi 搜索（最多 {max_results} 条），并将结果写入数据库..."
        ):
            try:
                params: dict = {"q": live_query, "max_results": max_results}
                if countries_param:
                    params["countries"] = countries_param
                if status_param:
                    params["status"] = status_param
                if sort_param:
                    params["sort"] = sort_param
                if dups_param:
                    params["dups"] = dups_param
                if type_param:
                    params["patent_type"] = type_param
                if after_param:
                    params["after"] = after_param
                if before_param:
                    params["before"] = before_param

                with httpx.Client(timeout=120.0) as client:
                    resp = client.get(f"{api_base}/api/patents/search", params=params)
                    resp.raise_for_status()
                    raw_results = resp.json()

                if not raw_results:
                    st.info("未找到匹配的专利结果，请尝试调整关键词或筛选条件")
                    st.session_state["live_results"] = []
                    return

                # 前端二次过滤：SerpApi country 参数已做一次筛选
                # 此处再对 country_status 做确认，排除无该国记录的专利
                if _ALL_OPTION not in selected_countries_zh and country_codes:
                    results = [
                        p
                        for p in raw_results
                        if any(
                            c in (p.get("country_status") or {}) for c in country_codes
                        )
                    ]
                else:
                    results = raw_results

                # 专利有效性后过滤（SerpApi 不支持该参数，本地过滤）
                if live_validity_value:
                    results = [
                        p
                        for p in results
                        if live_validity_value
                        in (p.get("country_status") or {}).values()
                    ]

                # 只匹配标题：仅保留标题中包含搜索关键词的结果
                if title_only and live_query:
                    # 提取核心关键词（去除布尔运算符和括号）
                    import re

                    raw_kw = re.sub(r"\b(OR|AND|NOT)\b", " ", live_query)
                    raw_kw = re.sub(r"[()\"']", " ", raw_kw)
                    keywords = [
                        kw.strip().lower()
                        for kw in raw_kw.split()
                        if kw.strip() and len(kw.strip()) > 1
                    ]
                    if keywords:
                        results = [
                            p
                            for p in results
                            if any(
                                kw in (p.get("title") or "").lower() for kw in keywords
                            )
                        ]

                # 存入 session_state，重置到第 0 页
                st.session_state["live_results"] = results
                st.session_state["live_results_total_fetched"] = len(raw_results)
                st.session_state["live_page"] = 0
                st.session_state["live_filter_tags"] = filter_tags

            except Exception as e:
                st.error(f"❌ 搜索失败: {e}")
                return

    # ── 展示结果（session_state，支持翻页）─────────────────────
    results = st.session_state.get("live_results", [])
    if not results:
        return

    total_fetched = st.session_state.get("live_results_total_fetched", len(results))
    filter_tags = st.session_state.get("live_filter_tags", [])

    PAGE_SIZE = 10
    total_pages = max(1, (len(results) + PAGE_SIZE - 1) // PAGE_SIZE)
    page = max(0, min(st.session_state.get("live_page", 0), total_pages - 1))

    # 统计栏
    fetched_note = f"共获取 **{total_fetched}** 条"
    if len(results) < total_fetched:
        fetched_note += f"，过滤后剩余 **{len(results)}** 条"
    st.success(f"✅ {fetched_note}，第 **{page + 1}/{total_pages}** 页")

    # 翻页控件
    nav_l, nav_mid, nav_r = st.columns([1, 4, 1])
    with nav_l:
        if st.button("◀ 上一页", disabled=(page == 0), key="live_prev"):
            st.session_state["live_page"] = page - 1
            st.rerun()
    with nav_mid:
        st.caption(
            f"第 {page + 1} / {total_pages} 页 · 每页 {PAGE_SIZE} 条 · 共 {len(results)} 条"
        )
    with nav_r:
        if st.button("下一页 ▶", disabled=(page >= total_pages - 1), key="live_next"):
            st.session_state["live_page"] = page + 1
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # 渲染当前页卡片
    start_idx = page * PAGE_SIZE
    for idx, p in enumerate(results[start_idx : start_idx + PAGE_SIZE]):
        _render_patent_card(p, start_idx + idx)


# ================================================================
# 主渲染入口
# ================================================================
tab_db, tab_live = st.tabs(["📚 历史专利（数据库）", "🌐 实时专利搜索"])

with tab_db:
    render_db_patent_matrix()

with tab_live:
    render_live_search()

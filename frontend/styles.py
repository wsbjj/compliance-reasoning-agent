"""
frontend/styles.py — 合规优化智能体 统一 CSS 样式模块

所有页面通过 inject_global_styles() 函数注入样式，保持一致性。
"""
import streamlit as st


COMMON_STYLES = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;600;700&family=Fira+Sans:wght@300;400;500;600;700&display=swap');

/* ==========================================
   CSS 变量 — 合规优化智能体设计令牌
   ========================================== */
:root {
    --ai-primary:          #3B82F6;
    --ai-primary-dark:     #1E40AF;
    --ai-primary-glow:     rgba(59, 130, 246, 0.15);
    --ai-accent:           #F59E0B;
    --ai-accent-glow:      rgba(245, 158, 11, 0.15);
    --ai-success:          #10B981;
    --ai-warning:          #F59E0B;
    --ai-danger:           #EF4444;

    --ai-bg-page:          #0A0F1E;
    --ai-bg-card:          #0F172A;
    --ai-bg-card-hover:    #1E293B;
    --ai-bg-sidebar:       #080D1A;

    --ai-text-primary:     #E2E8F0;
    --ai-text-secondary:   #94A3B8;
    --ai-text-muted:       #64748B;

    --ai-border:           rgba(59, 130, 246, 0.2);
    --ai-border-strong:    rgba(59, 130, 246, 0.45);
    --ai-border-muted:     rgba(255, 255, 255, 0.06);

    --ai-radius-sm:        6px;
    --ai-radius-md:        12px;
    --ai-radius-lg:        16px;

    --ai-shadow-card:      0 4px 24px rgba(0, 0, 0, 0.5);
    --ai-shadow-glow:      0 0 24px rgba(59, 130, 246, 0.2);
    --ai-transition:       all 0.22s ease;
}

/* ==========================================
   字体
   ========================================== */
html, body, [class*="css"] {
    font-family: 'Fira Sans', -apple-system, sans-serif !important;
}

/* ==========================================
   页面标题组件
   ========================================== */
.ai-page-title {
    font-family: 'Fira Code', monospace !important;
    font-size: 2.2rem !important;
    font-weight: 700 !important;
    background: linear-gradient(135deg, #3B82F6 0%, #60A5FA 55%, #F59E0B 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -0.5px;
    line-height: 1.2;
    margin-bottom: 0.2rem;
}

.ai-page-subtitle {
    color: var(--ai-text-secondary);
    font-size: 0.95rem;
    font-weight: 400;
    margin-bottom: 2rem;
    display: flex;
    align-items: center;
    gap: 6px;
}

/* ==========================================
   状态徽章
   ========================================== */
.ai-badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.3px;
}
.ai-badge-blue   { background: var(--ai-primary-glow);  color: var(--ai-primary);  border: 1px solid var(--ai-border); }
.ai-badge-amber  { background: var(--ai-accent-glow);   color: var(--ai-accent);   border: 1px solid rgba(245,158,11,0.3); }
.ai-badge-green  { background: rgba(16,185,129,0.12);   color: var(--ai-success);  border: 1px solid rgba(16,185,129,0.3); }
.ai-badge-red    { background: rgba(239,68,68,0.12);    color: var(--ai-danger);   border: 1px solid rgba(239,68,68,0.3); }

/* ==========================================
   分割线
   ========================================== */
.ai-divider {
    border: none;
    border-top: 1px solid var(--ai-border-muted);
    margin: 1.5rem 0;
}

/* ==========================================
   侧边栏
   ========================================== */
[data-testid="stSidebar"] {
    background: var(--ai-bg-sidebar) !important;
    border-right: 1px solid var(--ai-border) !important;
}
[data-testid="stSidebar"] .stMarkdown p {
    color: var(--ai-text-secondary) !important;
}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
    gap: 0.25rem;
}

/* ==========================================
   输入框 & 文本域
   ========================================== */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background-color: #1E293B !important;
    border: 1px solid var(--ai-border) !important;
    border-radius: var(--ai-radius-sm) !important;
    color: var(--ai-text-primary) !important;
    font-family: 'Fira Sans', sans-serif !important;
    transition: var(--ai-transition) !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--ai-primary) !important;
    box-shadow: 0 0 0 3px var(--ai-primary-glow) !important;
}

/* ==========================================
   主按钮
   ========================================== */
.stButton > button[kind="primary"],
.stButton > button[data-testid="baseButton-primary"] {
    background: linear-gradient(135deg, #1E40AF 0%, #3B82F6 100%) !important;
    border: none !important;
    border-radius: var(--ai-radius-sm) !important;
    color: white !important;
    font-family: 'Fira Sans', sans-serif !important;
    font-weight: 600 !important;
    letter-spacing: 0.3px !important;
    padding: 0.55rem 1.5rem !important;
    transition: var(--ai-transition) !important;
}
.stButton > button[kind="primary"]:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4) !important;
}

/* 次要按钮 */
.stButton > button[kind="secondary"] {
    background: transparent !important;
    border: 1px solid var(--ai-border-strong) !important;
    border-radius: var(--ai-radius-sm) !important;
    color: var(--ai-primary) !important;
    font-weight: 500 !important;
    transition: var(--ai-transition) !important;
}
.stButton > button[kind="secondary"]:hover {
    background: var(--ai-primary-glow) !important;
    border-color: var(--ai-primary) !important;
}

/* ==========================================
   指标卡片
   ========================================== */
[data-testid="stMetric"] {
    background: var(--ai-bg-card) !important;
    border: 1px solid var(--ai-border) !important;
    border-radius: var(--ai-radius-md) !important;
    padding: 1rem 1.25rem !important;
    transition: var(--ai-transition) !important;
}
[data-testid="stMetric"]:hover {
    border-color: var(--ai-border-strong) !important;
    box-shadow: var(--ai-shadow-glow) !important;
}
[data-testid="stMetricValue"] {
    font-family: 'Fira Code', monospace !important;
    font-weight: 700 !important;
    color: var(--ai-primary) !important;
    font-size: 1.6rem !important;
}
[data-testid="stMetricLabel"] {
    color: var(--ai-text-secondary) !important;
    font-size: 0.8rem !important;
    font-weight: 500 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
}

/* ==========================================
   Tab 页
   ========================================== */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: var(--ai-bg-card);
    border-radius: var(--ai-radius-md);
    padding: 4px;
    border: 1px solid var(--ai-border);
}
.stTabs [data-baseweb="tab"] {
    border-radius: var(--ai-radius-sm) !important;
    padding: 8px 20px !important;
    font-family: 'Fira Sans', sans-serif !important;
    font-size: 0.875rem !important;
    font-weight: 500 !important;
    color: var(--ai-text-secondary) !important;
    transition: var(--ai-transition) !important;
    border: none !important;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #1E40AF, #3B82F6) !important;
    color: white !important;
}

/* ==========================================
   数据表格
   ========================================== */
[data-testid="stDataFrame"] {
    border: 1px solid var(--ai-border) !important;
    border-radius: var(--ai-radius-md) !important;
    overflow: hidden !important;
}
[data-testid="stDataFrame"] th {
    background: var(--ai-bg-card) !important;
    color: var(--ai-text-secondary) !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    font-size: 0.75rem !important;
    letter-spacing: 0.5px !important;
}

/* ==========================================
   展开面板
   ========================================== */
.streamlit-expanderHeader {
    background: var(--ai-bg-card) !important;
    border: 1px solid var(--ai-border) !important;
    border-radius: var(--ai-radius-sm) !important;
    color: var(--ai-text-primary) !important;
    font-weight: 500 !important;
}

/* ==========================================
   进度/信息提示
   ========================================== */
[data-testid="stAlert"] {
    border-radius: var(--ai-radius-sm) !important;
    border-left-width: 3px !important;
}

/* ==========================================
   滚动条
   ========================================== */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--ai-bg-page); }
::-webkit-scrollbar-thumb { background: var(--ai-border-strong); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--ai-primary); }

/* ==========================================
   侧边栏导航链接
   ========================================== */
.sidebar-nav-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 14px;
    border-radius: var(--ai-radius-sm);
    color: var(--ai-text-secondary);
    font-weight: 500;
    font-size: 0.9rem;
    transition: var(--ai-transition);
    margin-bottom: 4px;
    cursor: pointer;
    text-decoration: none;
}
.sidebar-nav-item:hover {
    background: var(--ai-primary-glow);
    color: var(--ai-primary);
}
.sidebar-nav-item.active {
    background: var(--ai-primary-glow);
    color: var(--ai-primary);
    border-left: 3px solid var(--ai-primary);
}

/* ==========================================
   章节标题
   ========================================== */
.section-title {
    font-family: 'Fira Sans', sans-serif;
    font-size: 1rem;
    font-weight: 600;
    color: var(--ai-text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 8px;
}
.section-title::after {
    content: '';
    flex: 1;
    height: 1px;
    background: var(--ai-border-muted);
}
</style>
"""


def inject_global_styles():
    """在页面中注入全局 CSS 样式，所有页面统一调用。"""
    st.markdown(COMMON_STYLES, unsafe_allow_html=True)


def page_title(title: str, subtitle: str = ""):
    """渲染统一风格的页面标题组件。"""
    html = f'<div class="ai-page-title">{title}</div>'
    if subtitle:
        html += f'<div class="ai-page-subtitle">{subtitle}</div>'
    st.markdown(html, unsafe_allow_html=True)


def section_header(label: str):
    """渲染章节分组标题。"""
    st.markdown(f'<div class="section-title">{label}</div>', unsafe_allow_html=True)


def risk_badge(level: str) -> str:
    """返回风险等级徽章 HTML。level: 'high' | 'medium' | 'low'"""
    mapping = {
        "high":   ("ai-badge-red",   "高风险"),
        "medium": ("ai-badge-amber", "中风险"),
        "low":    ("ai-badge-green", "低风险"),
    }
    cls, text = mapping.get(level, ("ai-badge-blue", level))
    return f'<span class="ai-badge {cls}">{text}</span>'

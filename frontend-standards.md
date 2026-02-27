# Frontend Standards — 合规优化智能体 UI 样式规范

> **适用范围**: 所有基于 Streamlit 构建的 AI 驱动项目前端界面
> **版本**: v1.0.0 | 创建于 2026-02-27

---

## 一、设计哲学

本规范基于以下三条核心原则：

1. **数据至上 (Data First)** — 界面服务于数据展示，减少视觉噪音
2. **专业可信 (Professional Trust)** — 深色调 + 品牌蓝，传递 AI 专业感
3. **清晰层次 (Clear Hierarchy)** — 通过字号、颜色、间距建立明确的信息层级

---

## 二、CSS 变量系统（全局令牌）

```css
/* =====================================================
   合规优化智能体 — 全局 CSS 设计令牌
   在 st.markdown(..., unsafe_allow_html=True) 中注入
   ===================================================== */
:root {
    /* --- 品牌色 --- */
    --ai-primary:          #3B82F6;   /* 品牌蓝：主按钮、强调 */
    --ai-primary-dark:     #1E40AF;   /* 深蓝：Hover 状态 */
    --ai-primary-glow:     rgba(59, 130, 246, 0.15);  /* 蓝色光晕 */
    --ai-accent:           #F59E0B;   /* 琥珀：高优预警、徽章 */
    --ai-accent-light:     rgba(245, 158, 11, 0.15);  /* 琥珀浅色背景 */
    --ai-success:          #10B981;   /* 绿色：通过/安全 */
    --ai-warning:          #F59E0B;   /* 橙色：中等风险 */
    --ai-danger:           #EF4444;   /* 红色：高风险/错误 */

    /* --- 背景色 --- */
    --ai-bg-page:          #0A0F1E;   /* 页面主背景：深空黑 */
    --ai-bg-card:          #0F172A;   /* 卡片背景：深蓝黑 */
    --ai-bg-card-hover:    #1E293B;   /* 卡片 Hover：浅一层 */
    --ai-bg-input:         #1E293B;   /* 输入框背景 */
    --ai-bg-sidebar:       #080D1A;   /* 侧边栏背景 */

    /* --- 文字色 --- */
    --ai-text-primary:     #E2E8F0;   /* 主文字：高对比 */
    --ai-text-secondary:   #94A3B8;   /* 次要文字：标签/说明 */
    --ai-text-muted:       #64748B;   /* 低调文字：时间/版本号 */
    --ai-text-inverse:     #FFFFFF;   /* 反色：深底白字 */

    /* --- 边框 --- */
    --ai-border:           rgba(59, 130, 246, 0.2);   /* 常规边框 */
    --ai-border-strong:    rgba(59, 130, 246, 0.4);   /* 强调边框 */
    --ai-border-muted:     rgba(255, 255, 255, 0.06); /* 低调分割线 */

    /* --- 圆角 --- */
    --ai-radius-sm:        6px;
    --ai-radius-md:        12px;
    --ai-radius-lg:        16px;
    --ai-radius-xl:        24px;

    /* --- 间距 --- */
    --ai-spacing-xs:       4px;
    --ai-spacing-sm:       8px;
    --ai-spacing-md:       16px;
    --ai-spacing-lg:       24px;
    --ai-spacing-xl:       40px;

    /* --- 阴影 --- */
    --ai-shadow-card:      0 4px 24px rgba(0, 0, 0, 0.4);
    --ai-shadow-glow:      0 0 20px rgba(59, 130, 246, 0.2);
    --ai-shadow-accent:    0 0 20px rgba(245, 158, 11, 0.15);

    /* --- 过渡动画 --- */
    --ai-transition:       all 0.2s ease;
    --ai-transition-slow:  all 0.4s ease;
}
```

---

## 三、颜色系统

| 用途 | 变量名 | Hex 值 | 说明 |
|:---|:---|:---|:---|
| 主色 / 品牌蓝 | `--ai-primary` | `#3B82F6` | 主按钮、链接、强调边框 |
| 深蓝 / Hover | `--ai-primary-dark` | `#1E40AF` | 悬停状态 |
| 琥珀高亮 | `--ai-accent` | `#F59E0B` | 预警标签、重要数字 |
| 成功绿 | `--ai-success` | `#10B981` | 分析通过、连接正常 |
| 危险红 | `--ai-danger` | `#EF4444` | 高风险专利、连接失败 |
| 页面背景 | `--ai-bg-page` | `#0A0F1E` | 最深层背景 |
| 卡片背景 | `--ai-bg-card` | `#0F172A` | 内容卡片 |
| 主文字 | `--ai-text-primary` | `#E2E8F0` | 正文 |
| 次要文字 | `--ai-text-secondary` | `#94A3B8` | 标签/描述 |

---

## 四、字体规范

| 场景 | 字体 | 权重 | 示例用途 |
|:---|:---|:---|:---|
| 主标题（H1） | Fira Code | 700 | 页面大标题 |
| 副标题（H2-H3） | Fira Sans | 600 | 章节标题 |
| 正文 | Fira Sans | 400 | 内容段落 |
| 标签/说明 | Fira Sans | 300 | 辅助说明文字 |
| 数据/代码 | Fira Code | 400 | 指标数值、代码片段 |

**Google Fonts 引入方式:**

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;600;700&family=Fira+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
```

---

## 五、组件样式规范

### 5.1 对话框 / 用户&AI 消息

| 发送者 | 对齐 | 背景 | 文字 | 特征 |
|:---|:---|:---|:---|:---|
| 用户 | 右对齐 | `--ai-primary` (#3B82F6) | 白色 | 蓝色实心气泡，圆角 12px |
| AI 回复 | 左对齐 | `--ai-bg-card` (#0F172A) | `--ai-text-primary` | 深色背景 + 左侧蓝色竖线 |

```css
/* 用户消息 */
.msg-user {
    background: var(--ai-primary);
    color: white;
    border-radius: var(--ai-radius-md);
    margin-left: 20%;
    padding: 12px 16px;
}

/* AI 消息 */
.msg-ai {
    background: var(--ai-bg-card);
    color: var(--ai-text-primary);
    border-left: 3px solid var(--ai-primary);
    border-radius: 0 var(--ai-radius-md) var(--ai-radius-md) 0;
    margin-right: 20%;
    padding: 12px 16px;
}
```

### 5.2 指标卡片（Metric Card）

```css
.metric-card {
    background: var(--ai-bg-card);
    border: 1px solid var(--ai-border);
    border-radius: var(--ai-radius-md);
    padding: var(--ai-spacing-lg);
    box-shadow: var(--ai-shadow-card);
    transition: var(--ai-transition);
}
.metric-card:hover {
    border-color: var(--ai-border-strong);
    box-shadow: var(--ai-shadow-glow);
    transform: translateY(-2px);
}
```

### 5.3 风险等级徽章（Risk Badge）

```css
.badge-high   { background: rgba(239, 68, 68, 0.15);  color: #EF4444; border: 1px solid rgba(239,68,68,0.3); }
.badge-medium { background: rgba(245,158,11, 0.15);   color: #F59E0B; border: 1px solid rgba(245,158,11,0.3); }
.badge-low    { background: rgba(16, 185,129, 0.15);  color: #10B981; border: 1px solid rgba(16,185,129,0.3); }

/* 通用 */
[class^="badge-"] {
    padding: 2px 8px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
}
```

---

## 六、Streamlit 集成

### 6.1 `config.toml` 主题配置

```toml
# .streamlit/config.toml
[theme]
primaryColor         = "#3B82F6"   # 品牌蓝
backgroundColor      = "#0A0F1E"   # 深空黑
secondaryBackgroundColor = "#0F172A"  # 卡片深蓝黑
textColor            = "#E2E8F0"   # 主文字
font                 = "sans serif"
```

### 6.2 注入全局样式的标准方式

```python
import streamlit as st

# 在每个页面顶部调用此函数
def inject_global_styles():
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# GLOBAL_CSS 定义在 frontend/styles.py 中统一维护
```

### 6.3 统一 `styles.py` 模块

建议创建 `frontend/styles.py`，集中管理所有 CSS，各页面 import 调用，避免重复代码。

---

## 七、布局规范

| 区域 | 说明 |
|:---|:---|
| 侧边栏宽度 | Streamlit 默认（约 288px），不建议修改 |
| 内容区最大宽度 | `layout="wide"` 模式下自动撑满 |
| 卡片内边距 | `padding: 1.5rem`（24px） |
| 章节间距 | `margin-bottom: 2rem`（32px） |
| 栅格列比例 | 2:1（输入区）/ 1:1:1:1（指标卡） |

---

## 八、图表规范（Plotly）

```python
# 全项目统一的 Plotly 图表主题设置
PLOTLY_THEME = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",   # 透明背景，融入页面
    plot_bgcolor="rgba(15,23,42,0.8)",
    font=dict(family="Fira Sans", color="#E2E8F0"),
    colorway=["#3B82F6", "#F59E0B", "#10B981", "#EF4444", "#8B5CF6"],
)
```

---

## 九、交互规范

| 元素 | 规则 |
|:---|:---|
| 所有可点击元素 | `cursor: pointer` |
| 悬停过渡 | `transition: all 0.2s ease` |
| 按钮悬停 | 亮度提升 + 细微上移 `translateY(-1px)` |
| 加载状态 | 使用 `st.spinner()` + 中文提示 |
| 成功/错误 | `st.success()` / `st.error()` 配合中文文案 |

---

## 十、文案规范（中文化标准）

| 原文（英文） | 规范中文用法 |
|:---|:---|
| Analyze | 开始分析 |
| Loading... | 正在加载... |
| Error | 发生错误 |
| Submit | 提交 |
| Patent Count | 专利数量 |
| CAGR | 年复合增长率（CAGR） |
| Status: success | 状态：已完成 |
| No data | 暂无数据 |

---

## 附录：Streamlit 样式注入模板

```python
# frontend/styles.py — 统一样式模块

COMMON_STYLES = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;600;700&family=Fira+Sans:wght@300;400;500;600;700&display=swap');

/* CSS 变量 */
:root {
    --ai-primary: #3B82F6;
    --ai-bg-card: #0F172A;
    --ai-bg-page: #0A0F1E;
    --ai-text-primary: #E2E8F0;
    --ai-text-secondary: #94A3B8;
    --ai-accent: #F59E0B;
    --ai-border: rgba(59, 130, 246, 0.2);
    --ai-radius-md: 12px;
    --ai-shadow-glow: 0 0 20px rgba(59, 130, 246, 0.2);
    --ai-transition: all 0.2s ease;
}

body { font-family: 'Fira Sans', sans-serif !important; }

/* 页面标题 */
.ai-page-title {
    font-family: 'Fira Code', monospace;
    font-size: 2.2rem;
    font-weight: 700;
    background: linear-gradient(135deg, #3B82F6 0%, #60A5FA 50%, #F59E0B 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -0.5px;
    margin-bottom: 0.25rem;
}

/* 页面副标题 */
.ai-page-subtitle {
    color: #94A3B8;
    font-size: 0.95rem;
    margin-bottom: 2rem;
}

/* 内容卡片 */
.ai-card {
    background: #0F172A;
    border: 1px solid rgba(59, 130, 246, 0.2);
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.4);
    transition: all 0.2s ease;
}
.ai-card:hover {
    border-color: rgba(59, 130, 246, 0.4);
    box-shadow: 0 0 20px rgba(59, 130, 246, 0.2);
}

/* 分割线 */
.ai-divider {
    border: none;
    border-top: 1px solid rgba(255, 255, 255, 0.06);
    margin: 1.5rem 0;
}

/* Tab 样式 */
.stTabs [data-baseweb="tab-list"] { gap: 4px; }
.stTabs [data-baseweb="tab"] {
    padding: 8px 20px;
    border-radius: 8px;
    font-family: 'Fira Sans', sans-serif;
    font-weight: 500;
}

/* 指标数值 */
[data-testid="stMetricValue"] {
    font-family: 'Fira Code', monospace !important;
    font-weight: 700 !important;
    color: #3B82F6 !important;
}

/* 输入框 */
.stTextInput input, .stTextArea textarea {
    background: #1E293B !important;
    border: 1px solid rgba(59, 130, 246, 0.3) !important;
    border-radius: 8px !important;
    color: #E2E8F0 !important;
    font-family: 'Fira Sans', sans-serif !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: rgba(59, 130, 246, 0.7) !important;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15) !important;
}

/* 主按钮 */
.stButton button[kind="primary"] {
    background: linear-gradient(135deg, #1E40AF, #3B82F6) !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    letter-spacing: 0.3px !important;
    transition: all 0.2s ease !important;
}
.stButton button[kind="primary"]:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 16px rgba(59, 130, 246, 0.4) !important;
}

/* 侧边栏 */
[data-testid="stSidebar"] {
    background: #080D1A !important;
    border-right: 1px solid rgba(59, 130, 246, 0.15) !important;
}

/* 数据表格 */
[data-testid="stDataFrame"] {
    border: 1px solid rgba(59, 130, 246, 0.2) !important;
    border-radius: 8px !important;
}
</style>
"""
```

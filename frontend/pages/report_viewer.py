"""
报告查看器 — 渲染 AI 生成的窗口期预警简报（Markdown 格式）
"""
import sys
import os
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from frontend.styles import inject_global_styles, page_title, section_header
from frontend.sidebar import render_sidebar

st.set_page_config(
    page_title="分析报告 | 合规优化智能体", page_icon="🔍", layout="wide"
)
inject_global_styles()
render_sidebar()

page_title("窗口期预警简报", "AI 深度分析报告 — 专利壁垒 × 市场趋势 × 进入时机研判")


def render_report_viewer():
    """渲染报告查看器"""

    if "latest_result" not in st.session_state:
        st.info("尚未运行分析。请先前往「分析看板」主页，输入产品关键词并启动分析。")
        st.markdown("<br>", unsafe_allow_html=True)
        section_header("示例报告预览")
        st.markdown(_example_report())
        return

    result = st.session_state["latest_result"]
    report = result.get("final_report", "")

    if not report:
        st.warning("当前分析结果暂无报告内容，请确认分析已正常完成")
        return

    # 报告信息栏
    section_header("报告基本信息")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("分析关键词", result.get("query", "—"))
    with col2:
        status_map = {"success": "✅ 已完成", "error": "❌ 失败"}
        raw = result.get("status", "unknown")
        st.metric("分析状态", status_map.get(raw, raw))
    with col3:
        st.metric("AI 审核迭代次数", result.get("iterations", 0))

    st.markdown("<br>", unsafe_allow_html=True)

    # 报告正文
    section_header("报告正文")
    st.markdown(report)

    # 下载区
    st.markdown("<br>", unsafe_allow_html=True)
    section_header("导出报告")
    dl1, dl2 = st.columns(2)
    with dl1:
        st.download_button(
            label="下载 Markdown 报告",
            data=report,
            file_name=f"合规分析报告_{result.get('query', 'analysis')}.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with dl2:
        import json
        st.download_button(
            label="下载完整数据（JSON）",
            data=json.dumps(result, ensure_ascii=False, indent=2),
            file_name=f"合规分析数据_{result.get('query', 'analysis')}.json",
            mime="application/json",
            use_container_width=True,
        )


def _example_report() -> str:
    """示例报告模板"""
    return """
# 窗口期预警简报 — Smart Ring 赛道分析

> **报告类型**: AI 合规分析 | **生成时间**: 2026-02-27 | **分析迭代**: 2 轮

---

## 一、执行摘要

当前 Smart Ring 赛道处于**早期增长期**，专利壁垒集中在传感器技术和健康监测算法，
但 AI 推理成本大幅下降为新进入者提供了差异化切入机会。

**核心结论**: 建议在未来 6 个月内启动产品研发，抢占专利空白区域。

---

## 二、专利格局分析

| 公司 | 专利数量 | 核心技术方向 | 风险评估 |
|:---|:---:|:---|:---:|
| Apple Inc. | 15 | 健康传感器、手势识别 | 🔴 高 |
| Samsung | 12 | 生物信号处理 | 🔴 高 |
| Oura Ring | 8 | 睡眠监测、温度传感 | 🟡 中 |
| Garmin | 5 | 运动追踪、GPS | 🟢 低 |

---

## 三、市场趋势解读

- Smart Ring 搜索量 **CAGR: 45.2%**（过去 36 个月）
- "AI wearable" 相关词汇月均增长 **3.1%**
- 用户对健康监测功能关注度持续上升

---

## 四、窗口期判断

**为什么现在是最佳入局时机？**

1. AI 端侧推理成本下降 80%，设备智能成为可能
2. MEMS 传感器模组价格持续下降，硬件门槛降低
3. 后疫情消费者健康意识显著增强
4. 核心专利申请高峰期已过，仍有大量空白技术方向

---

## 五、风险矩阵

| 风险类型 | 风险等级 | 规避策略 |
|:---|:---:|:---|
| Apple 传感器专利密集区 | 🔴 高 | 聚焦 AI 软件层，绕开硬件专利 |
| 传感器供应链集中 | 🟡 中 | 多元化供应商策略 |
| 差异化竞争空间 | 🟢 低 | AI 健康洞察是蓝海方向 |

---

## 六、行动建议

1. **聚焦 AI 健康洞察**：以算法优势建立软性护城河
2. **规避高密区**：Apple 传感器专利布局密集，选择外围突破
3. **早期供应商合作**：与 MEMS 传感器供应商建立战略关系
4. **尽快启动专利申请**：在 AI 赋能健康分析领域抢先布局
"""


render_report_viewer()

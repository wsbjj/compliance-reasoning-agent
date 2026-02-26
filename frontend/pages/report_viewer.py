"""
AI 报告查看器

渲染 Markdown 格式的窗口期预警简报
"""
import streamlit as st

st.set_page_config(page_title="AI 分析报告", page_icon="🔍", layout="wide")

st.title("🔍 窗口期预警简报")
st.markdown("AI 深度分析报告 — 专利壁垒 × 市场趋势 × 进入时机")


def render_report_viewer():
    """渲染报告查看器"""

    # 检查分析结果
    if "latest_result" not in st.session_state:
        st.info("请先在主页运行分析任务")

        # 展示示例报告
        st.markdown("---")
        st.markdown("### 📄 示例报告预览")
        st.markdown(_example_report())
        return

    result = st.session_state["latest_result"]
    report = result.get("final_report", "")

    if not report:
        st.warning("暂无分析报告")
        return

    # 报告信息栏
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("查询关键词", result.get("query", "N/A"))
    with col2:
        st.metric("分析状态", result.get("status", "unknown"))
    with col3:
        st.metric("审核迭代", result.get("iterations", 0))

    st.markdown("---")

    # 报告正文
    st.markdown(report)

    # 下载按钮
    st.markdown("---")
    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        st.download_button(
            label="📥 下载 Markdown 报告",
            data=report,
            file_name=f"compliance_report_{result.get('query', 'analysis')}.md",
            mime="text/markdown",
        )
    with col_dl2:
        # 完整结果 JSON
        import json

        st.download_button(
            label="📥 下载完整数据 (JSON)",
            data=json.dumps(result, ensure_ascii=False, indent=2),
            file_name=f"compliance_data_{result.get('query', 'analysis')}.json",
            mime="application/json",
        )


def _example_report() -> str:
    """示例报告模板"""
    return """
# 窗口期预警简报 — Smart Ring 赛道分析

## 1. 执行摘要
当前 Smart Ring 赛道处于**早期增长期**，专利壁垒集中在传感器技术和健康监测算法，
但 AI 成本大幅下降为新进入者提供了差异化机会。**建议在未来 6 个月内启动产品研发**。

## 2. 专利格局分析
| 公司 | 专利数量 | 核心技术方向 |
|------|---------|------------|
| Apple | 15 | 健康传感器、手势识别 |
| Samsung | 12 | 生物信号处理 |
| Oura | 8 | 睡眠监测、温度传感 |

## 3. 市场趋势解读
- Smart Ring 搜索指数 **CAGR: 45.2%**
- Wearable Health 搜索量持续上升

## 4. 窗口期判断
**为什么是现在？**
1. AI 推理成本下降 80%，使设备端智能成为可能
2. 传感器模组价格持续下降
3. 消费者健康意识后疫情时代持续增强

## 5. 风险评估
- 🔴 Apple 专利布局较密
- 🟡 供应链垄断风险
- 🟢 差异化空间仍然存在

## 6. 行动建议
1. 聚焦 **AI 健康洞察** 差异化定位
2. 规避 Apple 核心专利区域
3. 与传感器供应商建立早期合作
"""


render_report_viewer()

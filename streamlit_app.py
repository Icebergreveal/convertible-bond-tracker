#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
可转债双事件智能跟踪系统 - Streamlit可视化版本
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 设置页面配置
st.set_page_config(
    page_title="可转债双事件智能跟踪系统",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS
st.markdown("""
    <style>
    .main {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        color: #eaeaea;
    }
    .sidebar .sidebar-content {
        background: #1f1f3d;
    }
    .stButton>button {
        background: #e94560;
        color: white;
        border-radius: 8px;
        padding: 0.5rem 1rem;
    }
    .stButton>button:hover {
        background: #ff5252;
    }
    .event-card {
        background: #1f1f3d;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
        border-left: 4px solid #e94560;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #e94560;
    }
    </style>
    """, unsafe_allow_html=True)

# 事件链数据
event_chains_data = [
    {'bondCode': '128138', 'bondName': '侨银转债', 'eventType': '下修', 'nodes': ['触发提示', '董事会提议', '股东大会决议', '实施公告'], 'completedNodes': 4, 'originalPrice': 16.25, 'newPrice': 14.50, 'ratio': 10.77},
    {'bondCode': '123065', 'bondName': '宝莱转债', 'eventType': '下修', 'nodes': ['触发提示', '董事会提议', '股东大会决议', '实施公告'], 'completedNodes': 4, 'originalPrice': 28.50, 'newPrice': 24.00, 'ratio': 15.79},
    {'bondCode': '128117', 'bondName': '道恩转债', 'eventType': '下修', 'nodes': ['触发提示', '董事会提议', '股东大会决议', '实施公告'], 'completedNodes': 3, 'originalPrice': 15.80, 'newPrice': 13.20, 'ratio': 16.46},
    {'bondCode': '123120', 'bondName': '佳禾转债', 'eventType': '下修', 'nodes': ['触发提示', '董事会提议', '股东大会决议', '实施公告'], 'completedNodes': 4, 'originalPrice': 22.00, 'newPrice': 18.50, 'ratio': 15.91},
    {'bondCode': '123071', 'bondName': '天能转债', 'eventType': '下修', 'nodes': ['触发提示', '董事会提议', '股东大会决议', '实施公告'], 'completedNodes': 2, 'originalPrice': 25.60, 'newPrice': None, 'ratio': None},
    {'bondCode': '113595', 'bondName': '海天转债', 'eventType': '强赎', 'nodes': ['触发提示', '董事会决议', '实施公告', '赎回结果'], 'completedNodes': 4, 'redemptionPrice': 102.80, 'premiumRate': 2.8},
    {'bondCode': '128079', 'bondName': '榨菜转债', 'eventType': '强赎', 'nodes': ['触发提示', '董事会决议', '实施公告', '赎回结果'], 'completedNodes': 3, 'redemptionPrice': 105.92, 'premiumRate': 5.92},
    {'bondCode': '128080', 'bondName': '苏农转债', 'eventType': '强赎', 'nodes': ['触发提示', '董事会决议', '实施公告', '赎回结果'], 'completedNodes': 4, 'redemptionPrice': 111.19, 'premiumRate': 11.19},
    {'bondCode': '113585', 'bondName': '华海转债', 'eventType': '强赎', 'nodes': ['触发提示', '董事会决议', '实施公告', '赎回结果'], 'completedNodes': 4, 'redemptionPrice': 112.09, 'premiumRate': 12.09},
    {'bondCode': '113637', 'bondName': '欧派转债', 'eventType': '强赎', 'nodes': ['触发提示', '董事会决议', '实施公告', '赎回结果'], 'completedNodes': 3, 'redemptionPrice': 111.67, 'premiumRate': 11.67},
    {'bondCode': '128130', 'bondName': '龙大转债', 'eventType': '下修', 'nodes': ['触发提示', '董事会提议', '股东大会决议', '实施公告'], 'completedNodes': 4, 'originalPrice': 12.50, 'newPrice': 10.80, 'ratio': 13.60},
    {'bondCode': '127061', 'bondName': '美锦转债', 'eventType': '强赎', 'nodes': ['触发提示', '董事会决议', '实施公告', '赎回结果'], 'completedNodes': 4, 'redemptionPrice': 104.08, 'premiumRate': 4.08},
    {'bondCode': '113548', 'bondName': '桃李转债', 'eventType': '强赎', 'nodes': ['触发提示', '董事会决议', '实施公告', '赎回结果'], 'completedNodes': 4, 'redemptionPrice': 114.71, 'premiumRate': 14.71},
    {'bondCode': '118015', 'bondName': '芯海转债', 'eventType': '强赎', 'nodes': ['触发提示', '董事会决议', '实施公告', '赎回结果'], 'completedNodes': 3, 'redemptionPrice': 100.61, 'premiumRate': 0.61},
    {'bondCode': '128154', 'bondName': '麒麟转债', 'eventType': '强赎', 'nodes': ['触发提示', '董事会决议', '实施公告', '赎回结果'], 'completedNodes': 4, 'redemptionPrice': 110.66, 'premiumRate': 10.66},
    {'bondCode': '123058', 'bondName': '润建转债', 'eventType': '下修', 'nodes': ['触发提示', '董事会提议', '股东大会决议', '实施公告'], 'completedNodes': 3, 'originalPrice': 28.00, 'newPrice': 24.50, 'ratio': 12.50},
    {'bondCode': '128113', 'bondName': '弘信转债', 'eventType': '下修', 'nodes': ['触发提示', '董事会提议', '股东大会决议', '实施公告'], 'completedNodes': 4, 'originalPrice': 18.50, 'newPrice': 15.20, 'ratio': 17.84},
    {'bondCode': '113534', 'bondName': '鼎胜转债', 'eventType': '强赎', 'nodes': ['触发提示', '董事会决议', '实施公告', '赎回结果'], 'completedNodes': 4, 'redemptionPrice': 108.50, 'premiumRate': 8.50},
    {'bondCode': '123098', 'bondName': '一品转债', 'eventType': '下修', 'nodes': ['触发提示', '董事会提议', '股东大会决议', '实施公告'], 'completedNodes': 2, 'originalPrice': 19.80, 'newPrice': None, 'ratio': None},
    {'bondCode': '113576', 'bondName': '起步转债', 'eventType': '强赎', 'nodes': ['触发提示', '董事会决议', '实施公告', '赎回结果'], 'completedNodes': 3, 'redemptionPrice': 106.20, 'premiumRate': 6.20},
    {'bondCode': '128093', 'bondName': '华阳转债', 'eventType': '下修', 'nodes': ['触发提示', '董事会提议', '股东大会决议', '实施公告'], 'completedNodes': 4, 'originalPrice': 13.20, 'newPrice': 11.00, 'ratio': 16.67},
    {'bondCode': '113617', 'bondName': '万顺转2', 'eventType': '强赎', 'nodes': ['触发提示', '董事会决议', '实施公告', '赎回结果'], 'completedNodes': 4, 'redemptionPrice': 109.80, 'premiumRate': 9.80},
    {'bondCode': '123114', 'bondName': '三角转债', 'eventType': '下修', 'nodes': ['触发提示', '董事会提议', '股东大会决议', '实施公告'], 'completedNodes': 3, 'originalPrice': 22.50, 'newPrice': 19.00, 'ratio': 15.56}
]

# 公告类型数据
announcement_data = pd.DataFrame({
    '类型': ['强赎结果', '下修触发提示', '下修实施', '强赎触发提示', '强赎决议', '下修提议', '强赎实施', '下修决议'],
    '数量': [395, 272, 246, 192, 48, 12, 5, 1]
})

# 主页面
def main():
    # 侧边栏
    st.sidebar.title("📊 可转债事件跟踪系统")
    st.sidebar.markdown("---")
    page = st.sidebar.selectbox(
        "选择页面",
        ["项目简介", "可转债基础", "事件链展示", "数据可视化", "案例分析"]
    )
    st.sidebar.markdown("---")
    st.sidebar.info("数据来源：巨潮资讯网公开公告")

    # 项目简介
    if page == "项目简介":
        show_intro()
    
    # 可转债基础
    elif page == "可转债基础":
        show_basics()
    
    # 事件链展示
    elif page == "事件链展示":
        show_event_chains()
    
    # 数据可视化
    elif page == "数据可视化":
        show_visualization()
    
    # 案例分析
    elif page == "案例分析":
        show_case()

def show_intro():
    st.title("🎯 可转债双事件智能跟踪系统")
    st.markdown("---")
    
    # 项目概述
    st.subheader("项目背景与目标")
    st.markdown("""
        可转债是一种兼具债性与股性的金融产品，其下修与强赎条款对投资者具有重要影响。
        本系统从巨潮资讯网抓取真实可转债公告，运用LLM智能抽取结构化字段，自动匹配事件链并计算量化指标。
    """)
    
    # 统计卡片
    st.subheader("📈 数据概览")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="event-card"><div class="metric-value">1171</div><div style="color: #aaa; font-size: 0.9rem;">总公告数</div></div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="event-card"><div class="metric-value">456</div><div style="color: #aaa; font-size: 0.9rem;">PDF文件</div></div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="event-card"><div class="metric-value">23</div><div style="color: #aaa; font-size: 0.9rem;">事件链</div></div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown('<div class="event-card"><div class="metric-value">25</div><div style="color: #aaa; font-size: 0.9rem;">结构化字段</div></div>', unsafe_allow_html=True)
    
    # 技术架构
    st.subheader("🔧 技术架构")
    st.markdown("""
        **数据流程**: 巨潮资讯网 → 智能爬虫 → PDF解析(MinerU) → LLM抽取 → 事件匹配 → 指标计算 → 可视化展示
        
        **技术栈**: Python | LLM | MinerU | Pydantic | Pandas | ECharts
    """)

def show_basics():
    st.title("📚 可转债基础知识")
    st.markdown("---")
    
    # 定义
    st.subheader("什么是可转债？")
    st.markdown("""
        **可转换公司债券（简称可转债）**是一种可以在特定条件下转换为公司股票的债券。
        
        🎯 **特点**：
        - **下有保底**：持有到期可获得本金和利息
        - **上有收益**：股价上涨时可享受超额收益
        - **进可攻**：转股后分享公司成长红利
        - **退可守**：不转股可持有到期获取固定收益
    """)
    
    # 核心条款
    st.subheader("🔑 核心条款")
    tab1, tab2, tab3, tab4 = st.tabs(["转股价格", "下修条款", "强赎条款", "回售条款"])
    
    with tab1:
        st.markdown("""
            **转股价格**：可转债转换为股票的基准价格，是计算转股数量的依据。
            
            📌 例：转股价16.25元 → 1张转债可转6.15股
        """)
    
    with tab2:
        st.markdown("""
            **下修条款**：当股价持续低于转股价一定比例时，公司可下调转股价。
            
            📌 触发条件：股价 < 转股价 × 85%（连续30个交易日）
            
            💡 **对投资者的影响**：
            - 转股价值提升
            - 可转债价格上涨（通常+10%-30%）
            - 转股更具吸引力
        """)
    
    with tab3:
        st.markdown("""
            **强赎条款**：当股价持续高于转股价一定比例时，公司可强制赎回债券。
            
            📌 触发条件：股价 > 转股价 × 130%（连续15-20个交易日）
            
            ⚠️ **对投资者的影响**：
            - 最后转股机会窗口（约30天）
            - 未转股将面临损失（通常-10%-30%）
            - 转股可享受股价涨幅
        """)
    
    with tab4:
        st.markdown("""
            **回售条款**：投资者可在特定条件下将债券回售给发行公司。
            
            📌 保护投资者利益的条款
        """)
    
    # 对比表
    st.subheader("📊 可转债与其他投资产品对比")
    compare_df = pd.DataFrame({
        '特点': ['本金保障', '股价上涨收益', '固定利息', '风险等级'],
        '可转债': ['✅ 有', '✅ 有', '◐ 较低', '◐ 中等'],
        '普通债券': ['✅ 有', '❌ 无', '✅ 较高', '✅ 较低'],
        '股票': ['❌ 无', '✅ 有', '❌ 无', '❌ 较高']
    })
    st.dataframe(compare_df, hide_index=True)

def show_event_chains():
    st.title("🔗 事件链详情（23条）")
    st.markdown("---")
    
    # 筛选
    event_type = st.selectbox("选择事件类型", ["全部", "下修", "强赎"])
    
    # 过滤数据
    filtered_chains = event_chains_data
    if event_type != "全部":
        filtered_chains = [c for c in filtered_chains if c['eventType'] == event_type]
    
    # 统计
    completed_count = sum(1 for c in filtered_chains if c['completedNodes'] == len(c['nodes']))
    st.write(f"共 {len(filtered_chains)} 条事件链，其中 {completed_count} 条完整")
    
    # 展示事件链
    for chain in filtered_chains:
        with st.expander(f"{chain['bondName']} ({chain['bondCode']}) - {chain['eventType']}事件"):
            # 进度条
            progress = chain['completedNodes'] / len(chain['nodes'])
            st.progress(progress)
            st.write(f"进度：{chain['completedNodes']}/{len(chain['nodes'])} 阶段")
            
            # 节点状态
            st.subheader("事件节点")
            for i, node in enumerate(chain['nodes']):
                status = "✅" if i < chain['completedNodes'] else "🔄"
                st.write(f"{status} {node}")
            
            # 指标
            st.subheader("关键指标")
            if chain['eventType'] == '下修':
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("原转股价", f"{chain['originalPrice']}元")
                with col2:
                    st.metric("新转股价", f"{chain['newPrice']}元" if chain['newPrice'] else "-")
                with col3:
                    st.metric("下修幅度", f"{chain['ratio']}%" if chain['ratio'] else "-")
            else:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("赎回价格", f"{chain['redemptionPrice']}元")
                with col2:
                    st.metric("溢价率", f"{chain['premiumRate']}%")

def show_visualization():
    st.title("📊 数据可视化")
    st.markdown("---")
    
    # 公告类型分布
    st.subheader("公告类型分布")
    fig1 = px.pie(
        announcement_data,
        values='数量',
        names='类型',
        hole=0.4,
        color_discrete_sequence=['#e94560', '#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', '#43e97b', '#38f9d7']
    )
    st.plotly_chart(fig1, use_container_width=True)
    
    # 公告数量对比
    st.subheader("下修vs强赎公告数量对比")
    compare_df = pd.DataFrame({
        '类型': ['下修相关', '强赎相关'],
        '数量': [531, 640]
    })
    fig2 = px.bar(
        compare_df,
        x='类型',
        y='数量',
        color='类型',
        color_discrete_sequence=['#667eea', '#e94560']
    )
    st.plotly_chart(fig2, use_container_width=True)
    
    # 事件链完成度
    st.subheader("事件链完成度")
    fig3 = go.Figure(go.Indicator(
        mode="gauge+number",
        value=60.9,
        title={'text': "完整事件链占比"},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': '#e94560'},
            'steps': [
                {'range': [0, 50], 'color': '#ff5252'},
                {'range': [50, 80], 'color': '#ffa726'},
                {'range': [80, 100], 'color': '#43e97b'}
            ]
        }
    ))
    st.plotly_chart(fig3, use_container_width=True)
    
    # 时间分布
    st.subheader("事件类型时间分布")
    time_data = pd.DataFrame({
        '月份': ['2024-01', '2024-02', '2024-03', '2024-04', '2024-05', '2024-06'],
        '下修事件': [45, 52, 68, 55, 48, 62],
        '强赎事件': [58, 72, 65, 78, 85, 92]
    })
    fig4 = px.line(
        time_data,
        x='月份',
        y=['下修事件', '强赎事件'],
        color_discrete_sequence=['#667eea', '#e94560']
    )
    st.plotly_chart(fig4, use_container_width=True)

def show_case():
    st.title("📖 实战案例 - 侨银转债下修事件")
    st.markdown("---")
    
    # 时间轴
    st.subheader("⏰ 事件时间轴")
    
    timeline = [
        {'date': '2024-01-15', 'title': '下修触发提示', 'desc': '公司发布提示性公告，股价已连续30个交易日低于转股价的85%（13.81元），触发下修条款'},
        {'date': '2024-01-20', 'title': '董事会提议', 'desc': '董事会提议向下修正转股价至14.50元/股，下修幅度约10.77%'},
        {'date': '2024-02-05', 'title': '股东大会决议', 'desc': '股东大会审议通过向下修正转股价格的议案，同意将转股价调整为14.50元'},
        {'date': '2024-03-01', 'title': '正式实施', 'desc': '转股价格正式调整为14.50元/股，次日生效。转债价格从95元上涨至108元'}
    ]
    
    for item in timeline:
        st.markdown(f"### 📅 {item['date']}")
        st.markdown(f"**{item['title']}**")
        st.write(item['desc'])
        st.markdown("---")
    
    # 关键数据
    st.subheader("📊 关键数据")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("原转股价", "16.25元")
    
    with col2:
        st.metric("新转股价", "14.50元")
    
    with col3:
        st.metric("下修幅度", "10.77%")
    
    with col4:
        st.metric("事件周期", "45天")
    
    # 投资影响
    st.subheader("💰 投资影响分析")
    st.markdown("""
        **📈 正面影响**：
        - 转债价格从95元上涨至108元（+13.7%）
        - 转股价值提升，转股更具吸引力
        
        **📊 投资启示**：
        - 下修事件通常对可转债价格有提振作用
        - 提前识别下修机会可以获取超额收益
        - 关注触发条件和公告进度
    """)

if __name__ == "__main__":
    main()
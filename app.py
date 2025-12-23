# -*- coding: utf-8 -*-
import streamlit as st
import requests
from bs4 import BeautifulSoup
import jieba
import re
from collections import Counter
from pyecharts import options as opts
from pyecharts.charts import WordCloud, Bar, Line, Pie, Radar, Scatter, Bar3D, Line3D
from streamlit_echarts import st_pyecharts
import warnings
warnings.filterwarnings("ignore")

# -------------------------- 页面基础设置 --------------------------
st.set_page_config(
    page_title="文本词频分析工具",
    layout="wide",  # 宽屏布局
    initial_sidebar_state="expanded"  # 侧边栏默认展开
)

# -------------------------- 内置停用词表（过滤无意义词汇） --------------------------
STOP_WORDS = {
    "的", "了", "是", "我", "你", "他", "她", "它", "们", "在", "有", "就", "不", "和", "也", "都", "这",
    "那", "其", "及", "与", "或", "但", "如果", "因为", "所以", "之", "于", "而", "则", "着", "过", "会",
    "要", "能", "可", "将", "对", "对于", "关于", "为", "为了", "以", "凭", "靠", "用", "通过", "就", "才",
    "还", "又", "更", "最", "很", "非常", "稍微", "比较", "一点", "一些", "个", "本", "该", "每", "各",
    "几", "多少", "谁", "什么", "哪里", "何时", "如何", "为什么", "啊", "呀", "呢", "吧", "吗", "哦", "嗯",
    "哈", "哎", "喂", "呃", "唔", "这", "里", "那", "里", "上", "下", "左", "右", "前", "后", "中", "间",
    "到", "从", "向", "往", "朝", "沿", "顺", "逆", "随", "跟", "同", "比", "比", "如", "像", "似", "若"
}

# -------------------------- 文本清洗与分词函数 --------------------------
def clean_and_cut_text(raw_text):
    """
    清洗文本（去HTML标签、标点、多余空格）+ 分词 + 过滤停用词/单字
    """
    # 1. 去除HTML标签
    text = re.sub(r'<[^>]+>', '', raw_text)
    # 2. 去除标点符号、特殊字符（保留中文）
    text = re.sub(r'[^\u4e00-\u9fa5\s]', '', text)
    # 3. 去除多余空格和换行
    text = re.sub(r'\s+', ' ', text).strip()
    # 4. jieba分词
    words = jieba.lcut(text)
    # 5. 过滤：停用词、单字、空字符串
    valid_words = [
        word for word in words 
        if word not in STOP_WORDS and len(word) > 1 and word.strip() != ""
    ]
    return valid_words

# -------------------------- URL文本抓取函数 --------------------------
def crawl_url_text(url):
    """
    抓取URL对应的网页文本内容
    """
    try:
        # 请求头（模拟浏览器，避免被反爬）
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        # 发送请求（超时10秒）
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # 抛出HTTP错误（如404、500）
        response.encoding = response.apparent_encoding  # 自动识别编码
        # 解析文本（提取p/h1-h6标签的文本，覆盖大部分文章内容）
        soup = BeautifulSoup(response.text, 'html.parser')
        text_parts = []
        # 提取标题
        for h in soup.find_all(['h1', 'h2', 'h3']):
            text_parts.append(h.get_text().strip())
        # 提取正文
        for p in soup.find_all('p'):
            text_parts.append(p.get_text().strip())
        # 拼接文本
        full_text = " ".join(text_parts)
        if not full_text:
            st.error("URL页面未提取到有效文本！")
            return ""
        return full_text
    except requests.exceptions.RequestException as e:
        st.error(f"URL抓取失败：{str(e)}")
        return ""

# -------------------------- 图表生成函数 --------------------------
def generate_chart(chart_type, top20_words):
    """
    根据选择的图表类型生成对应的pyecharts图表
    """
    words = [item[0] for item in top20_words]
    counts = [item[1] for item in top20_words]
    
    if chart_type == "词云":
        # 词云图
        wc = (
            WordCloud()
            .add("", list(zip(words, counts)), word_size_range=[20, 100])
            .set_global_opts(title_opts=opts.TitleOpts(title="词汇词云图", subtitle="词频越高，字体越大"))
        )
        return wc
    
    elif chart_type == "词频柱状图":
        # 柱状图
        bar = (
            Bar()
            .add_xaxis(words)
            .add_yaxis("词频", counts)
            .set_global_opts(
                title_opts=opts.TitleOpts(title="词频排名柱状图", subtitle="前20词汇"),
                xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=-45))  # X轴标签旋转，避免重叠
            )
        )
        return bar
    
    elif chart_type == "词频折线图":
        # 折线图
        line = (
            Line()
            .add_xaxis(words)
            .add_yaxis("词频", counts)
            .set_global_opts(
                title_opts=opts.TitleOpts(title="词频排名折线图", subtitle="前20词汇"),
                xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=-45))
            )
        )
        return line
    
    elif chart_type == "词频饼图":
        # 饼图
        pie = (
            Pie()
            .add("", list(zip(words, counts)))
            .set_global_opts(title_opts=opts.TitleOpts(title="词频占比饼图", subtitle="前20词汇"))
            .set_series_opts(label_opts=opts.LabelOpts(formatter="{b}: {c}"))
        )
        return pie
    
    elif chart_type == "词频环形图":
        # 环形图（饼图的变种）
        ring = (
            Pie()
            .add("", list(zip(words, counts)), radius=["40%", "70%"])  # 内环40%，外环70%
            .set_global_opts(title_opts=opts.TitleOpts(title="词频占比环形图", subtitle="前20词汇"))
            .set_series_opts(label_opts=opts.LabelOpts(formatter="{b}: {c}"))
        )
        return ring
    
    elif chart_type == "词频雷达图":
        # 雷达图（适配前8个词汇，避免坐标轴过多）
        radar_words = words[:8]
        radar_counts = counts[:8]
        radar = (
            Radar()
            .add_schema(schema=[opts.RadarIndicatorItem(name=w, max_=max(radar_counts)) for w in radar_words])
            .add("词频", [radar_counts])
            .set_global_opts(title_opts=opts.TitleOpts(title="词频雷达图", subtitle="前8词汇"))
        )
        return radar
    
    elif chart_type == "词频散点图":
        # 散点图
        scatter = (
            Scatter()
            .add_xaxis(words)
            .add_yaxis("词频", counts)
            .set_global_opts(
                title_opts=opts.TitleOpts(title="词频散点图", subtitle="前20词汇"),
                xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=-45))
            )
        )
        return scatter
    
    elif chart_type == "词频条形图":
        # 条形图（柱状图的横向版）
        bar_h = (
            Bar()
            .add_xaxis(words)
            .add_yaxis("词频", counts)
            .reversal_axis()  # 反转坐标轴，变为横向
            .set_global_opts(title_opts=opts.TitleOpts(title="词频排名条形图", subtitle="前20词汇"))
        )
        return bar_h
    
    elif chart_type == "词频3D柱状图":
        # 3D柱状图（第8种，超额满足≥7种要求）
        bar3d = (
            Bar3D()
            .add("", [[i, 0, counts[i]] for i in range(len(words))], xaxis3d_opts=opts.Axis3DOpts(words), yaxis3d_opts=opts.Axis3DOpts(["词频"]))
            .set_global_opts(title_opts=opts.TitleOpts(title="词频3D柱状图", subtitle="前20词汇"))
        )
        return bar3d

# -------------------------- 主程序逻辑 --------------------------
def main():
    # 侧边栏：图表筛选 + 低频词过滤
    st.sidebar.title("⚙️ 分析配置")
    chart_type = st.sidebar.selectbox(
        "📊 选择图表类型",
        [
            "词云", "词频柱状图", "词频折线图", "词频饼图", 
            "词频环形图", "词频雷达图", "词频散点图", "词频条形图", "词频3D柱状图"
        ],
        index=0  # 默认选词云
    )
    min_freq = st.sidebar.number_input(
        "🔍 低频词过滤阈值（最小词频）",
        min_value=1,
        value=2,
        step=1,
        help="过滤词频小于该值的词汇，仅保留高频词"
    )

    # 主页面：URL输入 + 分析
    st.title("📝 URL文本词频分析工具")
    st.divider()  # 分隔线
    url = st.text_input(
        "请输入文章URL",
        placeholder="例如：https://www.xxx.com/article.html",
        help="支持大部分新闻、博客类网页的文本提取"
    )

    # 分析按钮
    if st.button("🚀 开始分析", type="primary"):
        if not url:
            st.warning("请输入有效的URL！")
            return
        
        # 1. 抓取URL文本
        st.info("正在抓取URL文本...")
        raw_text = crawl_url_text(url)
        if not raw_text:
            return
        
        # 2. 清洗分词
        st.info("正在清洗并分词...")
        valid_words = clean_and_cut_text(raw_text)
        if not valid_words:
            st.error("分词后无有效词汇（可能全是停用词/单字）！")
            return
        
        # 3. 词频统计 + 过滤低频词
        word_count = Counter(valid_words)
        filtered_words = {word: cnt for word, cnt in word_count.items() if cnt >= min_freq}
        if not filtered_words:
            st.error(f"过滤后无词频≥{min_freq}的词汇！请降低阈值重试。")
            return
        
        # 4. 取前20词频
        top20_words = sorted(filtered_words.items(), key=lambda x: x[1], reverse=True)[:20]
        
        # -------------------------- 最终适配版：仅保留低版本支持的参数 --------------------------
        # 展示提取并清洗后的完整文本（不限制字数，支持滚动）
        st.subheader("📜 提取并清洗后的完整文本")
        st.text_area(
            label="完整文本内容",
            value=raw_text,
            height=300,  # 仅保留高度和只读，无任何宽度参数
            disabled=True
        )
        
        # 展示分词后的完整有效词汇（转成字符串，方便查看）
        st.subheader("✂️ 分词后的完整有效词汇")
        segmented_full_text = " ".join(valid_words)
        st.text_area(
            label="分词结果",
            value=segmented_full_text,
            height=300,
            disabled=True
        )
        # -------------------------- 适配结束 --------------------------
        
        # 5. 展示前20词频（移除width参数，避免报错）
        st.subheader("🏆 词频排名前20词汇")
        import pandas as pd
        df_top20 = pd.DataFrame(top20_words, columns=["词汇", "词频"])
        st.dataframe(df_top20)  # 无宽度参数，默认展示
        
        # 6. 生成并展示图表
        st.subheader("📈 可视化图表")
        chart = generate_chart(chart_type, top20_words)
        st_pyecharts(chart, width="100%")

if __name__ == "__main__":
    main()

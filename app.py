import streamlit as st
from streamlit_echarts import st_pyecharts
import requests
from bs4 import BeautifulSoup
import jieba
from collections import Counter
import re
import warnings
warnings.filterwarnings('ignore')

# -------------------------- 工具函数 --------------------------
def crawl_url_text(url):
    """抓取URL的文本内容"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = response.apparent_encoding or 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 移除script、style、nav、footer等非正文标签
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'iframe', 'aside']):
            tag.decompose()
        
        # 提取正文（优先取article、div[class*="content"]、p标签）
        article = soup.find('article')
        if article:
            text = article.get_text(strip=True, separator='\n')
        else:
            content_div = soup.find('div', class_=re.compile(r'content|article|main', re.I))
            if content_div:
                text = content_div.get_text(strip=True, separator='\n')
            else:
                # 提取所有p标签文本
                p_tags = soup.find_all('p')
                text = '\n'.join([p.get_text(strip=True) for p in p_tags if p.get_text(strip=True)])
        
        # 过滤空文本
        if not text or len(text) < 50:
            st.error("未能提取到有效文本（可能是反爬或页面结构不支持）！")
            return ""
        
        return text
    except Exception as e:
        st.error(f"URL抓取失败：{str(e)}")
        return ""

def clean_and_cut_text(text):
    """清洗文本并分词"""
    # 1. 清洗：只保留中文、英文、数字，移除特殊字符
    text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    # 2. 分词
    words = jieba.lcut(text)
    
    # 3. 过滤停用词和无效词汇（单字、空白）
    stop_words = set([
        '的', '了', '是', '在', '有', '和', '就', '不', '人', '我', '到', '来', '去', '上', '下', '大', '小',
        '多', '少', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十', '百', '千', '万', '亿',
        '这', '那', '哪', '此', '彼', '其', '它', '他', '她', '你', '我', '他', '我们', '你们', '他们',
        '这里', '那里', '哪里', '什么', '怎么', '为什么', '因为', '所以', '但是', '而且', '虽然', '如果',
        '对于', '关于', '一定', '可能', '可以', '应该', '需要', '会', '要', '没', '没有', '还', '也', '都',
        '只', '只', '又', '再', '更', '最', '很', '非常', '特别', '比较', '稍微', '几乎', '差不多',
        '着', '过', '过', '呢', '吗', '吧', '啊', '呀', '哦', '嗯', '哈', '哼', '呵',
        'http', 'https', 'com', 'www', 'html', 'php', 'jsp', 'asp', 'css', 'js', 'img', 'src', 'href'
    ])
    
    valid_words = [
        word for word in words 
        if len(word) > 1  # 过滤单字
        and word not in stop_words  # 过滤停用词
        and not word.isdigit()  # 过滤纯数字
        and len(word.strip()) > 0  # 过滤空白
    ]
    
    return valid_words

def generate_chart(chart_type, top20_words):
    """生成可视化图表"""
    words = [item[0] for item in top20_words]
    counts = [item[1] for item in top20_words]
    
    from pyecharts import options as opts
    from pyecharts.charts import Bar, Line, WordCloud, Pie, Radar, Scatter
    
    if chart_type == "词云":
        chart = (
            WordCloud()
            .add("", list(zip(words, counts)), word_size_range=[20, 100])
            .set_global_opts(title_opts=opts.TitleOpts(title="词频Top20 - 词云"))
        )
    elif chart_type == "词频柱状图":
        chart = (
            Bar()
            .add_xaxis(words)
            .add_yaxis("词频", counts)
            .set_global_opts(
                title_opts=opts.TitleOpts(title="词频Top20 - 柱状图"),
                xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=-45)),
                legend_opts=opts.LegendOpts(is_show=False)
            )
        )
    elif chart_type == "词频折线图":
        chart = (
            Line()
            .add_xaxis(words)
            .add_yaxis("词频", counts, markpoint_opts=opts.MarkPointOpts(data=[opts.MarkPointItem(type_="max")]))
            .set_global_opts(
                title_opts=opts.TitleOpts(title="词频Top20 - 折线图"),
                xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=-45)),
                legend_opts=opts.LegendOpts(is_show=False)
            )
        )
    elif chart_type == "词频饼图":
        chart = (
            Pie()
            .add("", list(zip(words, counts)))
            .set_global_opts(
                title_opts=opts.TitleOpts(title="词频Top20 - 饼图"),
                legend_opts=opts.LegendOpts(orient="vertical", pos_top="15%", pos_left="2%")
            )
            .set_series_opts(label_opts=opts.LabelOpts(formatter="{b}: {c}"))
        )
    elif chart_type == "词频环形图":
        chart = (
            Pie()
            .add("", list(zip(words, counts)) , radius=["40%", "70%"])
            .set_global_opts(
                title_opts=opts.TitleOpts(title="词频Top20 - 环形图"),
                legend_opts=opts.LegendOpts(orient="vertical", pos_top="15%", pos_left="2%")
            )
            .set_series_opts(label_opts=opts.LabelOpts(formatter="{b}: {c}"))
        )
    elif chart_type == "词频雷达图":
        # 雷达图需要构造维度数据
        radar_data = [{"name": words[i], "value": [counts[i]]} for i in range(len(words))]
        schema = [{"name": "词频", "max": max(counts), "min": min(counts)}]
        
        chart = (
            Radar()
            .add_schema(schema)
            .add("词频", radar_data)
            .set_global_opts(
                title_opts=opts.TitleOpts(title="词频Top20 - 雷达图"),
                legend_opts=opts.LegendOpts(is_show=False)
            )
        )
    elif chart_type == "词频散点图":
        chart = (
            Scatter()
            .add_xaxis(words)
            .add_yaxis("词频", counts)
            .set_global_opts(
                title_opts=opts.TitleOpts(title="词频Top20 - 散点图"),
                xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=-45)),
                yaxis_opts=opts.AxisOpts(min_=0),
                legend_opts=opts.LegendOpts(is_show=False)
            )
        )
    elif chart_type == "词频条形图":
        chart = (
            Bar()
            .add_xaxis(words)
            .add_yaxis("词频", counts)
            .reversal_axis()  # 反转坐标轴实现条形图
            .set_global_opts(
                title_opts=opts.TitleOpts(title="词频Top20 - 条形图"),
                legend_opts=opts.LegendOpts(is_show=False)
            )
        )
    else:  # 默认词云
        chart = (
            WordCloud()
            .add("", list(zip(words, counts)), word_size_range=[20, 100])
            .set_global_opts(title_opts=opts.TitleOpts(title="词频Top20 - 词云"))
        )
    return chart

# -------------------------- 主程序 --------------------------
def main():
    # 侧边栏设置
    st.sidebar.title("⚙️ 配置选项")
    chart_type = st.sidebar.selectbox(
        "📊 选择可视化图表类型",
        ["词云", "词频柱状图", "词频折线图", "词频饼图", "词频环形图", "词频雷达图", "词频散点图", "词频条形图"],
        index=0
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
    st.divider()
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
        with st.spinner("正在抓取URL文本..."):
            raw_text = crawl_url_text(url)
        if not raw_text:
            return
        
        # 2. 清洗分词
        with st.spinner("正在清洗并分词..."):
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
        
        # 展示提取并清洗后的完整文本
        st.subheader("📜 提取并清洗后的完整文本")
        st.text_area(
            label="完整文本内容",
            value=raw_text,
            height=300,
            disabled=True
        )
        
        # 展示分词后的完整有效词汇
        st.subheader("✂️ 分词后的完整有效词汇")
        segmented_full_text = " ".join(valid_words)
        st.text_area(
            label="分词结果",
            value=segmented_full_text,
            height=300,
            disabled=True
        )
        
        # 展示前20词频（用Streamlit内置表格，无需pandas）
        st.subheader("🏆 词频排名前20词汇")
        # 转换为列表格式，Streamlit可直接展示
        top20_list = [[word, cnt] for word, cnt in top20_words]
        st.dataframe(top20_list, column_config={"0": "词汇", "1": "词频"})
        
        # 5. 生成并展示图表
        st.subheader("📈 可视化图表")
        chart = generate_chart(chart_type, top20_words)
        st_pyecharts(chart, width="100%")

if __name__ == "__main__":
    main()

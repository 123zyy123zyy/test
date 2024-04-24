from flask import Flask, render_template , request, jsonify , redirect, url_for, render_template_string 
import pandas as pd  
import plotly.express as px  
import pymysql # type: ignore
import plotly.graph_objects as go 
import random

app = Flask(__name__)  

@app.route('/')  
def index():  
    # 读取数据  
    moviedata = pd.read_excel(r'moviedata.xlsx')  

    moviedata.dropna(subset=['豆瓣评分', '豆瓣评论数','类型'], inplace=True)  # 确保两个字段都没有缺失值  
    # 创建散点图  
    scatter_fig = px.scatter(moviedata, x="豆瓣评论数", y="豆瓣评分",    
                          title='豆瓣评分与豆瓣评论数散点图',    
                          labels={'豆瓣评论数': '评论数', '豆瓣评分': '评分'},    
                          width=380, height=270,    
                          color='豆瓣评分',  # 仍然使用'豆瓣评分'字段  
                          color_continuous_scale=px.colors.sequential.Plasma)  # 使用 Plasma 颜色序列
    # 设置散点图背景为透明  
    scatter_fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')   
    scatter_chart_html = scatter_fig.to_html(full_html=False, include_plotlyjs='cdn')  
    # 创建直方图  
    histogram_fig = px.histogram(moviedata, x="豆瓣评分", nbins=30,  
                                 title='电影评分分布',  
                                 opacity=0.8,  
                                 width=400, height=300)  
    # 更新所有柱子的颜色为红色  
    for trace in histogram_fig.data:  
        trace.marker.color = 'purple' 
    # 设置直方图背景为透明  
    histogram_fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')  
    histogram_chart_html = histogram_fig.to_html(full_html=False, include_plotlyjs='cdn')

    moviedata.dropna(subset=['豆瓣评分', '主演'], inplace=True)  # 确保字段没有缺失值  
    
    # 设置评分阈值  
    sta_value = 6  
    
    # 处理卡司数量  
    moviedata['卡司'] = moviedata['主演'].str.split('/')  
    moviedata['卡司数量'] = moviedata['卡司'].apply(lambda x: len(x))  
    
    # 创建分组并计算烂片数量  
    bins = [1, 2, 4, 6, 9, 20]  
    moviedata['主演人数'] = pd.cut(moviedata['卡司数量'], bins, labels=['1-2人', '3-4人', '5-6人', '7-9人', '10人以上'])  
    moviedata_gp = moviedata.groupby('主演人数')['电影名称'].count().reset_index(name='总数')  
    moviedata_lp = moviedata[moviedata['豆瓣评分'] < sta_value].groupby('主演人数')['电影名称'].count().reset_index(name='烂片数')  
    
    # 合并数据并计算烂片比例  
    moviedata_count = pd.merge(moviedata_gp, moviedata_lp, on='主演人数', how='left').fillna(0)  
    moviedata_count['烂片比例'] = moviedata_count['烂片数'] / moviedata_count['总数']  
    moviedata_count = moviedata_count.sort_values('烂片比例', ascending=False)  
    
    # 创建饼图数据  
    pie1_fig = px.pie(moviedata_count, values='烂片比例', names='主演人数', title='不同主演人数的烂片比例')  
    pie1_fig.update_traces(textposition='inside', textinfo='percent+label')  
    pie1_fig.update_layout(
        width=450,   
        height=240,plot_bgcolor='rgba(0,0,0,0)',  
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=60, l=0, r=0, b=0))  
    pie_chart_data_html = pie1_fig.to_html(full_html=False, include_plotlyjs='cdn')  # 重命名为 pie_chart_data_html  
    
    # 创建散点图数据  
    scatter_fig1 = px.scatter(moviedata, x="卡司数量", y="豆瓣评分", color="卡司数量",  
                            title='主演数量与豆瓣评分关系',  
                            labels={'卡司数量': '主演数量', '豆瓣评分': '评分'},  
                            width=320, height=300)  
    scatter_fig1.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)' )
    scatter_plot_html = scatter_fig1.to_html(full_html=False, include_plotlyjs='cdn')  

    # 将类型列中的空格去除，并使用 '/' 分隔符分割字符串，得到列表  
    moviedata['类型'] = moviedata['类型'].str.replace(' ', '').str.split('/')  
    
    # 使用 explode 方法将每个电影的类型展开成多行  
    moviedata_exploded = moviedata.explode('类型').reset_index(drop=True)  
    
    # 计算每种类型的电影数量  
    type_counts = moviedata_exploded['类型'].value_counts()  
    
    # 计算总电影数量  
    total_movies = len(moviedata_exploded)  
    
    # 计算每种类型的电影所占的比例  
    type_proportions = (type_counts / total_movies) * 100  
    
    # 找出比例低于2%的类型  
    other_types = type_proportions[type_proportions < 2].index  
    
    # 计算“其他”类型的比例  
    other_proportion = type_proportions[type_proportions < 2].sum()  
    
    # 更新 type_proportions，将低于2%的类型合并到“其他”  
    type_proportions = type_proportions.drop(other_types)  
    type_proportions['其他'] = other_proportion  
    
    # 创建一个 DataFrame 用于绘制饼图  
    type_proportions_df = pd.DataFrame({  
        '类型': type_proportions.index,  
        '比例': type_proportions.values  
    })  
    
    # 创建饼图  
    pie_fig = px.pie(type_proportions_df, values='比例', names='类型', title='不同“类型”的电影所占比例')  
    
    # 设置图的配色方案  
    pie_fig.update_traces(marker_colors=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'],  
                        textposition='inside', textinfo='label+percent')  
    
    
    # 调整饼图的扇区之间的间距和偏移量  
    pie_fig.update_layout(uniformtext_minsize=12, uniformtext_mode='hide')  
    pie_fig.update_traces(hoverinfo='label+percent+name', textfont_size=12)  
    
    # 设置图的宽度和高度来减小饼图的大小  
    pie_fig.update_layout(  
        width=450,  # 设置宽度，可以根据需要调整  
        height=280,  # 设置高度，可以根据需要调整  
        plot_bgcolor='rgba(0,0,0,0)',  
        paper_bgcolor='rgba(0,0,0,0)',  
        margin=dict(l=60, r=0, t=40, b=0)  # 调整边距，使饼图更居中  
    )  
    
    # 将饼图转换为HTML  
    pie_chart_html = pie_fig.to_html(full_html=False, include_plotlyjs='cdn')
      
    # 读取Excel文件  
    moviedata_line = pd.read_excel('豆瓣电影数据集5000.xlsx')  
    
    moviedata_line['上映日期'] = moviedata_line['上映日期'].str.strip("'")  # 去除字符串两端的引号  
    moviedata_line['上映日期'] = moviedata_line['上映日期'].str.extract(r'(\d{4})', expand=False)  # 提取四位数年份  
    
    # 检查并删除包含NaN值的行  
    moviedata_line = moviedata_line.dropna(subset=['上映日期'])  
    
    # 现在，将年份字符串转换为整数（确保没有NaN值，因为已经删除了它们）  
    moviedata_line['年份'] = moviedata_line['上映日期'].astype(int)  
    
    # 删除年份为零的行（假设零不是一个有效的年份）  
    moviedata_line = moviedata_line[moviedata_line['年份'] != 0]  
    
    # 按照年份分组并计算平均评分  
    yearly_average_scores = moviedata_line.groupby('年份')['评分'].mean().reset_index()

    
    line_fig = px.line(yearly_average_scores, x='年份', y='评分', title='上映年份与平均评分关系折线图')  
    line_fig.update_layout(width=450,   
        height=300,plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')  
    
    line_chart_html = line_fig.to_html(full_html=False, include_plotlyjs='cdn') 


    return render_template('index.html', line_chart_html=line_chart_html,scatter_plot_html=scatter_plot_html,pie_chart_data_html=pie_chart_data_html,scatter_chart_html=scatter_chart_html, histogram_chart_html=histogram_chart_html, pie_chart_html=pie_chart_html)

@app.route('/search', methods=['POST'])  
def search():
    moviedata = pd.read_excel(r'豆瓣电影数据集5000.xlsx')   
    movieName = request.form.get('movieName')  
    # 确保 movieName 不为空，否则不进行搜索  
    if not movieName:  
        return jsonify({'error': '电影名称不能为空'}), 400  
    # 在这里，我假设 moviedata 是一个 pandas DataFrame  
    # 使用 loc 而不是直接使用比较操作，这样可以更好地处理 pandas DataFrame  
    result = moviedata.loc[moviedata['电影名称'] == movieName]    
    # 检查是否找到结果  
    if not result.empty:  
       # 返回找到的电影信息  
       # 如果可能返回多个结果，您可能需要处理这些情况  
        movie_info = result.to_dict(orient='records')  
        # 如果只期望一个结果，并且已经通过取第一个元素来确保，可以只返回第一个字典  
        if len(movie_info) == 1:  
            return jsonify({'movie': movie_info[0]})  
        else:  
            # 如果可能返回多个结果，则返回所有结果  
            return jsonify({'movies': movie_info})  
    else:  
        # 如果没有找到电影，返回空信息  
        return jsonify({'movie': None})
    
@app.route('/index2.html')  

def index2(): 
    # 连接数据库  
    conn = pymysql.connect(host='localhost',  
                           port=3306,  
                           user='root',  
                           password='1234',  
                           db='bishe',  
                           charset='utf8mb4')  
    cursor = None  
    chart_html_ratings = ''  
    chart_html_comments = ''  
      
    try:  
        cursor = conn.cursor()  
          
        # 查询豆瓣评分>=9的电影  
        sql_ratings = "SELECT 电影名称, 豆瓣评分 FROM moviedata WHERE 豆瓣评分>=9;"  
        cursor.execute(sql_ratings)  
        results_ratings = cursor.fetchall()  
          
        # 绘制评分图形  
        if results_ratings:  
            movie_names_ratings = [row[0] for row in results_ratings]  
            douban_scores = [row[1] for row in results_ratings]  
        
            # 创建折线图  
            fig_ratings = go.Figure(data=[go.Scatter(x=movie_names_ratings, y=douban_scores, mode='lines+markers')])  
        
            # 美化图形  
            fig_ratings.update_layout(  
                width=450,  # 设置宽度  
                height=300,  # 设置高度  
                plot_bgcolor='rgba(255, 255, 255, 0)',  # 设置绘图背景颜色  
                paper_bgcolor='rgba(255, 255, 255, 0)',  # 设置纸张背景颜色  
                title='豆瓣评分>=9的电影评分',  
                xaxis_title='电影名称',  
                yaxis_title='豆瓣评分',  
                font=dict(  
                    family="Courier New, monospace",  
                    size=12,  
                    color="white"  
                ),  
                xaxis=dict(  
                    showticklabels=False,  # 显示x轴标签  
                    tickfont=dict(size=10),  # x轴标签字体大小  
                    tickangle=45,  # x轴标签倾斜角度  
                ),  
                yaxis=dict(  
                    tickfont=dict(size=10),  # y轴标签字体大小  
                ),  
                legend=dict(  
                    x=0,  
                    y=1,  
                    traceorder="normal",  
                    font=dict(  
                        family="sans-serif",  
                        size=12,  
                        color="black"  
                    ),  
                    bgcolor="LightSteelBlue",  
                    bordercolor="Black",  
                    borderwidth=2  
                ),  
                margin=dict(  
                    l=50,  # 左边距  
                    r=50,  # 右边距  
                    t=60,  # 上边距  
                    b=40,  # 下边距  
                    pad=4  # 内边距  
                )  
            )  
        
            # 生成HTML  
            chart_html_ratings = fig_ratings.to_html(full_html=False, include_plotlyjs='cdn')  
          
        sql_comments = "SELECT 电影名称, 豆瓣评论数 FROM moviedata WHERE 豆瓣评分>=9;"  
        cursor.execute(sql_comments)  
        results_comments = cursor.fetchall()  
          
        if results_comments:  
            movie_names_comments = [row[0] for row in results_comments]  
            douban_comments = [row[1] for row in results_comments]  
        
            # 生成随机颜色列表  
            def generate_random_color():  
                return "#{:06x}".format(random.randint(0, 0xFFFFFF))  
            random_colors = [generate_random_color() for _ in range(len(movie_names_comments))]  
        
            fig_comments = go.Figure(data=[go.Bar(x=movie_names_comments, y=douban_comments, marker_color=random_colors)])  
            fig_comments.update_layout(width=450,  # 设置宽度  
                                        height=300,  # 设置高度  
                                        plot_bgcolor='rgba(0,0,0,0)',  
                                        paper_bgcolor='rgba(0,0,0,0)',  
                                        title='豆瓣评分>=9的电影的评论数',  
                                        xaxis_title='电影名称',  
                                        yaxis_title='豆瓣评论数',
                                        font=dict(  
                                        family="Courier New, monospace",  
                                        size=12,  
                                        color="white"  
                                    ))  
            fig_comments.update_xaxes(showticklabels=False)  # 显示x轴标签  
        
            chart_html_comments = fig_comments.to_html(full_html=False, include_plotlyjs='cdn')   
          
        # 渲染模板并返回HTML  
        return render_template('index2.html', chart_html_ratings=chart_html_ratings, chart_html_comments=chart_html_comments)  
      
    except pymysql.MySQLError as e:  
        print(f"数据库查询出错: {e}")  
        return "数据库查询出错", 500  
      
    finally:  
        # 确保关闭游标和连接  
        if cursor:  
            cursor.close()  
        conn.close()  

if __name__ == '__main__':  
    app.run(debug=True)
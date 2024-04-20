from flask import Flask, render_template  
import pandas as pd  
import plotly.express as px  
  
app = Flask(__name__)  
  
@app.route('/')  
def index():  
    # 读取数据  
    moviedata = pd.read_excel(r'moviedata.xlsx')  
    moviedata.dropna(subset=['豆瓣评分', '豆瓣评论数'], inplace=True)  # 确保两个字段都没有缺失值  
  
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
                                 width=380, height=270,
                                )  
    # 更新所有柱子的颜色为红色  
    for trace in histogram_fig.data:  
        trace.marker.color = 'red' 
      
    # 设置直方图背景为透明  
    histogram_fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')  
      
    histogram_chart_html = histogram_fig.to_html(full_html=False, include_plotlyjs='cdn')  
  
    # 返回渲染模板，并将两个图表的 HTML 传入  
    return render_template('index.html', scatter_chart_html=scatter_chart_html, histogram_chart_html=histogram_chart_html)  
  
if __name__ == '__main__':  
    app.run(debug=True)
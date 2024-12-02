# 检索
# 搜索框是文书内容的全文搜索，并类似知网提供筛选条件(高级检索)
from flask import Blueprint,request, render_template, jsonify
from utils import db_context_query
from sqlalchemy.exc import SQLAlchemyError
from Database.model import *

searcher_bp=Blueprint('searcher',__name__,template_folder='app/templates/searcher',static_folder='app/static/searcher',url_prefix='/searcher')

@searcher_bp.route('/')
def index():
    return render_template('search_page.html')

    

#筛选字段需更新
@searcher_bp.route('/search', methods=['POST'])
def search():
    # 获取搜索条件
    query = request.form.get('query', '').strip()
    doc_type = request.form.get('doc_type', '')
    date_from = request.form.get('date_from', '')
    date_to = request.form.get('date_to', '')
    
    try:
        # 执行查询
        results = db_context_query(query, doc_type, date_from, date_to)
    except SQLAlchemyError as e:
        print(f"Error: {e}")
        return None
    
    # 将结果传递给模板进行渲染
    return render_template('search_results.html', results=results)


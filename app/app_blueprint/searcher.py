# 检索
# 搜索框是文书内容的全文搜索，并类似知网提供筛选条件(高级检索)
from flask import Blueprint,request, render_template, jsonify
from utils import db_context_query, db_advanced_search
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text, or_
from Database.model import *
from Database.config import db

searcher_bp=Blueprint('searcher',__name__,template_folder='app/templates/searcher',static_folder='app/static/searcher',url_prefix='/searcher')

@searcher_bp.route('/')
def index():
    return render_template('searcher/search_page.html')

    

#筛选字段需更新
@searcher_bp.route('/search', methods=['POST'])
def search():
    try:
        data = request.get_json()
        search_type = data.get('type', 'basic')  # 搜索类型：basic 或 advanced
        
        if search_type == 'advanced':
            # 精细搜索
            person = data.get('person', '').strip()
            title = data.get('title', '').strip()
            results = db_advanced_search(title=title, person=person)
            
            # 格式化结果
            formatted_results = [{
                'Doc_id': row.Doc_id,
                'Doc_title': row.Doc_title,
                'Doc_type': row.Doc_type,
                'Doc_createdData': row.Doc_createdData,
                'Doc_summary': row.Doc_summary,
                'Participants': row.Participants,
                'Contractors': row.Contractors
            } for row in results]
        else:
            # 基本搜索（全文检索）
            keyword = data.get('keyword', '').strip()
            doc_type = data.get('docType')
            start_date = data.get('startDate')
            end_date = data.get('endDate')
            
            results = db_context_query(
                query=keyword,
                doc_type=doc_type,
                date_from=start_date,
                date_to=end_date
            )
            
            # 格式化结果
            formatted_results = [doc.to_dict() for doc in results]

        return jsonify(formatted_results)

    except Exception as e:
        print(f"Search error: {str(e)}")
        return jsonify([])

@searcher_bp.route('/documents/<category>')
def get_documents(category):
    """获取不同分类的文书列表"""
    try:
        if category == 'recent':
            # 获取最近上传的文书
            documents = Documents.query.order_by(Documents.Doc_createdGregorianDate.desc()).limit(20).all()
        elif category == 'popular':
            # 获取热门文书（可以基于浏览记录统计）
            documents = Documents.query.join(UserBrowsingHistory).\
                       group_by(Documents.Doc_id).\
                       order_by(func.count(UserBrowsingHistory.Browse_id).desc()).limit(20).all()
        else:
            # 获取全部文书
            documents = Documents.query.limit(20).all()
            
        return jsonify([{
            'Doc_id': doc.Doc_id,
            'Doc_title': doc.Doc_title,
            'Doc_type': doc.Doc_type,
            'Doc_createdData': doc.Doc_createdData,
            'Doc_summary': doc.Doc_summary[:200] + '...' if doc.Doc_summary and len(doc.Doc_summary) > 200 else doc.Doc_summary
        } for doc in documents])
    except Exception as e:
        print(f"Error fetching documents: {str(e)}")
        return jsonify([])


# 阅读器 
# (1)文书详情阅读，标记、笔记、导出
# (2)讨论区，差错提交

from flask import Blueprint,render_template,request,jsonify
from utils import *
from sqlalchemy.exc import SQLAlchemyError

reader_bp=Blueprint('reader',__name__,template_folder='app/templates/reader',static_folder='app/static/reader',url_prefix='/reader')

@reader_bp.route('/')
def index():
    return render_template('reader/index.html')

#筛选字段需更新
@reader_bp.route('/search', methods=['POST'])
def search():
    try:
        # 获取前端发送的 JSON 数据
        search_params = request.get_json()
        
        # 提取搜索参数
        keyword = search_params.get('keyword', '').strip()
        doc_type = search_params.get('documentType', '')
        date = search_params.get('date', '')
        results = []
        # 调用数据库查询函数
        if keyword:
            results = db_context_query(
                query=keyword,
                doc_type=doc_type if doc_type else None,
                date_from=date if date else None
            )
        else:
            conditions = {
                'Doc_title':keyword,
                'Doc_type':doc_type if doc_type else None,
                'Doc_createdAt':date if date else None
            }
            results = db_query_by_conditions(Documents,conditions)
        
        # 将查询结果转换为前端需要的格式
        formatted_results = []
        for doc in results:
            formatted_results.append({
                'id': doc.Doc_id,  # 假设字段名是 Doc_id
                'title': doc.Doc_title,
                'date': doc.Doc_createdAt.strftime('%Y-%m-%d') if doc.Doc_createdAt else '',
                'summary': doc.Doc_simplifiedText[:200] + '...' if len(doc.Doc_simplifiedText) > 200 else doc.Doc_simplifiedText,
                'court': doc.Doc_court,
                'caseType': doc.Doc_type
            })
        
        return jsonify(formatted_results)
        
    except SQLAlchemyError as e:
        print(f"Database error: {e}")
        return jsonify([]), 500
    except Exception as e:
        print(f"Error: {e}")
        return jsonify([]), 500

@reader_bp.route('/document/<int:doc_id>')
def document_detail(doc_id):
    try:
        # 查询文档详情
        document = Documents.query.get_or_404(doc_id)
        return render_template('reader/document.html', document=document)
    except Exception as e:
        print(f"Error: {e}")
        return "未找到文书", 404
# 阅读器Blueprint
# (1)文书详情阅读,标记、笔记、导出
# (2)讨论区,差错提交

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from flask import Blueprint,render_template,request,jsonify,flash,redirect,url_for, make_response, abort, current_app
from Database.model import Documents, Comments, Notes, Highlights, DocumentDisplayView, Folders, AuditLog
from Database.config import db
from flask_login import login_required, current_user
from datetime import datetime
from sqlalchemy import text
import logging
import json
import traceback
from urllib.parse import quote
from docx import Document
from io import BytesIO
from flask import send_file
from sqlalchemy.sql import func

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

reader_bp=Blueprint('reader',__name__,template_folder='app/templates/reader',static_folder='app/static/reader',url_prefix='/reader')

@reader_bp.route('/')
def index():
    return render_template('reader/index.html')


# 文书详情页
@reader_bp.route('/document/<doc_id>')
def document(doc_id):
    try:
        # 获取文档数据
        doc = Documents.query.get_or_404(doc_id)
        
        # 获取高亮和批注数据
        highlights = []
        notes = []
        if current_user.is_authenticated:
            highlights = Highlights.query.filter_by(
                Doc_id=doc_id,
                User_id=current_user.User_id
            ).all()
            notes = Notes.query.filter_by(
                Doc_id=doc_id,
                User_id=current_user.User_id
            ).all()
            
        # 获取所有评论
        comments = Comments.query.filter_by(Doc_id=doc_id).all()
        
        # 获取契约人信息
        contractors = DocumentDisplayView.query.filter_by(Doc_id=doc_id).first()
        
        # 获取参与人信息
        participants = DocumentDisplayView.query.filter_by(Doc_id=doc_id).first()
        
        return render_template('reader/document.html', 
                             document=doc,
                             content=doc.Doc_originalText,
                             highlights=highlights,
                             notes=notes,
                             comments=comments,
                             contractors=contractors,
                             participants=participants)
    except Exception as e:
        logger.error(f"Error in document route: {str(e)}")
        flash('获取文档失败，请稍后重试', 'error')
        return redirect(url_for('searcher.index'))

# 添加批注
@reader_bp.route('/add_note', methods=['POST'])
@login_required
def add_note():
    try:
        # 只返回成功，不保存到数据库
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"处理批注失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

# 添加评论  
@reader_bp.route('/add_comment', methods=['POST'])
@login_required
def add_comment():
    try:
        data = request.get_json()
        
        new_comment = Comments(
            Doc_id=data.get('doc_id'),
            User_id=current_user.User_id,
            Comment_text=data.get('comment_text')
        )
        
        db.session.add(new_comment)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"发表评论失败: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

# 导出文档
@reader_bp.route('/export/<doc_id>/<text_type>')
@login_required
def export_document(doc_id, text_type):
    try:
        if not current_user.is_authenticated:
            return redirect(url_for('user.login', next=request.url))
            
        doc = Documents.query.get(doc_id)
        if not doc:
            abort(404)
        
        # 创建 Word 文档
        word_doc = Document()
        
        # 添加标题
        word_doc.add_heading(doc.Doc_title, 0)
        
        # 添加基本信息
        word_doc.add_paragraph(f'文书类型: {doc.Doc_type}')
        word_doc.add_paragraph(f'文书大意: {doc.Doc_summary}')
        
        # 添加正文
        word_doc.add_heading('正文', level=1)
        if text_type == 'simplified':
            content = doc.Doc_simplifiedText or doc.Doc_originalText
        else:
            content = doc.Doc_originalText
        word_doc.add_paragraph(content)
        
        # 添加高亮和批注
        if current_user.is_authenticated:
            highlights = Highlights.query.filter_by(
                Doc_id=doc_id,
                User_id=current_user.User_id  
            ).all()
            
            notes = Notes.query.filter_by(
                Doc_id=doc_id,
                User_id=current_user.User_id
            ).all()
            
            if highlights or notes:
                word_doc.add_heading('标记与批注', level=1)
                
                if highlights:
                    word_doc.add_heading('高亮部分', level=2)
                    for h in highlights:
                        try:
                            highlighted_text = content[h.Highlight_startPosition:h.Highlight_endPosition]
                            word_doc.add_paragraph(f'• {highlighted_text}')
                        except Exception as e:
                            logger.error(f"处理高亮文本时出错: {str(e)}")
                
                if notes:
                    word_doc.add_heading('批注内容', level=2)
                    for n in notes:
                        try:
                            noted_text = content[n.Note_startPosition:n.Note_endPosition]
                            p = word_doc.add_paragraph()  
                            p.add_run(f'原文: {noted_text}').bold = True
                            p.add_run(f'\n批注: {n.Note_annotationText}')
                        except Exception as e:
                            logger.error(f"处理批注文本时出错: {str(e)}")
        
        # 添加评论
        comments = Comments.query.filter_by(Doc_id=doc_id).all()
        if comments:
            word_doc.add_heading('评论区', level=1)
            for comment in comments:
                word_doc.add_paragraph(f'• {comment.Comment_content}')
        
        # 保存到内存中  
        file_stream = BytesIO()
        word_doc.save(file_stream)
        file_stream.seek(0)
        
        # 返回文件
        filename = f"{doc.Doc_title}_{text_type}.docx"
        return send_file(
            file_stream,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f"导出错误: {str(e)}")
        logger.error(traceback.format_exc())
        abort(500)

@reader_bp.route('/add_highlight', methods=['POST'])
@login_required
def add_highlight():
    try:
        # 只返回成功，不保存到数据库
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"处理高亮失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

# 添加获取高亮和批注的路由
@reader_bp.route('/get_highlights/<doc_id>')
@login_required
def get_highlights(doc_id):
    try:
        # 返回空数据
        return jsonify({
            "highlights": [],
            "notes": []
        })
    except Exception as e:
        logger.error(f"获取高亮和批注失败: {str(e)}")
        return jsonify({"error": str(e)}), 500

@reader_bp.route('/add_favorite', methods=['POST'])
@login_required
def add_favorite():
    try:
        data = request.get_json()
        
        new_folder = Folders(
            User_id=current_user.User_id,
            Doc_id=data.get('doc_id'),
            Folder_name=data.get('folder_name', '默认收藏夹')
        )
        db.session.add(new_folder)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"收藏失败: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@reader_bp.route('/check_auth')  
def check_auth():
    return jsonify({'authenticated': current_user.is_authenticated})

@reader_bp.route('/get_text/<doc_id>/<text_type>')
def get_text(doc_id, text_type):
    try:
        doc = Documents.query.get(doc_id)
        if not doc:
            return jsonify({'success': False, 'error': '文档不存在'})
            
        if text_type == 'simplified':
            text = doc.Doc_simplifiedText or doc.Doc_originalText  # 如果简体文本不存在，返回原文
        else:
            text = doc.Doc_originalText
            
        return jsonify({
            'success': True,
            'text': text
        })
    except Exception as e:
        logger.error(f"Error getting text: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@reader_bp.route('/update_highlight', methods=['POST'])
@login_required
def update_highlight():
    try:
        data = request.get_json()
        
        highlight = Highlights.query.filter_by(
            Doc_id=data.get('doc_id'),
            User_id=current_user.User_id,
            Highlight_startPosition=data.get('start_offset'),
            Highlight_endPosition=data.get('end_offset')
        ).first()
        
        if highlight:
            highlight.Highlight_color = data.get('color')
            db.session.commit()
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': '未找到对应的高亮记录'})
    except Exception as e:
        logger.error(f"更新高亮颜色失败: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})
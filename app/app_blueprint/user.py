# 用户信息相关，有普通客户和管理员之分，管理员具有
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from utils import (
    db_query_all, 
    db_one_filter_records, 
    db_update_key, 
    db_one_filter_record, 
    db_add,
    process_document_text,  # 添加这个导入
    insert_document        # 添加这个导入
)
from Database.model import UserBrowsingHistory, Folders, Notes, Users, Documents, AuditLog, DocumentDisplayView, FolderContents, FolderDocumentStats
from Database.config import db
from datetime import datetime
from sqlalchemy import func
from functools import wraps
import os
from werkzeug.utils import secure_filename
from flask import current_app
import re
from sqlalchemy import or_
from flask_wtf.csrf import generate_csrf
from flask_wtf import FlaskForm
from wtforms import HiddenField

user_bp = Blueprint('user', __name__, 
                   template_folder='app/templates/user',
                   static_folder='app/static/user',
                   url_prefix='/user')

# 管理员权限装饰器
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.User_role != 'Admin':
            flash('您没有权限访问该页面', 'danger')
            return redirect(url_for('user.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@user_bp.route('/dashboard')
@login_required
def dashboard():
    # 获取active_tab参数，默认为None
    active_tab = request.args.get('active_tab', None)
    
    if current_user.User_role == 'Admin':
        # 获取管理员统计数据
        doc_count = Documents.query.count()
        user_count = Users.query.count()
        today = datetime.now().date()
        today_visits = UserBrowsingHistory.query.filter(
            func.date(UserBrowsingHistory.Browse_time) == today
        ).count()
        
        return render_template('user/admin_dashboard.html',
                             doc_count=doc_count,
                             user_count=user_count,
                             today_visits=today_visits)
    else:
        # 普通用户数据
        # 获取带有文书信息的浏览记录
        reading_history = (UserBrowsingHistory.query
            .filter_by(User_id=current_user.User_id)
            .join(Documents, UserBrowsingHistory.Doc_id == Documents.Doc_id)
            .with_entities(
                UserBrowsingHistory.Browse_time,
                UserBrowsingHistory.Doc_id,
                Documents.Doc_title,
                Documents.Doc_type
            )
            .order_by(UserBrowsingHistory.Browse_time.desc())
            .limit(10)
            .all())
        
        folders = db_one_filter_records(Folders, 'User_id', current_user.User_id)
        
        return render_template('user/dashboard.html',
                             reading_history=reading_history,
                             folders=folders,
                             active_tab=active_tab)


@user_bp.route('/profile')
@login_required
def profile():
    """个人设置页面"""
    return render_template('user/profile.html')


@user_bp.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    # 获取表单数据
    username = request.form.get('username').strip()
    email = request.form.get('email').strip()
    new_password = request.form.get('new_password')
    avatar_id = request.form.get('avatar_id')

    # 准备更新的数据
    update_data = {
        'User_name': username,
        'User_email': email,
        'avatar_id': avatar_id
    }
    
    if new_password:
        update_data['User_passwordHash'] = generate_password_hash(new_password)
    
    try:
        # 更新数据库
        db_update_key(Users, current_user.User_id, **update_data)
        
        # 记录审计日志，添加更详细的描述
        changes = []
        if current_user.User_name != username:
            changes.append('用户名')
        if current_user.User_email != email:
            changes.append('邮箱')
        if new_password:
            changes.append('密码')
        if current_user.avatar_id != avatar_id:
            changes.append('头像')

        change_desc = '、'.join(changes) if changes else "无修改项"
        log_audit('Update', 'Users', 
                 f'用户 {current_user.User_name} 更新了个人信息: {change_desc}')
        flash('个人信息更新成功！', 'success')

    except Exception as e:
        flash('更新失败，请稍后重试', 'danger')
        return redirect(url_for('user.profile'))
    
    return redirect(url_for('user.dashboard'))


def validate_password(password):
    """验证密码强度"""
    if len(password) < 6:
        return False, "密码长度必须至少为6个字符"
    return True, ""

def validate_username(username):
    """验证用户名"""
    """验证用户名"""
    if len(username) < 3 or len(username) > 20:
        return False, "用户名长度必须在3-20个字符之间"
    if not username.isalnum():
        return False, "用户名只能包含字母和数字"
        return False, "用户名只能包含字母和数字"
    return True, ""

@user_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('user.dashboard'))
        
    if request.method == 'POST':
        try:
            # 获取表单数据
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            
            # 基本验证
            if not all([username, email, password, confirm_password]):
                flash('所有字段都必须填写', 'danger')
                return render_template('user/register.html')
            
            # 基本验证
            if not all([username, email, password, confirm_password]):
                flash('所有字段都必须填写', 'danger')
                return render_template('user/register.html')
            
            # 验证用户输入
            if password != confirm_password:
                flash('两次输入的密码不一致', 'danger')
                return render_template('user/register.html')
            
            # 验证码强度
            is_valid, msg = validate_password(password)
            if not is_valid:
                flash(msg, 'danger')
                return render_template('user/register.html')
            
            # 验证用户名
            is_valid, msg = validate_username(username)
            if not is_valid:
                flash(msg, 'danger')
                return render_template('user/register.html')
            
            # 验证邮箱格式
            if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
                flash('邮箱格式不正确', 'danger')
                return render_template('user/register.html')
            
            # 检查用户名是否已存在
            if Users.query.filter_by(User_name=username).first():
                flash('用户名已存在', 'danger')
                return render_template('user/register.html')
            
            # 检查邮箱是否已注册
            if Users.query.filter_by(User_email=email).first():
                flash('邮箱已注册', 'danger')
                return render_template('user/register.html')
            
            # 创建新用户
            new_user = Users(
                User_name=username,
                User_email=email,
                User_passwordHash=generate_password_hash(password),
                User_role='Member',
                avatar_id='1'  # 默认头像
            )
            
            try:
                db.session.add(new_user)
                db.session.commit()
                
                # 记录审计日志
                log_audit('INSERT', 'Users', f'新用户注册: {username}')
                
                flash('注册成功！请登录', 'success')
                return redirect(url_for('user.login'))
                
            except Exception as e:
                db.session.rollback()
                print(f"数据库错误: {str(e)}")
                flash('注册失败，请稍后重试', 'danger')
                return render_template('user/register.html')
                
        except Exception as e:
            print(f"注册过程出错: {str(e)}")
            flash('注册失败，请稍后重试', 'danger')
            return render_template('user/register.html')
    
    return render_template('user/register.html')

@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember', False) == 'on'
        
        print(f"Login attempt - Username: {username}")
        
        # 测试数据库查询
        user = db_one_filter_record(Users, 'User_name', username)
        
        if not user:
            flash('用户名或密码错误', 'danger')
            return render_template('user/login.html')
        
        # 验证密码
        is_valid = check_password_hash(user.User_passwordHash, password)
        
        if is_valid:
            login_user(user, remember=remember)
            # 记录登录日志
            log_audit('Login', 'Users', f'用户 {username} 登录系统')
            next_page = request.args.get('next')
            if next_page and next_page != url_for('user.login'):
                return redirect(next_page)
            return redirect(url_for('home.index'))
        
        else:
            flash('用户名或密码错误', 'danger')
            return render_template('user/login.html')
        
    
    return render_template('user/login.html')

@user_bp.route('/logout')
@login_required
def logout():
    username = current_user.User_name
    # 记录登出日志
    log_audit('Logout', 'Users', f'用户 {username} 退出系统')
    username = current_user.User_name
    # 记录登出日志
    log_audit('Logout', 'Users', f'用户 {username} 退出系统')
    logout_user()
    return redirect(url_for('home.index'))

@user_bp.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    # 获取统计数据
    doc_count = Documents.query.count()
    user_count = Users.query.count()
    today = datetime.now().date()
    today_visits = UserBrowsingHistory.query.filter(
        func.date(UserBrowsingHistory.Browse_time) == today
    ).count()
    
    return render_template('user/admin_dashboard.html',
                         doc_count=doc_count,
                         user_count=user_count,
                         today_visits=today_visits)

@user_bp.route('/manage_documents')
@login_required
@admin_required
def manage_documents():
    return render_template('user/manage_documents.html')

@user_bp.route('/api/search_documents', methods=['POST'])
@login_required
@admin_required
def search_documents():
    try:
        data = request.get_json()
        keyword = data.get('keyword', '').strip()
        
        if not keyword:
            # 如果没有搜索关键词，返回所有文书
            results = DocumentDisplayView.query.all()
        else:
            # 使用视图进行搜索，添加册号搜索
            results = DocumentDisplayView.query.filter(
                or_(
                    DocumentDisplayView.Doc_id.like(f'%{keyword}%'),  # 添加册号搜索
                    DocumentDisplayView.Doc_title.like(f'%{keyword}%'),
                    DocumentDisplayView.ContractorInfo.like(f'%{keyword}%'),
                    DocumentDisplayView.ParticipantInfo.like(f'%{keyword}%')
                )
            ).all()
        
        # 格式化结果
        formatted_results = [{
            'doc_id': doc.Doc_id,
            'title': doc.Doc_title,
            'type': doc.Doc_type,
            'time': doc.Doc_time,
            'standard_time': doc.Doc_standardTime.strftime('%Y-%m-%d') if doc.Doc_standardTime else '',
            'contractors': doc.ContractorInfo,
            'participants': doc.ParticipantInfo
        } for doc in results]
        
        return jsonify(formatted_results)
        
    except Exception as e:
        print(f"搜索文书时出错: {str(e)}")
        return jsonify({'error': str(e)}), 500

@user_bp.route('/view_logs')
@login_required
@admin_required
def view_logs():
    """查看系统日志"""
    # 获取分页参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # 获取筛选参数
    action_type = request.args.get('action_type', '')
    target_table = request.args.get('target_table', '')
    
    # 构建查询
    query = AuditLog.query.order_by(AuditLog.Audit_timestamp.desc())
    
    # 应用筛选
    if action_type:
        query = query.filter(AuditLog.Audit_actionType == action_type)
    if target_table:
        query = query.filter(AuditLog.Audit_targetTable == target_table)
    
    # 执行分页查询
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    logs = pagination.items
    
    # 获取所有可能的操作类型和目标表（于筛选下拉框）
    action_types = db.session.query(AuditLog.Audit_actionType.distinct()).all()
    action_types = [t[0] for t in action_types]
    
    target_tables = db.session.query(AuditLog.Audit_targetTable.distinct()).all()
    target_tables = [t[0] for t in target_tables]
    
    return render_template('user/view_logs.html',
                         logs=logs,
                         pagination=pagination,
                         page=page,
                         per_page=per_page,
                         action_types=action_types,
                         target_tables=target_tables,
                         current_action_type=action_type,
                         current_target_table=target_table)

# 允许的图片文件扩展名
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class DocumentForm(FlaskForm):
    pass

@user_bp.route('/add_document', methods=['GET', 'POST'])
@login_required
@admin_required
def add_document():
    form = DocumentForm()  # 创建表单实例
    
    if request.method == 'POST':
        try:
            # 获取并验证册号
            doc_id = request.form.get('doc_id')
            if not doc_id or not re.match(r'^\d+-\d+-\d+-\d+$', doc_id):
                flash('册号格式不正确', 'danger')
                return redirect(request.url)
            
            # 检查册号是否已存在
            if Documents.query.get(doc_id):
                flash('该册号已存在', 'danger')
                return redirect(request.url)
                
            # 获取文书图片
            if 'document_image' not in request.files:
                flash('没有上传文件', 'danger')
                return redirect(request.url)
            
            file = request.files['document_image']
            if file.filename == '':
                flash('没有选择文件', 'danger')
                return redirect(request.url)
            
            if file and allowed_file(file.filename):
                try:
                    # 根据册号生成新的文件名
                    file_ext = file.filename.rsplit('.', 1)[1].lower()
                    new_filename = f'doc_img_{doc_id}.{file_ext}'
                    
                    # 确保存储路径存在
                    upload_folder = os.path.join(current_app.static_folder, 'images', 'documents')
                    os.makedirs(upload_folder, exist_ok=True)
                    
                    # 保存文件
                    file_path = os.path.join(upload_folder, new_filename)
                    file.save(file_path)
                    print(f"文件已保存到: {file_path}")
                    
                    # 使用相对路径
                    relative_path = os.path.join('images', 'documents', new_filename)
                    
                except Exception as e:
                    print(f'保存文件失败: {str(e)}')
                    flash(f'保存文件失败: {str(e)}', 'danger')
                    return redirect(request.url)
                
                # 获取文书文本
                original_text = request.form.get('document_text', '').strip()
                if not original_text:
                    flash('文书���本不能为空', 'danger')
                    return redirect(request.url)
                
                try:
                    # 处理文书信息
                    print(f"开始处理文书信息...")
                    doc_info = process_document_text(original_text, relative_path)
                    # 添加文书册号
                    doc_info['doc_id'] = doc_id
                    print(f"文书信息处理完成: {doc_info}")
                except Exception as e:
                    print(f'处理文书信息失败: {str(e)}')
                    flash(f'处理文书信息失败: {str(e)}', 'danger')
                    return redirect(request.url)
                
                try:
                    # 插入数据库
                    print(f"开始插入数据库...")
                    success, message = insert_document(doc_info)
                    print(f"数据库操作结果: success={success}, message={message}")
                    if success:
                        
                        # 记录审计日志，添加更多详细信息
                        log_audit('Insert', 'Documents', 
                                 f'管理员 {current_user.User_name} 添加了新文档: {doc_id}, 标题: {doc_info.get("title", "未知")}')
                        
                        flash('文书添加成功', 'success')
                        return redirect(url_for('user.manage_documents'))
                    else:
                        flash(f'文书添加失败: {message}', 'danger')
                        return redirect(request.url)
                except Exception as e:
                    print(f'数据库操作失败: {str(e)}')
                    flash(f'数据库操作失败: {str(e)}', 'danger')
                    return redirect(request.url)
            else:
                flash('不支持的文件类型', 'danger')
                flash('不支持的文件类型', 'danger')
                return redirect(request.url)
                
        except Exception as e:
            print(f'发生错误: {str(e)}')
            flash(f'发生错误: {str(e)}', 'danger')
            return redirect(request.url)
            
    return render_template('user/add_document.html', form=form)  # 传递表单到模板

@user_bp.route('/check_doc_id', methods=['POST'])
@login_required
@admin_required
def check_doc_id():
    try:
        data = request.get_json()
        doc_id = data.get('doc_id')
        
        # 检查格式
        if not re.match(r'^\d+-\d+-\d+-\d+$', doc_id):
            return jsonify({
                'exists': True, 
                'message': '册号格��不正确',
                'csrf_token': generate_csrf()  # 返回新的 CSRF token
            })
        
        # 检查是否存在
        existing_doc = Documents.query.get(doc_id)
        
        return jsonify({
            'exists': existing_doc is not None,
            'message': '册号已存在' if existing_doc else '册号可用',
            'csrf_token': generate_csrf()  # 返回新的 CSRF token
        })
        
    except Exception as e:
        print(f'检查册号时出错: {str(e)}')
        return jsonify({
            'error': str(e),
            'csrf_token': generate_csrf()  # 返回新的 CSRF token
        }), 500

@user_bp.route('/folder/<int:folder_id>')
@login_required
def folder_detail(folder_id):
    """显示收藏夹详情"""
    # 验证文件夹所有权
    folder = Folders.query.get_or_404(folder_id)
    if folder.User_id != current_user.User_id:
        flash('您没有权限访问该收藏夹', 'danger')
        return redirect(url_for('user.dashboard'))
    
    # 获取该收藏夹中的文书
    documents = (Documents.query
        .join(FolderContents, Documents.Doc_id == FolderContents.Doc_id)
        .filter(FolderContents.Folder_id == folder_id)
        .all())
    # 获取该收藏夹的文书类型统计信息
    stats = FolderDocumentStats.query.filter_by(Folder_id=folder_id).first()
    stats_dict = stats.to_dict() if stats else {}
    return render_template(
        'user/folder_detail.html',
        folder=folder,
        documents=documents,
        stats=stats_dict  # 将统计数据传递到模板
    )


@user_bp.route('/folder/<int:folder_id>/remove_document', methods=['POST'])
@login_required
def remove_document(folder_id):
    """从收藏夹中删除文书"""
    data = request.get_json()
    doc_id = data.get('doc_id')

    # 从 FolderContents 表中删除文书
    content = FolderContents.query.filter_by(Folder_id=folder_id, Doc_id=doc_id).first()
    if content:
        db.session.delete(content)
        db.session.commit()
        return jsonify({'success': True}), 200
    return jsonify({'error': '文书未找到'}), 404


def log_audit(action_type, target_table, description):
    """
    记录审计日志
    
    Args:
        action_type: 操作类型 (Insert/Update/Delete)
        target_table: 目标表名
        description: 操作描述
    """
    try:
        audit_log = AuditLog(
            User_id=current_user.User_id if current_user.is_authenticated else None,
            Audit_timestamp=datetime.now(),
            Audit_actionType=action_type,
            Audit_targetTable=target_table,
            Audit_actionDescription=description
        )
        db.session.add(audit_log)
        db.session.commit()
    except Exception as e:
        print(f"记录审计日志失败: {str(e)}")
        db.session.rollback()

@user_bp.route('/api/delete_document/<doc_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_document(doc_id):
    """删除文书API"""
    try:
        # 查找文书
        document = Documents.query.get(doc_id)
        if not document:
            return jsonify({
                'success': False,
                'error': '文书不存在'
            }), 404
            
        # 删除文书
        db.session.delete(document)
        db.session.commit()
        
        # 记录审计日志
        log_audit('DELETE', 'Documents', f'管理员删除了文书: {doc_id}')
        
        return jsonify({
            'success': True,
            'message': '文书删除成功'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"删除文书时出错: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

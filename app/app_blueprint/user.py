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
from Database.model import UserBrowsingHistory, Folders, Notes, Users, Documents, AuditLog
from Database.config import db
from datetime import datetime
from sqlalchemy import func
from functools import wraps
import os
from werkzeug.utils import secure_filename
from flask import current_app

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
        reading_history = db_one_filter_records(UserBrowsingHistory, 'User_id', current_user.User_id)
        folders = db_one_filter_records(Folders, 'User_id', current_user.User_id)
        
        return render_template('user/dashboard.html',
                             reading_history=reading_history[:10],
                             folders=folders)

@user_bp.route('/profile')
@login_required
def profile():
    """个人设置页面"""
    return render_template('user/profile.html')

@user_bp.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    # 获取表单数据
    username = request.form.get('username')
    email = request.form.get('email')
    new_password = request.form.get('new_password')
    avatar_id = request.form.get('avatar_id')
    
    # 更新用户信息
    update_data = {
        'User_name': username,
        'User_email': email,
        'avatar_id': avatar_id
    }
    
    if new_password:
        update_data['User_passwordHash'] = generate_password_hash(new_password)
    
    # 更新数据库
    db_update_key(Users, current_user.User_id, **update_data)
    
    flash('个人信息更新成功！', 'success')
    return redirect(url_for('user.dashboard'))

@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('user.dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember', False) == 'on'
        
        print(f"Login attempt - Username: {username}")
        
        # 测试数据库查询
        user = db_one_filter_record(Users, 'User_name', username)
        print(f"Query result - User found: {user is not None}")
        
        if user:
            print(f"User details - ID: {user.User_id}, Role: {user.User_role}")
            if check_password_hash(user.User_passwordHash, password):
                print("Password check: Success")
                login_user(user, remember=remember)
                next_page = request.args.get('next')
                if next_page:
                    return redirect(next_page)
                return redirect(url_for('user.dashboard'))
            else:
                print("Password check: Failed")
        
        else:
            flash('用户名或密码错误', 'danger')
    
    return render_template('user/login.html')

def validate_password(password):
    """验证密码强度"""
    if len(password) < 6:
        return False, "密码长度必须至少为6个字符"
    return True, ""

def validate_username(username):
    """验证用户名"""
    if len(username) < 3 or len(username) > 20:
        return False, "用户名长度必须在3-20个字符之间"
    if not username.isalnum():
        return False, "用户名不能包含字母和数字"
    return True, ""

@user_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('user.dashboard'))
        
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            
            # 验证用户输入
            if password != confirm_password:
                flash('两次输入的密码不一致', 'danger')
                return render_template('user/register.html')
            
            # 验证密码强度
            is_valid, msg = validate_password(password)
            if not is_valid:
                flash(msg, 'danger')
                return render_template('user/register.html')
            
            # 验证用户名
            is_valid, msg = validate_username(username)
            if not is_valid:
                flash(msg, 'danger')
                return render_template('user/register.html')
            
            # 创建新用户
            new_user = Users(
                User_name=username,
                User_email=email,
                User_passwordHash=generate_password_hash(password),
                User_role='Member',  # 默认角色
                avatar_id='1'  # 默认头像
            )
            
            try:
                db.session.add(new_user)
                db.session.commit()
                flash('注册成功！请登录', 'success')
                return redirect(url_for('user.login'))
            except Exception as e:
                db.session.rollback()
                print(f"数据库错误: {str(e)}")
                if "Duplicate entry" in str(e):
                    if "User_name" in str(e):
                        flash('用户名已存在', 'danger')
                    elif "User_email" in str(e):
                        flash('邮箱已注册', 'danger')
                    else:
                        flash('注册失败，请稍后重试', 'danger')
                else:
                    flash('注册失败，请稍后重试', 'danger')
                return render_template('user/register.html')
                
        except Exception as e:
            print(f"注册过程错误: {str(e)}")
            flash('注册失败，请稍后重试', 'danger')
            return render_template('user/register.html')
            
    return render_template('user/register.html')

@user_bp.route('/logout')
@login_required
def logout():
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
    data = request.get_json()
    keyword = data.get('keyword', '').strip()
    
    # 使用现有的搜索函数
    results = db_context_query(keyword)
    return jsonify([doc.to_dict() for doc in results])

@user_bp.route('/view_logs')
@login_required
@admin_required
def view_logs():
    """查看系统日志"""
    # 从 AuditLog 表中获取日志记录
    logs = AuditLog.query.order_by(AuditLog.Audit_timestamp.desc()).all()
    return render_template('user/view_logs.html', logs=logs)

# 允许的图片文件扩展名
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@user_bp.route('/add_document', methods=['GET', 'POST'])
@login_required
@admin_required
def add_document():
    if request.method == 'POST':
        try:
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
                    # 安全地获取文件名并保存
                    filename = secure_filename(file.filename)
                    # 确保存储路径存在
                    upload_folder = os.path.join(current_app.static_folder, 'images', 'documents')
                    os.makedirs(upload_folder, exist_ok=True)
                    # 保存文件
                    file_path = os.path.join(upload_folder, filename)
                    file.save(file_path)
                    print(f"文件已保存到: {file_path}")
                except Exception as e:
                    print(f'保存文件失败: {str(e)}')
                    flash(f'保存文件失败: {str(e)}', 'danger')
                    return redirect(request.url)
                
                # 获取文书文本
                original_text = request.form.get('document_text', '').strip()
                if not original_text:
                    flash('文书文本不能为空', 'danger')
                    return redirect(request.url)
                
                try:
                    # 处理文书信息
                    relative_path = os.path.join('images', 'documents', filename)
                    print(f"开始处理文书信息...")
                    doc_info = process_document_text(original_text, relative_path)
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
                return redirect(request.url)
                
        except Exception as e:
            print(f'发生错误: {str(e)}')
            flash(f'发生错误: {str(e)}', 'danger')
            return redirect(request.url)
            
    return render_template('user/add_document.html')

# 添加其他必要的路由...


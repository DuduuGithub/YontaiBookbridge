# 用户信息相关，有普通客户和管理员之分，管理员具有
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from utils import db_query_all, db_one_filter_records, db_update_key, db_one_filter_record, db_add
from Database.model import UserBrowsingHistory, Folders, Notes, Users
from Database.config import db

user_bp = Blueprint('user', __name__, 
                   template_folder='app/templates/user',
                   static_folder='app/static/user',
                   url_prefix='/user')

@user_bp.route('/dashboard')
@login_required
def dashboard():
    # 获取用户数据
    reading_history = db_one_filter_records(UserBrowsingHistory, 'User_id', current_user.User_id)
    folders = db_one_filter_records(Folders, 'User_id', current_user.User_id)
    
    return render_template('user/dashboard.html',
                         reading_history=reading_history[:10],  # 最近10条浏览记录
                         folders=folders)

@user_bp.route('/profile')
@login_required
def profile():
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
        return False, "用户名只能包含字母和数字"
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
                        flash('邮箱已��注册', 'danger')
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


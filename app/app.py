import sys
import os

# 将项目根目录添加到 sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from werkzeug.security import generate_password_hash
from flask import Flask, redirect, url_for
from app_blueprint import register_blueprints
from Database.model import *
from utils import *
from Database.config import db
import Database.config 
from flask_login import LoginManager
from sqlalchemy.sql import text

def init_database():
    with app.app_context():
        try:
            # 先删除视图和表
            try:
                db.session.execute(text('DROP VIEW IF EXISTS DocumentDisplayView'))
                db.session.commit()
            except:
                pass
            
            db.drop_all()
            db.session.commit()
            
            # 创建所有表
            db.create_all()
            db.session.commit()
            print("表创建成功！")
            # 这里未创建视图
            
            print("数据库初始化完成！，未创建视图")
            
        except Exception as e:
            print(f"数据库初始化失败: {str(e)}")
            db.session.rollback()
            raise

def create_admin():
    with app.app_context():
        # 检查管理员是否已存在
        if not Users.query.filter_by(User_name='admin').first():
            admin = Users(
                User_name='admin',
                User_passwordHash=generate_password_hash('admin123'),
                User_email='admin@example.com',
                User_role='Admin',
                avatar_id='1'
            )
            db.session.add(admin)
            db.session.commit()
            print("管理员账户创建成功")
        else:
            print("管理员账户已存在")

def createApp():
    app = Flask(__name__,
               static_folder='static',
               static_url_path='/static')
    
    # 加载配置
    app.config.from_object(Database.config)
    
    # 设置密钥
    app.secret_key = os.environ.get('SECRET_KEY', 'dev')
    
    # 初始化数据库
    db.init_app(app)
    
    app.config['SQLALCHEMY_ECHO'] = True
    
    # 添加自定义过滤器
    @app.template_filter('datetime')
    def format_datetime(value):
        if value is None:
            return ""
        return value.strftime('%Y-%m-%d %H:%M:%S')
    
    # 注册蓝图
    register_blueprints(app=app)
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'user.login'
    
    @login_manager.user_loader
    def load_user(user_id):
        return Users.query.get(int(user_id))
    
    return app

app = createApp()

# 根路由重定向到首页
@app.route('/')
def index():
    return redirect(url_for('home.index'))

# 返回一个JSON格式的收藏夹列表
@app.route('/get_all_folders', methods=['GET'])
def get_folders():
    folders = db_query_all(Folders)
    return jsonify(folders=folders)

if __name__ == '__main__':
    # 当数据库表结构发生变化时，需要执行一下这个
    # init_database()
    create_admin()  # 创建管理员账户
    app.run()





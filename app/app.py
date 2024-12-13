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

def init_database():
    with app.app_context():
        # 删除所有表
        db.drop_all()
        # 创建所有表
        db.create_all()  #这个函数的功能是对数据库没有这个表的话，创建这个表，如果存在，则不改变
        print("数据库初始化完成！")
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
               static_folder='static',  # 默认值，可以不写
               static_url_path='/static')  # 默认值，可以不写
    # 加载配置
    app.config.from_object(Database.config)
    
    # 设置密钥
    app.secret_key = os.environ.get('SECRET_KEY', 'dev')  # 在生产环境中应该使用环境变量
    
    # 初始化数据库
    db.init_app(app)

    app.config['SQLALCHEMY_ECHO'] = True
    
    # 添加自定义过滤器
    @app.template_filter('datetime')
    def format_datetime(value):
        if value is None:
            return ""
        return value.strftime('%Y-%m-%d %H:%M:%S')
    
    # 如果已经手动创建了数据库，可以删除自动创建表的代码
    with app.app_context():  # 创建应用上下文
        print("数据库表已加载")

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

# 根路由重���向到首页
@app.route('/')
def index():
    return redirect(url_for('home.index'))

# 返回一个JSON格式的收藏夹列表
@app.route('/get_all_folders', methods=['GET'])
def get_folders():
    folders = db_query_all(Folders)
    return jsonify(folders=folders)

if __name__ == '__main__':
    
    #当数据库表结构发生变化时，需要执行一下这个
    # init_database() 
    create_admin() # 创建管理员账户
    app.run(debug=True)





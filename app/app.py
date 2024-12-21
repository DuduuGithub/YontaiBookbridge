import sys
import os

# 将项目根目录添加到 sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from werkzeug.security import generate_password_hash
from flask import Flask, redirect, url_for, jsonify
from app_blueprint import register_blueprints
from Database.model import *
from utils import *
from Database.config import db
import Database.config 
from flask_login import LoginManager, current_user, login_required
from sqlalchemy.sql import text
from flask_wtf.csrf import CSRFProtect

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
            
<<<<<<< HEAD
=======
            # 创建视图
            create_view_sql = """
            CREATE VIEW DocumentDisplayView AS
            SELECT 
                d.Doc_id,
                d.Doc_title,
                d.Doc_type,
                d.Doc_summary,
                d.Doc_image_path,
                t1.createdData as Doc_time,
                t1.Standard_createdData as Doc_standardTime,
                CONCAT(
                    '《', 
                    (SELECT p1.Person_name FROM People p1 WHERE p1.Person_id = c.Alice_id),
                    '》《',
                    (SELECT p2.Person_name FROM People p2 WHERE p2.Person_id = c.Bob_id),
                    '》',
                    CASE 
                        WHEN r.Relation_type IS NOT NULL THEN CONCAT('（', r.Relation_type, '）')
                        ELSE ''
                    END
                ) as ContractorInfo,
                GROUP_CONCAT(
                    CONCAT('《', p.Person_name, '》（', pa.Part_role, '）')
                    ORDER BY pa.Part_role
                    SEPARATOR ''
                ) as ParticipantInfo
            FROM Documents d
            LEFT JOIN TimeRecord t1 ON d.Doc_createdTime_id = t1.Time_id
            LEFT JOIN Contractors c ON d.Doc_id = c.Doc_id
            LEFT JOIN Relations r ON (r.Alice_id = c.Alice_id AND r.Bob_id = c.Bob_id) 
                                OR (r.Alice_id = c.Bob_id AND r.Bob_id = c.Alice_id)
            LEFT JOIN Participants pa ON d.Doc_id = pa.Doc_id
            LEFT JOIN People p ON pa.Person_id = p.Person_id
            GROUP BY 
                d.Doc_id, 
                d.Doc_title, 
                d.Doc_type, 
                d.Doc_summary,
                d.Doc_image_path,
                t1.createdData,
                t1.Standard_createdData,
                c.Alice_id,
                c.Bob_id,
                r.Relation_type
            """
            
            db.session.execute(text(create_view_sql))
            db.session.commit()
            print("视图创建成功！")
            
>>>>>>> 7ba48e2da46a5638e85cdb81abcf6d2b685ea5fb
            print("数据库初始化完成！")
            
        except Exception as e:
            print(f"数据库初始化失败: {str(e)}")
            db.session.rollback()
            raise

def create_admin():
    """创建管理员账户"""
    with app.app_context():
        # 检查是否已存在管理员账户
        admin = Users.query.filter_by(User_role='Admin').first()
        if not admin:
            # 使用 werkzeug.security 中的 generate_password_hash 来哈希密码
            password_hash = generate_password_hash('admin123')
            admin = Users(
                User_name='admin',
                User_passwordHash=password_hash,  # 存储哈希后的密码
                User_email='admin@example.com',
                User_role='Admin',
                avatar_id='1'
            )
            db.session.add(admin)
            db.session.commit()
            print("管理员账户创建成功")
        else:
            # 如果管理员已存在但密码是明文，更新为哈希值
            if admin.User_passwordHash == 'admin123':  # 检查是否是明文密码
                admin.User_passwordHash = generate_password_hash('admin123')
                db.session.commit()
                print("管理员密码已更新为哈希值")
            print("管理员账户已存在")

def createApp():
    app = Flask(__name__,
               static_folder='static',
               static_url_path='/static')
               
    # 初始化 CSRF 保护
    csrf = CSRFProtect()
    csrf.init_app(app)
<<<<<<< HEAD
    
    # 设置密钥（确保这个密钥是安全的随机值）
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24))
=======
>>>>>>> 7ba48e2da46a5638e85cdb81abcf6d2b685ea5fb
    
    # 加载配置
    app.config.from_object(Database.config)
    
<<<<<<< HEAD
=======
    # 设置密钥
    app.secret_key = os.environ.get('SECRET_KEY', 'dev')

>>>>>>> 7ba48e2da46a5638e85cdb81abcf6d2b685ea5fb
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
@app.route('/api/get_folders', methods=['GET'])
@login_required
def get_folders():
    # 只获取当前用户的收藏夹
    folders = Folders.query.filter_by(User_id=current_user.User_id).all()
    folder_list = [{
        'Folder_id': folder.Folder_id,
        'Folder_name': folder.Folder_name,
        'User_id': folder.User_id,
        'Remarks': folder.Remarks,
        'Folder_createdAt': folder.Folder_createdAt.strftime('%Y-%m-%d %H:%M:%S') if folder.Folder_createdAt else None
    } for folder in folders]
    return jsonify(folders=folder_list)

if __name__ == '__main__':
    # 当数据库表结构发生变化时，需执行一下这个
    # init_database()
<<<<<<< HEAD
    create_admin()  # 创建管理员账
=======
    create_admin()  # 创建管理员账户
>>>>>>> 7ba48e2da46a5638e85cdb81abcf6d2b685ea5fb
    app.run()
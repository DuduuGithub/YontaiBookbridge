from werkzeug.security import generate_password_hash
from Database.model import Users

def init_database():
    with app.app_context():
        # 删除所有表
        db.drop_all()
        # 创建所有表
        db.create_all()
        
        # 创建视图
        with open('Database/create_views.sql', 'r', encoding='utf-8') as f:
            sql = f.read()
            db.session.execute(text(sql))
        
        # 创建管理员用户
        admin = Users(
            User_name='admin',
            User_password=generate_password_hash('admin123'),  # 设置默认密码
            User_email='admin@example.com',
            User_type='admin'
        )
        db.session.add(admin)
        db.session.commit()
            
        print("数据库初始化完成！")
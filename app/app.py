import sys
import os

# 将项目根目录添加到 sys.path,Python默认从当前文件所在的目录开始找，也就是app文件夹开始找
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask
from app_blueprint import register_blueprints
from Database.model import *

from Database.config import db
import Database.config 




def createApp():
    
    app = Flask(__name__)
    # 加载配置
    app.config.from_object(Database.config)

    # 初始化数据库
    db.app=app
    db.init_app(app)
 
     # 确保只在首次运行时创建数据库表
    with app.app_context():  # 创建应用上下文
        if not os.path.exists(Database.config.SQLALCHEMY_DATABASE_URI):  # 检查数据库文件是否存在
            db.create_all()  # 实现py表与数据库表的映射
            print("数据库表已创建")
        
    #注册蓝图
    register_blueprints(app=app)
    
    return app


app=createApp()
app.run()

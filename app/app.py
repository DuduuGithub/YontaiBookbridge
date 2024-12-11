import sys
import os

# 将项目根目录添加到 sys.path,Python默认从当前文件所在的目录开始找，也就是app文件夹开始找
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask
from app_blueprint import register_blueprints
from Database.model import *
from utils import *
from Database.config import db
import Database.config 




def createApp():
    app = Flask(__name__)
    # 加载配置
    app.config.from_object(Database.config)

    # 初始化数据库
    db.app = app
    db.init_app(app)

    # 如果已经手动创建了数据库，可以删除自动创建表的代码
    with app.app_context():  # 创建应用上下文
        # 这里不再调用 db.create_all()，因为你已经在 MySQL 中创建了表
        # 如果你希望检查表是否存在，可以手动检查
        print("数据库表已加载")

    # 注册蓝图
    register_blueprints(app=app)
    
    return app


app=createApp()
app.run()

# 返回一个JSON格式的收藏夹列表
@app.route('/get_all_folders', methods=['GET'])
def get_folders():

    folders= db_query_all(Folders)
    return jsonify(folders=folders)
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

USERNAME = 'root'
PASSWORD = '123456'
HOST ='127.0.0.1'
PORT = '3306'
DATABASE ='flaskdb'
DB_URI = 'mysql://{}:{}@{}:{}/{}?charset=utf8'.format(USERNAME,PASSWORD,HOST,PORT,DATABASE)

# 设置数据库的连接URI
SQLALCHEMY_DATABASE_URI = DB_URI
# 设置动态追踪修改,如未设置只会提示警告
SQLALCHEMY_TRACK_MODIFICATIONS = False
# 设置查询时会显示原始SQL语句
SQLALCHEMY_ECHO = True
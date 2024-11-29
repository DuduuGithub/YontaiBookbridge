from flask_sqlalchemy import SQLAlchemy
import pymysql
pymysql.install_as_MySQLdb() 
db = SQLAlchemy()

USERNAME = 'root'
PASSWORD = '123456'
HOST ='127.0.0.1'
PORT = '3306'
DATABASE ='java_bookdb'
DB_URI = 'mysql://{}:{}@{}:{}/{}?charset=utf8'.format(USERNAME,PASSWORD,HOST,PORT,DATABASE)

SQLALCHEMY_DATABASE_URI = DB_URI
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ECHO = True


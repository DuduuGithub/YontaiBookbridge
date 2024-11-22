# 主界面以及登录等小功能

from flask import Blueprint

home_bp=Blueprint('home',__name__,static_folder='static/home',url_prefix='/home')

# 主页面
@home_bp.route('/')
def home():
    pass


@home_bp.route('login')
def login():
    pass

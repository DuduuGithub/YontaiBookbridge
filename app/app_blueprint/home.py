# 主界面以及登录等小功能

from flask import Blueprint, render_template

home_bp = Blueprint('home', __name__, 
                   template_folder='app/templates/home',
                   static_folder='app/static/home',
                   url_prefix='/home')

# 主页面
@home_bp.route('/')
def index():
    return render_template('home/index.html')


@home_bp.route('/login')
def login():
    pass

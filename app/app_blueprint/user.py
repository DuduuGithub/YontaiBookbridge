# 用户信息相关
from flask import Blueprint

user_bp=Blueprint('user',__name__,static_folder='static/user',url_prefix='/user')


# 用户信息相关，有普通客户和管理员之分，管理员具有
from flask import Blueprint

user_bp=Blueprint('user',__name__,template_folder='app/templates/user',static_folder='app/static/user',url_prefix='/user')


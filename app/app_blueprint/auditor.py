# 审核
from flask import Blueprint

auditor_bp=Blueprint('auditor',__name__,static_folder='static/auditor',url_prefix='/auditor')
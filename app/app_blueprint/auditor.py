# 审核
from flask import Blueprint

auditor_bp=Blueprint('auditor',__name__,template_folder='app/templates/auditor',static_folder='app/static/auditor',url_prefix='/auditor')
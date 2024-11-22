from flask import Blueprint

analysis_bp=Blueprint('analysis',__name__,static_folder='static/analysis',url_prefix='/analysis')

from flask import Blueprint

reader_bp=Blueprint('reader',__name__,static_folder='static/reader',url_prefix='/reader')


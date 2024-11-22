# 阅读器 
# (1)文书详情阅读，标记、笔记、导出
# (2)讨论区，差错提交

from flask import Blueprint

reader_bp=Blueprint('reader',__name__,static_folder='static/reader',url_prefix='/reader')


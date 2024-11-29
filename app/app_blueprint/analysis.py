from flask import Blueprint, jsonify, render_template, request
from utils import *
from Database.model import Folders

analysis_bp=Blueprint('analysis',__name__,template_folder='app/templates/analysis',static_folder='app/static/analysis',url_prefix='/analysis')



@analysis_bp.route('/')
def index():
    return render_template('/index.html')


# 返回一个JSON格式的收藏夹列表
@analysis_bp.route('/get_all_folders', methods=['GET'])
def get_folders():

    folders= db_query_all(Folders)
    return jsonify(folders=folders)

@analysis_bp.route('/generate_graph', methods=['POST'])
def generate_graph():
    data = request.get_json()
    folders = data.get('folders', [])

    # 根据选择的收藏夹生成图数据
    # 这里是一个示例，可以根据实际需求进行修改
    nodes = []
    edges = []

    for i, folder in enumerate(folders):
        nodes.append({'id': str(i+1), 'label': folder})
        if i > 0:
            edges.append({'source': str(i), 'target': str(i+1), 'label': '关系'})

    return jsonify({
        'success': True,
        'data': {
            'nodes': nodes,
            'edges': edges
        }
    })
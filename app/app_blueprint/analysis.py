from flask import Blueprint, jsonify, render_template, request
from utils import *
from Database.model import Folders

analysis_bp=Blueprint('analysis',__name__,template_folder='app/templates/analysis',static_folder='app/static/analysis',url_prefix='/analysis')



@analysis_bp.route('/')
def index():
    return render_template('/index.html')


# 本蓝图而来的函数
# 返回一个JSON格式的收藏夹列表



@analysis_bp.route('/generate_graph', methods=['POST'])
def generate_graph():
    data = request.get_json()
    folders = data.get('folders', [])
    nodes = []
    edges = []
    # 使用 set 保证节点不重复
    node_set = set()
    
    
    for folder in folders:
        document=db_query_key(Documents,folder.Doc_id)
        
        # Relations
        contractor=db_query_key(Contractors,document.Doc_id)
        
        Alice_id=contractor.Alice_id
        Bob_id=contractor.Bob_id
        
        Alice_name=db_query_key(Persons,Alice_id).Person_name
        Bob_name=db_query_key(Persons,Bob_id).Person_name
        
        relation_type=get_relation_by_ids(Alice_id,Bob_id).Relation_type
        
        # 处理节点：使用 Alice_name 和 Bob_name
        if Alice_id not in node_set:
            node_set.add(Alice_name)
            nodes.append({'id': Alice_id, 'label': Alice_name})  # 节点格式为字典
        if Bob_id not in node_set:
            node_set.add(Bob_name)
            nodes.append({'id': Bob_id, 'label': Bob_name})  # 节点格式为字典
        
        # 添加边：根据关系，directed是设置关系边为无方向
        edges.append({'source': Alice_id, 
                      'target': Bob_id, 
                      'label': relation_type,
                      'directed': False  })
        
        # Role
        participants=db_one_filter_records(Participants,'Doc_id',document.Doc_id)
        for participant in participants:
            participant_id=participant.Person_id
            participant_name=db_query_key(Persons,participant_id).Person_name
            if participant_id not in node_set:
                node_set.add(participant_name)
                nodes.append({'id': participant_id, 'label': participant_name})  # 节点格式为字典
            
            edges.append({'source': participant_id,
                          'target': Alice_id, 
                          'label': participant.Part_role+'相关文书编号为'+str(document.Doc_id),
                          'directed': True})
    
    # 这里是一个示例，可以根据实际需求进行修改
    nodes_test=[{'id':'1','label':'alice'},{'id':'2','label':'bob'},{'id':'3','label':'carol'}]
    edges_test=[{'source':'1','target':'2','label':'叔侄','directed':False},{'source':'3','target':'2','label':'父母','directed':False}]
    
    return jsonify({
        'success': True,
        'data': {
            'nodes': nodes_test,
            'edges': edges_test
        }
    })
    
    # return jsonify({
    #     'success': True,
    #     'data': {
    #         'nodes': nodes,
    #         'edges': edges
    #     }
    # })
from flask import Blueprint, jsonify, render_template, request
from utils import *
from Database.model import Folders, FolderContents, Documents, TimeRecord
from flask_login import current_user
from sqlalchemy.sql import func

analysis_bp = Blueprint('analysis', __name__, url_prefix='/analysis')

@analysis_bp.route('/')
def index():
    """
    渲染分析主页面
    """
    try:
        return render_template('analysis/index.html')
    except Exception as e:
        logging.error(f"Error rendering analysis template: {str(e)}")
        return f"Error: {str(e)}", 500


@analysis_bp.route('/api/get_folders', methods=['GET'])
def get_folders():
    """
    获取当前用户的收藏夹列表
    """
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': '用户未登录'}), 401

    try:
        user_id = current_user.User_id
        folders = Folders.query.filter_by(User_id=user_id).all()

        folder_list = [{'id': folder.Folder_id, 'name': folder.Folder_name} for folder in folders]
        return jsonify({'success': True, 'folders': folder_list})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取收藏夹失败: {str(e)}'}), 500



@analysis_bp.route('/generate_graph', methods=['GET'])
def generate_graph():
    """
    生成关系网络的节点和边数据
    """
    try:
        folder_id = request.args.get('folder_id')
        if not folder_id:
            return jsonify({'success': False, 'message': '缺少 folder_id 参数'}), 400

        # 验证 folder_id 是否是有效的收藏夹 ID
        folder = Folders.query.filter_by(Folder_id=folder_id).first()
        if not folder:
            return jsonify({'success': False, 'message': '无效的 folder_id！'}), 400

        # 查询收藏夹中的文书
        folder_contents = db.session.query(FolderContents.Doc_id).filter(FolderContents.Folder_id == folder_id).all()
        doc_ids = [item[0] for item in folder_contents]

        if not doc_ids:
            return jsonify({'success': False, 'message': '该收藏夹中没有文书'}), 400

        nodes = []
        edges = []
        node_set = set()

        for doc_id in doc_ids:
            contractor = db.session.query(Contractors).filter(Contractors.Doc_id == doc_id).first()
            if contractor:
                alice_id = contractor.Alice_id
                bob_id = contractor.Bob_id

                # 优化查询：批量查询人物名称
                people_names = db.session.query(People.Person_id, People.Person_name).filter(
                    People.Person_id.in_([alice_id, bob_id])
                ).all()
                alice_name = next((name for pid, name in people_names if pid == alice_id), None)
                bob_name = next((name for pid, name in people_names if pid == bob_id), None)

                # 查询关系类型
                relation_type = db.session.query(Relations.Relation_type).filter(
                    ((Relations.Alice_id == alice_id) & (Relations.Bob_id == bob_id)) |
                    ((Relations.Alice_id == bob_id) & (Relations.Bob_id == alice_id))
                ).scalar()

                if alice_id not in node_set:
                    node_set.add(alice_id)
                    nodes.append({'id': alice_id, 'label': alice_name})
                if bob_id not in node_set:
                    node_set.add(bob_id)
                    nodes.append({'id': bob_id, 'label': bob_name})

                edges.append({'source': alice_id, 'target': bob_id, 'label': relation_type or '未知关系', 'directed': False})

            participants = db.session.query(Participants).filter(Participants.Doc_id == doc_id).all()
            for participant in participants:
                participant_id = participant.Person_id
                participant_role = participant.Part_role

                participant_name = db.session.query(People.Person_name).filter(People.Person_id == participant_id).scalar()

                if participant_id not in node_set:
                    node_set.add(participant_id)
                    nodes.append({'id': participant_id, 'label': participant_name})

                if contractor:
                    edges.append({
                        'source': participant_id,
                        'target': contractor.Alice_id,
                        'label': f'{participant_role}（文书编号: {doc_id}）',
                        'directed': True
                    })

        # 增加元数据返回
        return jsonify({
            'success': True,
            'data': {
                'nodes': nodes,
                'edges': edges,
                'metadata': {
                    'node_count': len(nodes),
                    'edge_count': len(edges)
                }
            }
        })

    except Exception as e:
        logging.error(f"Error generating graph: {str(e)}")
        return jsonify({'success': False, 'message': f"服务器内部错误：{str(e)}"}), 500



@analysis_bp.route('/relationship_network', methods=['GET'])
def relationship_network():
    """
    渲染人际关系网络分析页面
    """
    folder_id = request.args.get('folder_id', None)

    if not folder_id:
        return "错误：缺少收藏夹 ID 参数！", 400

    # 可加入逻辑：验证 folder_id 是否有效

    return render_template('analysis/relationship_network.html', folder_id=folder_id)





@analysis_bp.route('/api/get_statistics', methods=['GET'])
def statistics_data():
    """
    获取统计数据 API
    """
    source_id = request.args.get('folder_id', None)  # 改为前端传递的参数名称
    dimension = request.args.get('dimension', None)

    # 参数校验
    if not source_id or not dimension:
        return jsonify({'success': False, 'message': '缺少参数！'}), 400

    if dimension not in ['time', 'type']:
        return jsonify({'success': False, 'message': '无效的统计维度！'}), 400

    # 验证 source_id 是否是有效的收藏夹 ID
    folder = Folders.query.filter_by(Folder_id=source_id).first()
    if not folder:
        return jsonify({'success': False, 'message': '无效的 folder_id！'}), 400

    try:
        # 查询统计数据逻辑
        if dimension == 'time':
            data = db.session.query(
                TimeRecord.Standard_createdData.label('time'),
                func.count(Documents.Doc_id).label('count')
            ).join(TimeRecord, Documents.Doc_createdTime_id == TimeRecord.Time_id) \
             .join(FolderContents, Documents.Doc_id == FolderContents.Doc_id) \
             .filter(FolderContents.Folder_id == source_id) \
             .group_by(TimeRecord.Standard_createdData) \
             .all()

            chart_data = {
                'labels': [record.time for record in data],
                'datasets': [{
                    'label': '文书数量',
                    'data': [record.count for record in data],
                    'backgroundColor': 'rgba(54, 162, 235, 0.5)',
                    'borderColor': 'rgba(54, 162, 235, 1)',
                    'borderWidth': 1
                }]
            }

        elif dimension == 'type':
            data = db.session.query(
                Documents.Doc_type.label('type'),
                func.count(Documents.Doc_id).label('count')
            ).join(FolderContents, Documents.Doc_id == FolderContents.Doc_id) \
             .filter(FolderContents.Folder_id == source_id) \
             .group_by(Documents.Doc_type) \
             .all()

            chart_data = {
                'labels': [record.type for record in data],
                'datasets': [{
                    'label': '文书数量',
                    'data': [record.count for record in data],
                    'backgroundColor': [
                        'rgba(255, 99, 132, 0.5)', 'rgba(54, 162, 235, 0.5)', 'rgba(255, 206, 86, 0.5)'
                    ],
                    'borderColor': [
                        'rgba(255, 99, 132, 1)', 'rgba(54, 162, 235, 1)', 'rgba(255, 206, 86, 1)'
                    ],
                    'borderWidth': 1
                }]
            }

        return jsonify({'success': True, 'chartData': chart_data})

    except Exception as e:
        return jsonify({'success': False, 'message': f'统计数据查询失败: {str(e)}'}), 500



    




from flask import Blueprint, request, make_response
from io import StringIO
import csv
import logging
@analysis_bp.route('/api/export_statistics', methods=['GET'])
def export_statistics():
    """
    导出统计分析结果
    """
    source_id = request.args.get('source_id', None)
    dimension = request.args.get('dimension', None)

    if not source_id or not dimension:
        return "缺少参数！", 400

    try:
        # 查询统计数据逻辑
        data = []
        if dimension == 'time':
            # 示例按时间统计逻辑
            data = [
                ["时间点", "统计值"],
                ["2023-01-01", 10],
                ["2023-02-01", 20]
            ]
        elif dimension == 'type':
            # 示例按类型统计逻辑
            data = [
                ["类型", "统计值"],
                ["类型A", 15],
                ["类型B", 25]
            ]
        else:
            return "无效的统计维度！", 400

        # 生成 CSV 文件内容
        output = StringIO()
        writer = csv.writer(output)
        writer.writerows(data)
        file_content = output.getvalue()
        output.close()

        # 返回 CSV 文件响应
        response = make_response(file_content)
        response.headers["Content-Disposition"] = "attachment; filename=statistics_export.csv"
        response.headers["Content-Type"] = "text/csv"
        return response
    except Exception as e:
        logging.error(f"导出统计失败: {str(e)}")
        return f"导出失败: {str(e)}", 500



@analysis_bp.route('/statistics_analysis', methods=['GET'])
def statistics_analysis():
    """
    渲染统计分析页面
    """
    source_id = request.args.get('source_id', None)
    dimension = request.args.get('dimension', None)

    # 参数校验
    if not source_id or not dimension:
        return "错误：缺少参数！", 400

    if dimension not in ['time', 'type']:
        return "错误：无效的统计维度！", 400

    folder = Folders.query.filter_by(Folder_id=source_id).first()
    if not folder:
        return "错误：无效的 source_id！", 400

    # 渲染页面
    return render_template(
        'analysis/statistics_analysis.html', 
        source_id=source_id, 
        dimension=dimension
    )


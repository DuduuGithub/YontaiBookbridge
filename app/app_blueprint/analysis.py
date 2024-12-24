from flask import Blueprint, jsonify, render_template, request, make_response
from utils import *
from Database.model import Folders, FolderContents, Documents, TimeRecord, Contractors, Relations, People
from flask_login import current_user
from sqlalchemy.sql import func
from io import StringIO
import csv
import logging

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
        # 添加日志调试
        logging.debug(f"Fetching folders for user_id: {user_id}")
        
        folders = Folders.query.filter_by(User_id=user_id).all()
        
        # 添加日志调试
        logging.debug(f"Found {len(folders)} folders")
        
        folder_list = [{'id': folder.Folder_id, 'name': folder.Folder_name} for folder in folders]
        return jsonify({'success': True, 'folders': folder_list})
    except Exception as e:
        logging.error(f"Error fetching folders: {str(e)}")
        return jsonify({'success': False, 'message': f'获取收藏夹失败: {str(e)}'}), 500



@analysis_bp.route('/generate_graph', methods=['GET'])
def generate_graph():
    """
    生成关系网络的节点和边数据 - 只显示Relations表中的关系
    同名的人物会被合并为同一个节点
    如果一个人名包含另一个人名(如"叔文藻"包含"文藻")，则认为是同一个人，使用较长的名字
    """
    try:
        folder_id = request.args.get('folder_id')
        if not folder_id:
            return jsonify({'success': False, 'message': '缺少 folder_id 参数'}), 400

        logging.debug(f"Generating graph for folder_id: {folder_id}")

        # 验证 folder_id
        folder = Folders.query.filter_by(Folder_id=folder_id).first()
        if not folder:
            return jsonify({'success': False, 'message': '无效的 folder_id！'}), 400

        # 获取收藏夹中的文书ID
        folder_contents = db.session.query(FolderContents.Doc_id).filter(
            FolderContents.Folder_id == folder_id
        ).all()
        doc_ids = [item[0] for item in folder_contents]

        if not doc_ids:
            return jsonify({'success': False, 'message': '该收藏夹中没有文书'}), 400

        # 获取这些文书相关的所有人物ID
        person_ids = set()
        contractors = db.session.query(Contractors).filter(
            Contractors.Doc_id.in_(doc_ids)
        ).all()
        
        for contractor in contractors:
            person_ids.add(contractor.Alice_id)
            person_ids.add(contractor.Bob_id)

        if not person_ids:
            return jsonify({'success': False, 'message': '未找到相关人物关系'}), 400

        # 修改查询逻辑，排除 Relation_type 为 "null" 的记录
        relations = db.session.query(Relations).filter(
            db.and_(
                db.or_(
                    Relations.Alice_id.in_(person_ids),
                    Relations.Bob_id.in_(person_ids)
                ),
                Relations.Relation_type != "null"  # 只排除字符串 "null"
            )
        ).all()

        # 添加日志，查看实际查询到的关系
        logging.debug(f"Found relations: {[(r.Alice_id, r.Bob_id, r.Relation_type) for r in relations]}")

        # 收集需要显示的所有人物ID
        related_person_ids = set()
        for relation in relations:
            related_person_ids.add(relation.Alice_id)
            related_person_ids.add(relation.Bob_id)

        # 获取这些人物的信息
        people = db.session.query(People).filter(
            People.Person_id.in_(related_person_ids)
        ).all()

        # 处理名字映射
        name_groups = {}  # 用于存储相关名字组
        all_names = [person.Person_name for person in people]
        
        # 按名字长度降序排序，确保较长的名字先被处理
        all_names.sort(key=len, reverse=True)
        
        # 构建名字组
        for name in all_names:
            found_group = False
            for group_name in list(name_groups.keys()):
                # 如果当前名字包含在组名中，或组名包含在当前名字中
                if name in group_name or group_name in name:
                    # 使用较长的名字作为组名
                    new_group_name = name if len(name) > len(group_name) else group_name
                    if group_name != new_group_name:
                        name_groups[new_group_name] = name_groups.pop(group_name)
                    name_groups[new_group_name].add(name)
                    found_group = True
                    break
            if not found_group:
                name_groups[name] = {name}

        # 创建名字到标准名字(组名)的映射
        name_to_standard = {}
        for standard_name, group in name_groups.items():
            for name in group:
                name_to_standard[name] = standard_name

        # 创建标准名字到ID的映射
        standard_name_to_id = {}
        id_to_standard_name = {}
        for person in people:
            standard_name = name_to_standard[person.Person_name]
            if standard_name not in standard_name_to_id:
                standard_name_to_id[standard_name] = person.Person_id
            id_to_standard_name[person.Person_id] = standard_name

        # 构建节点和边
        nodes = []
        edges = set()  # 使用集合去重

        # 添加节点 - 只为每个标准名字添加一个节点
        added_names = set()
        for person_id in related_person_ids:
            if person_id in id_to_standard_name:
                standard_name = id_to_standard_name[person_id]
                if standard_name not in added_names:
                    nodes.append({
                        'id': standard_name_to_id[standard_name],
                        'label': standard_name
                    })
                    added_names.add(standard_name)

        # 添加边 - 使用标准名字来判断重复
        for relation in relations:
            alice_standard_name = id_to_standard_name[relation.Alice_id]
            bob_standard_name = id_to_standard_name[relation.Bob_id]
            alice_id = standard_name_to_id[alice_standard_name]
            bob_id = standard_name_to_id[bob_standard_name]
            
            # 创建边的唯一标识
            edge_key = tuple(sorted([alice_id, bob_id]) + [relation.Relation_type])
            if edge_key not in edges:
                edges.add(edge_key)

        # 将边的集合转换为列表
        edges_list = [
            {
                'source': edge[0],
                'target': edge[1],
                'label': edge[2],
                'directed': False
            }
            for edge in edges
        ]

        # 添加日志，查看生成的节点和边
        logging.debug(f"Generated nodes: {nodes}")
        logging.debug(f"Generated edges: {edges_list}")

        return jsonify({
            'success': True,
            'data': {
                'nodes': nodes,
                'edges': edges_list,
                'metadata': {
                    'node_count': len(nodes),
                    'edge_count': len(edges_list)
                }
            }
        })

    except Exception as e:
        logging.error(f"Error generating graph: {str(e)}")
        return jsonify({'success': False, 'message': f"生成网络图失败：{str(e)}"}), 500




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
def get_statistics():
    """
    获取统计数据 API
    """
    try:
        folder_id = request.args.get('folder_id')
        dimension = request.args.get('dimension')
        
        if not folder_id or not dimension:
            return jsonify({'success': False, 'error': '缺少必要参数'}), 400

        # 验证文件夹是否存在
        folder = Folders.query.filter_by(Folder_id=folder_id).first()
        if not folder:
            return jsonify({'success': False, 'error': '无效的文件夹ID'}), 400

        if dimension == 'time':
            # 获取该收藏夹中所有文书的时间分布
            time_stats = db.session.query(
                TimeRecord.createdData,
                func.count(Documents.Doc_id).label('count')
            ).join(
                Documents,
                Documents.Doc_createdTime_id == TimeRecord.Time_id
            ).join(
                FolderContents,
                FolderContents.Doc_id == Documents.Doc_id
            ).filter(
                FolderContents.Folder_id == folder_id
            ).group_by(
                TimeRecord.createdData
            ).order_by(
                TimeRecord.createdData
            ).all()

            # 直接返回时间统计结果，不需要进一步的粒度处理
            if not time_stats:
                return jsonify({
                    'success': True,
                    'bar_chart': {'labels': [], 'values': []},
                    'pie_chart': {'labels': [], 'values': []}
                })

            # 准备图表数据
            labels = [stat[0] for stat in time_stats]  # 时间数据
            values = [stat[1] for stat in time_stats]  # 对应的数量

            return jsonify({
                'success': True,
                'bar_chart': {
                    'labels': labels,
                    'values': values
                },
                'pie_chart': {
                    'labels': labels,
                    'values': values
                }
            })

        elif dimension == 'type':
            # 获取该收藏夹中所有文书的类型分布
            type_stats = db.session.query(
                Documents.Doc_type,
                func.count(Documents.Doc_id).label('count')
            ).join(
                FolderContents,
                FolderContents.Doc_id == Documents.Doc_id
            ).filter(
                FolderContents.Folder_id == folder_id
            ).group_by(
                Documents.Doc_type
            ).order_by(
                Documents.Doc_type
            ).all()

            if not type_stats:
                return jsonify({
                    'success': True,
                    'bar_chart': {'labels': [], 'values': []},
                    'pie_chart': {'labels': [], 'values': []}
                })

            # 准备图表数据
            labels = [stat[0] for stat in type_stats]  # 文书类型
            values = [stat[1] for stat in type_stats]  # 对应的数量

            return jsonify({
                'success': True,
                'bar_chart': {
                    'labels': labels,
                    'values': values
                },
                'pie_chart': {
                    'labels': labels,
                    'values': values
                }
            })

        else:
            return jsonify({'success': False, 'error': '无效的统计维度'}), 400

    except Exception as e:
        logging.error(f"Error generating statistics: {str(e)}")
        return jsonify({'success': False, 'error': f'生成统计数据失败：{str(e)}'}), 500




    




@analysis_bp.route('/api/export_statistics', methods=['GET'])
def export_statistics():
    """
    导出统计分析结果
    """
    try:
        folder_id = request.args.get('source_id')
        dimension = request.args.get('dimension')

        if not folder_id or not dimension:
            return "缺少参数！", 400

        if dimension == 'time':
            # 获取时间维度的统计数据
            time_stats = db.session.query(
                TimeRecord.createdData,
                func.count(Documents.Doc_id).label('count')
            ).join(
                Documents,
                Documents.Doc_createdTime_id == TimeRecord.Time_id
            ).join(
                FolderContents,
                FolderContents.Doc_id == Documents.Doc_id
            ).filter(
                FolderContents.Folder_id == folder_id
            ).group_by(
                TimeRecord.createdData
            ).order_by(
                TimeRecord.createdData
            ).all()

            # 准备 CSV 数据
            data = [
                ["年份", "文书数量"]  # CSV 表头
            ]
            # 添加统计数据
            for stat in time_stats:
                data.append([stat[0], stat[1]])  # stat[0] 是 createdData，stat[1] 是 count

        elif dimension == 'type':
            # 获取类型维度的统计数据
            type_stats = db.session.query(
                Documents.Doc_type,
                func.count(Documents.Doc_id).label('count')
            ).join(
                FolderContents,
                FolderContents.Doc_id == Documents.Doc_id
            ).filter(
                FolderContents.Folder_id == folder_id
            ).group_by(
                Documents.Doc_type
            ).order_by(
                Documents.Doc_type
            ).all()

            # 准备 CSV 数据
            data = [
                ["文书类型", "文书数量"]  # CSV 表头
            ]
            # 添加统计数据
            for stat in type_stats:
                data.append([stat[0], stat[1]])

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
        response.headers["Content-Disposition"] = f"attachment; filename=statistics_{dimension}.csv"
        response.headers["Content-Type"] = "text/csv; charset=utf-8"
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
        return "错误：无效的统计维度", 400

    folder = Folders.query.filter_by(Folder_id=source_id).first()
    if not folder:
        return "错误：无效的 source_id！", 400

    # 渲染页面
    return render_template(
        'analysis/statistics_analysis.html', 
        source_id=source_id, 
        dimension=dimension
    )


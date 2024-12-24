# 连接数据库的基本功能
import sys
import os

from flask import jsonify
from sqlalchemy import text
# 将项目根目录添加到 sys.path,Python默认从当前文件所在的目录开始找，也就是app文件夹开始找
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Database.config import db
from Database.model import *


from sqlalchemy import or_

from flask import session
from flask_login import current_user

import json

from yearToyearTools.run import convert_to_gregorian

#在数据库中加一条记录
def set_session_variables(db_session):
    """设置数据库会话变量"""
    # 从 Flask session 获取用户信息
    if current_user.is_authenticated:
        user_id = current_user.User_id
        role = current_user.User_role
    else:
        user_id = None
        role = 'NonMember'
        
    # 设置数据库会话变量
    db_session.execute(text("SET @current_id = :user_id, @current_role = :role"), 
                      {"user_id": user_id, "role": role})

def db_add(model, **kwargs):
    """
    向数据库添加一条记录
    :param model: 数据库模型类
    :param kwargs: 字段名和值的键值对
    :return: 添加的记录对象
    """
    try:
        # 创建模型实例
        instance = model(**kwargs)
        # 添加到会话
        db.session.add(instance)
        
        # 设置会话变量
        set_session_variables(db.session)
            
        # 提交事务
        db.session.commit()
        return instance
    except Exception as e:
        # 发生错误时回滚
        db.session.rollback()
        print(f"db_add error: {e}")
        raise e
# 注册用户
def db_add_register(model, **kwargs):
    """
    注册用户专用的数据库添加函数，包含手动添加审计日志
    :param model: 数据库模型类（应该是 Users）
    :param kwargs: 字段名和值的键值对
    :return: 添加的记录对象
    """
    try:
        # 创建模型实例
        instance = model(**kwargs)
        # 添加到会话
        db.session.add(instance)
        
        # 设置会话变量
        set_session_variables(db.session)
            
        # 提交事务
        db.session.commit()

        # 手动添加审计日志
        audit_log = AuditLog(
            User_id=instance.User_id,  # 新注册用户的ID
            Audit_actionType='INSERT',
            Audit_actionDescription=f'新用户注册: {instance.User_name}',
            Audit_targetTable='Users'
        )
        db.session.add(audit_log)
        db.session.commit()

        return instance
    except Exception as e:
        # 发生错误时回滚
        db.session.rollback()
        print(f"db_add_register error: {e}")
        raise e
    
#在数据库中以主键删除一条记录：(主键可能有两个)
def db_delete_key(model, key):
    """
    根据主键删除记录
    """
    try:
        record = model.query.get(key)
        if record:
            # 设置会话变量
            set_session_variables(db.session)
            db.session.delete(record)
            db.session.commit()
        else:
            print("db_delete wrong")
    except Exception as e:
        db.session.rollback()
        print(f"db_delete error: {e}")
        raise e


# 更新,针对单一主键
def db_update_key(model, key, **update_data):
    """
    更新记录
    """
    try:
        record = model.query.get(key)
        if record:
            # 设置会话变量
            set_session_variables(db.session)
            
            # 更新字段
            for field, value in update_data.items():
                if hasattr(record, field):
                    setattr(record, field, value)
            
            db.session.commit()
            return record
    except Exception as e:
        db.session.rollback()
        print(f"db_update error: {e}")
        raise e

#针对双主键
def db_update_keys(model, key1,key2, **update_data):
    # 通过主键查找记录
    record = model.query.get((key1,key2))

    if record:
        # 遍历字典并更新字段
        for field, value in update_data.items():
            if hasattr(record, field):  # 确保字段存在于模型中
                setattr(record, field, value)  # 更新字段的值
                
        db.session.commit()  # 提交更新
        return record  # 返回更新后的记录
    
    return None  # 如果记录不存在，返回 None

# 查询所有数据
def db_query_all(model):
    return model.query.all()

# 根据单一主键查询数据
def db_query_key(model, record_id):
    return model.query.get(record_id)

#双主键查询
def db_query_keys(model, key1,key2):
    return model.query.get((key1,key2))
   
# 由两个人的id获得两个人的关系
def get_relation_by_ids(alice_id, bob_id):

    return Relations.query.filter(
        or_(
            (Relations.Alice_id == alice_id, Relations.Bob_id == bob_id),
            (Relations.Alice_id == bob_id, Relations.Bob_id == alice_id)
        )
    )
#通用函数：根据一个字段名和值筛选出所有满足条件的记录
def db_one_filter_records(model, column_name, value):
    # 通过 getattr 动态获取模型的列属性
    column = getattr(model, column_name)
    
    # 执行查询，筛选出符合条件的记录
    records = model.query.filter(column == value).all()

    return records

def db_query_by_conditions(model, conditions: dict):
    session = db.session()
    # 构建基本的查询语句
    sql = f"SELECT * FROM {model.__tablename__} WHERE 1=1"
    # 遍历条件字典，添加查询条件
    for column, value in conditions.items():
        if value is not None:  # 排除值为 None 的情况
            sql += f" AND {column} = :{column}"
    
    # 执行查询
    results = session.execute(text(sql), conditions).all()

    
    # 返回查询到的记录列表
    return results
#全文搜索
def db_context_query(query, doc_type=None, date_from=None, date_to=None):
    """
    实现全文检索，查询文书标题或原文中包含关键字的记录，并支持高级搜索。
    支持部分匹配和多个关键词。
    """
    try:
        # 处理搜索关键词，添加通配符和 + 操作符
        search_terms = query.split()
        formatted_query = ' '.join([f'+*{term}*' for term in search_terms])
        
        # 构��基本的全文检索 SQL 查询
        sql = """
            SELECT Doc_id FROM Documents
            WHERE MATCH(Doc_title, Doc_simplifiedText, Doc_originalText) 
            AGAINST(:query IN BOOLEAN MODE)
            OR Doc_title LIKE :like_query
            OR Doc_simplifiedText LIKE :like_query
            OR Doc_originalText LIKE :like_query
        """
        params = {
            'query': formatted_query,
            'like_query': f'%{query}%'  # 添加 LIKE 查询作为备选
        }
        
        # 添加文档类型筛选条件（如果提供）
        if doc_type:
            sql += " AND Doc_type = :doc_type"
            params['doc_type'] = doc_type
        
        # 添加日期范围筛选条件（如果提供）
        if date_from:
            sql += " AND Doc_createdAt >= :date_from"
            params['date_from'] = date_from
        if date_to:
            sql += " AND Doc_createdAt <= :date_to"
            params['date_to'] = date_to
        
        # 添加排序条件
        sql += """ 
            ORDER BY MATCH(Doc_title, Doc_simplifiedText, Doc_originalText) 
            AGAINST(:query IN BOOLEAN MODE) DESC
        """
        
        print(f"Executing search with query: {formatted_query}")
        print(f"SQL: {sql}")
        print(f"Params: {params}")
        
        # 执行查询获取文档ID
        result = db.session.execute(text(sql), params)
        doc_ids = [row[0] for row in result.fetchall()]
        
        if not doc_ids:
            return []
            
        # 使用找到的文档ID从 DocumentDisplayView 中获取完整信息
        display_results = DocumentDisplayView.query.filter(
            DocumentDisplayView.Doc_id.in_(doc_ids)
        ).all()
        
        return display_results
        
    except Exception as e:
        print(f"全文搜索出错: {str(e)}")
        return []


import opencc
from sparkai.llm.llm import ChatSparkLLM, ChunkPrintHandler
from sparkai.core.messages import ChatMessage
import re
from datetime import datetime
from sqlalchemy import text
from Database.model import *

def process_document_text(original_text: str, image_path: str):
    """处理文书文本，返回所有需要的信息"""
    # 预处理文本：删除所有空格和换行符
    original_text = ''.join(original_text.split())  # 删除所有空白字符（包括空格、换行符、制表符等）
    
    # 1. 转换繁简体
    simplified_text = convert_to_simplified(original_text)
    
    # 2. 调用大模型获取文书信息
    doc_info = get_document_info(simplified_text)
    
    # 3. 转换创建时间格式
    created_time = doc_info.get('created_time', '')
    if created_time:
        standard_time = convert_to_gregorian(created_time)
        if standard_time != "未找到对应年号" and standard_time != "格式错误，请包含'年'字":
            year, month, day = map(int, standard_time.split(':'))
            if month == 0:
                standard_time = f"{year}-01-01"  # 如果没有月份，默认为1月1日
            elif day == 0:
                standard_time = f"{year}-{month:02d}-01"  # 如果没有日期，默认为1日
            else:
                standard_time = f"{year}-{month:02d}-{day:02d}"
        else:
            standard_time = None
    else:
        standard_time = None
    
    # 4. 转换修改时间格式
    updated_time = doc_info.get('updated_time')
    if updated_time:
        standard_updated_time = convert_to_gregorian(updated_time)
        if standard_updated_time != "未找到对应年号" and standard_updated_time != "格式错误，请包含'年'字":
            year, month, day = map(int, standard_updated_time.split(':'))
            if month == 0:
                standard_updated_time = f"{year}-01-01"
            elif day == 0:
                standard_updated_time = f"{year}-{month:02d}-01"
            else:
                standard_updated_time = f"{year}-{month:02d}-{day:02d}"
        else:
            standard_updated_time = None
    else:
        standard_updated_time = None
    
    # 5. 整理返回数据
    return {
        'doc_id': doc_info.get('doc_id', ''),
        'original_text': original_text,  # 已经去除空格和换行符的原文
        'simplified_text': doc_info['simple_text'],  # 断句且再次简体化的简体版本
        'image_path': image_path,
        'title': doc_info['title'],
        'type': doc_info['type'],
        'summary': doc_info['summary'],
        'created_time': created_time,
        'standard_time': standard_time,
        'updated_time': updated_time,
        'standard_updated_time': standard_updated_time,
        'keywords': doc_info['keywords'],
        'contractors': doc_info['contractors'],
        'relation': doc_info.get('relation'),
        'participants': doc_info['participants']
    }

def generate_doc_id():
    """生成文书ID"""
    try:
        # 获取当前最大的文书ID
        result = db.session.execute(text("""
            SELECT MAX(Doc_id) as max_id 
            FROM Documents
        """))
        max_id = result.fetchone()[0]
        
        if max_id is None:
            # 如果没有文书，从 1-1-1-1 开始
            return "1-1-1-1"
        else:
            # 解析当前最大ID
            parts = max_id.split('-')
            if len(parts) != 4:
                return "1-1-1-1"
                
            # 增加最后一个数字
            new_id = f"{parts[0]}-{parts[1]}-{parts[2]}-{int(parts[3])+1}"
            return new_id
            
    except Exception as e:
        print(f"生成文书ID失败: {str(e)}")
        # 返回一个带时间戳的ID作为备选
        return f"1-1-1-{int(datetime.now().timestamp())}"

def convert_to_simplified(text: str):
    """将繁体文本转换为简体"""
    converter = opencc.OpenCC('t2s.json')
    return converter.convert(text)

def get_document_info(text: str):
    """调用星火大模型API获取文书信息"""
    try:
        # 配置星火认知大模型
        spark = ChatSparkLLM(
            spark_api_url='wss://spark-api.xf-yun.com/v4.0/chat',
            spark_app_id='ce9ffe63',
            spark_api_key='37a6c3241c800fc455c445176efddc0d',
            spark_api_secret='ODhjMzViODcwODU4Njk0ZTgxZWI1ZGVh',
            spark_llm_domain='4.0Ultra',
            streaming=False
        )
        
        # 构建提示词
        prompt_base = """分析下面这份清代契约文书，提取以下信息：
        1. 文书标题（根据内容生成一个合适的标题）
        2. 文书类型（借钱契、租赁契、抵押契、赋税契、诉状、判决书、祭祀契约、祠堂契、劳役契、其他）
        3. 文书大意（200字以内）
        4. 签订时间（从文书中提取具体的时间）
        5. 更改时间（如果有）
        6. 关键词（3-5个）
        7. 契约双方（两个人的姓名）
        8. 契约双方关系（如叔侄、父子等，如果有）
        9. 参与人及其身份（如见证人、代书等，可能有多人）
        10.对文书内容进行断句，如果有字体仍为繁体则将其转换为简体，返回断句且再次简体化的文书内容

        请用JSON格式返回结果，格式如下：
        {
            "title": "文书标题",
            "type": "文书类型",
            "summary": "文书大意",
            "created_time": "签订时间",
            "updated_time": "更改时间（如果有则填写，没有则为null）",
            "keywords": ["关键词1", "关键词2", "关键词3"],
            "contractors": [
                {"name": "第一个契约人姓名"},
                {"name": "第二个契约人姓名"}
            ],
            "relation": "契约双方关系（如果有则填写，没有则为null）",
            "participants": [
                {"name": "参与人1姓名", "role": "参与人1身份"},
                {"name": "参与人2姓名", "role": "参与人2身份"}
            ],
            "simple_text": "文书内容断句且简体化"
        }

        请严格按照上述JSON格���返回结果。以下是文书内容：
        """
        
        # 创建消息
        messages = [ChatMessage(role="user", content=prompt_base+text)]
        
        # 调用API
        handler = ChunkPrintHandler()
        response = spark.generate([messages], callbacks=[handler])
        print("问答完成\n")
        
        # 获取并清理JSON字符串
        if isinstance(response.generations[0], list):
            json_str = response.generations[0][0].text
        else:
            json_str = response.generations[0].text
            
        json_str = json_str.strip()
        if json_str.startswith("```json"):
            json_str = json_str[7:]
        if json_str.endswith("```"):
            json_str = json_str[:-3]
        json_str = json_str.strip()
        
        # 解析返回的JSON
        try:
            result = json.loads(json_str)
            # 验证返回的数据是否包含所有必要字段
            required_fields = ['title', 'type', 'summary', 'created_time', 'keywords', 
                             'contractors', 'participants', 'simple_text']
            for field in required_fields:
                if field not in result:
                    raise ValueError(f"API返回的数据缺少必要字段: {field}")
            return result
        except Exception as e:
            print(f"解析文书信息失败: {e}")
            print(f"尝试解析的字符串: {json_str}")
            raise ValueError(f"解析文书信息失败: {str(e)}")
            
    except Exception as e:
        print(f"调用星火API失败: {e}")
        raise

def insert_document(doc_info: dict):
    """调用存储过程插入文书数据"""
    try:
        # 检查必要字段
        required_fields = ['title', 'type', 'summary', 'original_text', 'simplified_text', 
                         'image_path', 'created_time', 'keywords', 'contractors', 'participants']
        for field in required_fields:
            if field not in doc_info:
                return False, f"缺少必要字段: {field}"
        
        # 将数据转换为JSON字符串
        data_json = json.dumps(doc_info, ensure_ascii=False)
        print(f"准备插入的数据: {data_json}")
        
        # 调用存储过程
        try:
            # 确保没有活动的事务
            db.session.rollback()
            
            # 执行存储过程
            result = db.session.execute(
                text('CALL InsertDocument(:data)'),
                {'data': data_json}
            )
            
            # 获取存储过程的返回值
            proc_result = result.fetchone()
            print(f"存储过程返回值: {proc_result}")
            
            if proc_result and proc_result[0] == 'success':
                db.session.commit()
                return True, "文书添加成功"
            else:
                db.session.rollback()
                return False, "存储过程执行失败"
                
        except Exception as e:
            db.session.rollback()
            print(f"存储过程执行失败: {str(e)}")
            return False, f"存储过程执行失败: {str(e)}"
            
    except Exception as e:
        print(f"数据处理失败: {str(e)}")
        return False, f"数据处理失败: {str(e)}"

# 在现有函数之外添加新函数
def db_one_filter_record(model, field, value):
    """
    根据单个字段查询一条记录
    :param model: 数据库模型类
    :param field: 字段名
    :param value: 字段值
    :return: 查询到的记录或None
    """
    try:
        return model.query.filter(getattr(model, field) == value).first()
    except Exception as e:
        print(f"db_one_filter_record error: {e}")
        return None

def db_advanced_search(title=None, person=None):
    """
    在 DocumentDisplayView 视图中进行精细搜索
    使用正则表达式在《》内匹配人名
    """
    try:
        query = text("""
            SELECT * FROM DocumentDisplayView
            WHERE (:title IS NULL OR Doc_title LIKE :title_pattern)
            AND (
                :person IS NULL OR 
                ContractorInfo REGEXP :person_pattern OR 
                ParticipantInfo REGEXP :person_pattern
            )
        """)
        
        # 构建正则表达式模式：匹配《》内的人名
        person_pattern = f"《[^》]*{person}[^》]*》" if person else None
        
        params = {
            'title': title,
            'title_pattern': f'%{title}%' if title else None,
            'person': person,
            'person_pattern': person_pattern
        }
        
        # 执行查询
        result = db.session.execute(query, params)
        return result.fetchall()
    except Exception as e:
        print(f"Advanced search error: {str(e)}")
        return []
    
# 这是一个测试类，用于测试文档处理功能
class TestDocumentProcessing():
    def __init__(self):
        """测试前的设置"""        
        # 测试用的文书文本
        self.test_text = """
        清道光十二年十二月黃興忠立撮字
        立撮字黃興忠撮出錢壹仟貳百文正言約俟至癸巳年拾月中旬約紙照價里还不敢過期如是過��照例行息不敢久欠如是久欠保認代賠不負字照
        道光拾貳年拾二月日立撮字黃興忠
        保認侄長善
        代���兄文廉
        """
        
        # 测试用的片路径
        self.test_image_path = "static/images/test_doc.jpg"

    def test_convert_to_simplified(self):
        """测试繁体转简体功能"""
        try:
            simplified = convert_to_simplified(self.test_text)
            print(f"\n原文本: {self.test_text[:50]}...")
            print(f"简体文本: {simplified[:50]}...")
            return True
        except Exception as e:
            print(f"繁体转简体失败: {str(e)}")
            return False

    def test_get_document_info(self):
        """测试文书信息提取功能"""
        try:
            doc_info = get_document_info(self.test_text)
            # 检查返回的字典是否包含所有必要的键
            required_keys = [
                'title', 'type', 'summary', 'created_time',
                'keywords', 'contractors', 'participants'
            ]
            for key in required_keys:
                if key not in doc_info:
                    print(f"缺少必要的键: {key}")
                    return False
            
            # 打印提取的信息
            print("\n提取文书信息:")
            for key, value in doc_info.items():
                print(f"{key}: {value}")
            return True
                
        except Exception as e:
            print(f"书信息提取失败: {str(e)}")
            return False

    def test_process_document_text(self):
        """测试完整的文书处理流程"""
        try:
            result = process_document_text(self.test_text, self.test_image_path)
            
            # 检查返回的字典是否包含所有必要的键
            required_keys = [
                'original_text', 'simplified_text', 'image_path',
                'title', 'type', 'summary', 
                'created_time', 'standard_time',  # 创建时间
                'updated_time', 'standard_updated_time',  # 修改时间
                'keywords', 'contractors', 'participants'
            ]
            for key in required_keys:
                if key not in result:
                    print(f"缺少必要的键: {key}")
                    return False
            
            # 打印处理结果
            print("\n文书处理结果:")
            for key, value in result.items():
                if key not in ['original_text', 'simplified_text']:  # 跳过长文本
                    print(f"{key}: {value}")
                
            # 验证时间转换
            if result['created_time']:
                print(f"\n创建时间转换:")
                print(f"原始时间: {result['created_time']}")
                print(f"标准时间: {result['standard_time']}")
                
            if result['updated_time']:
                print(f"\n修改时间转换:")
                print(f"原始时间: {result['updated_time']}")
                print(f"标准时间: {result['standard_updated_time']}")
                
            return True
                
        except Exception as e:
            print(f"文书处理失败: {str(e)}")
            return False

def test_insert_document():
    """测试存储过程是否能正确插入数据"""
    from app import app  # 导入应用实例
    
    # 准备测试数据
    test_data = {
    "doc_id":"1-1-1-1",
    "title": "测试文书",
    "type": "借钱契",
    "summary": "这是一份测试用的文书",
    "original_text": "清嘉慶十一年十一月黃盛漢立撮字（廢契）",
    "simplified_text": "清嘉庆十一年十一月黄盛汉立撮字（废契）",
    "image_path": "images/documents/test.jpg",
    "created_time": "嘉庆十一年十一月",
    "standard_time": "1806-11-01",
    "updated_time": 'null',
    "standard_updated_time": 'null',
    "keywords": ["借钱", "契约", "测试"],
    "contractors": [
        {"name": "黄盛汉"},
        {"name": "吴光璧"}
    ],
    "relation": "叔侄",
    "participants": [
        {"name": "侄兴科", "role": "见证人"},
        {"name": "进益", "role": "代书"}
    ]
}

    # 使用应用上下文
    with app.app_context():
        try:
            # 开始测试
            print("开始测试存储过程...")
            print(f"测试数据: {json.dumps(test_data, ensure_ascii=False, indent=2)}")

            # 转换为JSON字符串
            data_json = json.dumps(test_data, ensure_ascii=False)
            
            # 执行存储过程
            result = db.session.execute(
                text('CALL InsertDocument(:data)'),
                {'data': data_json}
            )
            
            # 获取存储过程的返回值
            proc_result = result.fetchone()
            print(f"存储过程返回值: {proc_result}")
            
            if proc_result and proc_result[0] == 'success':
                doc_id = proc_result[1]
                print(f"文书添加成功，ID: {doc_id}")
                
                # 验证数据是否正确插入
                print("\n验证插入的数据:")
                
                # 检查文书基本信息
                doc = Documents.query.get(doc_id)
                if doc:
                    print(f"文书标题: {doc.Doc_title}")
                    print(f"文书类型: {doc.Doc_type}")
                    print(f"文书大意: {doc.Doc_summary}")
                else:
                    print("未找到文书记录")
                
                # 检查关键词
                keywords = DocKeywords.query.filter_by(Doc_id=doc_id).all()
                print(f"\n关键词: {[kw.KeyWord for kw in keywords]}")
                
                # 检查契约人
                contractors = Contractors.query.filter_by(Doc_id=doc_id).first()
                if contractors:
                    alice = People.query.get(contractors.Alice_id)
                    bob = People.query.get(contractors.Bob_id)
                    print(f"\n契约人: {alice.Person_name} 和 {bob.Person_name}")
                else:
                    print("未找到契约人记录")
                
                # 检查参与人
                participants = Participants.query.filter_by(Doc_id=doc_id).all()
                print("\n参与人:")
                for p in participants:
                    person = People.query.get(p.Person_id)
                    print(f"{person.Person_name} ({p.Part_role})")
                
                return True, "测试成功"
            else:
                print("存储过程执行失败")
                return False, "存储过程执行失败"
                
        except Exception as e:
            print(f"测试失败: {str(e)}")
            db.session.rollback()
            return False, f"测试失败: {str(e)}"

if __name__ == '__main__':
    test = TestDocumentProcessing()
    
    # print("测试繁体转简体功能...")
    # if test.test_convert_to_simplified():
    #     print("✓ 繁体转简体测试通过")
    # else:
    #     print("✗ 繁体转简体测试失败")
        
    # print("\n测试文书信息提取功能...")
    # if test.test_get_document_info():
    #     print("✓ 文书信息提取测试通过")
    # else:
    #     print("✗ 文书信息提取测试失败")
        
    # print("\n测试完整的文书处理流程...")
    if test_insert_document():
        print("✓ 文书处理流程测试通过")
    else:
        print("✗ 文书处理流程测试失败")


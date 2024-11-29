# 连接数据库的基本功能
import sys
import os

from flask import jsonify

# 将项目根目录添加到 sys.path,Python默认从当前文件所在的目录开始找，也就是app文件夹开始找
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Database.config import db
from Database.model import *
from app import app


#在数据库中加一条记录
def db_add(model,**kwargs):
    try:
        record = model(**kwargs)
        db.session.add(record)
        db.session.commit()
    except Exception :
        db.session.rollback()
        print("db_add wrong")
        raise

#在数据库中以主键删除一条记录：(主键可能有两个)
def db_delete_key(model,key):
    record=model.query.get(key)
    if record:
        db.session.delete(record)  # 删除记录
        db.session.commit()  # 提交事务
    else:
        print("db_delete wrong")


# 更新,针对单一主键
def db_update_key(model, key, **update_data):
    # 通过主键查找记录
    record = model.query.get(key)
    
    if record:
        # 遍历字典并更新字段
        for field, value in update_data.items():
            if hasattr(record, field):  # 确保字段存在于模型中
                setattr(record, field, value)  # 更新字段的值
        
        db.session.commit()  # 提交更新
        return record  # 返回更新后的记录
    
    return None  # 如果记录不存在，返回 None

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

#双主键
def db_query_keys(model, key1,key2):
    return model.query.get((key1,key2))
    


# 返回一个JSON格式的收藏夹列表
@app.route('/get_all_folders', methods=['GET'])
def get_folders():

    folders= db_query_all(Folders)
    return jsonify(folders=folders)


# 根据文书编号返回文书记录




import opencc
from sparkai.llm.llm import ChatSparkLLM, ChunkPrintHandler
from sparkai.core.messages import ChatMessage
import re
def db_book_input(hard:str):
    
    def getOpenccSimple(hard:str):
        def replace_invalid_utf8_with_O(input_text):
            result = ""
            for char in input_text:
                try:
                    # 尝试将字符编码为 UTF-8
                    char.encode('utf-8')
                    result += char
                except UnicodeEncodeError:
                    # 如果编码失败，使用 'O' 替代该字符
                    result += 'O'
            return result
    
        converter = opencc.OpenCC('t2s.json')
        return converter.convert(replace_invalid_utf8_with_O(hard))
    
    def getInput(openccSimple:str):
        #星火认知大模型Spark 4.0的URL值，其他版本大模型URL值请前往文档（https://www.xfyun.cn/doc/spark/Web.html）查看
        SPARKAI_URL = 'wss://spark-api.xf-yun.com/v4.0/chat'
        #星火认知大模型调用秘钥信息，请前往讯飞开放平台控制台（https://console.xfyun.cn/services/bm35）查看
        SPARKAI_APP_ID = ''
        SPARKAI_API_SECRET = ''
        SPARKAI_API_KEY = ''
        #星火认知大模型Spark 4.0的domain值，其他版本大模型domain值请前往文档（https://www.xfyun.cn/doc/spark/Web.html）查看
        SPARKAI_DOMAIN = '4.0Ultra'
        
        spark = ChatSparkLLM(
        spark_api_url=SPARKAI_URL,
        spark_app_id=SPARKAI_APP_ID,
        spark_api_key=SPARKAI_API_KEY,
        spark_api_secret=SPARKAI_API_SECRET,
        spark_llm_domain=SPARKAI_DOMAIN,
        streaming=False,
        )
        messages = [ChatMessage(
        role="user",
        content='''下面我会给你提供一篇文言文契约文书，你有个任务。
        任务1：你要给文言文断句,不要留下长句，同时如果其中有繁体字你要改为简体字；
        任务2：概括出本篇文言文的大意；
        任务3：识别出这份契约的签约人，可能有多个，都要识别出来；
        任务4：识别出契约者之间的关系；任务5：识别出这份契约的签订日期。你要把你的结果放在{}中。
        回答格式：修正后的文本:{}，大意:{}，签约人:{}，签约人的关系:{}，签订日期{}。
        下面是文本内容：'''+openccSimple
        )]
        handler = ChunkPrintHandler()
        response = spark.generate([messages], callbacks=[handler])
        
        response_text = response.generations
        result={}
        if response_text and isinstance(response_text, list):  # 确保是列表
            first_generation = response_text[0]  # 获取第一个 ChatGeneration 对象
            if isinstance(first_generation, list) and first_generation:  # 如果是嵌套列表
                first_item = first_generation[0]  # 获取嵌套列表的第一个元素
                responseContent = first_item.message.content  # 提取 content 属性
            else:  # 如果不是嵌套列表，直接访问
                responseContent = first_generation.message.content  # 提取 content 属性
            # print(f"提取的 content 内容: {responseContent}")
        
        else:
            print("getInput未找到生成内容")
            
        def extract_text_in_braces(text):
            # 使用正则表达式匹配所有花括号内的内容
            matches = re.findall(r'\{(.*?)\}', text)
            return matches

        def save_as_dict(text):
            # 提取花括号内的内容
            extracted_text = extract_text_in_braces(text)
            
            # 根据提取的内容构造字典
            result_dict = {
                "简体": extracted_text[0],  # 第一个提取的内容为简体
                "大意": extracted_text[1],  # 第二个提取的内容为大意
                "契约人": extracted_text[2],  # 第三个提取的内容为契约人
                "关系类型": extracted_text[3],  # 第四个提取的内容为关系类型
                "时间": extracted_text[4]  # 第五个提取的内容为时间
            }
            
            return result_dict
        
        return save_as_dict(responseContent)
    
    # 下面需要补充 生成一个表记录对象 使用db_add来加入
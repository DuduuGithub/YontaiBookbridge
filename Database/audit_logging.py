# audit_logging.py

from datetime import datetime
from .model import AuditLog, db, Users
from .config import init_db
from flask import current_app
import logging
import traceback

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def create_audit_log(user_id, action_type, description, target_table):
    """创建审计日志记录"""
    try:
        # 检查参数
        if not action_type:
            logger.error("审计日志创建失败: action_type不能为空")
            return False
            
        if not target_table:
            logger.error("审计日志创建失败: target_table不能为空")
            return False
            
        # 创建新的审计日志记录
        new_audit_log = AuditLog(
            User_id=user_id,
            Audit_actionType=action_type,
            Audit_actionDescription=description or "无描述",
            Audit_targetTable=target_table,
            Audit_timestamp=datetime.now()
        )
        
        # 添加到数据库会话
        db.session.add(new_audit_log)
        
        try:
            db.session.commit()
            logger.info(f"审计日志创建成功: user_id={user_id}, action={action_type}, table={target_table}")
            return True
        except Exception as commit_error:
            logger.error(f"审计日志提交失败: {str(commit_error)}")
            logger.error(traceback.format_exc())
            db.session.rollback()
            return False
            
    except Exception as e:
        logger.error(f"创建审计日志失败: {str(e)}")
        logger.error(traceback.format_exc())
        try:
            db.session.rollback()
        except:
            pass
        return False

def get_audit_logs(limit=100, offset=0, user_id=None, action_type=None, target_table=None):
    """获取审计日志记录"""
    try:
        query = AuditLog.query
        
        if user_id:
            query = query.filter(AuditLog.User_id == user_id)
        if action_type:
            query = query.filter(AuditLog.Audit_actionType == action_type)
        if target_table:
            query = query.filter(AuditLog.Audit_targetTable == target_table)
            
        query = query.order_by(AuditLog.Audit_timestamp.desc())
        
        logs = query.limit(limit).offset(offset).all()
        return logs, None
        
    except Exception as e:
        logger.error(f"获取审计日志失败: {str(e)}")
        logger.error(traceback.format_exc())
        return None, str(e)

if __name__ == '__main__':
    from flask import Flask
    app = Flask(__name__)
    init_db(app)
    
    with app.app_context():
        try:
            success = create_audit_log(
                user_id=1,
                action_type='TEST',
                description='测试审计日志',
                target_table='test_table'
            )
            print("审计日志创建成功" if success else "审计日志创建失败")
        except Exception as e:
            print(f"测试失败: {str(e)}")
            print(traceback.format_exc())

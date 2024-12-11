# audit_logging.py

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 1. 配置数据库连接
DATABASE_URI = 'mysql+pymysql://root:H3250306y@localhost/永泰文书'

# 创建引擎
engine = create_engine(DATABASE_URI, echo=False)

# 创建会话工厂
Session = sessionmaker(bind=engine)

def set_audit_session_variables(session, user_id):
    """
    设置会话变量 @current_id 和 @current_role
    """
    # 获取用户角色
    result = session.execute(
        text("SELECT User_role FROM Users WHERE User_id = :user_id"),
        {"user_id": user_id}
    ).fetchone()
    
    if result:
        user_role = result['User_role']
    else:
        user_role = 'Unknown'
    
    # 设置会话变量
    session.execute(
        text("SET @current_id = :user_id, @current_role = :user_role"),
        {"user_id": user_id, "user_role": user_role}
    )

def delete_user_browsing_history(session, browse_id, operator_id):
    """
    删除用户浏览记录，并确保触发器记录审计日志
    """
    # 设置会话变量
    set_audit_session_variables(session, operator_id)
    
    # 执行删除操作
    session.execute(
        text("DELETE FROM UserBrowsingHistory WHERE Browse_id = :browse_id"),
        {"browse_id": browse_id}
    )

def main():
    # 假设当前操作的用户的 User_id 是 123，Browse_id 是 456
    operator_id = 123  # 当前操作用户的 User_id
    browse_id_to_delete = 456  # 需要删除的 Browse_id
    
    # 创建会话
    session = Session()
    
    try:
        # 开始事务
        session.begin()
        
        # 执行被审计的操作
        delete_user_browsing_history(session, browse_id_to_delete, operator_id)
        
        # 提交事务
        session.commit()
        print("操作成功，审计日志已记录。")
    except Exception as e:
        # 回滚事务
        session.rollback()
        print("操作失败，事务已回滚。错误信息：", e)
    finally:
        # 关闭会话
        session.close()

if __name__ == "__main__":
    main()

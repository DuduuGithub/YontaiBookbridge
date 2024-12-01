# 表设计，以3NF及以上为设计目标

# 用户主题：

# 用户信息表：uid,账号，密码，身份等
# 用户浏览记录表 只需要记忆 浏览过的文书的记录


# 文书主题:

# 文书数据表：编号，文本内容，契约人，大意……评论区
# 文书纠错表：用于管理员查看用户提交的文书的纠错内容


# 用户文书表：uid,编号,标记、笔记等

# 日志表 记录对文书数据表的更改日志

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Text, Date, Enum, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config import db

# 文书类：Documents
class Documents(db.Model):
    __tablename__ = 'Documents'  # 定义表名为 'Documents'

    # 文书的基本字段
    Doc_id = Column(Integer, primary_key=True, autoincrement=True)  # 文书序号，自增主键
    Doc_number = Column(String(20),nullable=False)  #归档编号，非空
    Doc_title = Column(String(255), nullable=False)  # 文书标题，非空
    Doc_originalText = Column(Text, nullable=False)  # 文书的繁体原文，非空
    Doc_simplifiedText = Column(Text, default=None)  # 文书的简体原文，默认为空
    Doc_type = Column(Enum('借贷', '契约', '其他'), nullable=False)  # 文书类型，可参考第二次小组作业
    Doc_summary = Column(Text, default=None)  # 文书的大意，默认为空
    Doc_createdAt = Column(String(50),default=None)  # 文书创建时间，默认为空
    Doc_updatedAt = Column(String(50),default=None)  # 最后修改时间，默认为空
    
    # 关系定义：
    participants = relationship('Participants', backref='document', cascade='all, delete-orphan')  # 与参与者的关系
    highlights = relationship('Highlights', backref='document', cascade='all, delete-orphan')  # 高亮记录
    notes = relationship('Notes', backref='document', cascade='all, delete-orphan')  # 批注记录
    comments = relationship('Comments', backref='document', cascade='all, delete-orphan')  # 评论记录
    corrections = relationship('Corrections', backref='document', cascade='all, delete-orphan')  # 纠错记录
    keywords = relationship('DocKeywords', backref='document', cascade='all, delete-orphan')  # 文书关键词
    
    """
    每个文书可以有多个参与者、高亮、批注等。当文书被删除时，所有相关记录都会自动删除，防止孤立数据。
    cascade='all, delete-orphan'：这确保了如果父表(如 Documents)被删除，所有子表中的相关数据也会被删除。
    此外，如果子对象从父对象的关系中脱离（例如删除了 Participants 记录，且没有重新关联到其他 Documents),它也会被删除。
    backref='document'：这是反向关系。通过 document 可以从子表（如 Participants)访问父表 Documents。
    """

    # 定义索引：帮助优化查询
    __table_args__ = (
        db.Index('idx_Doc_number','Doc_number'), #为'归档编号'建立索引
        db.Index('idx_Doc_type', 'Doc_type'),  # 为'文书类型'创建索引
        db.Index('idx_Doc_createdAt', 'Doc_createdAt'),  # 为文'书创建时间' 创建索引
    )



# 文书关键词类：DocKeywords
class DocKeywords(db.Model):
    __tablename__ = 'DocKeywords' #表名为 'DocKeywords'

    KeyWord_id = Column(Integer,primary_key=True,autoincrement=True)  #关键词序号，自增主键
    Doc_id = Column(Integer, ForeignKey('Documents.Doc_id'), nullable=False)  #文书ID
    KeyWord = Column(String(50),nullable=False)  #关键词，非空



# 参与者类：Participants
class Participants(db.Model):
    __tablename__ = 'Participants'  # 表名为 'Participants'
    
    Part_id = Column(Integer, primary_key=True, autoincrement=True)  # 参与者序号，自增主键
    Doc_id = Column(Integer, ForeignKey('Documents.Doc_id'), nullable=False)  # 外键，关联到 'Documents' 表的 Doc_id
    Part_name = Column(String(255), nullable=False)  # 参与者姓名，非空
    Part_role = Column(String(50), nullable=False)  # 参与者的角色（如签署人、见证人），非空



# 用户类：Users
class Users(db.Model):
    __tablename__ = 'Users'  # 表名为 'Users'
    
    User_id = Column(Integer, primary_key=True, autoincrement=True)  # 用户的唯一标识符
    User_name = Column(String(100), nullable=False, unique=True)  # 用户名，唯一，非空
    User_passwordHash = Column(String(255), nullable=False)  # 密码的哈希值，非空
    User_email = Column(String(150), nullable=False, unique=True)  # 用户邮箱，唯一，非空
    User_role = Column(Enum('Admin', 'Member', 'NonMember'), nullable=False)  # 用户角色，'Admin'、'Member' 或 'NonMember'
    
    # 关系定义：
    highlights = relationship('Highlights', backref='user', cascade='all, delete-orphan')  # 用户与高亮记录的关联
    notes = relationship('Notes', backref='user', cascade='all, delete-orphan')  # 用户与批注记录的关联
    folders = relationship('Folders', backref='user', cascade='all, delete-orphan')  # 用户与收藏夹的关联
    corrections = relationship('Corrections', backref='user', cascade='all, delete-orphan')  # 用户与纠错记录的关联
    comments = relationship('Comments', backref='user', cascade='all, delete-orphan')  # 用户与评论记录的关联



# 高亮类：Highlights
class Highlights(db.Model):
    __tablename__ = 'Highlights'  # 表名为 'Highlights'
    
    Highlight_id = Column(Integer, primary_key=True, autoincrement=True)  # 高亮记录的序号，自增主键
    Doc_id = Column(Integer, ForeignKey('Documents.Doc_id'), nullable=False)  # 外键，关联到 'Documents' 表的 Doc_id
    User_id = Column(Integer, ForeignKey('Users.User_id'), nullable=False)  # 外键，关联到 'Users' 表的 User_id
    Highlight_startPosition = Column(Integer, nullable=False)  # 高亮起始位置（字符索引）
    Highlight_endPosition = Column(Integer, nullable=False)  # 高亮结束位置（字符索引）
    Highlight_color = Column(String(20), default='yellow')  # 高亮颜色，默认为 'yellow'
    Highlight_createdAt = Column(TIMESTAMP, default=func.current_timestamp())  # 高亮操作时间，默认为当前时间戳

    # 建立索引优化查询
    __table_args__ = (
        db.Index('idx_Highlight_user', 'User_id'),
        db.Index('idx_Highlight_doc', 'Doc_id'),
    )




# 批注类：Notes
class Notes(db.Model):
    __tablename__ = 'Notes'  # 表名为 'Notes'
    
    Note_id = Column(Integer, primary_key=True, autoincrement=True)  # 批注记录的序号，自增主键
    Doc_id = Column(Integer, ForeignKey('Documents.Doc_id'), nullable=False)  # 外键，关联到 'Documents' 表的 Doc_id
    User_id = Column(Integer, ForeignKey('Users.User_id'), nullable=False)  # 外键，关联到 'Users' 表的 User_id
    Note_annotationText = Column(Text, nullable=False)  # 批注内容，非空
    Note_startPosition = Column(Integer, nullable=False)  # 批注起始位置（字符索引）
    Note_endPosition = Column(Integer, nullable=False)  # 批注结束位置（字符索引）
    Note_createdAt = Column(TIMESTAMP, default=func.current_timestamp())  # 批注创建时间，默认为当前时间戳

    # 建立索引优化查询
    __table_args__ = (
        db.Index('idx_Note_user', 'User_id'),
        db.Index('idx_Note_doc', 'Doc_id'),
    )




# 收藏夹类：Folders
class Folders(db.Model):
    __tablename__ = 'Folders'  # 表名为 'Folders'
    
    Folder_id = Column(Integer, primary_key=True, autoincrement=True)  # 收藏夹的序号，自增主键
    User_id = Column(Integer, ForeignKey('Users.User_id'), nullable=False)  # 外键，关联到用户ID
    Doc_id = Column(Integer, ForeignKey('Documents.Doc_id'),nullable=False) # 外键，文书ID
    Folder_name = Column(String(255), nullable=False)  # 收藏夹名称，非空
    Folder_createdAt = Column(TIMESTAMP, default=func.current_timestamp())  # 收藏夹创建时间，默认为当前时间戳

    # 确保同一用户不能为同一文书创建多个相同名称的文件夹
    __table_args__ = (
        db.UniqueConstraint('User_id', 'Doc_id', 'Folder_name', name='unique_folder_doc'),
    )




# 审计日志类：AuditLog
class AuditLog(db.Model):
    __tablename__ = 'AuditLog'  # 表名为 'AuditLog'
    
    Audit_id = Column(Integer, primary_key=True, autoincrement=True)  # 审计记录的唯一标识符
    User_id = Column(Integer, ForeignKey('Users.User_id'), nullable=True)  # 外键，关联到 'Users' 表的 User_id（可为空）,一般为管理员
    Audit_actionType = Column(String(50), nullable=False)  # 操作类型（如创建、更新等），非空
    Audit_actionDescription = Column(Text, nullable=False)  # 操作的详细描述，非空
    Audit_targetTable = Column(String(50), nullable=True)  # 被操作的表名
    Audit_timestamp = Column(TIMESTAMP, default=func.current_timestamp())  # 操作时间，默认为当前时间戳
    



# 纠错类：Corrections
class Corrections(db.Model):
    __tablename__ = 'Corrections'  # 表名为 'Corrections'
    
    Correction_id = Column(Integer, primary_key=True, autoincrement=True)  # 纠错记录的唯一标识符
    Doc_id = Column(Integer, ForeignKey('Documents.Doc_id'), nullable=False)  # 外键，关联到 'Documents' 表的 Doc_id
    User_id = Column(Integer, ForeignKey('Users.User_id'), nullable=True)  # 外键，关联到 'Users' 表的 User_id
    Correction_text = Column(Text, nullable=False)  # 纠错内容，非空
    Correction_createdAt = Column(TIMESTAMP, default=func.current_timestamp())  # 纠错提交时间，默认为当前时间戳




# 评论类：Comments
class Comments(db.Model):
    __tablename__ = 'Comments'  # 表名为 'Comments'
    
    Comment_id = Column(Integer, primary_key=True, autoincrement=True)  # 评论记录的唯一标识符
    Doc_id = Column(Integer, ForeignKey('Documents.Doc_id'), nullable=False)  # 外键，关联到 'Documents' 表的 Doc_id
    User_id = Column(Integer, ForeignKey('Users.User_id'), nullable=True)  # 外键，关联到 'Users' 表的 User_id
    Comment_text = Column(Text, nullable=False)  # 评论内容，非空
    Comment_createdAt = Column(TIMESTAMP, default=func.current_timestamp())  # 评论创建时间，默认为当前时间戳




# 笔记类：Evernote
class Evernote(db.Model):
    __tablename__ = 'Evernote'  # 表名为 'History'
    
    Evernote_id = Column(Integer, primary_key=True, autoincrement=True)  # 笔记的唯一标识符
    User_id = Column(Integer, ForeignKey('Users.User_id'), nullable=False)  # 外键，关联到 'Users' 表的 User_id
    Doc_id = Column(Integer, ForeignKey('Documents.Doc_id'), nullable=False)  # 外键，关联到 'Documents' 表的 Doc_id
    Evernote_text = Column(Text,nullable=False) #笔记内容，非空
    Evernote_viewedAt = Column(TIMESTAMP, default=func.current_timestamp())  # 笔记时间，默认为当前时间戳




# 用户浏览记录类：UserBrowsingHistory
class UserBrowsingHistory(db.Model):
    __tablename__ = 'UserBrowsingHistory'  # 表名为 'UserBrowsingHistory'
    
    Browse_id = Column(Integer, primary_key=True, autoincrement=True)  # 浏览记录的序号，自增主键
    User_id = Column(Integer, ForeignKey('Users.User_id'), nullable=False)  # 外键，关联到 'Users' 表的 User_id
    Doc_id = Column(Integer, ForeignKey('Documents.Doc_id'), nullable=False)  # 外键，关联到 'Documents' 表的 Doc_id
    Browse_time = Column(TIMESTAMP, default=func.current_timestamp())  # 浏览时间，默认为当前时间戳
    
    # 定义索引优化查询
    __table_args__ = (
    db.Index('idx_User_id_Doc_id', 'User_id', 'Doc_id'),  # 联合索引
)


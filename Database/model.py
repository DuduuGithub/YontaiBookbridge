# 表设计，以3NF及以上为设计目标

# 用户主题：

# 用户信息表：uid,账号，密码，身份等
# 用户浏览记录表 只需要记忆 浏览过的文书的记录


# 文书主题:

# 文书数据表：编号，文本内容，契约人，大意……评论区
# 文书纠错表：用于管理员查看用户提交的文书的纠错内容

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Database.config import db  # 导入 Database/config.py 中的 db 实例


# 用户文书表：uid,编号,标记、笔记等

# 日志表 记录对文书数据表的更改日志

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Text, Date, Enum, TIMESTAMP, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from Database.config import db
from flask_login import UserMixin

# 1、文书类：Documents
class Documents(db.Model):
    __tablename__ = 'Documents'  # 定义表名为 'Documents'

    # 文书的基本字段
    Doc_id = Column(String(20), primary_key=True)  # 文书序号，与书籍中编号一致
    Doc_title = Column(String(255), nullable=False)  # 文书标题，非空
    Doc_originalText = Column(Text, nullable=False)  # 文书的繁体原文，非空
    Doc_simplifiedText = Column(Text)  # 文书的简体原文，默认为空
    Doc_type = Column(Enum('借贷', '契约', '其他'), nullable=False)  # 文书类型，可参考第二次小组作业
    Doc_summary = Column(Text)  # 文书的大意，默认为空
    Doc_createdData = Column(String(50))  # 文书创建时间（如"康熙三年"）
    Doc_updatedData = Column(String(50))  # 文书修改时间（如"康熙四年"）
    Doc_createdGregorianDate = Column(DateTime)  # 文书公历创建时间
    Doc_updatedGregorianDate = Column(DateTime)  # 文书公历修改时间
    
    
    # 关系定义：
    participants = relationship('Participants', backref='document', cascade='all, delete-orphan')  # 与参与者的关系
    highlights = relationship('Highlights', backref='document', cascade='all, delete-orphan')  # 高亮记录
    notes = relationship('Notes', backref='document', cascade='all, delete-orphan')  # 批注记录
    comments = relationship('Comments', backref='document', cascade='all, delete-orphan')  # 评论记录
    corrections = relationship('Corrections', backref='document', cascade='all, delete-orphan')  # 纠错记录
    keywords = relationship('DocKeywords', backref='document', cascade='all, delete-orphan')  # 文书关键词

    # 定义索引：帮助优化查询
    __table_args__ = (
        db.Index('idx_Doc_id', 'Doc_id'),  # 为'文书序号'建立索引，使用正确的列名
        db.Index('idx_Doc_type', 'Doc_type'),  # 为'文书类型'创建索引
        db.Index('idx_Doc_createdGregorianDate', 'Doc_createdGregorianDate'),  # 为文'书创建日期' 创建索引
        db.Index('idx_doc_created_data', 'Doc_createdData'),  # 为文'书创建时间' 创建索引
        db.Index('idx_doc_updated_data', 'Doc_updatedData'),  # 添加修改时间的索引
        {'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'}
    )

#标准创建时间表
class StandardCreationTime(db.Model):
    __tablename__ = 'StandardCreationTime'

    Time_id = Column(Integer, primary_key=True, autoincrement=True)  # 自增主键
    createdData = Column(String(50), ForeignKey('Documents.Doc_createdData', ondelete='CASCADE'), nullable=False)  # 外键，引用 Doc_createdData
    Standard_createdData = Column(TIMESTAMP, nullable=False)  # 标准化时间（公历时间）
    Doc_id = Column(String(20), ForeignKey('Documents.Doc_id', ondelete='CASCADE'), nullable=False)  # 外键，关联到 Documents 表

    # 修改关系定义，明确指定外键
    document = relationship('Documents', 
                          foreign_keys=[Doc_id],  # 明确指定使用 Doc_id 作为外键
                          backref=db.backref('standard_creation_time', uselist=False))

    # 在 Standard_creation_time 上建立索引，优化查询
    __table_args__ = (
        db.Index('idx_Standard_createdData', 'Standard_createdData'),  # 为标准时间字段添加索引
        db.Index('idx_Doc_id', 'Doc_id'),  # 为 Doc_id 添加索引
        {'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'}
    )


#标准修改时间表
class StandardUpdateTime(db.Model):
    __tablename__ = 'StandardUpdateTime'

    Time_id = Column(Integer, primary_key=True, autoincrement=True)  # 自增主键
    updatedData = Column(String(50), ForeignKey('Documents.Doc_updatedData', ondelete='CASCADE'), nullable=False)  # 外键，引用 Doc_updatedData
    Standard_updatedData = Column(DateTime, nullable=False)  # 标准化时间（公历时间）
    Doc_id = Column(String(20), ForeignKey('Documents.Doc_id', ondelete='CASCADE'), nullable=False)  # 外键，关联到 Documents 表

    # 修改关系定义，明确指定外键
    document = relationship('Documents', 
                          foreign_keys=[Doc_id],  # 明确指定使用 Doc_id 作为外键
                          backref=db.backref('standard_update_time', uselist=False))

    # 在 Standard_update_time 上建立索引，优化查询
    __table_args__ = (
        db.Index('idx_Standard_updatedData', 'Standard_updatedData'),  # 为标准时间字段添加索引
        db.Index('idx_Doc_id', 'Doc_id'),  # 为 Doc_id 添加索引
        {'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'}
    )



# 2、文书关键词类：DocKeywords
class DocKeywords(db.Model):
    __tablename__ = 'DocKeywords' #表名为 'DocKeywords'

    KeyWord_id = Column(Integer,primary_key=True,autoincrement=True)  #关键词序号，自主键
    Doc_id = Column(String(20), ForeignKey('Documents.Doc_id', ondelete='CASCADE'), nullable=False) #文书ID
    KeyWord = Column(String(50),nullable=False)  #关键词，非空

    __table_args__ = (
        db.Index('idx_Doc_id', 'Doc_id'),
        db.Index('idx_KeyWord', 'KeyWord'),
        {'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'}
    )


# 人物类：People
class People(db.Model):
    __tablename__ = 'People'  # 表名为 'People'

    Person_id = Column(Integer, primary_key=True, autoincrement=True)  # 人物序号，自增主键
    Person_name = Column(String(100), nullable=False)  # 人物名称

    __table_args__ = (
        {'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'}
    )


# 文书参与类：Participants 参与者只有代写等等人，对于契约人不涉及，相当于将他们当作两种类型
class Participants(db.Model):
    __tablename__ = 'Participants'  # 表名为 'Participants'
    
    Person_id = Column(Integer, ForeignKey('People.Person_id', ondelete='CASCADE'), primary_key=True)
    Doc_id = Column(String(20), ForeignKey('Documents.Doc_id', ondelete='CASCADE'), primary_key=True)
    Part_role = Column(String(50), nullable=False)

    __table_args__ = (
        db.Index('idx_Person_id', 'Person_id'),
        db.Index('idx_Doc_id', 'Doc_id'),
        {'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'}
    )

# 契约人类：Contractors
class Contractors(db.Model):
    __tablename__ = 'Contractors'

    Doc_id = Column(String(20), ForeignKey('Documents.Doc_id', ondelete='CASCADE'), primary_key=True)
    Alice_id = Column(Integer, ForeignKey('People.Person_id', ondelete='CASCADE'), nullable=False)
    Bob_id = Column(Integer, ForeignKey('People.Person_id', ondelete='CASCADE'), nullable=False)

    Alice = relationship('People', foreign_keys=[Alice_id])
    Bob = relationship('People', foreign_keys=[Bob_id])

    __table_args__ = (
        db.Index('idx_doc_id', 'Doc_id'),
        db.Index('idx_alice_id', 'Alice_id'),
        db.Index('idx_bob_id', 'Bob_id'),
        {'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'}
    )


# 人物关系类：Relations 
class Relations(db.Model):
    __tablename__ = 'Relations'  # 表名为 'Relations'

    Alice_id = Column(Integer, ForeignKey('People.Person_id', ondelete='CASCADE'), primary_key=True)
    Bob_id = Column(Integer, ForeignKey('People.Person_id', ondelete='CASCADE'), primary_key=True)
    Relation_type = Column(String(50))

    alice = relationship('People', foreign_keys=[Alice_id], backref='alice_relations')
    bob = relationship('People', foreign_keys=[Bob_id], backref='bob_relations')

    __table_args__ = (
        db.Index('idx_Alice_Bob', 'Alice_id', 'Bob_id'),
        {'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'}
    )

    
# 用户类：Users
class Users(db.Model, UserMixin):
    __tablename__ = 'Users'  # 表名为 'Users'
    
    User_id = Column(Integer, primary_key=True, autoincrement=True)  # 用户的唯一标识符
    User_name = Column(String(100), nullable=False, unique=True)  # 用户名，唯一，非空
    User_passwordHash = Column(String(255), nullable=False)  # 密码的哈希值，非空
    User_email = Column(String(150), nullable=False, unique=True)  # 用户邮箱，唯一，非空
    User_role = Column(Enum('Admin', 'Member', 'NonMember'), nullable=False)  # 用户角色
    avatar_id = Column(String(10), default='1')  # 添加头像ID字段，默认为'1'
    
    # 关系定义：
    highlights = relationship('Highlights', backref='user', cascade='all, delete-orphan')  # 用户与高亮记录的关联
    notes = relationship('Notes', backref='user', cascade='all, delete-orphan')  # 用户与批注记录的关联
    folders = relationship('Folders', backref='user', cascade='all, delete-orphan')  # 用户与收藏夹的关联
    corrections = relationship('Corrections', backref='user', cascade='all, delete-orphan')  # 用户与纠错记录的关联
    comments = relationship('Comments', backref='user', cascade='all, delete-orphan')  # 用户与评论记录的关联

    __table_args__ = (
        {'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'}
    )

    def get_id(self):
        return str(self.User_id)



# 高亮类：Highlights
class Highlights(db.Model):
    __tablename__ = 'Highlights'  # 表名为 'Highlights'
    
    Highlight_id = Column(Integer, primary_key=True, autoincrement=True)  # 高亮记录的序号，自增主键
    Doc_id = Column(String(20), ForeignKey('Documents.Doc_id', ondelete='CASCADE'), nullable=False)  # 外键，关联到 'Documents' 表的 Doc_id
    User_id = Column(Integer, ForeignKey('Users.User_id', ondelete='CASCADE'), nullable=False)  # 外键，关联到 'Users' 表的 User_id
    Highlight_startPosition = Column(Integer, nullable=False)  # 高亮起始位置（字符索引）
    Highlight_endPosition = Column(Integer, nullable=False)  # 高亮结束位置（字符索引）
    Highlight_color = Column(String(20), default='yellow')  # 高亮颜色，默认为 'yellow'
    Highlight_createdAt = Column(TIMESTAMP, default=func.current_timestamp())  # 高亮创建时间，默认为当前时间戳

    # 建立索引优化查询
    __table_args__ = (
        db.Index('idx_Highlight_user', 'User_id'),
        db.Index('idx_Highlight_doc', 'Doc_id'),
        {'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'}
    )




# 批注类：Notes
class Notes(db.Model):
    __tablename__ = 'Notes'  # 表名为 'Notes'
    
    Note_id = Column(Integer, primary_key=True, autoincrement=True)  # 批注记录的序号，自增主
    Doc_id = Column(String(20), ForeignKey('Documents.Doc_id', ondelete='CASCADE'), nullable=False)  # 外键，关联到 'Documents' 表的 Doc_id
    User_id = Column(Integer, ForeignKey('Users.User_id', ondelete='CASCADE'), nullable=False)  # 外键，关联到 'Users' 表的 User_id
    Note_annotationText = Column(Text, nullable=False)  # 批注内容，非空
    Note_startPosition = Column(Integer, nullable=False)  # 批注起始位置（字符索引）
    Note_endPosition = Column(Integer, nullable=False)  # 批注结束位置（字符索引）
    Note_createdAt = Column(TIMESTAMP, default=func.current_timestamp())  # 批注创建时间，默认为当前时间戳

    # 建立索引优化查询
    __table_args__ = (
        db.Index('idx_Note_user', 'User_id'),
        db.Index('idx_Note_doc', 'Doc_id'),
        {'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'}
    )




# 收藏夹类：Folders
class Folders(db.Model):
    __tablename__ = 'Folders'  # 表名为 'Folders'
    
    Folder_id = Column(Integer, primary_key=True, autoincrement=True)  # 收藏夹的序号，自增主键
    User_id = Column(Integer, ForeignKey('Users.User_id', ondelete='CASCADE'), nullable=False)  # 外键，关联到用户ID
    Doc_id = Column(String(20), ForeignKey('Documents.Doc_id', ondelete='CASCADE'), nullable=False)  # 外键，文书ID
    Folder_name = Column(String(255), nullable=False)  # 收藏夹名称，非空
    Folder_createdAt = Column(TIMESTAMP, default=func.current_timestamp())  # 收藏夹创建时间，默认为当前时间戳

    # 确保同一用户不能为同一文书创建多个相同名称的文件夹
    __table_args__ = (
        db.UniqueConstraint('User_id', 'Doc_id', 'Folder_name', name='unique_folder_doc'),
        {'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'}
    )




# 审计日志类：AuditLog
class AuditLog(db.Model):
    __tablename__ = 'AuditLog'  # 表名为 'AuditLog'
    
    Audit_id = Column(Integer, primary_key=True, autoincrement=True)  # 审计记录的唯一标识符
    User_id = Column(Integer, ForeignKey('Users.User_id', ondelete='SET NULL'))  # 外键，关联到 'Users' 表的 User_id
    Audit_actionType = Column(String(50), nullable=False)  # 操作类型（如创建、更新等），非空
    Audit_actionDescription = Column(Text, nullable=False)  # 操作的详细描述，非空
    Audit_targetTable = Column(String(50))  # 被操作的表
    Audit_timestamp = Column(TIMESTAMP, default=func.current_timestamp())  # 操作时间，默认为当前时间戳
    
    __table_args__ = (
        {'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'}
    )



# 纠错类：Corrections
class Corrections(db.Model):
    __tablename__ = 'Corrections'  # 表名为 'Corrections'
    
    Correction_id = Column(Integer, primary_key=True, autoincrement=True)  # 纠错记录的唯一标识符
    Doc_id = Column(String(20), ForeignKey('Documents.Doc_id', ondelete='CASCADE'), nullable=False)  # 外键，联到 'Documents' 表的 Doc_id
    User_id = Column(Integer, ForeignKey('Users.User_id', ondelete='SET NULL'))  # 外键，关联到 'Users' 表的 User_id
    Correction_text = Column(Text, nullable=False)  # 纠错内容，非空
    Correction_createdAt = Column(TIMESTAMP, default=func.current_timestamp())  # 纠错提交时间，默认为当前时间戳

    __table_args__ = (
        {'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'}
    )




# 评论类：Comments
class Comments(db.Model):
    __tablename__ = 'Comments'  # 表名为 'Comments'
    
    Comment_id = Column(Integer, primary_key=True, autoincrement=True)  # 评论记录的唯一标识符
    Doc_id = Column(String(20), ForeignKey('Documents.Doc_id', ondelete='CASCADE'), nullable=False)  # 外键，关联到 'Documents' 表的 Doc_id
    User_id = Column(Integer, ForeignKey('Users.User_id', ondelete='SET NULL'))  # 外键，关联到 'Users' 表的 User_id
    Comment_text = Column(Text, nullable=False)  # 评论内容，非空
    Comment_createdAt = Column(TIMESTAMP, default=func.current_timestamp())  # 评论创建时间，默认为当前时间戳

    __table_args__ = (
        {'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'}
    )




# 笔记类：Evernote
class Evernote(db.Model):
    __tablename__ = 'Evernote'  # 表名为 'History'
    
    Evernote_id = Column(Integer, primary_key=True, autoincrement=True)  # 笔记的唯一标识符
    User_id = Column(Integer, ForeignKey('Users.User_id', ondelete='CASCADE'), nullable=False)  # 外键，关联到 'Users' 表的 User_id
    Doc_id = Column(String(20), ForeignKey('Documents.Doc_id', ondelete='CASCADE'), nullable=False)  # 外键，关联到 'Documents' 表的 Doc_id
    Evernote_text = Column(Text, nullable=False)  # 笔记内容，非空
    Evernote_viewedAt = Column(TIMESTAMP, default=func.current_timestamp())  # 笔记时间，默认为当前时间戳

    __table_args__ = (
        {'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'}
    )




# 用户浏览记录类：UserBrowsingHistory
class UserBrowsingHistory(db.Model):
    __tablename__ = 'UserBrowsingHistory'  # 表名为 'UserBrowsingHistory'
    
    Browse_id = Column(Integer, primary_key=True, autoincrement=True)  # 浏览记录的序号
    User_id = Column(Integer, ForeignKey('Users.User_id', ondelete='CASCADE'), nullable=False)  # 外键，删除用户时级联删除浏览记录
    Doc_id = Column(String(20), ForeignKey('Documents.Doc_id', ondelete='CASCADE'), nullable=False)  # 外键，删除文书时级联删除浏览记录
    Browse_time = Column(TIMESTAMP, default=func.current_timestamp())  # 浏览��间，默认为当前时间戳
    
    __table_args__ = (
        db.Index('idx_User_id_Doc_id', 'User_id', 'Doc_id'),  # 联合索引，提高查询效率
        {'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'}  # 设置字符集
    )

print("程序已成功运行")

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

#1、时间表
class TimeRecord(db.Model):
    __tablename__ = 'TimeRecord'

    Time_id = Column(Integer, primary_key=True, autoincrement=True)
    createdData = Column(String(50), nullable=False)  # 原始时间（"康熙三年"）
    Standard_createdData = Column(TIMESTAMP, nullable=False)  # 标准化时间（公历时间）
    __table_args__ = (
        db.Index('idx_createdData', 'createdData'),
        db.Index('idx_Standard_createdData', 'Standard_createdData'),
        {'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'}
    )


# 2、文书类：Documents
class Documents(db.Model):
    __tablename__ = 'Documents'

    Doc_id = Column(String(20), primary_key=True)
    Doc_title = Column(String(255), nullable=False)
    Doc_originalText = Column(Text, nullable=False)
    Doc_simplifiedText = Column(Text)
    Doc_type = Column(Enum('借钱契', '租赁契', '抵押契','赋税契','诉状','判决书','祭祀契约','祠堂契','劳役契','其他'), nullable=False)
    Doc_summary = Column(Text)
    Doc_image_path = Column(String(255), nullable=False, default='images/documentsdoc_img_{doc_id}.jpg')  # 文书图片路径
    
    # 修改外键关系
    Doc_createdTime_id = Column(Integer, 
                               ForeignKey('TimeRecord.Time_id', 
                                        ondelete='SET NULL', 
                                        onupdate='CASCADE'))
    Doc_updatedTime_id = Column(Integer, 
                               ForeignKey('TimeRecord.Time_id', 
                                        ondelete='SET NULL', 
                                        onupdate='CASCADE'))

    # 关系定义：
    participants = relationship('Participants', backref='document', cascade='all, delete-orphan')  # 与参与者的关系
    highlights = relationship('Highlights', backref='document', cascade='all, delete-orphan')  # 高亮记录
    notes = relationship('Notes', backref='document', cascade='all, delete-orphan')  # 批注记录
    comments = relationship('Comments', backref='document', cascade='all, delete-orphan')  # 评论记录
    corrections = relationship('Corrections', backref='document', cascade='all, delete-orphan')  # 纠错记录
    keywords = relationship('DocKeywords', backref='document', cascade='all, delete-orphan')  # 文书关键词

    # 定义索引：帮助优化查询
    __table_args__ = (
        db.Index('idx_Doc_id', 'Doc_id'),  # 为'文书序号'建立索引
        db.Index('idx_Doc_type', 'Doc_type'),  # 为'文书类型'创建索引
        db.Index('idx_Doc_createdTime_id', 'Doc_createdTime_id'),  # 为'文书创建日期'创建索引
        db.Index('idx_Doc_updatedTime_id', 'Doc_updatedTime_id'),  # 添加修改时间的索引
        db.Index('ft_doc_content', 'Doc_title', 'Doc_simplifiedText', 'Doc_originalText', mysql_prefix='FULLTEXT'),
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

    Person_id = Column(Integer, primary_key=True, autoincrement=True)  # 人物序号，增主键
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
    notes = relationship('Notes', backref='user', cascade='all, delete-orphan')  # 用户与批注记���的关联
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
    Highlight_color = Column(String(20), default='yellow')  # 高亮颜色，默认������������� 'yellow'
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
    Note_annotationText = Column(Text, nullable=False)  # ��注内容，非空
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

    Folder_id = Column(Integer, primary_key=True, autoincrement=True)  # 收藏夹序号
    User_id = Column(Integer, ForeignKey('Users.User_id', ondelete='CASCADE'), nullable=False)  # 外键，用户ID
    Folder_name = Column(String(255), nullable=False)  # 文件夹名称
    Remarks = Column(String(255), default=None)  # 备注字段
    Folder_createdAt = Column(TIMESTAMP, default=func.current_timestamp())  # 文件夹创建时间

    __table_args__ = (
        db.Index('idx_User_id', 'User_id'),  # 为 User_id 创建索引
        {'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'}
    )

# 收藏内容类：FolderContent（作为关联表）
class FolderContent(db.Model):
    __tablename__ = 'FolderContent'
    
    Content_id = Column(Integer, primary_key=True, autoincrement=True)
    Folder_id = Column(Integer, ForeignKey('Folders.Folder_id', ondelete='CASCADE'), nullable=False)
    Doc_id = Column(String(20), ForeignKey('Documents.Doc_id', ondelete='CASCADE'), nullable=False)
    CreatedAt = Column(TIMESTAMP, default=func.current_timestamp())

    __table_args__ = (
        db.UniqueConstraint('Folder_id', 'Doc_id', name='unique_folder_document'),  # 确保同一文件夹不会重复收藏同一文档
        db.Index('idx_Folder_id', 'Folder_id'),
        db.Index('idx_Doc_id', 'Doc_id'),
        {'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'}
    ) 




# 审计日志类：AuditLog
class AuditLog(db.Model):
    __tablename__ = 'AuditLog'
    
    Audit_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    User_id = db.Column(db.String(20), db.ForeignKey('Users.User_id'), nullable=False)
    Audit_actionType = db.Column(db.String(50), nullable=False)  # 操作类型
    Audit_actionDescription = db.Column(db.String(200), nullable=False)  # 操作描述
    Audit_targetTable = db.Column(db.String(50), nullable=False)
    Audit_timestamp = db.Column(db.DateTime, nullable=False)  # 操作时间
    



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
    __tablename__ = 'Comments'  # 表为 'Comments'
    
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
    
    Browse_id = Column(Integer, primary_key=True, autoincrement=True)  # �����览记录的序号
    User_id = Column(Integer, ForeignKey('Users.User_id', ondelete='CASCADE'), nullable=False)  # 外键，删除用户时级联删除浏览记录
    Doc_id = Column(String(20), ForeignKey('Documents.Doc_id', ondelete='CASCADE'), nullable=False)  # 外键，删除文书时级联删除浏览记录
    Browse_time = Column(TIMESTAMP, default=func.current_timestamp())  # 浏览时间，默认为当前时间戳
    
    __table_args__ = (
        db.Index('idx_User_id_Doc_id', 'User_id', 'Doc_id'),  # 联合索引，提高查询效率
        {'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'}  # 设置字符集
    )

# 文书展示视图模型
class DocumentDisplayView(db.Model):
    """
    文书展示视图
    用于在页面中展示文书的基本信息，同时支持搜索功能
    """
    __tablename__ = 'DocumentDisplayView'
    __table_args__ = {'info': {'is_view': True}}
    
    Doc_id = Column(String(20), primary_key=True)
    Doc_title = Column(String(255))         # 文书标题
    Doc_type = Column(Enum('借钱契', '租赁契', '抵押契','赋税契','诉状','判决书','祭祀契约','祠堂契','劳役契','其他'))  # 文书类型
    Doc_summary = Column(Text)              # 文书大意
    Doc_image_path = Column(String(255))         # 文书图片路径
    Doc_time = Column(String(50))           # 签约时间（原始格式）
    Doc_standardTime = Column(TIMESTAMP)    # 签约时间（公历格式）
    ContractorInfo = Column(Text)           # 格式：《张三》《李四》（叔侄）
    ParticipantInfo = Column(Text)          # 格式：《王五》（见证人）《赵六》（代书）

    def __repr__(self):
        return f'<DocumentDisplay {self.Doc_title}>'
    
    def to_dict(self):
        """转换为字典格式，方便JSON序列化"""
        return {
            'doc_id': self.Doc_id,
            'title': self.Doc_title,
            'type': self.Doc_type,
            'time': self.Doc_time,
            'image': self.Doc_image,
            'summary': self.Doc_summary[:200] + '...' if self.Doc_summary and len(self.Doc_summary) > 200 else self.Doc_summary,
            'contractors': self.ContractorInfo,
            'participants': self.ParticipantInfo
        }

# 新增 FolderContents 表模型
class FolderContents(db.Model):
    __tablename__ = 'FolderContents'  # 表名为 'FolderContents'

    Content_id = Column(Integer, primary_key=True, autoincrement=True)  # 自增主键
    Folder_id = Column(Integer, ForeignKey('Folders.Folder_id', ondelete='CASCADE'), nullable=False)  # 外键，关联到 Folders 表的 Folder_id
    Doc_id = Column(String(20), ForeignKey('Documents.Doc_id', ondelete='CASCADE'), nullable=False)  # 外键，文书ID
    CreatedAt = Column(TIMESTAMP, default=func.current_timestamp())  # 创建时间
    
    
    __table_args__ = (
        db.Index('idx_Folder_id', 'Folder_id'),  # 为 Folder_id 创建索引
        db.Index('idx_Doc_id', 'Doc_id'),  # 为 Doc_id 创建索引
        {'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'}
    )

from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

#新增收藏夹统计视图
class FolderDocumentStats(db.Model):
    __tablename__ = 'FolderDocumentStats'

    Folder_id = Column(Integer, primary_key=True)  # 收藏夹ID
    Folder_name = Column(String)                    # 收藏夹名称
    Borrow_Contract = Column(Integer)               # 借钱契数量
    Lease_Contract = Column(Integer)                # 租赁契数量
    Mortgage_Contract = Column(Integer)             # 抵押契数量
    Tax_Contract = Column(Integer)                  # 赋税契数量
    Lawsuit = Column(Integer)                       # 诉状数量
    Judgement = Column(Integer)                     # 判决书数量
    Sacrificial_Contract = Column(Integer)          # 祭祀契约数量
    Ancestral_Hall_Contract = Column(Integer)       # 祠堂契数量
    Labor_Contract = Column(Integer)                # 劳役契数量
    Other_Contract = Column(Integer)                # 其他类型数量
    
    # 自定义序列化方法，将对象转换为字典
    def to_dict(self):
        return {
            'Folder_id': self.Folder_id,
            'Folder_name': self.Folder_name,
            'Borrow_Contract': self.Borrow_Contract,
            'Lease_Contract': self.Lease_Contract,
            'Mortgage_Contract': self.Mortgage_Contract,
            'Tax_Contract': self.Tax_Contract,
            'Lawsuit': self.Lawsuit,
            'Judgement': self.Judgement,
            'Sacrificial_Contract': self.Sacrificial_Contract,
            'Ancestral_Hall_Contract': self.Ancestral_Hall_Contract,
            'Labor_Contract': self.Labor_Contract,
            'Other_Contract': self.Other_Contract
        }
        
     # 删除 `autoload_with`，不需要在这里自动加载表结构
    __table_args__ = {'extend_existing': True}

print("程序已成功运行")

CREATE DATABASE IF NOT EXISTS 永泰文书 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE 永泰文书;

-- 1、TimeRecord
CREATE TABLE IF NOT EXISTS TimeRecord (
    Time_id INT AUTO_INCREMENT PRIMARY KEY,  -- 自增主键
    createdData VARCHAR(50) NOT NULL,  -- 原始时间（如“康熙三年”）
    Standard_createdData DATETIME NOT NULL,  -- 标准化时间（公历时间）
    
    INDEX idx_createdData (createdData),  -- 原始时间索引
    INDEX idx_Standard_createdData (Standard_createdData) -- 标准化时间索引
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2、文书类：Documents
CREATE TABLE IF NOT EXISTS Documents (
    Doc_id VARCHAR(20) PRIMARY KEY,  -- 文书序号
    Doc_title VARCHAR(255) NOT NULL,  -- 文书标题
    Doc_originalText TEXT NOT NULL,  -- 文书的繁体原文
    Doc_simplifiedText TEXT DEFAULT NULL,  -- 文书的简体原文
    Doc_type ENUM('借钱契', '租赁契', '抵押契','赋税契','诉状','判决书','祭祀契约','祠堂契','劳役契','其他') NOT NULL,  -- 文书类型
    Doc_summary TEXT DEFAULT NULL,  -- 文书的大意
    Doc_createdTime_id INT,
    Doc_updatedTime_id INT,
    Doc_image_path VARCHAR(255) DEFAULT 'images/document_img/doc_0.jpg', -- 图片路径
    
    -- 外键约束
    CONSTRAINT fk_doc_created_time FOREIGN KEY (Doc_createdTime_id) REFERENCES TimeRecord(Time_id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_doc_updated_time FOREIGN KEY (Doc_updatedTime_id) REFERENCES TimeRecord(Time_id) ON DELETE SET NULL ON UPDATE CASCADE,
        
    INDEX idx_Doc_id (Doc_id),  -- 文书序号索引
    INDEX idx_Doc_type (Doc_type),  -- 文书类型索引
    INDEX idx_Doc_createdTime_id (Doc_createdTime_id),  -- 创建时间索引
    INDEX idx_Doc_updatedTime_id (Doc_updatedTime_id)  -- 修改时间索引
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;  -- 设置字符集为 utf8mb4
ALTER TABLE documents ADD FULLTEXT INDEX ft_doc_content (Doc_title,Doc_simplifiedText,Doc_originalText) WITH PARSER ngram;   -- 添加全文索引

-- 4、文书关键词类：DocKeywords
CREATE TABLE IF NOT EXISTS DocKeywords (
    KeyWord_id INT AUTO_INCREMENT PRIMARY KEY,  -- 关键词序号
    Doc_id VARCHAR(20) NOT NULL,  -- 文书ID
    KeyWord VARCHAR(50) NOT NULL,  -- 关键词
    FOREIGN KEY (Doc_id) REFERENCES Documents(Doc_id) ON DELETE CASCADE,
    INDEX idx_Doc_id (Doc_id),  -- 为 Doc_id 添加索引
    INDEX idx_KeyWord (KeyWord)  -- 为 KeyWord 添加索引
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;



-- 5、人物类：People
CREATE TABLE IF NOT EXISTS People (
    Person_id INT AUTO_INCREMENT PRIMARY KEY,  -- 人物序号
    Person_name VARCHAR(100) NOT NULL  -- 人物名称
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;



-- 6、文书参与者类：Participants 参与者只有代写等等人，对于契约人不涉及，相当于将他们当作两种类型
CREATE TABLE IF NOT EXISTS Participants (
    Person_id INT NOT NULL,  -- 外键，人物ID
    Doc_id VARCHAR(20) NOT NULL,  -- 外键，文书ID
    Part_role VARCHAR(50) NOT NULL,  -- 参与者的角色
    PRIMARY KEY (Person_id, Doc_id),  -- 联合主键
    FOREIGN KEY (Person_id) REFERENCES People(Person_id) ON DELETE CASCADE,  -- 外键约束，引用 People 表
    FOREIGN KEY (Doc_id) REFERENCES Documents(Doc_id) ON DELETE CASCADE,  -- 外键约束，引用 Documents 表
    INDEX idx_Person_id (Person_id),  -- 为 Person_id 添加索引
    INDEX idx_Doc_id (Doc_id)  -- 为 Doc_id 添加索引
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;



-- 7、契约人类：Contractors
CREATE TABLE IF NOT EXISTS Contractors (
    Doc_id VARCHAR(20) NOT NULL,  -- 外键，文书ID
    Alice_id INT NOT NULL,  -- 外键，人物ID
    Bob_id INT NOT NULL,  -- 外键，人物ID
    PRIMARY KEY (Doc_id),  -- 文书ID作为主键
    FOREIGN KEY (Doc_id) REFERENCES Documents(Doc_id) ON DELETE CASCADE,  -- 外键约束，引用 Documents 表
    FOREIGN KEY (Alice_id) REFERENCES People(Person_id) ON DELETE CASCADE,  -- 外键约束，引用 People 表
    FOREIGN KEY (Bob_id) REFERENCES People(Person_id) ON DELETE CASCADE,  -- 外键约束，引用 People 表
    INDEX idx_doc_id (Doc_id),  -- 为 Doc_id 添加索引
    INDEX idx_alice_id (Alice_id),  -- 为 Alice_id 添加索引
    INDEX idx_bob_id (Bob_id)  -- 为 Bob_id 添加索引
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;



--  8、人物关系类：
CREATE TABLE IF NOT EXISTS Relations (
    Alice_id INT NOT NULL,  -- 外键，人物ID
    Bob_id INT NOT NULL,  -- 外键，人物ID
    Relation_type VARCHAR(50) DEFAULT NULL,  -- 关系类型
    PRIMARY KEY (Alice_id, Bob_id),  -- 联合主键，确保 Alice 和 Bob 的组合唯一
    FOREIGN KEY (Alice_id) REFERENCES People(Person_id) ON DELETE CASCADE,  -- 外键约束，引用 People 表
    FOREIGN KEY (Bob_id) REFERENCES People(Person_id) ON DELETE CASCADE,  -- 外键约束，引用 People 表
    INDEX idx_Alice_Bob (Alice_id, Bob_id)  -- 为 Alice_id 和 Bob_id 添加组合索引
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;



-- 9、用户类：Users
CREATE TABLE IF NOT EXISTS Users (
    User_id INT AUTO_INCREMENT PRIMARY KEY,  -- 用户唯一标识符
    User_name VARCHAR(100) NOT NULL UNIQUE,  -- 用户名，确保唯一
    User_passwordHash VARCHAR(255) NOT NULL,  -- 密码哈希
    User_email VARCHAR(150) NOT NULL UNIQUE,  -- 用户邮箱，确保唯一
    User_role ENUM('Admin', 'Member', 'NonMember') NOT NULL,  -- 用户角色
    avatar_id VARCHAR(10) DEFAULT '1'  -- 添加头像ID字段，默认为'1'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;



-- 10、高亮类：Highlights
CREATE TABLE IF NOT EXISTS Highlights (
    Highlight_id INT AUTO_INCREMENT PRIMARY KEY,  -- 高亮记录的序号
    Doc_id VARCHAR(20) NOT NULL,  -- 外键，文书ID
    User_id INT NOT NULL,  -- 外键，用户ID
    Highlight_startPosition INT NOT NULL,  -- 高亮起始位置
    Highlight_endPosition INT NOT NULL,  -- 高亮结束位置
    Highlight_color VARCHAR(20) DEFAULT 'yellow',  -- 高亮颜色
    Highlight_createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 高亮时间
    FOREIGN KEY (Doc_id) REFERENCES Documents(Doc_id) ON DELETE CASCADE,
    FOREIGN KEY (User_id) REFERENCES Users(User_id) ON DELETE CASCADE,
    INDEX idx_Highlight_user (User_id),  -- 为 User_id 创建索引
    INDEX idx_Highlight_doc (Doc_id)  -- 为 Doc_id 创建索引
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;



-- 11、批注类：Notes
CREATE TABLE IF NOT EXISTS Notes (
    Note_id INT AUTO_INCREMENT PRIMARY KEY,  -- 批注记录的序号
    Doc_id VARCHAR(20) NOT NULL,  -- 外键，文书ID
    User_id INT NOT NULL,  -- 外键，用户ID
    Note_annotationText TEXT NOT NULL,  -- 批注内容
    Note_startPosition INT NOT NULL,  -- 批注起始位置
    Note_endPosition INT NOT NULL,  -- 批注结束位置
    Note_createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 批注创建时间
    FOREIGN KEY (Doc_id) REFERENCES Documents(Doc_id) ON DELETE CASCADE,
    FOREIGN KEY (User_id) REFERENCES Users(User_id) ON DELETE CASCADE,
    INDEX idx_Note_user (User_id),  -- 为 User_id 创建索引
    INDEX idx_Note_doc (Doc_id)  -- 为 Doc_id 创建索引
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- 12、收藏夹类：Folders
CREATE TABLE IF NOT EXISTS Folders (
    Folder_id INT AUTO_INCREMENT PRIMARY KEY,  -- 收藏夹序号
    User_id INT NOT NULL,  -- 用户ID
    Folder_name VARCHAR(255) NOT NULL,  -- 文件夹名称
    Remarks VARCHAR(255) DEFAULT NULL,  -- 备注
    Folder_createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 文件夹创建时间
    FOREIGN KEY (User_id) REFERENCES Users(User_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;



-- 13、审计日志类：AuditLog
CREATE TABLE IF NOT EXISTS AuditLog (
    Audit_id INT AUTO_INCREMENT PRIMARY KEY,  -- 审计记录的唯一标识符
    User_id INT DEFAULT NULL,  -- 外键，用户ID，允许为空
    Audit_actionType VARCHAR(50) NOT NULL,  -- 操作类型（创建、更新等）
    Audit_actionDescription TEXT NOT NULL,  -- 操作描述
    Audit_targetTable VARCHAR(50) DEFAULT NULL,  -- 被操作的表名
    Audit_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 操作时间
    FOREIGN KEY (User_id) REFERENCES Users(User_id) ON DELETE SET NULL  -- 外键约束，删除用户时将 User_id 设置为 NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;



-- 14、纠错类：Corrections
CREATE TABLE IF NOT EXISTS Corrections (
    Correction_id INT AUTO_INCREMENT PRIMARY KEY,  -- 纠错记录的唯一标识符
    Doc_id VARCHAR(20) NOT NULL,  -- 外键，关联到 'Documents' 表的 Doc_id
    User_id INT DEFAULT NULL,  -- 外键，关联到 'Users' 表的 User_id
    Correction_text TEXT NOT NULL,  -- 纠错内容
    Correction_createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 纠错提交时间，默认为当前时间戳
    FOREIGN KEY (Doc_id) REFERENCES Documents(Doc_id) ON DELETE CASCADE,  -- 外键，删除文书时，删���相关纠错记录
    FOREIGN KEY (User_id) REFERENCES Users(User_id) ON DELETE SET NULL  -- 外键，删除用户时，设置纠错记录中的 User_id 为 NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;




-- 15、评论类：Comments
CREATE TABLE IF NOT EXISTS Comments (
    Comment_id INT AUTO_INCREMENT PRIMARY KEY,  -- 评论记录的唯一标识符
    Doc_id VARCHAR(20) NOT NULL,  -- 外键，关联到 'Documents' 表的 Doc_id
    User_id INT DEFAULT NULL,  -- 外键，关联到 'Users' 表的 User_id
    Comment_text TEXT NOT NULL,  -- 评论内容
    Comment_createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 评论创建时间，默认为当前时间戳
    FOREIGN KEY (Doc_id) REFERENCES Documents(Doc_id) ON DELETE CASCADE,  -- 外键，删除文书时，删除相关评论
    FOREIGN KEY (User_id) REFERENCES Users(User_id) ON DELETE SET NULL  -- 外键，删除用户时，设置评论记录中的 User_id 为 NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;



-- 16、笔记类：Evernote
CREATE TABLE IF NOT EXISTS Evernote (
    Evernote_id INT AUTO_INCREMENT PRIMARY KEY,  -- 笔记记录的唯一标识符
    User_id INT NOT NULL,  -- 外键，关联到 'Users' 表的 User_id
    Doc_id VARCHAR(20) NOT NULL,  -- 外键，关联到 'Documents' 表的 Doc_id
    Evernote_text TEXT NOT NULL,  -- 笔记内容
    Evernote_viewedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 笔记时间，默认为当前时间戳
    FOREIGN KEY (User_id) REFERENCES Users(User_id) ON DELETE CASCADE,  -- 外键，删除用户时级联删除笔记
    FOREIGN KEY (Doc_id) REFERENCES Documents(Doc_id) ON DELETE CASCADE  -- 外键，删除文书时级联删除笔记
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;



-- 17、用户浏览记录类：UserBrowsingHistory
CREATE TABLE IF NOT EXISTS UserBrowsingHistory (
    Browse_id INT AUTO_INCREMENT PRIMARY KEY,  -- 浏览记录的序号
    User_id INT NOT NULL,  -- 外键，关联到 'Users' 表的 User_id
    Doc_id VARCHAR(20) NOT NULL,  -- 外键，关联到 'Documents' 表的 Doc_id
    Browse_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 浏览时间，默认为当前时间戳
    FOREIGN KEY (User_id) REFERENCES Users(User_id) ON DELETE CASCADE,  -- 外键，删除用户时级联删除浏览记录
    FOREIGN KEY (Doc_id) REFERENCES Documents(Doc_id) ON DELETE CASCADE,  -- 外键，删除文书时级联删除浏览记录
    INDEX idx_User_id_Doc_id (User_id, Doc_id)  -- 联合索引，提高查询效率
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;



-- 18、收藏夹内容表 FolderContents
CREATE TABLE IF NOT EXISTS FolderContents (
    Content_id INT AUTO_INCREMENT PRIMARY KEY,  -- 自增主键
    Folder_id INT NOT NULL,  -- 外键，关联到 Folders 表的 Folder_id
    Doc_id VARCHAR(20) NOT NULL,  -- 外键，关联到 Documents 表的 Doc_id
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 创建时间
    FOREIGN KEY (Folder_id) REFERENCES Folders(Folder_id) ON DELETE CASCADE,  -- 外键，删除文件夹时级联删除
    FOREIGN KEY (Doc_id) REFERENCES Documents(Doc_id) ON DELETE CASCADE,  -- 外键，删除文书时级联删除
    INDEX idx_Folder_id (Folder_id),  -- 为 Folder_id 添加索引
    INDEX idx_Doc_id (Doc_id)  -- 为 Doc_id 添加索引
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 19、缓存表
CREATE TABLE cached_documents (
    doc_id VARCHAR(20) PRIMARY KEY,
    doc_originalText TEXT NOT NULL,
    image_path VARCHAR(255) DEFAULT NULL
);


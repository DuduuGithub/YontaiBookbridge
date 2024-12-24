-- Active: 1733227608922@@seasalt@3306@永泰文书
USE 永泰文书;

-- 1. 文书表（插入）
DELIMITER $$

CREATE TRIGGER After_Document_Insert
AFTER INSERT ON Documents
FOR EACH ROW
BEGIN
    INSERT INTO AuditLog (User_id, Audit_actionType, Audit_actionDescription, Audit_targetTable, Audit_timestamp)
    VALUES (@current_id, 'Create', 
            CONCAT(@current_role, '创建了文书: ', NEW.Doc_id), 
            'Documents', NOW());
END $$

-- 2. 文书表（更新）
CREATE TRIGGER After_Document_Update
AFTER UPDATE ON Documents
FOR EACH ROW
BEGIN
    INSERT INTO AuditLog (User_id, Audit_actionType, Audit_actionDescription, Audit_targetTable, Audit_timestamp)
    VALUES (@current_id, 'Update', 
            CONCAT(@current_role, '更新了文书: ', NEW.Doc_id), 
            'Documents', NOW());
END $$

-- 3. 文书表（删除）
CREATE TRIGGER After_Document_Delete
AFTER DELETE ON Documents
FOR EACH ROW
BEGIN
    INSERT INTO AuditLog (User_id, Audit_actionType, Audit_actionDescription, Audit_targetTable, Audit_timestamp)
    VALUES (@current_id, 'Delete', 
            '删除了文书: ', 
            'Documents', NOW());
END $$
-- 4. 标准时间表（插入）
CREATE TRIGGER After_TimeRecord_Insert
AFTER INSERT ON TimeRecord
FOR EACH ROW
BEGIN
    INSERT INTO AuditLog (User_id, Audit_actionType, Audit_actionDescription, Audit_targetTable, Audit_timestamp)
    VALUES (@current_id, 'Insert', 
            CONCAT(@current_role, ', 原始时间 = ', NEW.createdData, ', 标准化时间 = ', NEW.Standard_createdData), 
            'TimeRecord', NOW());
END $$


-- 5. 标准时间表（更新）
CREATE TRIGGER After_TimeRecord_Update
AFTER UPDATE ON TimeRecord
FOR EACH ROW
BEGIN
    INSERT INTO AuditLog (User_id, Audit_actionType, Audit_actionDescription, Audit_targetTable, Audit_timestamp)
    VALUES (@current_id, 'Update', 
            CONCAT(@current_role, 
                   ', 原始时间 = ', OLD.createdData, ' -> ', NEW.createdData,
                   ', 标准化时间 = ', OLD.Standard_createdData, ' -> ', NEW.Standard_createdData),
            'StandardCreationTime', NOW());
END $$


-- 6. 标准时间表（删除）
CREATE TRIGGER After_TimeRecord_Delete
AFTER DELETE ON TimeRecord
FOR EACH ROW
BEGIN
    INSERT INTO AuditLog (User_id, Audit_actionType, Audit_actionDescription, Audit_targetTable, Audit_timestamp)
    VALUES (@current_id, 'Delete', 
            CONCAT(@current_role, 
                   ', 原始时间 = ', OLD.createdData, ', 标准化时间 = ', OLD.Standard_createdData),
            'StandardCreationTime', NOW());
END $$

-- 10. 关键词表（插入）
CREATE TRIGGER After_DocKeywords_Insert
AFTER INSERT ON DocKeywords
FOR EACH ROW
BEGIN
    INSERT INTO AuditLog (User_id, Audit_actionType, Audit_actionDescription, Audit_targetTable, Audit_timestamp)
    VALUES (@current_id, 'Insert', 
            CONCAT(@current_role, '插入文书关键词记录: Doc_id = ', NEW.Doc_id, ', 关键词 = ', NEW.KeyWord), 
            'DocKeywords', NOW());
END $$

-- 11. 关键词表（更新）
CREATE TRIGGER After_DocKeywords_Update
AFTER UPDATE ON DocKeywords
FOR EACH ROW
BEGIN
    INSERT INTO AuditLog (User_id, Audit_actionType, Audit_actionDescription, Audit_targetTable, Audit_timestamp)
    VALUES (@current_id, 'Update', 
            CONCAT(@current_role, '更新文书关键词记录: Doc_id = ', OLD.Doc_id, ' -> ', NEW.Doc_id, 
                   ', 关键词 = ', OLD.KeyWord, ' -> ', NEW.KeyWord),
            'DocKeywords', NOW());
END $$

-- 12. 关键词表（删除）
CREATE TRIGGER After_DocKeywords_Delete
AFTER DELETE ON DocKeywords
FOR EACH ROW
BEGIN
    INSERT INTO AuditLog (User_id, Audit_actionType, Audit_actionDescription, Audit_targetTable, Audit_timestamp)
    VALUES (@current_id, 'Delete', 
            '删除文书关键词记录: ',
            'DocKeywords', NOW());
END $$

-- 13. 人物表（插入）
CREATE TRIGGER After_People_Insert
AFTER INSERT ON People
FOR EACH ROW
BEGIN
    INSERT INTO AuditLog (User_id, Audit_actionType, Audit_actionDescription, Audit_targetTable, Audit_timestamp)
    VALUES (@current_id, 'Insert', 
            CONCAT(@current_role, '插入人物记录: Person_id = ', NEW.Person_id, ', 人物名称 = ', NEW.Person_name), 
            'People', NOW());
END $$


-- 14. 人物表（更新）
CREATE TRIGGER After_People_Update
AFTER UPDATE ON People
FOR EACH ROW
BEGIN
    INSERT INTO AuditLog (User_id, Audit_actionType, Audit_actionDescription, Audit_targetTable, Audit_timestamp)
    VALUES (@current_id, 'Update', 
            CONCAT(@current_role, '更新人物记录: Person_id = ', OLD.Person_id, ' -> ', NEW.Person_id, 
                   ', 人物名称 = ', OLD.Person_name, ' -> ', NEW.Person_name),
            'People', NOW());
END $$

-- 15. 人物表（删除）
CREATE TRIGGER After_People_Delete
AFTER DELETE ON People
FOR EACH ROW
BEGIN
    INSERT INTO AuditLog (User_id, Audit_actionType, Audit_actionDescription, Audit_targetTable, Audit_timestamp)
    VALUES (@current_id, 'Delete', 
            CONCAT(@current_role, '删除人物记录: Person_id = ', OLD.Person_id, ', 人物名称 = ', OLD.Person_name),
            'People', NOW());
END $$

-- 16. 参与者表（插入）
CREATE TRIGGER After_Participants_Insert
AFTER INSERT ON Participants
FOR EACH ROW
BEGIN
    INSERT INTO AuditLog (User_id, Audit_actionType, Audit_actionDescription, Audit_targetTable, Audit_timestamp)
    VALUES (@current_id, 'Insert', 
            CONCAT(@current_role, '插入文书参与者记录: Person_id = ', NEW.Person_id, 
                   ', Doc_id = ', NEW.Doc_id, ', 角色 = ', NEW.Part_role), 
            'Participants', NOW());
END $$

-- 17. 参与者表（更新）
CREATE TRIGGER After_Participants_Update
AFTER UPDATE ON Participants
FOR EACH ROW
BEGIN
    INSERT INTO AuditLog (User_id, Audit_actionType, Audit_actionDescription, Audit_targetTable, Audit_timestamp)
    VALUES (@current_id, 'Update', 
            CONCAT(@current_role, '更新文书参与者记录: Person_id = ', OLD.Person_id, ' -> ', NEW.Person_id, 
                   ', Doc_id = ', OLD.Doc_id, ' -> ', NEW.Doc_id, 
                   ', 角色 = ', OLD.Part_role, ' -> ', NEW.Part_role),
            'Participants', NOW());
END $$

-- 18. 参与者表（删除）
CREATE TRIGGER After_Participants_Delete
AFTER DELETE ON Participants
FOR EACH ROW
BEGIN
    INSERT INTO AuditLog (User_id, Audit_actionType, Audit_actionDescription, Audit_targetTable, Audit_timestamp)
    VALUES (@current_id, 'Delete', 
            CONCAT(@current_role, '删除文书参与者记录: Person_id = ', OLD.Person_id, 
                   ', Doc_id = ', OLD.Doc_id, ', 角色 = ', OLD.Part_role),
            'Participants', NOW());
END $$


-- 19.  契约人表（插入）
CREATE TRIGGER After_Contractors_Insert
AFTER INSERT ON Contractors
FOR EACH ROW
BEGIN
    INSERT INTO AuditLog (User_id, Audit_actionType, Audit_actionDescription, Audit_targetTable, Audit_timestamp)
    VALUES (@current_id, 'Insert', 
            CONCAT(@current_role, '插入契约人记录: Doc_id = ', NEW.Doc_id, 
                   ', Alice_id = ', NEW.Alice_id, ', Bob_id = ', NEW.Bob_id), 
            'Contractors', NOW());
END $$


-- 20. 契约人表（更新）
CREATE TRIGGER After_Contractors_Update
AFTER UPDATE ON Contractors
FOR EACH ROW
BEGIN
    INSERT INTO AuditLog (User_id, Audit_actionType, Audit_actionDescription, Audit_targetTable, Audit_timestamp)
    VALUES (@current_id, 'Update', 
            CONCAT(@current_role, '更新契约人记录: Doc_id = ', OLD.Doc_id, ' -> ', NEW.Doc_id, 
                   ', Alice_id = ', OLD.Alice_id, ' -> ', NEW.Alice_id, 
                   ', Bob_id = ', OLD.Bob_id, ' -> ', NEW.Bob_id),
            'Contractors', NOW());
END $$

-- 21. 契约人表（删除）
CREATE TRIGGER After_Contractors_Delete
AFTER DELETE ON Contractors
FOR EACH ROW
BEGIN
    INSERT INTO AuditLog (User_id, Audit_actionType, Audit_actionDescription, Audit_targetTable, Audit_timestamp)
    VALUES (@current_id, 'Delete', 
            CONCAT(@current_role, '删除契约人记录: Doc_id = ', OLD.Doc_id, 
                   ', Alice_id = ', OLD.Alice_id, ', Bob_id = ', OLD.Bob_id),
            'Contractors', NOW());
END $$

-- 22. 人物关系表（插入）
CREATE TRIGGER After_Relations_Insert
AFTER INSERT ON Relations
FOR EACH ROW
BEGIN
    INSERT INTO AuditLog (User_id, Audit_actionType, Audit_actionDescription, Audit_targetTable, Audit_timestamp)
    VALUES (@current_id, 'Insert', 
            CONCAT(@current_role, '插入关系记录: Alice_id = ', NEW.Alice_id, 
                   ', Bob_id = ', NEW.Bob_id, 
                   ', Relation_type = ', NEW.Relation_type), 
            'Relations', NOW());
END $$

-- 23. 人物关系表（更新）
CREATE TRIGGER After_Relations_Update
AFTER UPDATE ON Relations
FOR EACH ROW
BEGIN
    INSERT INTO AuditLog (User_id, Audit_actionType, Audit_actionDescription, Audit_targetTable, Audit_timestamp)
    VALUES (@current_id, 'Update', 
            CONCAT(@current_role, '更新关系记录: Alice_id = ', OLD.Alice_id, ' -> ', NEW.Alice_id, 
                   ', Bob_id = ', OLD.Bob_id, ' -> ', NEW.Bob_id, 
                   ', Relation_type = ', OLD.Relation_type, ' -> ', NEW.Relation_type),
            'Relations', NOW());
END $$

-- 24. 人物关系表（删除）
CREATE TRIGGER After_Relations_Delete
AFTER DELETE ON Relations
FOR EACH ROW
BEGIN
    INSERT INTO AuditLog (User_id, Audit_actionType, Audit_actionDescription, Audit_targetTable, Audit_timestamp)
    VALUES (@current_id, 'Delete', 
            CONCAT(@current_role, '删除关系记录: Alice_id = ', OLD.Alice_id, 
                   ', Bob_id = ', OLD.Bob_id, 
                   ', Relation_type = ', OLD.Relation_type),
            'Relations', NOW());
END $$


-- 25. 用户表（插入）
-- CREATE TRIGGER After_Users_Insert
-- AFTER INSERT ON Users
-- FOR EACH ROW
-- BEGIN
--     INSERT INTO AuditLog (User_id, Audit_actionType, Audit_actionDescription, Audit_targetTable, Audit_timestamp)
--     VALUES (@current_id, 'Insert', 
--             CONCAT(@current_role, '插入用户记录: User_name = ', NEW.User_name, 
--                    ', User_email = ', NEW.User_email, 
--                    ', User_role = ', NEW.User_role), 
--             'Users', NOW());
-- END $$

-- 26. 用户表（更新）
CREATE TRIGGER After_Users_Update
AFTER UPDATE ON Users
FOR EACH ROW
BEGIN
    INSERT INTO AuditLog (User_id, Audit_actionType, Audit_actionDescription, Audit_targetTable, Audit_timestamp)
    VALUES (@current_id, 'Update', 
            CONCAT(@current_role, '更新用户记录: User_name = ', OLD.User_name, ' -> ', NEW.User_name, 
                   ', User_email = ', OLD.User_email, ' -> ', NEW.User_email, 
                   ', User_role = ', OLD.User_role, ' -> ', NEW.User_role),
            'Users', NOW());
END $$


-- 27. 用户表（删除）
CREATE TRIGGER After_Users_Delete
AFTER DELETE ON Users
FOR EACH ROW
BEGIN
    INSERT INTO AuditLog (User_id, Audit_actionType, Audit_actionDescription, Audit_targetTable, Audit_timestamp)
    VALUES (@current_id, 'Delete', 
            CONCAT(@current_role, '删除用户记录: User_name = ', OLD.User_name, 
                   ', User_email = ', OLD.User_email, 
                   ', User_role = ', OLD.User_role),
            'Users', NOW());
END $$


-- 28. 高亮表（插入）
CREATE TRIGGER After_Highlights_Insert
AFTER INSERT ON Highlights
FOR EACH ROW
BEGIN
    INSERT INTO AuditLog (
        User_id, 
        Audit_actionType, 
        Audit_actionDescription, 
        Audit_targetTable, 
        Audit_timestamp
    )
    VALUES (
        @current_id,  -- 如果能够获取当前操作的用户ID，建议替换NULL为实际的User_id
        'Insert', 
        CONCAT(@current_role, 
            '插入高亮记录: Highlight_id = ', NEW.Highlight_id, 
            ', Doc_id = ', NEW.Doc_id, 
            ', User_id = ', NEW.User_id, 
            ', 起始位置 = ', NEW.Highlight_startPosition, 
            ', 结束位置 = ', NEW.Highlight_endPosition, 
            ', 颜色 = ', NEW.Highlight_color, 
            ', 创建时间 = ', NEW.Highlight_createdAt
        ), 
        'Highlights', 
        NOW()
    );
END $$


-- 29. 高亮表（更新）
CREATE TRIGGER After_Highlights_Update
AFTER UPDATE ON Highlights
FOR EACH ROW
BEGIN
    INSERT INTO AuditLog (
        User_id, 
        Audit_actionType, 
        Audit_actionDescription, 
        Audit_targetTable, 
        Audit_timestamp
    )
    VALUES (
        @current_id,  -- 如果能够获取当前操作的用户ID，建议替换NULL为实际的User_id
        'Update', 
        CONCAT(@current_role, 
            '更新高亮记录: Highlight_id = ', OLD.Highlight_id, ' -> ', NEW.Highlight_id, 
            ', Doc_id = ', OLD.Doc_id, ' -> ', NEW.Doc_id, 
            ', User_id = ', OLD.User_id, ' -> ', NEW.User_id, 
            ', 起始位置 = ', OLD.Highlight_startPosition, ' -> ', NEW.Highlight_startPosition, 
            ', 结束位置 = ', OLD.Highlight_endPosition, ' -> ', NEW.Highlight_endPosition, 
            ', 颜色 = ', OLD.Highlight_color, ' -> ', NEW.Highlight_color, 
            ', 创建时间 = ', OLD.Highlight_createdAt, ' -> ', NEW.Highlight_createdAt
        ), 
        'Highlights', 
        NOW()
    );
END $$


-- 30. 高亮表（删除）
CREATE TRIGGER After_Highlights_Delete
AFTER DELETE ON Highlights
FOR EACH ROW
BEGIN
    INSERT INTO AuditLog (
        User_id, 
        Audit_actionType, 
        Audit_actionDescription, 
        Audit_targetTable, 
        Audit_timestamp
    )
    VALUES (
        @current_id,  -- 如果能够获取当前操作的用户ID，建议替换NULL为实际的User_id
        'Delete', 
        CONCAT(@current_role, 
            '删除高亮记录: Highlight_id = ', OLD.Highlight_id, 
            ', Doc_id = ', OLD.Doc_id, 
            ', User_id = ', OLD.User_id, 
            ', 起始位置 = ', OLD.Highlight_startPosition, 
            ', 结束位置 = ', OLD.Highlight_endPosition, 
            ', 颜色 = ', OLD.Highlight_color, 
            ', 创建时间 = ', OLD.Highlight_createdAt
        ), 
        'Highlights', 
        NOW()
    );
END $$

-- 40. 笔记表（插入）
CREATE TRIGGER After_Notes_Insert
AFTER INSERT ON Notes
FOR EACH ROW
BEGIN
    INSERT INTO AuditLog (
        User_id, 
        Audit_actionType, 
        Audit_actionDescription, 
        Audit_targetTable, 
        Audit_timestamp
    )
    VALUES (
        @current_id,  -- 如果希望记录操作用户的ID
        'Insert', 
        CONCAT(@current_role, 
            '插入批注记录: Note_id = ', NEW.Note_id, 
            ', Doc_id = ', NEW.Doc_id, 
            ', User_id = ', NEW.User_id, 
            ', 批注内容 = "', NEW.Note_annotationText, '"', 
            ', 起始位置 = ', NEW.Note_startPosition, 
            ', 结束位置 = ', NEW.Note_endPosition, 
            ', 创建时间 = ', NEW.Note_createdAt
        ), 
        'Notes', 
        NOW()
    );
END $$

-- 41. 笔记表（更新）
CREATE TRIGGER After_Notes_Update
AFTER UPDATE ON Notes
FOR EACH ROW
BEGIN
    INSERT INTO AuditLog (
        User_id, 
        Audit_actionType, 
        Audit_actionDescription, 
        Audit_targetTable, 
        Audit_timestamp
    )
    VALUES (
        @current_id,  -- 假设更新操作由 NEW.User_id 指定的用户执行
        'Update', 
        CONCAT(@current_role, 
            '更新批注记录: Note_id = ', OLD.Note_id, 
            ', Doc_id = ', OLD.Doc_id, ' -> ', NEW.Doc_id, 
            ', User_id = ', OLD.User_id, ' -> ', NEW.User_id, 
            ', 批注内容 = "', OLD.Note_annotationText, '" -> "', NEW.Note_annotationText, '"',
            ', 起始位置 = ', OLD.Note_startPosition, ' -> ', NEW.Note_startPosition, 
            ', 结束位置 = ', OLD.Note_endPosition, ' -> ', NEW.Note_endPosition, 
            ', 创建时间 = ', OLD.Note_createdAt, ' -> ', NEW.Note_createdAt
        ), 
        'Notes', 
        NOW()
    );
END $$

-- 42. 笔记表（删除）
CREATE TRIGGER After_Notes_Delete
AFTER DELETE ON Notes
FOR EACH ROW
BEGIN
    INSERT INTO AuditLog (
        User_id, 
        Audit_actionType, 
        Audit_actionDescription, 
        Audit_targetTable, 
        Audit_timestamp
    )
    VALUES (
        @current_id,  -- 记录被删除批注的创建用户ID
        'Delete', 
        CONCAT(@current_role, 
            '删除批注记录: Note_id = ', OLD.Note_id, 
            ', Doc_id = ', OLD.Doc_id, 
            ', User_id = ', OLD.User_id, 
            ', 批注内容 = "', OLD.Note_annotationText, '"', 
            ', 起始位置 = ', OLD.Note_startPosition, 
            ', 结束位置 = ', OLD.Note_endPosition, 
            ', 创建时间 = ', OLD.Note_createdAt
        ), 
        'Notes', 
        NOW()
    );
END $$

-- 43. 纠错表（插入）
CREATE TRIGGER After_Corrections_Insert
AFTER INSERT ON Corrections
FOR EACH ROW
BEGIN
    INSERT INTO AuditLog (
        User_id, 
        Audit_actionType, 
        Audit_actionDescription, 
        Audit_targetTable, 
        Audit_timestamp
    )
    VALUES (
        @current_id,  -- 如果希望记录执行操作的用户ID，建议替换为实际的用户ID获取方式
        'Insert', 
        CONCAT(@current_role, 
            '插入纠错记录: Correction_id = ', NEW.Correction_id, 
            ', Doc_id = ', NEW.Doc_id, 
            ', User_id = ', NEW.User_id, 
            ', 纠错内容 = "', NEW.Correction_text, '"', 
            ', 创建时间 = ', NEW.Correction_createdAt
        ), 
        'Corrections', 
        NOW()
    );
END $$

-- 44. 纠错表（更新）
CREATE TRIGGER After_Corrections_Update
AFTER UPDATE ON Corrections
FOR EACH ROW
BEGIN
    INSERT INTO AuditLog (
        User_id, 
        Audit_actionType, 
        Audit_actionDescription, 
        Audit_targetTable, 
        Audit_timestamp
    )
    VALUES (
        @current_id,  -- 如果希望记录执行操作的用户ID，建议替换为实际的用户ID获取方式
        'Update', 
        CONCAT(@current_role, 
            '更新纠错记录: Correction_id = ', OLD.Correction_id, 
            ', Doc_id = ', OLD.Doc_id, ' -> ', NEW.Doc_id, 
            ', User_id = ', OLD.User_id, ' -> ', NEW.User_id, 
            ', 纠错内容 = "', OLD.Correction_text, '" -> "', NEW.Correction_text, '"', 
            ', 创建时间 = ', OLD.Correction_createdAt, ' -> ', NEW.Correction_createdAt
        ), 
        'Corrections', 
        NOW()
    );
END $$

-- 45. 纠错表（删除)
CREATE TRIGGER After_Corrections_Delete
AFTER DELETE ON Corrections
FOR EACH ROW
BEGIN
    INSERT INTO AuditLog (
        User_id, 
        Audit_actionType, 
        Audit_actionDescription, 
        Audit_targetTable, 
        Audit_timestamp
    )
    VALUES (
        @current_id,  -- 或者使用 @current_user_id
        'Delete', 
        CONCAT(@current_role, 
            '删除纠错记录: Correction_id = ', OLD.Correction_id, 
            ', Doc_id = ', OLD.Doc_id, 
            ', User_id = ', OLD.User_id, 
            ', 纠错内容 = "', OLD.Correction_text, '"', 
            ', 创建时间 = ', OLD.Correction_createdAt
        ), 
        'Corrections', 
        NOW()
    );
END $$

-- 46. 评论表（插入）
CREATE TRIGGER After_Comments_Insert
AFTER INSERT ON Comments
FOR EACH ROW
BEGIN
    INSERT INTO AuditLog (
        User_id, 
        Audit_actionType, 
        Audit_actionDescription, 
        Audit_targetTable, 
        Audit_timestamp
    )
    VALUES (
        @current_id,  -- 记录评论的创建者ID
        'Insert', 
        CONCAT(@current_role, 
            '插入评论记录: Comment_id = ', NEW.Comment_id, 
            ', Doc_id = ', NEW.Doc_id, 
            ', User_id = ', NEW.User_id, 
            ', 评论内容 = "', NEW.Comment_text, '"', 
            ', 创建时间 = ', NEW.Comment_createdAt
        ), 
        'Comments', 
        NOW()
    );
END $$

-- 47. 评论表（更新）
CREATE TRIGGER After_Comments_Update
AFTER UPDATE ON Comments
FOR EACH ROW
BEGIN
    INSERT INTO AuditLog (
        User_id, 
        Audit_actionType, 
        Audit_actionDescription, 
        Audit_targetTable, 
        Audit_timestamp
    )
    VALUES (
        @current_id,  -- 记录更新后的评论创建者ID
        'Update', 
        CONCAT(@current_role, 
            '更新评论记录: Comment_id = ', OLD.Comment_id, 
            ', Doc_id = ', OLD.Doc_id, ' -> ', NEW.Doc_id, 
            ', User_id = ', OLD.User_id, ' -> ', NEW.User_id, 
            ', 评论内容 = "', OLD.Comment_text, '" -> "', NEW.Comment_text, '"', 
            ', 创建时间 = ', OLD.Comment_createdAt, ' -> ', NEW.Comment_createdAt
        ), 
        'Comments', 
        NOW()
    );
END $$

-- 48. 评论表（删除）
CREATE TRIGGER After_Comments_Delete
AFTER DELETE ON Comments
FOR EACH ROW
BEGIN
    INSERT INTO AuditLog (
        User_id, 
        Audit_actionType, 
        Audit_actionDescription, 
        Audit_targetTable, 
        Audit_timestamp
    )
    VALUES (
        @current_id,  -- 记录被删除评论的创建者ID
        'Delete', 
        CONCAT(@current_role, 
            '删除评论记录: Comment_id = ', OLD.Comment_id, 
            ', Doc_id = ', OLD.Doc_id, 
            ', User_id = ', OLD.User_id, 
            ', 评论内容 = "', OLD.Comment_text, '"', 
            ', 创建时间 = ', OLD.Comment_createdAt
        ), 
        'Comments', 
        NOW()
    );
END $$


-- 49. 笔记表（插入）
CREATE TRIGGER After_Evernote_Insert
AFTER INSERT ON Evernote
FOR EACH ROW
BEGIN
    INSERT INTO AuditLog (
        User_id, 
        Audit_actionType, 
        Audit_actionDescription, 
        Audit_targetTable, 
        Audit_timestamp
    )
    VALUES (
        @current_id,  -- 记录笔记的创建者ID
        'Insert', 
        CONCAT(@current_role, 
            '插入笔记记录: Evernote_id = ', NEW.Evernote_id, 
            ', Doc_id = ', NEW.Doc_id, 
            ', User_id = ', NEW.User_id, 
            ', 笔记内容 = "', NEW.Evernote_text, '"', 
            ', 创建时间 = ', NEW.Evernote_viewedAt
        ), 
        'Evernote', 
        NOW()
    );
END $$

-- 50. 笔记表（更新）
CREATE TRIGGER After_Evernote_Update
AFTER UPDATE ON Evernote
FOR EACH ROW
BEGIN
    INSERT INTO AuditLog (
        User_id, 
        Audit_actionType, 
        Audit_actionDescription, 
        Audit_targetTable, 
        Audit_timestamp
    )
    VALUES (
        @current_id,  -- 记录更新后的笔记创建者ID
        'Update', 
        CONCAT(@current_role, 
            '更新笔记记录: Evernote_id = ', OLD.Evernote_id, 
            ', Doc_id = ', OLD.Doc_id, ' -> ', NEW.Doc_id, 
            ', User_id = ', OLD.User_id, ' -> ', NEW.User_id, 
            ', 笔记内容 = "', OLD.Evernote_text, '" -> "', NEW.Evernote_text, '"', 
            ', 创建时间 = ', OLD.Evernote_viewedAt, ' -> ', NEW.Evernote_viewedAt
        ), 
        'Evernote', 
        NOW()
    );
END $$

-- 60. 笔记表（删除）
CREATE TRIGGER After_Evernote_Delete
AFTER DELETE ON Evernote
FOR EACH ROW
BEGIN
    INSERT INTO AuditLog (
        User_id, 
        Audit_actionType, 
        Audit_actionDescription, 
        Audit_targetTable, 
        Audit_timestamp
    )
    VALUES (
        @current_id,  -- 记录被删除笔记的创建者ID
        'Delete', 
        CONCAT(@current_role, 
            '删除笔记记录: Evernote_id = ', OLD.Evernote_id, 
            ', Doc_id = ', OLD.Doc_id, 
            ', User_id = ', OLD.User_id, 
            ', 笔记内容 = "', OLD.Evernote_text, '"', 
            ', 创建时间 = ', OLD.Evernote_viewedAt
        ), 
        'Evernote', 
        NOW()
    );
END $$

-- 61. 用户浏览记录（插入）
CREATE TRIGGER After_UserBrowsingHistory_Insert
AFTER INSERT ON UserBrowsingHistory
FOR EACH ROW
BEGIN
    INSERT INTO AuditLog (
        User_id, 
        Audit_actionType, 
        Audit_actionDescription, 
        Audit_targetTable, 
        Audit_timestamp
    )
    VALUES (
        @current_id, 
        'Insert', 
        CONCAT(@current_role, 
            '插入用户浏览记录: Browse_id = ', NEW.Browse_id, 
            ', User_id = ', NEW.User_id, 
            ', Doc_id = ', NEW.Doc_id, 
            ', 浏览时间 = ', NEW.Browse_time
        ), 
        'UserBrowsingHistory', 
        NOW()
    );
END $$

-- 62. 用户浏览记录（更新）
CREATE TRIGGER After_UserBrowsingHistory_Update
AFTER UPDATE ON UserBrowsingHistory
FOR EACH ROW
BEGIN
    INSERT INTO AuditLog (
        User_id, 
        Audit_actionType, 
        Audit_actionDescription, 
        Audit_targetTable, 
        Audit_timestamp
    )
    VALUES (
        @current_id, 
        'Update', 
        CONCAT(@current_role, 
            '更新用户浏览记录: Browse_id = ', OLD.Browse_id, 
            ', User_id = ', OLD.User_id, ' -> ', NEW.User_id, 
            ', Doc_id = ', OLD.Doc_id, ' -> ', NEW.Doc_id, 
            ', 浏览时间 = ', OLD.Browse_time, ' -> ', NEW.Browse_time
        ), 
        'UserBrowsingHistory', 
        NOW()
    );
END $$

-- 63. 用户浏览记录（删除）
CREATE TRIGGER After_UserBrowsingHistory_Delete
AFTER DELETE ON UserBrowsingHistory
FOR EACH ROW
BEGIN
    INSERT INTO AuditLog (
        User_id, 
        Audit_actionType, 
        Audit_actionDescription, 
        Audit_targetTable, 
        Audit_timestamp
    )
    VALUES (
        @current_id, 
        'Delete', 
        CONCAT(@current_role, 
            '删除用户浏览记录: Browse_id = ', OLD.Browse_id, 
            ', User_id = ', OLD.User_id, 
            ', Doc_id = ', OLD.Doc_id, 
            ', 浏览时间 = ', OLD.Browse_time
        ), 
        'UserBrowsingHistory', 
        NOW()
    );
END $$


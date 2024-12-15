show  full processlist;

use 永泰文书;
DROP PROCEDURE IF EXISTS InsertDocument;

DELIMITER //

CREATE PROCEDURE InsertDocument(IN data JSON)
BEGIN
    DECLARE doc_id VARCHAR(20);
    DECLARE created_time_id INT;
    DECLARE updated_time_id INT;
    DECLARE error_message VARCHAR(255);
    DECLARE alice_person_id INT;
    DECLARE bob_person_id INT;
    DECLARE participant_person_id INT;
    DECLARE participant_name VARCHAR(100);
    DECLARE participant_role VARCHAR(50);
    DECLARE done BOOLEAN DEFAULT FALSE;
    
    SET doc_id = JSON_UNQUOTE(JSON_EXTRACT(data, '$.doc_id'));
    -- 设置会话变量
    SET @current_id = IFNULL(@current_id, 1);  -- 默认用户ID为1
    SET @current_role = IFNULL(@current_role, 'System');  -- 默认角色为System
    SET @current_doc_id = NULL;  -- 初始化文档ID
    
    
    START TRANSACTION;
    
    -- 1. 处理创建时间
    BEGIN
        -- 获取创建时间
        SET @created_time = JSON_UNQUOTE(JSON_EXTRACT(data, '$.created_time'));
        
        -- 如果创建时间为空，则跳过
        IF @created_time IS NOT NULL AND @created_time != '' THEN
            -- 查找时间是���存在
            SELECT Time_id INTO created_time_id
            FROM TimeRecord 
            WHERE createdData = @created_time;
            
            -- 如果不存在则插入
            IF created_time_id IS NULL THEN
                INSERT INTO TimeRecord (createdData, Standard_createdData)
                VALUES (
                    @created_time,
                    CASE 
                        WHEN JSON_UNQUOTE(JSON_EXTRACT(data, '$.standard_time')) IS NOT NULL AND JSON_UNQUOTE(JSON_EXTRACT(data, '$.standard_time')) != '' 
                        THEN CAST(JSON_UNQUOTE(JSON_EXTRACT(data, '$.standard_time')) AS DATE)
                        ELSE NULL
                    END
                );
                SET created_time_id = LAST_INSERT_ID();
                
                -- 添加时间记录的审计日志
                INSERT INTO AuditLog (
                    User_id,
                    Audit_actionType,
                    Audit_actionDescription,
                    Audit_targetTable,
                    Audit_timestamp
                ) VALUES (
                    @current_id,
                    'INSERT',
                    '添加时间记录: ',
                    'TimeRecord',
                    NOW()
                );
            END IF;
        END IF;
    END;
    
    -- 2. 处理更新时间（如果有）
    SET @updated_time = JSON_UNQUOTE(JSON_EXTRACT(data, '$.updated_time'));
    IF @updated_time IS NOT NULL AND @updated_time != 'null' THEN
        BEGIN
            -- 查找更新时间是否存在
            SELECT Time_id INTO updated_time_id
            FROM TimeRecord 
            WHERE createdData = @updated_time;
            
            -- 如果不存在则插入
            IF updated_time_id IS NULL THEN
                INSERT INTO TimeRecord (createdData, Standard_createdData)
                VALUES (
                    @updated_time,
                    CASE 
                        WHEN JSON_UNQUOTE(JSON_EXTRACT(data, '$.standard_updated_time')) IS NOT NULL AND JSON_UNQUOTE(JSON_EXTRACT(data, '$.standard_updated_time')) != '' 
                        THEN CAST(JSON_UNQUOTE(JSON_EXTRACT(data, '$.standard_updated_time')) AS DATE)
                        ELSE NULL
                    END
                );
                SET updated_time_id = LAST_INSERT_ID();
            END IF;
        END;
    END IF;

    -- 如果没有提供更新时间，则将其设置为创建时间
    IF @updated_time IS NULL OR @updated_time = '' THEN
        SET updated_time_id = created_time_id;
    END IF;
    -- 3. 插入文书基本信息
    INSERT INTO Documents (
        Doc_id,
        Doc_title,
        Doc_originalText,
        Doc_simplifiedText,
        Doc_type,
        Doc_summary,
        Doc_image_path,
        Doc_createdTime_id,
        Doc_updatedTime_id
    ) VALUES (
        JSON_UNQUOTE(JSON_EXTRACT(data, '$.doc_id')),
        JSON_UNQUOTE(JSON_EXTRACT(data, '$.title')),
        JSON_UNQUOTE(JSON_EXTRACT(data, '$.original_text')),
        JSON_UNQUOTE(JSON_EXTRACT(data, '$.simplified_text')),
        JSON_UNQUOTE(JSON_EXTRACT(data, '$.type')),
        JSON_UNQUOTE(JSON_EXTRACT(data, '$.summary')),
        JSON_UNQUOTE(JSON_EXTRACT(data, '$.image_path')),
        created_time_id,
        updated_time_id
    );
    
    -- 添加文书的审计日志
    INSERT INTO AuditLog (
        User_id,
        Audit_actionType,
        Audit_actionDescription,
        Audit_targetTable,
        Audit_timestamp
    ) VALUES (
        @current_id,
        'INSERT',
        CONCAT('添加文书: ', IFNULL(JSON_UNQUOTE(JSON_EXTRACT(data, '$.title')), '未知文书')),
        'Documents',
        NOW()
    );

    -- 4. 插入关键词
    INSERT INTO DocKeywords (Doc_id, KeyWord)
    SELECT doc_id, keyword
    FROM JSON_TABLE(
        JSON_EXTRACT(data, '$.keywords'),
        '$[*]' COLUMNS (keyword VARCHAR(50) PATH '$')
    ) AS keywords;
    
    -- 5. 处理契约人
    BEGIN
        -- 获取第一个契约人
        SET alice_person_id = (
            SELECT Person_id 
            FROM People 
            WHERE Person_name = JSON_UNQUOTE(JSON_EXTRACT(data, '$.contractors[0].name'))
        );
        
        -- 如果第一个契约人不存在，则插入
        IF alice_person_id IS NULL THEN
            INSERT INTO People (Person_name) 
            VALUES (JSON_UNQUOTE(JSON_EXTRACT(data, '$.contractors[0].name')));
            SET alice_person_id = LAST_INSERT_ID();
        END IF;
        
        -- 获取第二个契约人
        SET bob_person_id = (
            SELECT Person_id 
            FROM People 
            WHERE Person_name = JSON_UNQUOTE(JSON_EXTRACT(data, '$.contractors[1].name'))
        );
        
        -- 如果第二个契约人不存在，则插入
        IF bob_person_id IS NULL THEN
            INSERT INTO People (Person_name) 
            VALUES (JSON_UNQUOTE(JSON_EXTRACT(data, '$.contractors[1].name')));
            SET bob_person_id = LAST_INSERT_ID();
        END IF;
        
        -- 插入契约人关系到 Contractors 表
        INSERT INTO Contractors (Doc_id, Alice_id, Bob_id)
        VALUES (doc_id, alice_person_id, bob_person_id);
        
        -- 获取关系类型
        SET @relation_type = JSON_UNQUOTE(JSON_EXTRACT(data, '$.relation'));
        
        -- ��果有关系类型，则插入到 Relations 表
        IF @relation_type IS NOT NULL AND @relation_type != '' THEN
            -- 直接插入关系
            INSERT INTO Relations (Alice_id, Bob_id, Relation_type)
            VALUES (alice_person_id, bob_person_id, @relation_type);
        END IF;
    END;
    
    -- 6. 处理参与者
    BEGIN
        DECLARE participant_cursor CURSOR FOR
        SELECT 
            JSON_UNQUOTE(JSON_EXTRACT(participant, '$.name')) as name,
            JSON_UNQUOTE(JSON_EXTRACT(participant, '$.role')) as role
        FROM JSON_TABLE(
            JSON_EXTRACT(data, '$.participants'),
            '$[*]' COLUMNS (participant JSON PATH '$')
        ) as participants;
        
        DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;
        
        OPEN participant_cursor;
        
        participant_loop: LOOP
            FETCH participant_cursor INTO participant_name, participant_role;
            IF done THEN
                LEAVE participant_loop;
            END IF;
            
            -- 检查参与者是否存在
            SET participant_person_id = (
                SELECT Person_id 
                FROM People 
                WHERE Person_name = participant_name
            );
            
            -- 如果参与者不存在，则插入
            IF participant_person_id IS NULL THEN
                INSERT INTO People (Person_name) VALUES (participant_name);
                SET participant_person_id = LAST_INSERT_ID();
            END IF;
            
            -- 插入参与者关系
            INSERT INTO Participants (Doc_id, Person_id, Part_role)
            VALUES (doc_id, participant_person_id, participant_role);
        END LOOP;
        
        CLOSE participant_cursor;
    END;
    
    COMMIT;
    
    -- 返回成功信息和文书ID
    SELECT 'success' as result, doc_id as document_id;
END //

DELIMITER ; 

CALL InsertDocument('{
    "doc_id":"1-1-1-1",
    "title": "测试文书",
    "type": "借钱契",
    "summary": "这是一份测试用的文书",
    "original_text": "清嘉慶十一年十一月黃盛漢立撮字（廢契）",
    "simplified_text": "清嘉庆十一年十一月黄盛汉立撮字（废契）",
    "image_path": "images/documents/test.jpg",
    "created_time": "嘉庆十一年十一月",
    "standard_time": "1806-11-01",
    "updated_time": null,
    "standard_updated_time": null,
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
}');

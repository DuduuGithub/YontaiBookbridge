-- 创建文书展示视图
CREATE OR REPLACE VIEW DocumentDisplayView AS
SELECT 
    d.Doc_id,
    d.Doc_title,                           -- 文书标题
    d.Doc_type,                            -- 文书类型
    d.Doc_summary,                         -- 文书大意
    d.Doc_image,                           -- 文书图片路径
    t.createdData as Doc_time,             -- 签约时间（原始格式）
    t.Standard_createdData as Doc_standardTime,  -- 签约时间（公历格式）
    -- 契约人（格式：《张三》《李四》（叔侄））
    CONCAT(
        '《', 
        (SELECT p1.Person_name FROM People p1 WHERE p1.Person_id = c.Alice_id),
        '》《',
        (SELECT p2.Person_name FROM People p2 WHERE p2.Person_id = c.Bob_id),
        '》（',
        -- 获取关系类型
        (SELECT r.Relation_type
         FROM Relations r 
         WHERE (r.Alice_id = c.Alice_id AND r.Bob_id = c.Bob_id) 
            OR (r.Alice_id = c.Bob_id AND r.Bob_id = c.Alice_id)
         LIMIT 1),
        '）'
    ) as ContractorInfo,
    -- 参与人（格式：《王五》（见证人）《赵六》（代书））
    GROUP_CONCAT(
        CONCAT('《', p.Person_name, '》（', pa.Part_role, '）')
        ORDER BY pa.Part_role
        SEPARATOR ''
    ) as ParticipantInfo
FROM Documents d
LEFT JOIN TimeRecord t ON d.Doc_createdTime_id = t.Time_id
LEFT JOIN Contractors c ON d.Doc_id = c.Doc_id
LEFT JOIN Participants pa ON d.Doc_id = pa.Doc_id
LEFT JOIN People p ON pa.Person_id = p.Person_id
GROUP BY 
    d.Doc_id, 
    d.Doc_title, 
    d.Doc_type, 
    d.Doc_summary,
    d.Doc_image, 
    t.createdData,
    t.Standard_createdData,
    c.Alice_id,
    c.Bob_id; 
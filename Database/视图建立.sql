use 永泰文书;
-- 创建文书展示视图
CREATE OR REPLACE VIEW DocumentDisplayView AS
SELECT 
    d.Doc_id,
    d.Doc_title,                           -- 文书标题
    d.Doc_type,                            -- 文书类型
    d.Doc_summary,                         -- 文书大意
    d.Doc_image_path,                      -- 文书图片路径
    t.createdData as Doc_time,             -- 签约时间（原始格式）
    t.Standard_createdData as Doc_standardTime,  -- 签约时间（公历格式）
    -- 契约人（格式：《张三》《李四》（叔侄））
    CONCAT(
        '《', 
        (SELECT p1.Person_name FROM People p1 WHERE p1.Person_id = c.Alice_id),
        '》《',
        (SELECT p2.Person_name FROM People p2 WHERE p2.Person_id = c.Bob_id),
        '》',
        CASE 
            WHEN r.Relation_type IS NOT NULL AND r.Relation_type != 'null' 
            THEN CONCAT('（', r.Relation_type, '）')
            ELSE ''
        END
    ) as ContractorInfo,
    -- 参与人（格式：《王五》（见证人）《赵六》（代书））
    GROUP_CONCAT(
        CONCAT('《', p.Person_name, '》（', pa.Part_role, '）')
        ORDER BY pa.Part_role
        SEPARATOR ''
    ) as ParticipantInfo,
    -- 添加文书类型字段，用于筛选
    CASE d.Doc_type
        WHEN '借钱契' THEN '借钱契'
        WHEN '租赁契' THEN '租赁契'
        WHEN '抵押契' THEN '抵押契'
        WHEN '赋税契' THEN '赋税契'
        WHEN '诉状' THEN '诉状'
        WHEN '判决书' THEN '判决书'
        WHEN '祭祀契约' THEN '祭祀契约'
        WHEN '祠堂契' THEN '祠堂契'
        WHEN '劳役契' THEN '劳役契'
        ELSE '其他'
    END as Doc_category
FROM Documents d
LEFT JOIN TimeRecord t ON d.Doc_createdTime_id = t.Time_id
LEFT JOIN Contractors c ON d.Doc_id = c.Doc_id
LEFT JOIN Relations r ON (r.Alice_id = c.Alice_id AND r.Bob_id = c.Bob_id) 
                     OR (r.Alice_id = c.Bob_id AND r.Bob_id = c.Alice_id)
LEFT JOIN Participants pa ON d.Doc_id = pa.Doc_id
LEFT JOIN People p ON pa.Person_id = p.Person_id
GROUP BY 
    d.Doc_id, 
    d.Doc_title, 
    d.Doc_type, 
    d.Doc_summary,
    d.Doc_image_path,
    t.createdData,
    t.Standard_createdData,
    c.Alice_id,
    c.Bob_id,
    r.Relation_type;
    
-- 创建收藏夹视图
CREATE VIEW FolderDocumentStats AS
SELECT 
    f.Folder_id,                        -- 收藏夹ID
    f.Folder_name,                      -- 收藏夹名称
    COUNT(CASE WHEN d.Doc_type = '借钱契' THEN 1 END) AS Borrow_Contract,  -- 借钱契数量
    COUNT(CASE WHEN d.Doc_type = '租赁契' THEN 1 END) AS Lease_Contract,  -- 租赁契数量
    COUNT(CASE WHEN d.Doc_type = '抵押契' THEN 1 END) AS Mortgage_Contract,  -- 抵押契数量
    COUNT(CASE WHEN d.Doc_type = '赋税契' THEN 1 END) AS Tax_Contract,  -- 赋税契数量
    COUNT(CASE WHEN d.Doc_type = '诉状' THEN 1 END) AS Lawsuit,  -- 诉状数量
    COUNT(CASE WHEN d.Doc_type = '判决书' THEN 1 END) AS Judgement,  -- 判决书数量
    COUNT(CASE WHEN d.Doc_type = '祭祀契约' THEN 1 END) AS Sacrificial_Contract,  -- 祭祀契约数量
    COUNT(CASE WHEN d.Doc_type = '祠堂契' THEN 1 END) AS Ancestral_Hall_Contract,  -- 祠堂契数量
    COUNT(CASE WHEN d.Doc_type = '劳役契' THEN 1 END) AS Labor_Contract,  -- 劳役契数量
    COUNT(CASE WHEN d.Doc_type = '其他' THEN 1 END) AS Other_Contract   -- 其他类型数量
FROM 
    Folders f
JOIN 
    FolderContents fc ON f.Folder_id = fc.Folder_id   -- 连接文件夹内容
JOIN 
    Documents d ON fc.Doc_id = d.Doc_id                -- 连接文书表
GROUP BY 
    f.Folder_id, f.Folder_name;                        -- 按文件夹分组

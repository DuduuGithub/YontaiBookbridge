use `永泰文书`;

-- 查询特定类型的文书列表（例如，所有土地契约）
SELECT * FROM documents
WHERE Doc_type ='借钱契';
  
-- 查询涉及某一人物的所有文书。
SELECT d.Doc_id, d.Doc_title, d.Doc_summary, d.Doc_simplifiedText
FROM documents d 
JOIN participants p ON d.Doc_id = p.Doc_id
JOIN people pe ON p.Person_id = pe.Person_id
WHERE pe.Person_name = '黄盛汉'
UNION
SELECT d.Doc_id, d.Doc_title, d.Doc_summary, d.Doc_simplifiedText
FROM documents d 
JOIN contractors c ON d.Doc_id = c.Doc_id
JOIN people pe ON (c.Alice_id = pe.Person_id OR c.Bob_id = pe.Person_id)
WHERE pe.Person_name = '黄盛汉';

-- 查询包含特定关键词的转录文本。
SELECT d.Doc_id,d.Doc_title,d.Doc_summary,d.Doc_simplifiedText
FROM documents d
JOIN dockeywords dw ON d.Doc_id=dw.Doc_id
WHERE dw.KeyWord='借钱';

-- 查询某个收藏中的所有文书。
SELECT DISTINCT d.Doc_id, d.Doc_title, d.Doc_summary, d.Doc_simplifiedText
FROM documents d
WHERE d.Doc_id IN 
  (SELECT DISTINCT fc.Doc_id
   FROM foldercontents fc
   JOIN folders f ON fc.Folder_id = f.Folder_id
   WHERE f.Folder_name = 'tttt');

-- 统计每种类型文书的数量。
SELECT Doc_type,COUNT(*) 
FROM documents
GROUP BY Doc_type;

-- 列出最近添加的注释。
SELECT *
FROM comments c
JOIN users u ON c.User_id=u.User_id
WHERE u.User_id= 2
ORDER BY c.Comment_createdAt DESC
LIMIT 5;

-- 全文索引查询示例
SELECT Doc_id,Doc_title, Doc_simplifiedText, Doc_originalText 
FROM documents
WHERE MATCH(Doc_title, Doc_simplifiedText, Doc_originalText) 
AGAINST('凭票支出钱贰仟四百文正期约本年十' IN BOOLEAN MODE)
ORDER BY MATCH(Doc_title, Doc_simplifiedText, Doc_originalText) 
AGAINST('凭票支出钱贰仟四百文正期约本年十' IN BOOLEAN MODE) DESC;

-- DROP TRIGGER IF EXISTS After_Relations_Update;


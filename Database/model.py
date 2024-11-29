# 表设计，以3NF及以上为设计目标

# 用户主题：

# 用户信息表：uid,账号，密码，身份等
# 用户浏览记录表 只需要记忆 浏览过的文书的记录


# 文书主题:

# 文书数据表：编号，文本内容，契约人，大意……评论区
# 文书纠错表：用于管理员查看用户提交的文书的纠错内容


# 用户文书表：uid,编号,标记、笔记等

# 日志表 记录对文书数据表的更改日志
from Database.config import db

class Documents:
    pass

class Participants:
    pass


class Users:
    pass

class Highlights:
    pass

class Notes:
    pass

class Folders:
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    pass

class AuditLog:
    pass

class Corrections:
    pass

class Comments:
    pass

class History:
    pass

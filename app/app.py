# 主路由
from flask import Flask
from app_blueprint import analysis,reader,user

app=Flask(__name__)

# 将对应模块下的蓝图对象注册到app中
app.register_blueprint(analysis.analysis_bp)
app.register_blueprint(reader.reader_bp)
app.register_blueprint(user.user_bp)



#登录以及主页面
@app.route('/')
def home():
    pass
    
@app.route('login')
def login():
    pass



# 若使用Flask服务器，则不等于main
if __name__=="main":
    app.run()
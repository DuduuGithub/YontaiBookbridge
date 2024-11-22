# 主路由
from flask import Flask
from app_blueprint import register_blueprints

app=Flask(__name__)

register_blueprints(app=app)

app.run()
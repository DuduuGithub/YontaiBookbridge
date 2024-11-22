import os
import importlib
from flask import Blueprint

def register_blueprints(app):
    # 获取当前文件夹下的所有 Python 文件
    current_dir = os.path.dirname(os.path.abspath(__file__))
    for filename in os.listdir(current_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            # 动态导入模块
            module_name = f"app_blueprint.{filename[:-3]}"
            module = importlib.import_module(module_name)

            # 检查是否定义了蓝图对象
            for attr in dir(module):
                blueprint = getattr(module, attr)
                if isinstance(blueprint, Blueprint):
                    app.register_blueprint(blueprint)


print(1)
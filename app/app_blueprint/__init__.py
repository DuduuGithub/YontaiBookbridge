import os
import importlib
from flask import Blueprint
from .home import home_bp
from .user import user_bp
from .reader import reader_bp
from .analysis import analysis_bp
from .searcher import searcher_bp

def register_blueprints(app):
    app.register_blueprint(home_bp, url_prefix='/home')
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(reader_bp, url_prefix='/reader')
    app.register_blueprint(analysis_bp, url_prefix='/analysis')
    app.register_blueprint(searcher_bp, url_prefix='/searcher')

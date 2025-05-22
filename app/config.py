from dotenv import load_dotenv
from os import getenv
from pathlib import Path
from os.path import dirname, join
from datetime import timedelta


load_dotenv()

class Config:
    # jwt
    JWT_SECRET_KEY = 'blogs.app'
    JWT_ACCESS_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_EXPIRES = timedelta(days=1)
    # app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=10)
    JWT_TOKEN_LOCATION = ['headers']
    PROPAGATE_EXCEPTIONS = True # 开启调试模式查看JWT错误
    JWT_BLACKLIST_TOKEN_CHECKS = ['access']
    JWT_BLACKLIST_ENABLED = True
    # app.config['JWT_COOKIE_SECURE'] = True # 启用CSRF保护
    # app.config['JWT_CSRF_CHECK_FORM'] = True# 检查表单中的csrf-token

    SQLALCHEMY_DATABASE_URI = getenv('DATABASE_SQLALCHEMY_DATABASE_URI')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = False
    UPLOAD_FOLDER = join(dirname(__file__), 'static/images')

    # 邮箱信息
    MAIL_SERVER = getenv('MAIL_SERVER')
    MAIL_PORT = getenv('MAIL_PORT')
    MAIL_USE_TLS = True
    MAIL_USERNAME = getenv('MAIL_USERNAME')
    MAIL_PASSWORD = getenv('MAIL_PASSWORD')

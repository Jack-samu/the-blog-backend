from dotenv import load_dotenv
from os import getenv
from os.path import dirname, join
from datetime import timedelta


load_dotenv()

class Config:
    # jwt
    JWT_SECRET_KEY = 'blogs.app'
    JWT_ACCESS_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_EXPIRES = timedelta(days=1)
    JWT_TOKEN_LOCATION = ['headers']
    PROPAGATE_EXCEPTIONS = True # 开启调试模式查看JWT错误
    JWT_BLACKLIST_TOKEN_CHECKS = ['access']
    JWT_BLACKLIST_ENABLED = True

    # 数据库
    SQLALCHEMY_DATABASE_URI = getenv('DATABASE_URI')
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True
    }
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = join(dirname(__file__), 'static/images')

    # 邮箱信息
    MAIL_SERVER = getenv('MAIL_SERVER')
    MAIL_PORT = int(getenv('MAIL_PORT'))
    MAIL_USE_TLS = True
    MAIL_USERNAME = getenv('MAIL_USERNAME')
    MAIL_PASSWORD = getenv('MAIL_PASSWORD')
from flask import Flask
from os.path import abspath, dirname, join
from loguru import logger


from .config import Config
from .extensions import db, migrate, cors
from .hooks import register_hooks, register_commands
from .events import register_events


def create_app(name='blog-app', config = Config):

    baseDir = abspath(dirname(__file__))
    projectDir = dirname(baseDir)
    staticP = join(projectDir, 'static')

    logger.add(
        'logs/app.log',
        rotation="1 week",
        retention='4 weeks',
        level="DEBUG",
        format="{time: YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}"
    )

    app = Flask(
        name, 
        static_folder=staticP
    )
    
    app.config.from_object(config)
    app.config['UPLOAD_FOLDER'] = join(staticP, 'images')
    app.config['JSON_AS_ASCII'] = False

    if name == 'testing':
        app.config['TESTING'] = True

    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app, supports_credentials=True)

    register_hooks(app)
    register_events(app)
    register_commands(app)

    # 蓝图注册
    from app.routes import article_bp, auth_bp, comment_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(article_bp)
    app.register_blueprint(comment_bp)

    return app
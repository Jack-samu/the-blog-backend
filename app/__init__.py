from flask import Flask
from flask_cors import CORS
from os.path import abspath, dirname, join


from .config import Config
from .extensions import db, migrate
from .hooks import register_hooks, register_commands
from .events import register_events



def create_app(name='blog-app', config = Config):

    baseDir = abspath(dirname(__file__))
    projectDir = dirname(baseDir)
    staticP = join(projectDir, 'static')

    app = Flask(
        name, 
        static_folder=staticP
    )
    CORS(
        app, 
        supports_credentials=True
    )
    app.config.from_object(config)
    app.config['UPLOAD_FOLDER'] = join(staticP, 'images')
    app.config['JSON_AS_ASCII'] = False
    if name == 'testing':
        app.config['TESTING'] = True

    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    register_hooks(app)
    register_events(app)
    register_commands(app)

    # 蓝图注册
    from .routes import article_bp, auth_bp, comment_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(article_bp)
    app.register_blueprint(comment_bp)

    return app
from flask import Flask
from flask_cors import CORS
from os.path import abspath, dirname, join


from .config import Config
from .extensions import db, migrate
from .hooks import register_hooks



def create_app(config = Config):

    baseDir = abspath(dirname(__file__))
    projectDir = dirname(baseDir)
    staticP = join(projectDir, 'static')

    app = Flask(
        __name__, 
        static_folder=staticP
    )
    CORS(
        app, 
        resources={r'/*': {"origins":"http://localhost:5173"}}, supports_credentials=True
    )
    app.config.from_object(config)
    app.config['UPLOAD_FOLDER'] = join(staticP, 'images')

    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    register_hooks(app)

    # 蓝图注册
    from .article.routes import article_bp
    from .auth.routes import auth_bp
    from .comment.routes import comment_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(article_bp)
    app.register_blueprint(comment_bp)

    return app
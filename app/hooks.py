from flask import current_app
from .extensions import db


def register_hooks(app):
    
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        current_app.logger.info('session teardown')
        db.session.remove()
        if exception and current_app.config['DEBUG']:
            current_app.logger.error(f"session teardow error: {exception}")

    @app.after_request
    def after_request(resp):
        # 缓存预检结果1小时
        resp.headers['Access-Control-Max-Age'] = 3600  
        resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, DELETE, OPTIONS'
        return resp
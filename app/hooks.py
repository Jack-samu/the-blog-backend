from flask import current_app, Flask, request
import click
from functools import wraps

from app.extensions import db
from app.models import User
from app.utils import get_current_user


# flask日志默认level为warn，所以只能用warn进行输出
def register_hooks(app):
    
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        current_app.logger.warning('session teardown')
        db.session.close()
        if exception and current_app.config['DEBUG']:
            current_app.logger.error(f"session teardow error: {exception}")

    @app.after_request
    def after_request(resp):
        # 缓存预检结果1小时
        current_app.logger.warning(f"响应：{resp.status}")
        resp.headers['Access-Control-Max-Age'] = 3600  
        resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, DELETE, OPTIONS'
        if 'application/json' in resp.headers['Content-Type']:
            resp.headers['Content-Type'] = 'application/json; charset=utf-8'
        return resp
    
    @app.before_request
    def before_request():
        current_app.logger.warning(f"请求：{request.method} {request.path}")

    # 后续添上错误统一处理
    

def register_commands(app: Flask):
    @app.cli.command('init-db')
    @click.option('--admin-email', default='admin@secure.com', help='管理员邮箱')
    @click.option('--admin-password', prompt=True, hide_input=True, confirmation_prompt=True)
    def init_system(admin_email, admin_password):
        try:
            db.session.begin()
            admin = User.create_admin(email=admin_email, pwd=admin_password)
            User.get_deleted_user()
            click.echo(f'初始化动作完成，管理员ID：{admin.id}')
        except Exception as e:
            current_app.logger.error(f'初始化出错，{str(e)}')
            db.session.rollback()
    
def token_optional(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        current_user = get_current_user()
        return f(current_user, *args, **kwargs)
    return decorated

# token校验装饰器
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        current_user = get_current_user()
        if not current_user:
            return {'err': '认证信息缺失或无效'}, 401
        
        return f(current_user, *args, **kwargs)
    return decorated
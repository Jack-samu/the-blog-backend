from flask import current_app, Flask
from app.extensions import db
from app.models import User
import click


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
        if 'application/json' in resp.headers['Content-Type']:
            resp.headers['Content-Type'] = 'application/json; charset=utf-8'
        return resp
    

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
            app.logger.error(f'初始化出错，{str(e)}')
            db.session.rollback()
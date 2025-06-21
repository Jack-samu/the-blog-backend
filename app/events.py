from sqlalchemy import event
from flask import Flask

from app.extensions import db
from app.models import Image


def register_events(app: Flask):
                
    with app.app_context():
        if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
            @event.listens_for(db.engine, 'connect')
            def set_sqlite_pragma(db_connection, connection_record):
                from sqlite3 import Connection
                if isinstance(db_connection, Connection):
                    cursor = db_connection.cursor()
                    # 设置外键支持
                    cursor.execute('PRAGMA foreign_keys=ON')
                    # 启用WAL模式
                    cursor.execute('PRAGMA journal_mode=WAL')
                    cursor.close()
                    app.logger.info('执行了')
        
        @event.listens_for(Image, 'after_delete')
        def delete_img_file(mapper, connection, target):
            from os import path, remove
            try:
                p = f"static/images/{target.name}"
                if path.exists(p):
                    remove(p)
                    app.logger.info(f"图片文件已删除，{p}")
                else:
                    app.logger.info(f"图片路径不存在，检查{p}路径")
            except Exception as e:
                app.logger.error(f"图片删除出错，{str(e)}")
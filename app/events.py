from sqlalchemy import event
from sqlalchemy.orm import object_session
from flask import Flask

from app.extensions import db
from app.models import Image, Post, Draft


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
        
        @event.listens_for(Image, 'after_delete')
        def delete_img_file(mapper, connection, target):
            from os import path, remove
            try:
                p = f"static/images/{target.name}"
                if path.exists(p):
                    remove(p)
                else:
                    app.logger.info(f"图片路径不存在，检查{p}路径")
            except Exception as e:
                app.logger.error(f"图片删除出错，{str(e)}")

        @event.listens_for(Draft, 'after_delete')
        def draft_delete(mapper, connection, target):
            if target.category:
                post_cnt = Post.query.filter_by(category_id = target.category.id).count()
                draft_cnt = Draft.query.filter_by(category_id = target.category.id).count()
                if draft_cnt == 0 and post_cnt == 0:
                    db.session.delete(target.category)
            
            for tag in target.tags:
                if not tag.is_referenced():
                    db.session.delete(tag)

        @event.listens_for(Post, 'after_delete')
        def post_delete(mapper, connection, target):
            if target.category:
                post_cnt = Post.query.filter_by(category_id = target.category.id).count()
                draft_cnt = Draft.query.filter_by(category_id = target.category.id).count()
                if draft_cnt == 0 and post_cnt == 0:
                    db.session.delete(target.category)
            
            for tag in target.tags:
                if not tag.is_referenced():
                    db.session.delete(tag)

        @event.listens_for(Draft.tags, 'remove')
        @event.listens_for(Post.tags, 'remove')
        def remove_tag(target, value, initiator):
            session = object_session(target)
            if session and not value.is_referenced():
                session.delete(value)
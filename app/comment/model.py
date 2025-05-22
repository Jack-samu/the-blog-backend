from ..extensions import db

from sqlalchemy import event
from sqlalchemy.orm import validates
from markupsafe import escape

    
class Comment(db.Model):
    __tablename__ = 'comment'
    # 基础信息
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    content = db.Column(db.Text, nullable=False)
    like_cnt = db.Column(db.Integer, default=0)
    reply_cnt = db.Column(db.Integer, default=0)
    is_top = db.Column(db.Boolean, default=False)
    # 时间戳
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    updated_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), onupdate=db.func.now())
    # 外键
    article_id = db.Column(db.Integer, db.ForeignKey('article.id'), index=True)
    user_id = db.Column(db.String(36), db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    # 自关联
    # user = db.relationship('User', backref='comments')
    replies = db.relationship('Reply', backref='parent_comment', cascade='all, delete-orphan')
    likers = db.relationship('User', secondary='comment_likes')
    
    @validates('content')
    def validate_content(self, key, value):
        # 添加内容过滤，因为主要是markdown内容，大部分不会有html标签，所以做暂时处理
        return escape(value.strip())

class Reply(db.Model):
    __tablename__ = 'replies'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    like_cnt = db.Column(db.Integer, default=0)
    # 时间戳
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    updated_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), onupdate=db.func.now())
    comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'), index=True)
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'))

    user = db.relationship('User', backref='replies')


# reply添加就自动刷新comment中reply数
@event.listens_for(Reply, 'before_insert')
def increase_cnt(mapper, connection, target):
    connection.execute(
        db.update(Comment)
            .where(Comment.id == target.comment_id)
            .values(reply_cnt = Comment.reply_cnt + 1)
    )

    
comment_likes = db.Table('comment_likes',
            db.Column('user_id', db.String(36), db.ForeignKey('user.id'), primary_key=True),
            db.Column('comment_id', db.Integer, db.ForeignKey('comment.id'), primary_key=True),
            db.Column('created_at', db.DateTime, default=db.func.now())
        )
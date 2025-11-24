from app.extensions import db

from sqlalchemy import exists, update
from sqlalchemy.orm import validates

    
class Comment(db.Model):
    __tablename__ = 'comment'
    # 基础信息
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    content = db.Column(db.Text, nullable=False)
    like_cnt = db.Column(db.Integer, default=0)
    # 时间戳
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    updated_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), onupdate=db.func.now())
    # 外键
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id', ondelete='CASCADE'), index=True)
    replies = db.relationship('Reply', backref='comment', foreign_keys="[Reply.comment_id]", cascade='all, delete-orphan')

    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', back_populates='comments', lazy='select')
    
    @validates('content')
    def validate_content(self, key, value):
        # 添加内容过滤，因为主要是markdown内容，大部分不会有html标签，所以做暂时处理
        return value.strip() 
    
    def __str__(self):
        return f"[comment: {self.id}, {self.content}, {self.user_id}]"
    
    @classmethod
    def transfer_to_deleted_user(cls, user_id):
        '''转移用户评论到注销用户下'''
        from .auth import User
        deleted_user = User.get_deleted_user()
        db.session.execute(
            update(cls)
            .where(cls.user_id == user_id)
            .values(user_id=deleted_user.id)
        )
    

class Reply(db.Model):
    __tablename__ = 'replies'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    like_cnt = db.Column(db.Integer, default=0)
    # 时间戳
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    updated_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), onupdate=db.func.now())

    comment_id = db.Column(db.Integer, db.ForeignKey('comment.id', name='fk_reply_comment', ondelete='CASCADE'), index=True)
    
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', back_populates='replies', lazy='select')

    parent_id = db.Column(db.Integer, db.ForeignKey('replies.id', name='fk_reply_parent', ondelete='CASCADE'))
    replies = db.relationship(
        'Reply', 
        backref=db.backref('parent', remote_side=[id]),
        cascade='all, delete-orphan',
        lazy='dynamic'
    )

    @validates('content')
    def validate_content(self, key, value):
        # 添加内容过滤，因为主要是markdown内容，大部分不会有html标签，所以做暂时处理
        return value.strip()
    
    @classmethod
    def transfer_to_deleted_user(cls, user_id):
        '''转移用户评论到注销用户下'''
        from .auth import User
        deleted_user = User.get_deleted_user()
        db.session.execute(
            update(cls)
            .where(cls.user_id == user_id)
            .values(user_id=deleted_user.id)
        )
    

class Like(db.Model):
    __tablename__ = 'likes'

    user_id = db.Column(db.String(36), db.ForeignKey('user.id', name='fk_like_operator', ondelete='CASCADE'), primary_key=True)
    target_type = db.Column(db.String(20), primary_key=True)
    target_id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

    # 优化符合索引
    __table_args__ = (
        db.Index('idx_like_target', 'target_type', 'target_id'),        # 加速特定类型的所有点赞记录查询
        db.Index('idx_user_likes', 'user_id', 'target_type')            # 加速用户特定类型目标的所有点赞
    )

    @classmethod
    def is_liked(cls, user_id, target_type, target_id):
        return db.session.query(
            exists().where(
                cls.user_id == user_id,
                cls.target_type == target_type,
                cls.target_id == target_id
            )
        ).scalar()
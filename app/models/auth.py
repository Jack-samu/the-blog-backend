from bcrypt import gensalt, hashpw, checkpw
from uuid import uuid4

from app.extensions import db


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    bio = db.Column(db.String(120))
    username = db.Column(db.String(30), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(10), default='normal', nullable=False)

    last_login = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    login_failed_attempts = db.Column(db.Integer, nullable=False, default=0)
    is_active = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    updated_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), onupdate=db.func.now())
    
    # 外键，article和imgs级联删除
    posts = db.relationship('Post', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    drafts = db.relationship('Draft', backref='author', lazy='dynamic', cascade='all,delete-orphan')
    categories = db.relationship('Category', backref='user', lazy='dynamic', cascade='all,delete-orphan')
    imgs = db.relationship('Image', backref='uploader', lazy='dynamic', cascade='all, delete-orphan')

    # 用户被删除后，评论会设定为NULL
    comments = db.relationship('Comment', back_populates='user', lazy='dynamic', passive_deletes=True)
    replies = db.relationship('Reply', back_populates='user', lazy='dynamic', passive_deletes=True)

    def set_pwd(self, password):
        salt = gensalt()
        self.password = hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def check_pwd(self, password):
        return checkpw(password.encode('utf-8'), self.password.encode('utf-8'))

    def update_last_login(self):
        self.last_login = db.func.now()
        db.session.commit()

    def increment_login_failed_cnt(self):
        self.login_failed_attempts += 1
    
    def check_login_lock(self):
        return self.login_failed_attempts >= 5
    
    def __str__(self):
        return f"[user: {self.id}, {self.username}, {self.email}, {self.created_at}, {self.updated_at}]"
    
    @property
    def is_admin(self):
        return self.role == 'admin'
    
    @classmethod
    def create_admin(cls, email, pwd):
        if cls.query.filter_by(username='admin').first():
            return
        admin = cls(username='admin', email=email, role='admin')
        admin.set_pwd(pwd)
        db.session.add(admin)
        db.session.commit()
        return admin
    
    @classmethod
    def delete_user(cls, user_id):
        # 外部调用往往有事务开启，这里不进行事务展开
        # 调用Comment和Reply的删除方法进行评论转移
        from .comment import Comment, Reply
        Comment.transfer_to_deleted_user(user_id)
        Reply.transfer_to_deleted_user(user_id)

        user_to_delete = cls.query.get(user_id)
        if user_to_delete.is_admin:
            raise ValueError('干嘛呢？这是管理员账号')
        db.session.delete(user_to_delete)
    
    @classmethod
    def get_deleted_user(cls):
        deleted_user = db.session.query(cls).filter_by(
            username = '已注销',
            is_active = False
        ).first()
        if not deleted_user:
            deleted_user = cls(
                username='已注销',
                email='deleted@aba.com',
                role='deleted',
                is_active=False
            )
            deleted_user.set_pwd('deleted')
            db.session.add(deleted_user)
            db.session.commit()
        return deleted_user
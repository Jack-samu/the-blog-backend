from ..extensions import db

from bcrypt import gensalt, hashpw, checkpw
from uuid import uuid4

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    last_login = db.Column(db.DateTime) # 下线时间
    login_failed_attempts = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    updated_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), onupdate=db.func.now())
    # 外键
    articles = db.relationship('Article', backref='author', lazy='dynamic')
    imgs = db.relationship('Image', backref='uploader', lazy='dynamic')
    comments = db.relationship('Comment', backref='user', lazy='dynamic')

    def set_pwd(self, password):
        salt = gensalt()
        self.password = hashpw(password.encode('utf-8'), salt)

    def check_pwd(self, password):
        return checkpw(password.encode('utf-8'), self.password)

    def update_last_login(self):
        self.last_login = db.func.now()
        db.session.commit()

    def increment_login_failed_cnt(self):
        self.login_failed_attempts += 1
        db.session.commit()

    def get_avatar(self):
        img = self.imgs.filter_by(is_avatar=True).first()
        if img:
            return img
        return None
    
    def check_login_lock(self):
        return self.login_failed_attempts >= 5
    
    def __str__(self):
        return f"[user: {self.id}, {self.username}, {self.email}, {self.created_at}, {self.updated_at}]"
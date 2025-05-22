from ..extensions import db


from sqlalchemy import event
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.orm import validates
from markupsafe import escape



article_tags = db.Table('article_tags',
                    db.Column('article_id', db.Integer, db.ForeignKey('article.id'), primary_key=True),
                    db.Column('tags_id', db.Integer, db.ForeignKey('tags.id'), primary_key=True),
)


class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(20), unique=True, nullable=False)
    articles = db.relationship('Article', backref='category', lazy='dynamic')
    
    @classmethod
    def get_or_create(cls, session, name):
        try:
            return session.query(cls).filter_by(name=name).one()
        except NoResultFound:
            try:
                category = cls(name=name)
                session.add(category)
                session.flush()
                return category
            except IntegrityError:
                session.rollback()
                return session.query(cls).filter_by(name=name).one()


class Tag(db.Model):
    __tablename__ = 'tags'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(20), unique=True, nullable=False)

    __table_args__ = (
        db.Index('ix_tag_name', 'name'),
    )
    
    @classmethod
    def get_or_create(cls, session, name):
        try:
            return session.query(cls).filter_by(name=name).one()
        except NoResultFound:
            try:
                with session.no_autoflush:
                    tag = cls(name=name)
                    session.add(tag)
                    session.flush()
                return tag
            except IntegrityError:
                session.rollback()
                return session.query(cls).filter_by(name=name).one
            

class Article(db.Model):
    __tablename__ = 'article'
    # 基础信息
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(40), index=True)
    excerpt = db.Column(db.String(200))
    content = db.Column(db.Text)
    is_draft = db.Column(db.Boolean)
    views_cnt = db.Column(db.Integer, nullable=False, default=0)
    like_cnt = db.Column(db.Integer, default=0, server_default='0')
    # 时间戳
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), index=True)
    updated_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), onupdate=db.func.now())
    # 多对多关联，relationship的使用方便python代码进行关联对象的访问，对应另一方的ForeignKey
    tags = db.relationship("Tag", secondary=article_tags, backref='articles',lazy='joined')
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), index=True)
    user_id = db.Column(db.String(36), db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    comments = db.relationship('Comment', backref='article', lazy='joined')

    def __str__(self):
        return f"{self.title}, {self.author}, {self.excerpt}"
    
    def get_tags(self):
        return [tag.name for tag in self.tags]
    
    def view_increase(self):
        self.views_cnt += 1
        db.session.commit()
    
    @validates('content')
    def validate_content(self, key, value):
        return escape(value.strip())
    
class ArticleLike(db.Model):
    __tablename__ = 'article_likes'
    article_id = db.Column(db.Integer, db.ForeignKey('article.id', ondelete='CASCADE'), primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False, primary_key=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

# 自动触发计数器更新
@event.listens_for(ArticleLike, 'after_insert')
def article_like_increment(mapper, connection, target):
    connection.execute(
        db.update(Article)
         .where(Article.id == target.article_id)
         .values(like_cnt=Article.like_cnt + 1)
    )
    
    
class Image(db.Model):
    __tablename__ = 'image'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, unique=True, nullable=False)
    is_cover = db.Column(db.Boolean, default=False, server_default='false')
    is_avatar = db.Column(db.Boolean, default=False, server_default='false')
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

    # 外键
    article_id = db.Column(db.Integer, db.ForeignKey('article.id', ondelete='CASCADE'))
    user_id = db.Column(db.String(36), db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)

    def __str__(self):
        return f"{self.name}, {self.is_cover}, {self.is_avatar}, {self.user_id}"

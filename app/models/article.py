from app.extensions import db


from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import validates


post_tags = db.Table('post_tags',
                    db.Column('post_id', db.Integer, db.ForeignKey('posts.id'), primary_key=True),
                    db.Column('tags_id', db.Integer, db.ForeignKey('tags.id'), primary_key=True),
)

draft_tags = db.Table('draft_tags',
                    db.Column('draft_id', db.Integer, db.ForeignKey('drafts.id'), primary_key=True),
                    db.Column('tags_id', db.Integer, db.ForeignKey('tags.id'), primary_key=True),
)


class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(20), unique=True, nullable=False)
    # 级联删除
    user_id = db.Column(db.String(36), db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    posts = db.relationship('Post', backref='category', lazy='dynamic', cascade='all, delete-orphan')
    drafts = db.relationship('Draft', backref='category', lazy='dynamic')
    
    @classmethod
    def get_or_create(cls, name, user_id):
        instance = cls.query.filter(
                cls.name.collate('utf8mb4_0900_ai_ci') == name,
                cls.user_id == user_id
            ).first()
        if not instance:
            try:
                instance = cls(name=name, user_id=user_id)
                db.session.add(instance)
                db.session.flush()
            except IntegrityError:
                # 针对可能的并发创建
                db.session.rollback()
                return cls.query.filter(
                    cls.name.collate('utf8mb4_0900_ai_ci') == name,
                    cls.user_id == user_id
                ).first()
        return instance


class Tag(db.Model):
    __tablename__ = 'tags'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(20), unique=True, nullable=False)

    __table_args__ = (
        db.Index('ix_tag_name', 'name'),
    )

    def is_referenced(self):
        return len(self.posts) > 0 or len(self.drafts) > 0
    
    @classmethod
    def get_or_create(cls, name):
        instance = cls.query.filter(
                cls.name.collate('utf8mb4_0900_ai_ci') == name
            ).first()
        if not instance:
            try:
                instance = cls(name=name)
                db.session.add(instance)
                db.session.flush()
            except IntegrityError:
                # 针对可能的并发创建
                db.session.rollback()
                return cls.query.filter(
                    cls.name.collate('utf8mb4_0900_ai_ci') == name
                ).first()
        return instance
    

class Draft(db.Model):
    __tablename__ = 'drafts'
    # 基础信息
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(100), index=True)
    excerpt = db.Column(db.String(200))
    content = db.Column(db.Text)
    cover = db.Column(db.String(100), nullable=True)
    # 时间戳
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), index=True)
    updated_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), onupdate=db.func.now())

    user_id = db.Column(db.String(36), db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), index=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id', ondelete='SET NULL'))
    tags = db.relationship("Tag", secondary=draft_tags, backref='drafts', lazy='joined')

    def __str__(self):
        return f"[{self.id}, {self.title}]"
    
    def update_from_dict(self, data):
        self.title = data.get('title', self.title)
        self.excerpt = data.get('excerpt', self.excerpt)
        self.content = data.get('content', self.content)
        self.cover = data.get('cover', self.cover)

    @classmethod
    def create_from_dict(cls, data, user_id):
        instance = cls(user_id=user_id)
        for field in {'title', 'content', 'excerpt', 'cover'}:
            if field in data:
                setattr(instance, field, data[field])
        return instance
    

    def update_categories_tags(self, new_category=None, new_tags=None):
        if new_category is not None:
            self._update_category(new_category)

        if new_tags is not None:
            self._update_tags(new_tags)


    def _update_category(self, new_category):
        if not new_category:
            self.category_id = None
            return
        
        # 如果存在
        if self.category and self.category.name.casefold() == new_category.casefold():
            return
        
        new_category = Category.get_or_create(new_category, self.user_id)
        self.category = new_category

    def _update_tags(self, new_tag_names):
        if not new_tag_names:
            self.tags.clear()
            return
        
        current_tags = {t.name.casefold() for t in self.tags}
        new_tags_set = {t.casefold() for t in new_tag_names}

        to_remove = [t for t in self.tags if t.name not in new_tags_set]
        to_add = [Tag.get_or_create(name) for name in new_tag_names
                  if name not in current_tags]

        for t in to_remove:
            self.tags.remove(t)

        self.tags.extend(to_add)
    
    def to_post(self):
        post_data = {
            'title': self.title,
            'excerpt': self.excerpt,
            'content': self.content,
            'cover': self.cover
        }

        post = self.post
        if not post:
            post = Post.create_from_dict(post_data, self.user_id)
            db.session.add(post)
        post.category_id = self.category_id
        post.tags = self.tags
        db.session.flush()
        self.post_id = post.id
            

class Post(db.Model):
    __tablename__ = 'posts'
    # 基础信息
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(100), index=True)
    excerpt = db.Column(db.String(200))
    content = db.Column(db.Text)
    views_cnt = db.Column(db.Integer, nullable=False, default=0)
    like_cnt = db.Column(db.Integer, default=0, server_default='0')
    cover = db.Column(db.String(100), nullable=True)
    # 时间戳
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), index=True)
    updated_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), onupdate=db.func.now())

    user_id = db.Column(db.String(36), db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id", ondelete='CASCADE'), index=True)
    tags = db.relationship("Tag", secondary=post_tags, backref='posts', lazy='joined')
    comments = db.relationship('Comment', backref='post', lazy='dynamic', cascade='all, delete-orphan')
    replies = db.relationship('Reply', backref='post', lazy='dynamic', cascade='all, delete-orphan')
    draft = db.relationship('Draft', backref='post', lazy='dynamic')

    def __str__(self):
        return f"{self.title}, {self.author}, {self.created_at.isoformat()}"
    
    def get_tags(self):
        return [tag.name for tag in self.tags]
    
    @validates('content')
    def validate_content(self, key, value):
        return value.strip()

    @classmethod
    def create_from_dict(cls, data, user_id):
        instance = cls(user_id=user_id)
        for field in {'title', 'content', 'excerpt', 'cover'}:
            if field in data:
                setattr(instance, field, data[field])
        return instance
    

    def update_categories_tags(self, new_category=None, new_tags=None):
        if new_category is not None:
            self._update_category(new_category)

        if new_tags is not None:
            self._update_tags(new_tags)


    def _update_category(self, new_category):
        if not new_category:
            self.category_id = None
            return
        
        # 如果存在
        if self.category and self.category.name.casefold() == new_category.casefold():
            return
        
        new_category = Category.get_or_create(new_category, self.user_id)
        self.category = new_category

    def _update_tags(self, new_tag_names):
        if not new_tag_names:
            self.tags.clear()
            return
        
        current_tags = {t.name.casefold() for t in self.tags}
        new_tags_set = {t.casefold() for t in new_tag_names}

        to_remove = [t for t in self.tags if t.name not in new_tags_set]
        to_add = [Tag.get_or_create(name) for name in new_tag_names
                  if name not in current_tags]

        for t in to_remove:
            self.tags.remove(t)

        self.tags.extend(to_add)
            

    
class Image(db.Model):
    __tablename__ = 'image'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    is_avatar = db.Column(db.Boolean, default=False, server_default='0')
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

    user_id = db.Column(db.String(36), db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)

    def __str__(self):
        return f"{self.name}, {self.is_avatar}, {self.user_id}"
    
    @classmethod
    def get_or_create(cls, name, uploader):
        instance = cls.query.filter(
                cls.name == name,
                cls.user_id == uploader.id
            ).first()
        if not instance:
            try:
                instance = cls(name=name, uploader=uploader)
                db.session.add(instance)
                db.session.flush()
            except IntegrityError:
                # 针对可能的并发创建
                db.session.rollback()
                return cls.query.filter(
                    cls.name == name,
                    cls.user_id == uploader.id
                ).first()
        return instance
    
    @classmethod
    def set_avatar(cls, filename, uploader):
        try:
            with db.session.begin_nested():
                cover = uploader.imgs.filter_by(is_avatar=True).first()
                img = cls.get_or_create(filename, uploader)
                if cover:
                    if cover.name == filename:
                        return
                    else:
                        cover.is_avatar = False
                        img.is_avatar = True
                else:
                    img.is_avatar = True
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise(str(e))

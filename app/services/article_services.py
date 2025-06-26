from app.models.article import Post, Image, Draft
from app.extensions import db


# class ArticleService:
#     @classmethod
#     def create_or_update_article(cls, user_id, data):
#         with db.session.begin_nested():
#             draft = Draft.query.filter_by(
#                 id=data.get('id'),
#                 user_id=user_id
#             ).first() if data.get('id') else None

#             if draft:
#                 draft.update_from_dict(data)
#             else:
#                 draft = Draft.create_from_dict(data, user_id)
#                 db.session.add(draft)

#             db.session.flush()

#             ArticleService._process_relations(draft, data)
#             return draft
            

#     @classmethod
#     def _process_relations(cls, article: Post, data):

#         article.update_categories_tags(data.get('category'), data.get('tags'))


class ArticleSerializer:
    @classmethod
    def format_basic(cls, article):
        return {
            'id': article.id,
            'title': article.title,
            'created_at': article.created_at.isoformat() if article.created_at else '',
            'updated_at': article.updated_at.isoformat() if article.updated_at else ''
        }
    
    @classmethod
    def format_list(cls, article):
        base = ArticleSerializer.format_basic(article)
        base.update({
            'excerpt': article.excerpt,
            'category': article.category.name if article.category else None,
            'tags': [t.name for t in article.tags],
            'cover': article.cover,
            'author': article.author.username
        })
        if isinstance(article, Post):
            base.update({
                'views': article.views_cnt,
                'likes': article.like_cnt,
                'comments': article.comments.count(),
            })
        return base
    
    @classmethod
    def format_detail(cls, article):
        base = ArticleSerializer.format_list(article)
        author = article.author
        avatar = author.imgs.filter_by(is_avatar=True).first()
        base.update({
            'content': article.content,
            'author': {
                'id': author.id,
                'username': author.username,
                'avatar': avatar.name if avatar else ''
            }
        })
        return base
from app.models.article import Article, Image
from app.extensions import db


class ArticleService:
    @classmethod
    def create_or_update_article(cls, user_id, data):
        with db.session.begin_nested():
            article = Article.query.filter_by(
                id=data.get('id'),
                user_id=user_id
            ).first() if data.get('id') else None

            if article:
                article.update_from_dict(data)
            else:
                article = Article.create_from_dict(data, user_id)
                db.session.add(article)

            db.session.flush()

            ArticleService._process_relations(article, data)
            return article
            

    @classmethod
    def _process_relations(cls, article: Article, data):

        article.update_categories_tags(data.get('category'), data.get('tags'))


class ArticleSerializer:
    @classmethod
    def format_basic(cls, article: Article):
        return {
            'id': article.id,
            'title': article.title if article.title else '佚名',
            'created_at': article.created_at.isoformat() if article.created_at else '',
            'updated_at': article.updated_at.isoformat() if article.updated_at else ''
        }
    
    @classmethod
    def format_list(cls, article: Article):
        base = ArticleSerializer.format_basic(article)
        base.update({
            'excerpt': article.excerpt,
            'category': article.category.name if article.category else None,
            'tags': [t.name for t in article.tags],
            'views': article.views_cnt,
            'likes': article.like_cnt,
            'cover': article.cover,
            'comments': article.comments.count(),
            'author': article.author.username
        })
        return base
    
    @classmethod
    def format_detail(cls, article: Article):
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
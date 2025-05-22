from flask import Blueprint, jsonify, request
from urllib.parse import unquote

from loguru import logger


from .model import Article, ArticleLike, Tag, Category, Image
from ..extensions import db
from app.utils.auth import token_required



article_bp = Blueprint('article', __name__)


@article_bp.before_request
def log_request():
    logger.info(f"[{request.method}] {request.path}")


# 展示文章和对应
@article_bp.route("/articles", methods=["GET"])
def articles():
    page = request.args.get('page', 1, type=int)
    perpage = request.args.get('per_page', 10, type=int)

    try:
        # 对已发表post进行分页查询，常见的有joinedload，subqueryload和lazyload
        # joinedload可以同时加载关联对象，从而减少查询次数，避免N+1查询
        # lazyload是默认策略，查询主对象然后每次访问关联对象进行一次额外查询
        # subqueryload，子查询加载关联对象，生成一个单独子查询，对应复杂的关联关系
        articles = Article.query.filter_by(is_draft = False).order_by(Article.created_at)\
                .options(
                    db.joinedload(Article.category),
                    db.joinedload(Article.tags)
                )\
                .paginate(page=page, per_page=perpage, error_out=False)

        return jsonify({
            'articles':[{
                'id': article.id,
                'title': article.title,
                'excerpt': article.excerpt,
                'category': Category.query.filter_by(id=article.category_id).first().name,
                'tags': article.get_tags(),
                'created_at': article.created_at,
                'author': article.author.username,
                'cover': Image.query.filter_by(article_id=article.id).first().name,
                'comments': len(article.comments),
                'likes': article.like_cnt
            } for article in articles.items],
            'total': articles.total,
            'current_page': page
        }), 200
    except Exception as e:
        import traceback
        logger.error(traceback.format_exc())
        logger.error(e)
        return jsonify({'err': '服务器错误'}), 500


@article_bp.route('/articles/<string:title>', methods=["GET"])
def detail(title):
    article = Article.query.filter_by(
                is_draft = False,
                title = unquote(title)
            ).first()
    if article:
        article.view_increase()
        cover = Image.query.filter_by(article_id=article.id, is_cover=True).first()
        category = Category.query.filter_by(id=article.category_id).first()
        return jsonify({
            'article': {
                'id': article.id,
                'title': article.title,
                'content': article.content,
                'tags': [tag.name for tag in article.tags],
                'author': article.author.username,
                'category': {
                    category.name: [article.title for article in category.articles]
                },
                'created_at': article.created_at,
                'updated_at': article.updated_at,
                'cover': cover.name,
            }
        }), 200
    return jsonify({'err': 'article not found.'}), 404


@article_bp.route('/articles/publish', methods=['POST'])
@token_required
def publish_article(current_user):
    try:
        form = request.get_json()

        if not all([form.get('title'), form.get('content')]):
            return jsonify({'err': '标题和内容不能为空'}), 400

        db.session.begin()

        excerpt = form.get('excerpt') if form.get('excerpt') else form.get('title')

        if not excerpt:
            return jsonify({'err': '文章主体都是空的，保存个啥'}), 400
        category = Category.get_or_create(db.session, form.get('category'))
        tags = [Tag.get_or_create(db.session, tag) for tag in form.get('tags')]

        article = Article.query.filter_by(
                        id=form.get('id'),
                        user_id=current_user.id).first()
        if form.get('is_draft') and article:
            # 草稿需要修改
            article.title = form.get('title')
            article.content = form.get('content')
            article.excerpt = excerpt
            # 添加
            article.category_id = category.id
            article.is_draft = False
            article.tags.extend(tags)
            logger.info(article)
        else:
            # 没有草稿，是直接创建的文章
            article = Article(
                title = form.get('title'),
                content = form.get('content'),
                excerpt = excerpt,
                user_id = current_user.id,
                category_id = category.id,
                is_draft = False,
            )
            article.tags.extend(tags)
            db.session.add(article)

        if form.get('cover'):
            cover = Image(name=form.get('cover'), is_cover=True, user_id=current_user.id, article_id=article.id)
            db.session.add(cover)

        db.session.commit()
        return jsonify({'msg': '文章已发表'}), 201
    except Exception as e:
        logger.error(e)
        db.session.rollback()
        return jsonify({'err': '服务器错误，发表失败'}), 500


# 草稿保存，为了后续的草稿方面的修改和发表，需要返回文章id
@article_bp.route('/articles/save', methods=['POST'])
@token_required
def save_article(current_user):
    try:
        form = request.get_json()
        content = form.get('content')
        is_draft = form.get('is_draft')

        with db.session.begin_nested():

            if not content:
                return jsonify({'err': '参数错误，请检查'}), 400
            
            if is_draft:
                post = Article.query.filter_by(id=form.get('id'), user_id=current_user.id).first()
                if not post:
                    return jsonify({'err': '未能找到草稿'}), 404
                post.content = content
            else:
                post = Article(content = content, 
                            is_draft = True,
                            user_id = current_user.id)
                db.session.add(post)
            
        return jsonify({'msg': '草稿保存成功','id': post.id}), 201
    
    except Exception as e:
        logger.error(e)
        db.session.rollback()
        return jsonify({'err': '服务器错误'}), 500
    
# 文章删除
@article_bp.route('/articles/<int:id>', methods=['DELETE'])
@token_required
def delete_article(current_user, id):
    try:
        with db.session.begin_nested():
            article = Article.query.filter_by(id=id, user_id=current_user.id).first()
            if not article:
                return jsonify({'err': '未能找到文章'}), 404
            db.session.delete(article)
        
        return jsonify({'msg': '文章已删除'}), 200
    
    except Exception as e:
        logger.error(e)
        db.session.rollback()
        return jsonify({'err': '服务器错误'}), 500
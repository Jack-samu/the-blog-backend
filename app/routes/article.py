from flask import Blueprint, request
from urllib.parse import unquote
from loguru import logger


from app.extensions import db
from app.utils.auth import token_required
from app.utils.util import make_response, case_insensitive_dedupe_first
from app.models import Article, Tag, Category, Image, Like

from app.services.article_services import ArticleService, ArticleSerializer
from app.utils.validators import validate_data



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
        
        return make_response({
            'articles':[ ArticleSerializer.format_list(article) for article in articles.items],
            'total': articles.total,
            'current_page': page
        }, code=200)
    except Exception as e:
        import traceback
        logger.error(traceback.format_exc())
        logger.error(e)
        return make_response({'err': '服务器错误'}, code=500)


@article_bp.route('/articles/<string:title>', methods=["GET"])
def detail(title):
    try:
        with db.session.begin_nested():
            article = Article.query.filter_by(
                title=unquote(title), is_draft=False
            ).first()
            if article:
                article.views_cnt += 1
        db.session.commit()

        return make_response({'article': ArticleSerializer.format_detail(article)}, 200)
    except Exception as e:
        import traceback
        logger.error(traceback.format_exc())
        return make_response({'err': '服务器错误，获取文章详情'}, 500)


@article_bp.route('/articles/<int:id>', methods=["GET"])
def get_article(id):
    try:
        with db.session.begin_nested():
            article = Article.query.get(id)

        return make_response({'article': ArticleSerializer.format_detail(article)}, 200)
    except Exception as e:
        import traceback
        logger.error(traceback.format_exc())
        return make_response({'err': '服务器错误，获取文章详情'}, 500)
    

@article_bp.route('/articles/publish', methods=['GET'])
@token_required
def get_published_articles(current_user):
    try:
        page = request.args.get('page', 1, type=int)
        pageSize = request.args.get('pageSize', 10, type=int)

        published_articles = Article.query.filter_by(
            is_draft=False, user_id=current_user.id
        ).order_by(Article.created_at).options(
            db.joinedload(Article.category),
            db.joinedload(Article.tags)
        ).paginate(
            page = page,
            per_page = pageSize,
            error_out=False
        )

        return make_response({
            'publishedArticles': [
                ArticleSerializer.format_list(a) for a in published_articles
                ],
            'total': published_articles.total,
            'current_page': page
            }, 200)

    except Exception as e:
        import traceback
        logger.error(traceback.format_exc())
        return make_response({'err': '服务器错误，获取用户已发布文章列表失败'}, 500)
    

@article_bp.route('/articles/draft', methods=['GET'])
@token_required
def get_drafts(current_user):
    try:
        page = request.args.get('page', 1, type=int)
        pageSize = request.args.get('pageSize', 10, type=int)

        drafts = Article.query.filter_by(
            is_draft=True, user_id=current_user.id
        ).order_by(Article.created_at).options(
            db.joinedload(Article.category),
            db.joinedload(Article.tags)
        ).paginate(
            page = page,
            per_page = pageSize,
            error_out=False
        )

        return make_response({
            'drafts': [
                ArticleSerializer.format_list(a) for a in drafts
                ],
            'total': drafts.total,
            'current_page': page
        }, 200)

    except Exception as e:
        import traceback
        logger.error(traceback.format_exc())
        return make_response({'err': '服务器错误，获取用户草稿列表失败'}, 500)
    

# 后续可以加上页面导航
@article_bp.route('/articles/series', methods=['GET'])
@token_required
def get_series(current_user):
    try:

        categories = Category.query.filter_by(
            user_id=current_user.id
        ).all()

        return make_response({
            'categories': [ 
                {
                    'id': category.id,
                    'name': category.name, 
                    'articles': [ArticleSerializer.format_basic(article) for article in category.articles if not article.is_draft]
                } for category in categories]
        }, 200)

    except Exception as e:
        import traceback
        logger.error(traceback.format_exc())
        return make_response({'err': '服务器错误，获取用户草稿列表失败'}, 500)


# 涉及情况复杂，暂不做校验
@article_bp.route('/articles/publish', methods=['POST'])
@token_required
def publish_article(current_user):
    try:
        data = request.get_json()
        article = ArticleService.create_or_update_article(current_user.id, data)
        db.session.commit()

        return make_response({'title': article.title}, 201)
    except Exception as e:
        import traceback
        logger.error(traceback.format_exc())
        db.session.rollback()
        return make_response({'err': '服务器错误，发表失败'}, 500)


# 两种情况，一种是完整article表单，第二种是单content
@article_bp.route('/articles/save', methods=['POST'])
@token_required
def save_article(current_user):
    try:
        data = request.get_json()
        article = ArticleService.create_or_update_article(current_user.id, data)
        db.session.commit()
            
        return make_response({'msg': '草稿保存成功','id': article.id}, 201)
    
    except Exception as e:
        import traceback
        logger.error(traceback.format_exc())
        db.session.rollback()
        return make_response({'err': '服务器错误，草稿保存失败'}, 500)
    
    
# 文章删除，上次debug点
@article_bp.route('/articles/<int:id>', methods=['DELETE'])
@token_required
def delete_article(current_user, id):
    try:
        if not id:
            return make_response({'err': 'id为空'}, code=400)

        with db.session.begin_nested():
            article = Article.query.filter_by(id=id).first()
            if not article:
                return make_response({'err': '未能找到文章'}, 404)
            if article.user_id != current_user.id:
                logger.info(current_user.id)
                logger.info(article.user_id)
                return make_response({'err': '无权操作'}, 403)
            # 对应comments和replies级联删除
            db.session.delete(article)
        db.session.commit()
        
        return make_response({'msg': '文章已删除'}, 201)
    
    except Exception as e:
        import traceback
        logger.error(traceback.format_exc())
        db.session.rollback()
        return make_response({'err': '服务器错误，文章删除出错'}, 500)
    

# 文章点赞和取消点赞
@article_bp.route('/articles<int:id>/likes', methods=['POST'])
@token_required
def toggle_like(current_user, id):  
    try:
        if not id:
            return make_response({'err': 'id为空'}, code=400)

        with db.session.begin_nested():
            article = Article.query.get(id)

            like = Like.is_liked(current_user.id, 'article', id)

            if like:
                db.session.delete(like)
                article.like_cnt -= 1
                action = 'unliked'
            else:
                like = Like(
                    user_id=current_user.id, target_type='article', target_id=id
                )
                db.session.add(like)
                article.like_cnt += 1
                action = 'liked'
        db.session.commit()
        return make_response({
            'action': action,
            'cnt': article.like_cnt
        }, 201)

    except Exception as e:
        import traceback
        logger.error(traceback.format_exc())
        db.session.rollback()
        return make_response({'err': str(e)}, 500)


@article_bp.route('/article/<int:id>/like/status', methods=['GET'])
@token_required
def get_like_status(current_user, id):
    try:
        if not id:
            return make_response({'err': 'id为空'}, code=400)

        liked = Like.is_liked(current_user.id, 'article', id) is not None

        return make_response({'liked': liked}, 200)
        
    except Exception as e:
        import traceback
        logger.error(traceback.format_exc())
        return make_response({'err': '获取点赞状态时服务器出错'}, 500)
    


@article_bp.route('/health')
@token_required
def health_check(current_user):
    try:
        from sqlalchemy import text
        db.session.execute(text('select 1'))
        return make_response({'msg': 'Healthy, ok.'}, code=200)
    except Exception as e:
        logger.error(str(e))
        return make_response({'err': str(e)}, 500)
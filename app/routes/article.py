from flask import Blueprint, request
from loguru import logger


from app.extensions import db
from app.hooks import token_required
from app.utils import make_response
from app.models import Post, Draft, Category, Like

from app.services.article_services import ArticleSerializer



article_bp = Blueprint('article', __name__)


# 展示文章和对应
@article_bp.route("/articles", methods=["GET"])
def articles():
    page = request.args.get('page', 1, type=int)
    perpage = request.args.get('per_page', 10, type=int)
    # pageSize后续加吧

    try:
        # 对已发表post进行分页查询，常见的有joinedload，subqueryload和lazyload
        # joinedload可以同时加载关联对象，从而减少查询次数，避免N+1查询
        # lazyload是默认策略，查询主对象然后每次访问关联对象进行一次额外查询
        # subqueryload，子查询加载关联对象，生成一个单独子查询，对应复杂的关联关系
        posts = Post.query.order_by(Post.created_at)\
                .options(
                    db.joinedload(Post.category),
                    db.joinedload(Post.tags)
                )\
                .paginate(page=page, per_page=perpage, error_out=False)
        
        return make_response({
            'articles':[ ArticleSerializer.format_list(post) for post in posts.items],
            'total': posts.total,
            'current_page': page
        }, code=200)
    except Exception as e:
        import traceback
        logger.error(traceback.format_exc())
        return make_response({'err': '服务器错误，获取所有文章出错'}, code=500)


@article_bp.route('/articles/<int:id>', methods=["GET"])
def get_article(id):
    try:
        with db.session.begin_nested():
            post = Post.query.get(id)

        return make_response({'article': ArticleSerializer.format_detail(post)}, 200)
    except Exception as e:
        import traceback
        logger.error(traceback.format_exc())
        return make_response({'err': '服务器错误，获取文章详情出错'}, 500)


@article_bp.route('/articles/draft/<int:id>', methods=["GET"])
@token_required
def get_draft(current_user, id):
    try:
        with db.session.begin_nested():
            draft = Draft.query.get(id)

        return make_response({'article': ArticleSerializer.format_detail(draft)}, 200)
    except Exception as e:
        import traceback
        logger.error(traceback.format_exc())
        return make_response({'err': '服务器错误，获取草稿出错'}, 500)
    

@article_bp.route('/articles/publish', methods=['GET'])
@token_required
def get_published_personal(current_user):
    try:
        page = request.args.get('page', 1, type=int)
        pageSize = request.args.get('pageSize', 10, type=int)

        posts_personal = Post.query.filter_by(
            user_id=current_user.id
        ).order_by(Post.created_at).options(
            db.joinedload(Post.category),
            db.joinedload(Post.tags)
        ).paginate(
            page = page,
            per_page = pageSize,
            error_out=False
        )

        return make_response({
            'publishedArticles': [
                ArticleSerializer.format_list(a) for a in posts_personal
                ],
            'total': posts_personal.total,
            'current_page': page
            }, 200)

    except Exception as e:
        import traceback
        logger.error(traceback.format_exc())
        return make_response({'err': '服务器错误，获取用户已发布文章失败'}, 500)
    

@article_bp.route('/articles/drafts', methods=['GET'])
@token_required
def get_drafts_personal(current_user):
    try:
        page = request.args.get('page', 1, type=int)
        pageSize = request.args.get('pageSize', 10, type=int)

        drafts = Draft.query.filter_by(
            user_id=current_user.id
        ).order_by(Draft.created_at).options(
            db.joinedload(Draft.category),
            db.joinedload(Draft.tags)
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
        return make_response({'err': '服务器错误，获取用户草稿失败'}, 500)
    

# 后续可以加上页面导航
@article_bp.route('/articles/series/<string:id>', methods=['GET'])
@token_required
def get_series(current_user, id):
    try:

        categories = Category.query.filter_by(
            user_id=id
        ).all()

        return make_response({
            'categories': [ 
                {
                    'id': category.id,
                    'name': category.name, 
                    'articles': [ArticleSerializer.format_basic(article) for article in category.posts]
                } for category in categories if category.posts.count() != 0]
        }, 200)

    except Exception as e:
        import traceback
        logger.error(traceback.format_exc())
        return make_response({'err': '服务器错误，获取用户系列文章失败'}, 500)


# 一步publish和publish草稿，publish后需要删除draft
@article_bp.route('/articles/publish', methods=['POST'])
@token_required
def publish_article(current_user):
    try:
        data = request.get_json()
        post = Draft.query.get(data.get('id'))
        if post:
            post.update_from_dict(data)
            post.to_post()
            db.session.delete(post)
        else:
            post = Post.create_from_dict(data, current_user.id)
            db.session.add(post)
        post.update_categories_tags(data.get('category'), data.get('tags'))
        db.session.commit()
        return make_response({'msg': '发表成功', 'id': post.id}, 201)
    except Exception as e:
        import traceback
        logger.error(traceback.format_exc())
        db.session.rollback()
        return make_response({'err': '服务器错误，发表失败'}, 500)


# 对draft进行create、update和残缺update
@article_bp.route('/articles/save', methods=['POST'])
@token_required
def save_article(current_user):
    try:
        data = request.get_json()
        draft = Draft.query.get(data.get('id'))
        if draft:
            draft.update_from_dict(data)
        else:
            draft = Draft.create_from_dict(data, current_user.id)
            db.session.add(draft)
        
        draft.update_categories_tags(data.get('category'), data.get('tags'))
        db.session.commit()
            
        return make_response({'msg': '草稿保存成功','id': draft.id}, 201)
    
    except Exception as e:
        import traceback
        logger.error(traceback.format_exc())
        db.session.rollback()
        return make_response({'err': '服务器错误，草稿保存失败'}, 500)
    
    
# 文章删除
@article_bp.route('/articles/post/<int:id>', methods=['DELETE'])
@token_required
def delete_article(current_user, id):
    try:
        if not id:
            return make_response({'err': 'id为空'}, code=400)

        with db.session.begin_nested():
            article = Post.query.filter_by(id=id).first()
            if not article:
                return make_response({'err': '未能找到文章'}, 404)
            if article.user_id != current_user.id:
                return make_response({'err': '无权操作'}, 403)
            db.session.delete(article)
        db.session.commit()
        
        return make_response({'msg': '文章已删除'}, 201)
    
    except Exception as e:
        import traceback
        logger.error(traceback.format_exc())
        db.session.rollback()
        return make_response({'err': '服务器错误，文章删除出错'}, 500)
    

# 草稿删除
@article_bp.route('/articles/draft/<int:id>', methods=['DELETE'])
@token_required
def delete_draft(current_user, id):
    try:
        if not id:
            return make_response({'err': 'id为空'}, code=400)

        with db.session.begin_nested():
            article = Draft.query.filter_by(id=id).first()
            if not article:
                return make_response({'err': '未能找到草稿'}, 404)
            if article.user_id != current_user.id:
                return make_response({'err': '无权操作'}, 403)
            db.session.delete(article)
        db.session.commit()
        
        return make_response({'msg': '草稿已删除'}, 201)
    
    except Exception as e:
        import traceback
        logger.error(traceback.format_exc())
        db.session.rollback()
        return make_response({'err': '服务器错误，草稿删除出错'}, 500)
    

# 文章点赞和取消点赞
@article_bp.route('/articles<int:id>/likes', methods=['POST'])
@token_required
def toggle_like(current_user, id):  
    try:
        if not id:
            return make_response({'err': 'id为空'}, code=400)

        with db.session.begin_nested():
            article = Post.query.get(id)

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
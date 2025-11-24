from flask import Blueprint, request
from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import joinedload


from app.extensions import db
from app.models import Comment, Reply, Like, Post
from app.utils import make_response
from app.hooks import token_required, token_optional


comment_bp = Blueprint('comment', __name__)


def format_comment(comment: Comment, current_user = None):
    user = comment.user
    avatar = user.imgs.filter_by(is_avatar=True).first()
    data = {
        'id': comment.id,
        'post_id': comment.post_id,
        'user': {
            'id': user.id,
            'username': user.username,
            'avatar': avatar.name if avatar else '',
        },
        'content': comment.content,
        'updated_at': comment.updated_at.isoformat(),
        'likes': comment.like_cnt,
        'replies': len(comment.replies),
        'is_liked': Like.is_liked(current_user.id, 'comment', comment.id) if current_user else False
    }
    
    return data


def format_reply(reply: Reply, current_user = None):
    user = reply.user
    avatar = user.imgs.filter_by(is_avatar=True).first()
    data = {
        'id': reply.id,
        'user': {
            'id': user.id,
            'username': user.username,
            'avatar': avatar.name if avatar else ''
        },
        'comment_id': reply.comment_id,
        'content': reply.content,
        'likes': reply.like_cnt,
        'updated_at': reply.updated_at.isoformat(),
        'is_liked': Like.is_liked(current_user.id, 'reply', reply.id) if current_user else False
    }
    return data


# 获取文章评论列表
@comment_bp.route('/articles/<int:id>/comments', methods=['GET'])
@token_optional
def get_comments(current_user, id):
    try:

        # 待前台实现触底加载的功能后再来分页
        stmt = (
            select(Comment)
             .where(Comment.post_id == id)
             .order_by(Comment.updated_at.desc())
             .options(
                joinedload(Comment.user)
             )
        )
        comments = db.session.scalars(stmt).all()
        
        return make_response({
            'total': len(comments),
            'comments': [format_comment(c, current_user) for c in comments]
        }, code=200)

    except Exception as e:
        import traceback
        logger.error(traceback.format_exc())
        return make_response({'err': '获取评论时服务器出错'}, code=500)


# 获取子评论列表，需要实现前台点击展开功能
@comment_bp.route('/comments/<int:id>/replies', methods=['GET'])
@token_optional
def get_replies(current_user, id):
    try:
        
        comment = Comment.query.get(id)
        if not comment:
            return make_response({'err': '不存在该评论，操作出错'}, code=404)
        
        replies = Reply.query.filter_by(comment_id=id).order_by(Reply.updated_at.asc()).all()
        return make_response({
            'total': len(replies),
            'replies': [format_reply(r, current_user) for r in replies]
        }, code=200)
    except Exception as e:
        logger.error(f"获取子评论列表出错：{e}")
        return make_response({'err': '获取子评论列表时服务器出错'}, code=500)
    

# 创建主评论
@comment_bp.route('/articles/comments', methods=['POST'])
@token_required
def create_comment_top(current_user):
    try:
        
        data = request.get_json()

        id = data.get('article_id')
        if not id:
            return make_response({'err': '进行评论的文章id为空'}, code=400)

        content = data.get('content')
        if not content:
            return make_response({'err': '评论主体内容不能为空'},code=400)

        with db.session.begin_nested():
            post = Post.query.get(id)
            if not post:
                return make_response({'err': '进行评论的文章无法找到'}, 404)
            comment = Comment(
                post_id = post.id,
                user_id = current_user.id,
                content = content
            )
            db.session.add(comment)
        db.session.commit()
        return make_response({'comment': format_comment(comment, current_user)}, 201)
    except ValueError as e:
        return make_response({'err': str(e)}, 400)
    except Exception as e:
        logger.error(f"创建主评论出错：{e}")
        db.session.rollback()
        return make_response({'err': '创建主评论时服务器出错'}, code=500)


# 创建子评论
@comment_bp.route('/comments/replies', methods=['POST'])
@token_required
def create_reply(current_user):
    try:
        
        data = request.get_json()

        id = data.get('comment_id')
        if not id:
            return make_response({'err': '需要回复的评论的id为空'}, code=400)

        content = data.get('content')
        if not content:
            return make_response({'err': '评论主体内容不能为空'},code=400)

        parent_id = data.get('parent_id')
        
        with db.session.begin_nested():
            comment = Comment.query.get(id)
            if not comment:
                return make_response({'err': '没有对应评论，操作事务'}, 404)
            reply = Reply(
                comment_id = comment.id,
                user_id = current_user.id,
                content = content,
                parent_id = parent_id if parent_id else None
            )
            db.session.add(reply)
        db.session.commit()
        return make_response({'reply': format_reply(reply, current_user)}, 201)

    except ValueError as e:
        return make_response({'err': str(e)}, 400)
    except Exception as e:
        logger.error(f"创建子评论出错：{e}")
        db.session.rollback()
        return make_response({'err': '创建子评论时服务器出错'}, 500)
    

# 修改主评论
@comment_bp.route('/comments/modify', methods=['POST'])
@token_required
def modify_comment_top(current_user):
    try:
        
        data = request.get_json()

        id = data.get('comment_id')
        if not id:
            return make_response({'err': '需要修改的评论id为空'}, code=400)

        content = data.get('content')
        if not content:
            return make_response({'err': '评论主体内容不能为空'},code=400)

        with db.session.begin_nested():
            comment = Comment.query.get(id)
            if not comment:
                return make_response({'err': '无法找到该评论，操作失败'}, 404)
            if comment.user_id != current_user.id:
                return make_response({'err': "无权操作此内容"}, 401)
            if comment.content == content:
                return make_response({'err': '没有改动，滚'}, 400)
            comment.content = content
        db.session.commit()
        return make_response({'comment': format_comment(comment, current_user)}, 201)
    except ValueError as e:
        return make_response({'err': str(e)}, 400)
    except Exception as e:
        logger.error(f"修改主评论出错：{e}")
        db.session.rollback()
        return make_response({'err': '修改主评论时服务器出错'}, 500)


# 修改子评论
@comment_bp.route('/replies/modify', methods=['POST'])
@token_required
def modify_reply(current_user):
    try:

        data = request.get_json()

        id = data.get('id')
        if not id:
            return make_response({'err': '需要修改的回复的id为空'}, code=400)

        content = data.get('content')
        if not content:
            return make_response({'err': '评论主体内容不能为空'},code=400)

        with db.session.begin_nested():
            reply = Reply.query.get(id)
            if not reply:
                return make_response({'err': '无法找到该评论，操作失败'}, 404)
            if reply.user_id != current_user.id:
                return make_response({'err': "无权操作此内容"}, 401)
            if reply.content == content:
                return make_response({'err': '没有改动，滚'}, 400)
            reply.content = content
        db.session.commit()
        return make_response({'reply': format_reply(reply, current_user)}, 201)

    except ValueError as e:
        return make_response({'err': str(e)}, 400)
    except Exception as e:
        logger.error(f"修改子评论出错：{e}")
        db.session.rollback()
        return make_response({'err': '修改子评论时服务器出错'}, 500)
    

# 批量获取点赞状态
@comment_bp.route('/comments/like/status', methods=['POST'])
@token_required
def get_likes_status(current_user):
    data = request.get_json()

    result = {'comments': {}, 'replies': {}}

    try:
        if 'comments' in data:
            like_comments = db.session.scalars(
                select(Comment)
                 .where(
                    Like.user_id == current_user.id,
                    Like.target_type == 'comment',
                    Like.target_id.in_(data['comments'])
                 )
            ).all()
            result['comments'] = {
                l.target_id: True for l in like_comments
            }
        
        if 'replies' in data:
            like_replies = db.session.scalars(
                select(Reply)
                 .where(
                    Reply.user_id == current_user.id,
                    Reply.target_type == 'reply',
                    Reply.target_id.in_(data['replies'])
                 )
            ).all()
            result['replies'] = {
                l.target_id: True for l in like_replies
            }
        
        return make_response(result, 200)
    except Exception as e:
        import traceback
        logger.error(traceback.format_exc())
        return make_response({'err': '获取点赞状态时服务器出错'}, 500)
    

# 点赞和取消点赞
@comment_bp.route('/comments/likes', methods=['POST'])
@token_required
def toggle_like(current_user):
    data = request.get_json()

    target_type = data.get('type')
    target_id = data.get('id')

    if not all([target_id, target_type]):
        return make_response({'err': '点赞操作参数缺失'}, 400)
    
    try:
        with db.session.begin_nested():
            if target_type == 'comment':
                target = Comment.query.get(target_id)
            else:
                target = Reply.query.get(target_id)

            liked = Like.is_liked(current_user.id, target_type, target_id)

            if liked:
                like = db.session.scalar(
                    select(Like)
                     .where(
                         Like.user_id==current_user.id, 
                         Like.target_type==target_type, 
                         Like.target_id==target_id
                         )
                )
                db.session.delete(like)
                # 修改目标点赞数
                target.like_cnt -= 1
                action = 'unliked'
            else:
                like = Like(
                    user_id=current_user.id, target_type=target_type, target_id=target_id
                )
                db.session.add(like)
                target.like_cnt += 1
                action = 'liked'
        db.session.commit()
        return make_response({
            'action': action,
            'cnt': target.like_cnt
        }, 201)

    except Exception as e:
        import traceback
        logger.error(traceback.format_exc())
        db.session.rollback()
        return make_response({'err': str(e)}, 500)


# 删除评论
@comment_bp.route('/comments/<int:id>', methods=['DELETE'])
@token_required
def delete_comment(current_user, id):
    try:
        
        with db.session.begin_nested():
            comment = Comment.query.get(id)
            if not comment:
                return make_response({'err': '没有该评论，请检查'}, 404)
            if comment.user_id != current_user.id:
                return make_response({'err': '无权操作此评论'}, 403)

            db.session.delete(comment)
        db.session.commit()
        return make_response({'msg': '评论已删除'}, 201)

    except Exception as e:
        import traceback
        logger.error(traceback.format_exc())
        db.session.rollback()
        return make_response({'err': '删除评论时服务器出错'}, 500)
    

# 删除子评论
@comment_bp.route('/replies/<int:id>', methods=['DELETE'])
@token_required
def delete_reply(current_user, id):
    try:
        
        with db.session.begin_nested():
            reply = Reply.query.get(id)
            if not reply:
                return make_response({'err': '没有该评论，请检查'}, 404)
            if reply.user_id != current_user.id:
                return make_response({'err': '无权操作此评论'}, 403)

            db.session.delete(reply)
        db.session.commit()
        return make_response({'msg': '评论已删除'}, 201)

    except Exception as e:
        logger.error(f"删除评论出错：{e}")
        db.session.rollback()
        return make_response({'err': '删除评论时服务器出错'}, 500)
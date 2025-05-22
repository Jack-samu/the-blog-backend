from flask import Blueprint, request, jsonify, redirect
from loguru import logger
from sqlalchemy.orm import joinedload, subqueryload
from sqlalchemy import exists


from app.article.model import Article
from app.auth.model import User
from app.utils.auth import token_required

from ..extensions import db
from .model import Comment, Reply, comment_likes


comment_bp = Blueprint('comment', __name__)



# 这部分会是非常繁复的操作，需要引入异步操作来进行后台处理


def format_comment(comment: Comment):
    return {
        'id': comment.id,
        'user': {
            'id': comment.user.id,
            'username': comment.user.username,
            'avatar': comment.user.get_avatar().name
        },
        'content': comment.content,
        'updated_at': comment.updated_at.isoformat(),
        'likes': comment.like_cnt,
        'reply_cnt': comment.reply_cnt,
        'top':comment.is_top,
        'replies': [format_reply(r) for r in comment.replies]
    }


def format_reply(reply: Reply):
    return {
        'id': reply.id,
        'user': {
            'id': reply.user.id,
            'username': reply.user.username,
            'avatar': reply.user.get_avatar().name
        },
        'content': reply.content,
        'likes': reply.like_cnt,
        'updated_at': reply.updated_at.isoformat(),
    }


# 获取文章评论列表
@comment_bp.route('/articles/<int:id>/comments', methods=['GET'])
def get_comments(id):
    try:
        # 待前台实现触底加载的功能后再来分页
        comments = Comment.query.filter_by(article_id = id)\
                    .options(
                        joinedload(Comment.user).joinedload(User.imgs)
                    )\
                    .order_by(Comment.is_top.desc(), Comment.updated_at.desc())\
                    .all()
        
        return jsonify({
            'total': len(comments),
            'comments': [format_comment(comment) for comment in comments]
        }), 200

    except Exception as e:
        import traceback
        logger.error(traceback.format_exc())
        logger.error(f"评论获取出错：{e}")
        return jsonify({'err': '获取评论时服务器出错'}), 500


# 获取子评论列表
@comment_bp.route('/comments/<int:id>/replies', methods=['GET'])
def get_replies(id):
    try:
        comment = Comment.query.get(id)
        if not comment:
            return jsonify({'err': '不存在该评论，操作出错'}), 404
        replies = Reply.query.filter_by(comment_id=comment.id)\
                        .order_by(Reply.updated_at.asc()).all()
        return jsonify([format_reply(r) for r in replies]), 200
    except Exception as e:
        logger.error(f"获取子评论列表出错：{e}")
        return jsonify({'err': '获取子评论列表时服务器出错'}), 500
    

# 创建主评论
@comment_bp.route('/articles/<int:id>/comments', methods=['POST'])
@token_required
def create_comment_top(current_user, id):
    try:
        data = request.get_json()

        if not data.get('content'):
            return jsonify({'err': '评论主体内容不能为空'}), 400

        with db.session.begin_nested():
            article = Article.query.get(id)
            if not article:
                return jsonify({'err': '进行评论的文章无法找到'}), 404
            comment = Comment(
                article_id = article.id,
                user_id = current_user.id,
                content = data.get('content')
            )
            db.session.add(comment)
        return jsonify({'comment': format_comment(comment)}), 201
    except ValueError as e:
        return jsonify({'err': str(e)}), 400
    except Exception as e:
        logger.error(f"创建主评论出错：{e}")
        db.session.rollback()
        return jsonify({'err': '创建主评论时服务器出错'}), 500


# 创建子评论
@comment_bp.route('/comments/<int:id>/replies', methods=['POST'])
@token_required
def create_reply(current_user, id):
    try:
        data = request.get_json()

        if not data.get('content'):
            return jsonify({'err': '评论主体内容不能为空'}), 400
        
        with db.session.begin_nested():
            comment = Comment.query.get(id)
            if not comment:
                return jsonify({'err': '没有对应评论，操作事务'}), 404
            reply = Reply(
                comment_id = comment.id,
                user_id = current_user.id,
                content = data.get('content')
            )
            db.session.add(reply)
        return jsonify({'reply': format_reply(reply)}), 201

    except ValueError as e:
        return jsonify({'err': str(e)}), 400
    except Exception as e:
        logger.error(f"创建子评论出错：{e}")
        db.session.rollback()
        return jsonify({'err': '创建子评论时服务器出错'}), 500
    

# 修改主评论
@comment_bp.route('/comments/<int:id>/modify', methods=['POST'])
@token_required
def modify_comment_top(current_user, id):
    try:
        data = request.get_json()

        if not data.get('content'):
            return jsonify({'err': '要修改的评论主体内容不能为空'}), 400

        with db.session.begin_nested():
            comment = Comment.query.get(id)
            if not comment:
                return jsonify({'err': '无法找到该评论，操作失败'}), 404
            if comment.user_id != current_user.id:
                return jsonify({'err': "无权操作此内容"}), 401
            if comment.content == data.get('content'):
                return jsonify({'err': '没有改动，滚'}), 400
            comment.content = data.get('content')
        return jsonify({'comment': format_comment(comment)}), 201
    except ValueError as e:
        return jsonify({'err': str(e)}), 400
    except Exception as e:
        logger.error(f"修改主评论出错：{e}")
        db.session.rollback()
        return jsonify({'err': '修改主评论时服务器出错'}), 500


# 修改子评论
@comment_bp.route('/replies/<int:id>/modify', methods=['POST'])
@token_required
def modify_reply(current_user, id):
    try:
        data = request.get_json()

        if not data.get('content'):
            return jsonify({'err': '要修改的评论主体内容不能为空'}), 400

        with db.session.begin_nested():
            reply = Reply.query.get(id)
            if not reply:
                return jsonify({'err': '无法找到该评论，操作失败'}), 404
            if reply.user_id != current_user.id:
                return jsonify({'err': "无权操作此内容"}), 401
            if reply.content == data.get('content'):
                return jsonify({'err': '没有改动，滚'}), 400
            reply.content = data.get('content')
        return jsonify({'reply': format_reply(reply)}), 201

    except ValueError as e:
        return jsonify({'err': str(e)}), 400
    except Exception as e:
        logger.error(f"修改子评论出错：{e}")
        db.session.rollback()
        return jsonify({'err': '修改子评论时服务器出错'}), 500
    

# 评论点赞
@comment_bp.route('/comments/<int:id>/like', methods=['POST'])
@token_required
def comment_like(current_user, id):
    try:
        with db.session.begin_nested():
            comment = Comment.query.get(id)
            if not comment:
                return jsonify({'err': '要点赞的评论不存在，操作失误'}), 400

            stmt = db.select(comment_likes).where(
                (comment_likes.c.user_id == current_user.id) &
                (comment_likes.c.comment_id == id)
            )

            if db.session.execute(stmt).fetchone():
                return jsonify({'err': '已经点赞，重复操作'}), 400
            
            db.session.execute(comment_likes.insert().values(
                user_id=current_user.id,
                comment_id = id
            ))

            # 更新comment中点赞数量
            comment.like_cnt = comment.like_cnt + 1
            return jsonify({'liked': True}), 201

    except ValueError as e:
        return jsonify({'err': str(e)}), 400
    except Exception as e:
        import traceback
        logger.error(traceback.format_exc())
        db.session.rollback()
        return jsonify({'err': '点赞时服务器出错'}), 500
    

# 取消点赞
@comment_bp.route('/comments/<int:id>/unlike', methods=['POST'])
@token_required
def unlike_comment(current_user, id):
    try:
        with db.session.begin_nested():
            comment = Comment.query.get(id)
            if not comment:
                return jsonify({'err': '要操作的评论不存在，操作失误'}), 400

            stmt = db.select(comment_likes).where(
                (comment_likes.c.user_id == current_user.id) &
                (comment_likes.c.comment_id == id)
            )

            if not db.session.execute(stmt).fetchone():
                return jsonify({'err': '已经取消，重复操作'}), 400
            
            db.session.execute(comment_likes.delete().values(
                user_id=current_user.id,
                comment_id = id
            ))

            # 更新comment中点赞数量
            comment.like_cnt = comment.like_cnt - 1
            return jsonify({'liked': False}), 201

    except ValueError as e:
        return jsonify({'err': str(e)}), 400
    except Exception as e:
        import traceback
        logger.error(traceback.format_exc())
        db.session.rollback()
        return jsonify({'err': '取消点赞时服务器出错'}), 500


# 检查是否已经点赞
@comment_bp.route('/comments/<int:id>/likeornot', methods=['POST'])
@token_required
def like_or_not(current_user, id):
    try:
        with db.session.begin_nested():
            stmt = exists().where(
                (comment_likes.c.user_id == current_user.id) &
                (comment_likes.c.comment_id == id)
            ).select()
            already_liked = db.session.execute(stmt).scalar()
            logger.info(already_liked)
            return jsonify({'liked': already_liked}), 200
    except Exception as e:
        import traceback
        logger.error(traceback.format_exc())
        db.session.rollback()
        return jsonify({'err': '取消点赞时服务器出错'}), 500



# 删除评论
@comment_bp.route('/comments/<int:id>', methods=['DELETE'])
@token_required
def delete_comment(current_user, id):
    try:
        with db.session.begin_nested():
            comment = Comment.query.get(id)
            if not comment:
                return jsonify({'err': '没有该评论，请检查'}), 404
            if comment.user_id != current_user.id:
                return jsonify({'err': '无权操作此评论'}), 403

            db.session.delete(comment)
        return jsonify({'msg': '评论已删除'}), 201

    except Exception as e:
        logger.error(f"删除评论出错：{e}")
        db.session.rollback()
        return jsonify({'err': '删除评论时服务器出错'}), 500
    

# 删除子评论
@comment_bp.route('/replies/<int:id>', methods=['DELETE'])
@token_required
def delete_reply(current_user, id):
    try:
        with db.session.begin_nested():
            reply = Reply.query.get(id)
            if not reply:
                return jsonify({'err': '没有该评论，请检查'}), 404
            if reply.user_id != current_user.id:
                return jsonify({'err': '无权操作此评论'}), 403

            db.session.delete(reply)
        return jsonify({'msg': '评论已删除'}), 201

    except Exception as e:
        logger.error(f"删除评论出错：{e}")
        db.session.rollback()
        return jsonify({'err': '删除评论时服务器出错'}), 500
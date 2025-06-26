from flask import Blueprint, request, current_app, Response

from datetime import datetime
from random import choice
from email.mime.text import MIMEText
from uuid import uuid4, UUID
from loguru import logger
from os.path import join
from os import remove
from jwt import ExpiredSignatureError, InvalidTokenError, decode


from app.extensions import db
from app.utils.auth import generate_reset_token, token_required, generate_jwt_token, generate_refresh_token, verify_token
from app.utils.emails import send_msg
from app.utils.util import make_response
from app.models import Image, User


auth_bp = Blueprint('auth', __name__)

verification_codes = {}
def allowed_img(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}


def format_user_profile(user: User):
    avatar = user.imgs.filter_by(is_avatar=True).first()
    return {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'articleCount': user.posts.count(),
            'draftCount': user.posts.count(),
            'avatar': avatar.name if avatar else None,
        }


# 验证码获取
@auth_bp.route('/auth/getcode', methods=['POST'])
def send():
    try:
        form = request.get_json()
        username = form.get('username')
        email = form.get('email')

        user = User.query.filter_by(username=username).first()
        if not user:
            return make_response({'err': '用户不存在，检查是否输入错误'}, code=400)
        if user.email != email:
            return make_response({'err': '用户邮箱不正确，检查是否为该邮箱'}, code=400)
        # 刚发送还没1分钟，让老子停一下
        msg = verification_codes.get(username)
        if msg and (datetime.now() - msg['sent_at']).total_seconds() < 60:
            return make_response({'err': '请稍等，发送完还没一分钟'}, code=429)
        
        # 验证码操作
        from string import ascii_letters, digits
        chs = ascii_letters + digits
        code = ''.join(choice(chs) for _ in range(6))
        verification_codes[username] = {
            'code': code,
            'email': email,
            'sent_at': datetime.now(),
        }
        msg = MIMEText(f'{username}，你好，你的验证码为：{code}，有效期为3分钟')
        if send_msg(email, msg):
            return make_response({'msg': '验证码已发送'}, code=200)
        else:
            return make_response({'err': '验证码发送失败，请重试'}, code=500)
    except Exception as e:
        import traceback
        logger.error(traceback.format_exc())
        return make_response({'err': '验证码发送失败，请重试'}, code=500)
        


@auth_bp.route('/auth/verify', methods=['POST'])
def verify():
    form = request.get_json()
    username = form.get('username')
    code = form.get('verificationCode')

    # 邮箱验证码校验
    msg = verification_codes.get(username)
    if not msg:
        return make_response({'err': '服务器错误，请重试'}, code=500)
    # 超过5分钟了
    if (datetime.now() - msg['sent_at']).total_seconds() > 60 * 3:
        del verification_codes[username]
        return make_response({'err': '验证码已过期，请重新发送验证码'}, code=400)
    if msg['code'] != code:
        return make_response({'err': '验证码错误，请检查'}, code=400)
    
    # 身份校验通过
    email = verification_codes[username]['email']
    user = User.query.filter_by(username=username, email=email).first()
    token = generate_reset_token(user)
    uuid = str(uuid4())
    resset_link = f'http://192.168.1.10:8088/auth/reset/{token}/{uuid}'
    msg = MIMEText(f'{username}，你好，请点击以下链接进行密码重设：{resset_link}，有效期为5分钟')

    if send_msg(email, msg):
        del verification_codes[username]
        return make_response({'msg': '校验通过，密码重设链接已发送到邮箱'}, code=200)
    else:
        return make_response({'err':'服务器错误，请重试'}, code=500)
    

@auth_bp.route('/auth/reset/<string:token>/<string:uuid>', methods=['GET', 'POST'])
def reset(token, uuid):
    # 校验token
    try:
        UUID(uuid, version=4)

        data = decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])

        if request.method == 'POST':
            
            db.session.begin()
            user = User.query.get(data['id'])

            form = request.form
            new_password = form.get('password')
            pwd_confirm = form.get('pwdRepeat')

            if new_password != pwd_confirm:
                return make_response({'err': '密码不一致'}, code=400)
            if len(new_password) < 8:
                return make_response({'err': '密码长度需要大于8'}, code=400)
            if user.check_pwd(new_password):
                return make_response({'err': '恭喜你，想起了以前的密码了，就是这个'}, code=400)
            import re
            if not re.search(r'[a-zA-Z]', new_password) or not re.search(r'\d', new_password):
                return make_response({'err': '密码至少包含一个字母和一个数字'}, code=400)
            user.set_pwd(new_password)
            db.session.commit()
            return make_response({'msg': '密码已重置'}, code=200)
        else:
            return Response("""
            <form method="post">
                <input type="password" name="password" placeholder="输入新密码" required />
                <input type="password" name="pwdRepeat" placeholder="确认新密码" required />
                <input type="submit" value="重置密码">                   
            </form>
            """, mimetype='text/html')
        
    except ValueError as e:
        return make_response(str(e), code=400)
    except ExpiredSignatureError:
        import traceback
        logger.error(traceback.format_exc())
        return make_response({'err': '刷新token已过期'}, code=401)
    except InvalidTokenError as e:
        import traceback
        logger.error(traceback.format_exc())
        return make_response({'err': '刷新token不合法'}, code=401)
    except Exception as e:
        # 事务回滚，防止注册出错都进行存储
        import traceback
        logger.error(traceback.format_exc())
        logger.error(e)
        db.session.rollback()
        return make_response({'err': '服务器错误，注册失败'}, code=500)
    

@auth_bp.route('/auth/<string:id>/profile', methods=['GET'])
def profile(id):
    try:
        user = User.query.get(id)
        return make_response({
            'user': format_user_profile(user)
        }, 200)
    except Exception as e:
        # 事务回滚，防止注册出错都进行存储
        import traceback
        logger.error(traceback.format_exc())
        return make_response({'err': '服务器错误，注册失败'}, code=500)


@auth_bp.route('/auth/<string:id>/photos', methods=['GET'])
def get_photos(id):
    try:
        photos = Image.query.filter_by(user_id=id).all()
        return make_response({
            'photos': [
                {'id': pic.id,
                'name': pic.name} 
                for pic in photos]
        }, 200)
    except Exception as e:
        # 事务回滚，防止注册出错都进行存储
        import traceback
        logger.error(traceback.format_exc())
        return make_response({'err': '服务器错误，获取用户图片失败'}, code=500)



# 刷新token，反复debug貌似会有点问题
@auth_bp.route('/auth/refresh', methods=['POST'])
def refresh_the_token():
    try:
        refresh_token = request.headers.get('Authorization', '').replace('Bearer ', '').strip()
        if not refresh_token:
            return make_response({'err': '刷新token缺失'}, code=400)
        id = verify_token(refresh_token)
        user = User.query.get(id)
        new_token = generate_jwt_token(id, current_app.config['JWT_ACCESS_EXPIRES'])
        avatar = user.imgs.filter_by(is_avatar=True).first()
        # 暂时不将在线时间延长那么多，一天就够了
        # new_refresh_token = generate_refresh_token(id, current_app.config['JWT_REFRESH_EXPIRES'])
        return make_response({
            'token': new_token,
            'userInfo': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'avatar': avatar.name if avatar else '',
                    'posts': user.posts.count()
                },
        }, code=201)
    except ExpiredSignatureError:
        import traceback
        logger.error(traceback.format_exc())
        return make_response({'err': '刷新token已过期'}, code=400)
    except InvalidTokenError as e:
        import traceback
        logger.error(traceback.format_exc())
        return make_response({'err': '刷新token不合法'}, code=400)
    except Exception as e:
        return make_response({'err': '服务器出错'}, code=500)
    

@auth_bp.route('/auth/register', methods=['POST'])
def register():
    try:
        form = request.get_json()
        if form is None:
            return make_response({'err': '注册表单为空'}, code=400)
        
        username = form.get('username')
        password = form.get('password')
        email = form.get('email')

        # 针对非前台表单
        if not all([username, password, email]):
            return make_response({'err': '用户名、密码和邮箱为必需项'}, code=400)

        # 重置会话
        db.session.rollback()

        if User.query.filter_by(username=username).first():
            return make_response({'err': '用户已存在'}, code=400)
        if User.query.filter_by(email=email).first():
            return make_response({'err': '注册邮箱已存在'}, code=400)

        with db.session.begin_nested():
            new_user = User(username=username, email=email)
            new_user.set_pwd(password)
            db.session.add(new_user)
            db.session.flush()

            # 如果提交的表单有头像图片且在允许格式中
            if form.get('avatar'):
                img = Image(name=form.get('avatar'), uploader=new_user, is_avatar=True)
                db.session.add(img)
        db.session.commit()

        return make_response({'msg': '注册成功'}, code=200)
    except Exception as e:
        # 事务回滚，防止注册出错都进行存储
        import traceback
        logger.error(traceback.format_exc())
        logger.error(e)
        db.session.rollback()
        return make_response({'err': '服务器错误，注册失败'}, code=500)


@auth_bp.route('/auth/set-avatar', methods=['POST'])
@token_required
def set_avatar(current_user):
    try:
        if 'file' not in request.files:
            return make_response({'err': 'image part not found.'}, code=400)
        
        file = request.files['file']
        if not allowed_img(file.filename):
            return make_response({'err': '仅支持PNG/JPG/JPEG/GIF格式'}, code=400)
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid4().hex}.{ext}"
        file.save(join(current_app.config['UPLOAD_FOLDER'], filename))

        Image.set_avatar(filename, current_user)
        return make_response({'filename': filename}, code=201)

    except Exception as e:
        logger.error(e)
        db.session.rollback()
        return make_response({'err': '服务器错误'}, code=500)


@auth_bp.route('/auth/login', methods=['POST'])
def login():
    try:
        form = request.get_json()
        username = form.get('username')
        password = form.get('password')

        user = User.query.filter_by(username=username).first()
        if not user:
            return make_response({'err': '用户不存在'}, code=400)
        if user.check_login_lock():
            # 还需要补充计时逻辑
            return make_response({'err': '密码错误次数已达上限，限制登入一分钟'}, code=400)
        if not user.check_pwd(password):
            # 用户密码报错就进行登陆错误记录
            user.increment_login_failed_cnt()
            db.session.commit()
            return make_response({'err': '密码错误'}, code=400)
        access_token = generate_jwt_token(user.id, current_app.config['JWT_ACCESS_EXPIRES'])
        logger.info(f'生成的token：{access_token}')
        refresh_token = generate_refresh_token(user.id, current_app.config['JWT_REFRESH_EXPIRES'])
        logger.info(f'生成的refreshToken：{refresh_token}')
        avatar = user.imgs.filter_by(is_avatar=True).first()
        return make_response({
            'token': access_token, 
            'refreshToken': refresh_token,
            'userInfo': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'avatar': avatar.name if avatar else '',
                    'posts': user.posts.count(),
                },
            }, code=200)
    except Exception as e:
        import traceback
        logger.error(traceback.format_exc())
        logger.error(e)
        return make_response({'err': '服务器错误'}, code=500)
    

@auth_bp.route('/logout', methods=['GET'])
@token_required
def logout(current_user):
    try:
        current_user.update_last_login()
        return make_response({'last_activity': current_user.last_login.isoformat()}, code=200)
    except Exception as e:
        import traceback
        logger.error(traceback.format_exc())
        return make_response({'err': '服务器错误'}, code=500)


# 针对注册图片的上传
@auth_bp.route('/upload-img', methods=['POST'])
def save_img():
    try:
        if 'image' not in request.files:
            return make_response({'err': 'image part not found.'}, code=400)
        
        file = request.files['image']
        if not allowed_img(file.filename):
            return make_response({'err': '仅支持PNG/JPG/JPEG/GIF格式'}, code=400)
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid4().hex}.{ext}"
        file.save(join(current_app.config['UPLOAD_FOLDER'], filename))

        return make_response({'filename': filename}, code=201)
    except Exception as e:
        logger.error(e)
        return make_response({'err': '服务器错误'}, code=500)
    

@auth_bp.route('/img/<int:id>', methods=['DELETE'])
@token_required
def delete_img(current_user, id):
    try:
        img = Image.query.get(id)
        if not img:
            return make_response({'err': 'image not found.'}, 404)
        
        if img.user_id != current_user.id:
            return make_response({'err': '你无权操作这个图片'}, 403)
        
        name = img.name
        p = join(current_app.config['UPLOAD_FOLDER'], name)
        remove(p)
        
        db.session.delete(img)
        db.session.commit()

        return make_response({'msg': '文件已删除'}, code=201)
    except Exception as e:
        logger.error(e)
        db.session.rollback()
        return make_response({'err': '服务器错误'}, code=500)
    

@auth_bp.route('/auth/upload-img', methods=['POST'])
@token_required
def upload_img(current_user):
    try:
        if 'image' not in request.files:
            return make_response({'err': 'image part not found.'}, code=400)
        
        file = request.files['image']
        if not allowed_img(file.filename):
            return make_response({'err': '仅支持PNG/JPG/JPEG/GIF格式'}, code=400)
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid4().hex}.{ext}"
        file.save(join(current_app.config['UPLOAD_FOLDER'], filename))

        with db.session.begin_nested():
            img = Image(name=filename, uploader=current_user)
            db.session.add(img)
        db.session.commit()
        return make_response({'filename': filename}, code=201)
    except Exception as e:
        logger.error(e)
        db.session.rollback()
        return make_response({'err': '服务器错误'}, code=500)
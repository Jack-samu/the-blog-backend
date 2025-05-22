from flask import Blueprint, jsonify, request, Response, current_app

from datetime import datetime
from random import choice
from email.mime.text import MIMEText
from uuid import uuid4
from loguru import logger
from os.path import join
from jwt import ExpiredSignatureError, InvalidTokenError, decode

from app.extensions import db
from app.utils.auth import generate_reset_token, token_required, generate_jwt_token, generate_refresh_token, verify_token
from app.utils.emails import send_msg

from app.article.model import Image
from .model import User


auth_bp = Blueprint('auth', __name__)

verification_codes = {}

def allowed_img(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}


# 验证码获取
@auth_bp.route('/auth/getcode', methods=['POST'])
def send():
    form = request.get_json()
    username = form.get('username')
    email = form.get('email')

    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'err': '用户不存在，检查是否输入错误'}), 400
    if user.email != email:
        return jsonify({'err': '用户邮箱不正确，检查是否为该邮箱'}), 400
    # 刚发送还没1分钟，让老子停一下
    msg = verification_codes.get(username)
    if msg and (datetime.now() - msg['sent_at']).total_seconds() < 60:
        return jsonify({'err': '请稍等，发送完还没一分钟'}), 429
    
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
        logger.info(msg)
        return jsonify({'msg': '验证码已发送'}), 200
    else:
        return jsonify({'err': '验证码发送失败，请重试'}), 500


@auth_bp.route('/auth/verify', methods=['POST'])
def verify():
    form = request.get_json()
    username = form.get('username')
    code = form.get('verificationCode')

    # 邮箱验证码校验
    msg = verification_codes.get(username)
    if not msg:
        return jsonify({'err': '服务器错误，请重试'}), 500
    # 超过5分钟了
    if (datetime.now() - msg['sent_at']).total_seconds() > 60 * 3:
        del verification_codes[username]
        return jsonify({'err': '验证码已过期，请重新发送验证码'}), 400
    if msg['code'] != code:
        return jsonify({'err': '验证码错误，请检查'}), 400
    
    # 身份校验通过
    email = verification_codes[username]['email']
    user = User.query.filter_by(username=username, email=email)
    token = generate_reset_token(user)
    uuid = str(uuid4())
    resset_link = f'http://192.168.1.10:8088/auth/reset/{token}/{uuid}'
    msg = MIMEText(f'{username}，你好，请点击以下链接进行密码重设：{resset_link}，有效期为5分钟')

    if send_msg(email, msg):
        del verification_codes[username]
        return jsonify({'msg': '校验通过，密码重设链接已发送到邮箱'}), 200
    else:
        return jsonify({'err':'服务器错误，请重试'}), 500
    

@auth_bp.route('/auth/reset/<string:token>/<string:uuid>', methods=['GET', 'POST'])
def reset(token, uuid):
    # 校验token
    try:
        data = decode(token, current_app.config['JWT_SECRET_KEY'], algorithm=['HS256'])

        if request.method == 'POST':
            
            db.session.begin()
            user = User.query.get(data['id'])

            form = request.form
            new_password = form.get('password')
            pwd_confirm = form.get('pwdRepeat')

            if new_password != pwd_confirm:
                return jsonify({'err': '密码不一致'}), 400
            if len(new_password) < 8:
                return jsonify({'err': '密码长度需要大于8'}), 400
            if user.check_pwd(new_password):
                return jsonify({'err': '恭喜你，想起了以前的密码了，就是这个'}), 400
            import re
            if not re.search(r'[a-zA-Z]', new_password) or not re.search(r'\d', new_password):
                return jsonify({'err': '密码至少包含一个字母和一个数字'}), 400
            user.set_pwd(new_password)
            db.session.commit()
            return jsonify({'code': 200, 'msg': '密码已重置'}), 200
        else:
            return Response('''
            <form method="post">
                <input type="password" name="password" placeholder="输入新密码" required />
                <input type="password" name="pwdRepeat" placeholder="确认新密码" required />
                <input type="submit" value="重置密码">                   
            </form>
            ''', mimetype='text/html')
        
    except ExpiredSignatureError:
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'err': '刷新token已过期'}), 401
    except InvalidTokenError as e:
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'err': '刷新token不合法'}), 401
    except Exception as e:
        # 事务回滚，防止注册出错都进行存储
        import traceback
        logger.error(traceback.format_exc())
        logger.error(e)
        db.session.rollback()
        return jsonify({'err': '服务器错误，注册失败'}), 500


# 刷新token
@auth_bp.route('/auth/refresh', methods=['POST'])
def refresh_the_token():
    try:
        logger.info(request.headers.get('Authorization', ''))
        refresh_token = request.headers.get('Authorization', '').replace('Bearer ', '').strip()
        if not refresh_token:
            return jsonify({'err': '刷新token缺失'}), 401
        id = verify_token(refresh_token)
        user = User.query.get(id)
        new_token = generate_jwt_token(id, current_app.config['JWT_ACCESS_EXPIRES'])
        new_refresh_token = generate_refresh_token(id, current_app.config['JWT_REFRESH_EXPIRES'])
        return jsonify({
            'token': new_token,
            'refreshToken': new_refresh_token,
            'userInfo': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'avatar': user.get_avatar().name,
                    'posts': user.articles.count()
                },
        }), 201
    except ExpiredSignatureError:
        return jsonify({'err': '刷新token已过期'}), 401
    except InvalidTokenError as e:
        logger.info(e)
        return jsonify({'err': '刷新token不合法'}), 401
    except Exception as e:
        return jsonify({'err': '服务器出错'}), 500
    

# 带有头像上传的数据，格式为multipart/form-data
@auth_bp.route('/auth/register', methods=['POST'])
def register():
    try:
        form = request.get_json()
        if form is None:
            return jsonify({'err': '注册表单为空'}), 400
        
        username = form.get('username')
        password = form.get('password')
        email = form.get('email')

        # 针对非前台表单
        if not all([username, password, email]):
            return jsonify({'err': '用户名、密码和邮箱为必需项'}), 400

        # 重置会话
        db.session.rollback()

        if User.query.filter_by(username=username).first():
            return jsonify({'err': '用户已存在'}), 400
        if User.query.filter_by(email=email).first():
            return jsonify({'err': '注册邮箱已存在'}), 400

        if not username or not password or not email:
            return jsonify({'err': '参数缺失，请检查'}), 400

        with db.session.begin_nested():
            new_user = User(username=username, email=email)
            new_user.set_pwd(password)

            # 如果提交的表单有头像图片且在允许格式中
            if form.get('avatar'):
                avatar = Image(name=form.get('avatar'), is_avatar=True, user_id=new_user.id)
                new_user.imgs.append(avatar)

            db.session.add(new_user)

        return jsonify({'msg': '注册成功'}), 200
    except Exception as e:
        # 事务回滚，防止注册出错都进行存储
        import traceback
        logger.error(traceback.format_exc())
        logger.error(e)
        db.session.rollback()
        return jsonify({'err': '服务器错误，注册失败'}), 500


@auth_bp.route('/auth/set-avatar', methods=['POST'])
@token_required
def set_avatar(current_user):
    try:
        if 'image' not in request.files:
            return jsonify({'err': 'image part not found.'}), 400
        
        file = request.files['image']
        if not allowed_img(file.filename):
            return jsonify({'err': '仅支持PNG/JPG/JPEG/GIF格式'}), 400
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid4().hex}.{ext}"
        file.save(join(current_app.config['UPLOAD_FOLDER'], filename))

        with db.session.begin_nested():
            img = current_user.get_avatar()
            if img:
                img.is_avatar = False
            # 更换操作Image
            img = Image(name=filename, is_avatar=True, user_id=current_user.id)
            db.session.add(img)
        return jsonify({'filename': filename}), 201

    except Exception as e:
        logger.error(e)
        db.session.rollback()
        return jsonify({'err': '服务器错误'}), 500


@auth_bp.route('/auth/login', methods=['POST'])
def login():
    try:
        form = request.get_json()
        username = form.get('username')
        password = form.get('password')

        user = User.query.filter(User.username == username).first()
        if not user:
            return jsonify({'err': '用户不存在，请检查输入'}), 400
        if not user.check_pwd(password):
            # 用户密码报错就进行登陆错误记录
            user.increment_login_failed_cnt()
            return jsonify({'err': '密码错误'}), 400
        access_token = generate_jwt_token(user.id, current_app.config['JWT_ACCESS_EXPIRES'])
        logger.info(f'生成的token：{access_token}')
        refresh_token = generate_refresh_token(user.id, current_app.config['JWT_REFRESH_EXPIRES'])
        logger.info(f'生成的refreshToken：{refresh_token}')
        return jsonify({
            'token': access_token, 
            'refreshToken': refresh_token,
            'userInfo': {
                    'user_id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'avatar': user.get_avatar().name,
                    'posts': user.articles.count(),
                },
            },
        ), 200
    except Exception as e:
        import traceback
        logger.error(traceback.format_exc())
        logger.error(e)
        return jsonify({'err': '服务器错误'}), 500
    

@auth_bp.route('/logout', methods=['POST'])
@token_required
def logout(current_user):
    try:
        current_user.update_last_login()
        return jsonify({'last_activity': current_user.last_login}), 200
    except Exception as e:
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'err': '服务器错误'}), 500


# 只进行照片的保存
@auth_bp.route('/upload-img', methods=['POST'])
def save_img():
    try:
        logger.info(request.files)
        if 'image' not in request.files:
            return jsonify({'err': 'image part not found.'}), 400
        
        file = request.files['image']
        if not allowed_img(file.filename):
            return jsonify({'err': '仅支持PNG/JPG/JPEG/GIF格式'}), 400
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid4().hex}.{ext}"
        file.save(join(current_app.config['UPLOAD_FOLDER'], filename))
        return jsonify({'filename': filename}), 201
    except Exception as e:
        logger.error(e)
        return jsonify({'err': '服务器错误'}), 500
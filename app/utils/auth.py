import jwt
from flask import current_app, request
from datetime import datetime, timedelta,timezone
from functools import wraps
from loguru import logger

from app.models import User


# 临时链接用的token操作
def generate_reset_token(user: User):
    logger.info(user)
    payload = {
        'id': user.id,
        'exp': datetime.now(timezone.utc) + timedelta(minutes=5)
    }
    return jwt.encode(payload, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')

# 默认1小时
def generate_jwt_token(user_id, expires_in):
    payload = {
        'sub': user_id,
        'exp': datetime.now(timezone.utc) + expires_in,
        'iat': datetime.now(timezone.utc)
    }
    logger.info(payload['exp'])
    logger.info(payload['iat'])

    token = jwt.encode(payload=payload, key=current_app.config['JWT_SECRET_KEY'], algorithm='HS256')

    return token

# refresh-token刷新时间为一天
def generate_refresh_token(user_id, expires_in):
    return generate_jwt_token(user_id, expires_in)

# jwt-token校验，校验通过就返回user_id
def verify_token(token):
    logger.info(f"需要校验的token:{token}")
    payload = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
    return payload['sub']

def get_current_user():
    try:
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return None
        user_id = verify_token(token)
        current_user = User.query.get(user_id)
        if not current_user:
            return None
        logger.info(current_user)
        return current_user
    except jwt.ExpiredSignatureError:
        logger.info('token过期')
        return None
    except jwt.InvalidTokenError:
        logger.info('token非法')
        return None
    except Exception as e:
        logger.error(str(e))
        return None
    
def token_optional(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        current_user = get_current_user()
        return f(current_user, *args, **kwargs)
    return decorated

# token校验装饰器
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        current_user = get_current_user()
        if not current_user:
            return {'err': '认证信息缺失或无效'}, 401
        
        return f(current_user, *args, **kwargs)
    return decorated
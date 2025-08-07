import smtplib
import jwt
from flask import current_app, request, Response
from json import dumps

from datetime import datetime, timedelta,timezone
from loguru import logger
from threading import Lock

from app.models import User


class SafeDict:
    def __init__(self):
        self._data = {}
        self._lock = Lock()

    def set(self, key, value):
        with self._lock:
            self._data[key] = value

    def get(self, key):
        with self._lock:
            return self._data.get(key)
        
    def delete(self, key):
        with self._lock:
            if key in self._data:
                del self._data[key]
                return True
            return False


# 临时链接用的token操作
def generate_reset_token(user: User):
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
            logger.error(user_id)
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


def make_response(data, code=None, type='application/json'):
    resp = Response(dumps(data, ensure_ascii=False),mimetype=type)
    if code:
        resp.status_code = code
    return resp


# 发送邮箱验证码
def send_msg(email, msg):
    try:
        # 邮件操作
        msg = msg
        msg['Subject'] = '邮箱验证码'
        msg['From'] = current_app.config['MAIL_USERNAME']
        msg['To'] = email

        with smtplib.SMTP(current_app.config['MAIL_SERVER'], current_app.config['MAIL_PORT']) as server:
            server.starttls()
            server.login(current_app.config['MAIL_USERNAME'], current_app.config['MAIL_PASSWORD'])
            server.send_message(msg)
        return True
    except Exception as e:
        current_app.logger.error(str(e))
        return False
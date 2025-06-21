from flask import request
from functools import wraps
from html import escape

from app.utils.util import make_response


def validate_data(required_fields=None):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            data = request.get_json()
            if not data:
                return make_response({'err': '请求类型数据非json，检查请求Content-type或表单'}, 400)
            
            required = set(required_fields or [])
            if 'content' in required and 'content' not in data:
                required.add('content')
            
            missing = [f for f in required if f not in data]
            if missing:
                return make_response({'err': f'缺少必需字段：{", ".join(missing)}"'}, 400)
            
            # 敏感字段处理
            sensitive_fields = ['title', 'excerpt', 'content']
            for key in sensitive_fields:
                if key in data and isinstance(data[key], str):
                    data[key] = data[key]
            
            return f(*args, **kwargs, data=data)
        return wrapper
    return decorator
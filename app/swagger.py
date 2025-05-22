from flask_restx import Api, fields

authorizations = {
    'Bearer Auth': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization',
        'description': "输入格式：Bearer {token}"
    }
}

api = Api(
    title='Blog API',
    version='1.0',
    description='全栈博客系统后台API文档',
    authorizations=authorizations,
    security='Bearer Auth'
)

# 通用响应模型
error_model = api.model('Error', {
    'err': fields.String(description='错误信息')
})

pagination_model = api.model('Pagination', {
    'total': fields.Integer,
    'page': fields.Integer,
    'per_page': fields.Integer
})
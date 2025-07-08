import pytest
from faker import Faker
from app.models import User



class TestAuth:
    def test_register(self, clnt, session):
        f = Faker('zh-CN')
        pwd = f.password()
        data = {
            'username': f.name(),
            'email': f.email(),
            'password': pwd,
            'bio': f.sentence()
        }

        resp = clnt.post('/auth/register', json=data)
        assert resp.status_code == 201
        assert User.query.filter_by(username=data['username']).first() is not None

    def test_login(self, clnt, session):
        user = User(username='你猜', email='guest@what.com')
        user.set_pwd('GuestWhat123')
        session.add(user)
        session.commit()

        data = {
            'username': '你猜',
            'password': 'GuestWhat123'
        }
        
        resp = clnt.post('/auth/login', json=data)
        assert resp.status_code == 200
        assert 'token' in resp.json

        token = resp.json['token']
        refreshToken = resp.json['refreshToken']

        clnt.environ_base['HTTP_AUTHORIZATION'] = f'Bearer {token}'
        resp = clnt.get(f'/auth/{user.id}/profile')
        assert resp.status_code == 200
        assert 'user' in resp.json

        # 密码修改
        data = {
            'pwd': 'aaaabbbb',
            'pwdConfirm': 'aaaabbbb'
        }
        resp = clnt.post('/auth/resetpwd', json=data)
        assert resp.status_code == 201
        user = User.query.get(user.id)
        assert user.check_pwd('aaaabbbb')

        # 忘记密码逻辑

        # token刷新逻辑
        clnt.environ_base['HTTP_AUTHORIZATION'] = f'Bearer {refreshToken}'
        resp = clnt.post('/auth/refresh')
        assert resp.status_code == 201
        assert 'token' in resp.json
        assert 'refreshToken' not in resp.json

        # 退出
        resp = clnt.get('/logout')
        assert resp.status_code == 200
        clnt.environ_base['HTTP_AUTHORIZATION'] = ''
        resp = clnt.get(f'/auth/{user.id}/profile')
        assert resp.status_code == 401
        
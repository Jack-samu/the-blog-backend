import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from app import create_app
from app.extensions import db as _db


# 固定参数
@pytest.fixture(scope='session')
def app():
    # 创建测试用Flask实例
    app = create_app('testing')
    # create_app中包含了创表操作，所以不用进行创表了
    with app.app_context():
        yield app


@pytest.fixture(scope='session')
def db(app):
    # 提供用于测试用例的会话，方便独立不干涉
    _db.app = app
    _db.create_all()
    yield _db
    _db.drop_all()


@pytest.fixture(scope='function')
def session(db):
    """为每个测试函数提供独立的事务会话"""
    connection = db.engine.connect()
    transaction = connection.begin()
    
    # 创建新的会话
    session_factory = sessionmaker(bind=connection)
    session = scoped_session(session_factory)
    
    # 替换应用默认会话
    db.session = session
    
    yield session
    
    # 清理
    session.remove()
    transaction.rollback()
    connection.close()


@pytest.fixture
def clnt(app):
    return app.test_client()


@pytest.fixture
def auth_clnt(clnt, session):
    from app.models import User
    from app.utils import generate_jwt_token
    from faker import Faker

    f = Faker()

    user = User(username=f.name(), email=f.email())
    user.set_pwd(f.password())
    session.add(user)
    session.commit()

    from datetime import timedelta
    token = generate_jwt_token(user.id, timedelta(hours=1))
    clnt.environ_base['HTTP_AUTHORIZATION'] = f'Bearer {token}'
    return clnt
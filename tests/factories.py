import factory
from factory.alchemy import SQLAlchemyModelFactory
from app.models import User, Post, Draft
from app.extensions import db



class UserFactory(SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session = db.session

    username = factory.Sequence(lambda n: f'user_{n}')
    email = factory.Sequence(lambda n: f'user_{n}@test.com')
    password = factory.PostGenerationMethodCall('set_pwd', 'test1234')


class PostFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Post
        sqlalchemy_session = db.session
    
    title = factory.Faker('sentence')
    excerpt = factory.Faker('sentence')
    content = factory.Faker('text')
    author = factory.SubFactory(UserFactory)
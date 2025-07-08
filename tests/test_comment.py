import pytest
from faker import Faker
from app.models import Post, Comment, Reply


class TestComment:
    def test_comment(self, clnt, auth_clnt, session):
        
        f = Faker('zh-CN')
        data = {
            'title': f.sentence(),
            'content': f.text(max_nb_chars=200),
            'excerpt': f.sentence(),
            'category' : f.word(),
            'tags': f.words()
        }

        resp = auth_clnt.post('/articles/publish', json=data)
        assert resp.status_code == 201
        article_id = resp.json['id']

        # comment 添加
        data = {
            'article_id': article_id,
            'content': f.text(max_nb_chars=50)
        }
        resp = auth_clnt.post('/articles/comments', json=data)
        assert resp.status_code == 201
        assert Comment.query.count() == 1
        comment_id = resp.json['comment']['id']

        # reply添加
        data = {
            'comment_id': comment_id,
            'content': f.text(max_nb_chars=50)
        }
        resp = auth_clnt.post('/comments/replies', json=data)
        assert resp.status_code == 201
        assert Reply.query.count() == 1
        reply_id = resp.json['reply']['id']

        # 点赞
        data = {
            'type': 'comment',
            'id': comment_id
        }
        resp = auth_clnt.post('/comments/likes', json=data)
        assert resp.status_code == 201

        resp = auth_clnt.get(f'/articles/{article_id}/comments')
        assert resp.status_code == 200
        assert resp.json['comments'][0]['is_liked'] == True
        assert resp.json['comments'][0]['replies'] == 1

        resp = auth_clnt.get(f'/comments/{comment_id}/replies')
        assert resp.status_code == 200
        assert resp.json['replies'][0]['is_liked'] == False
        assert resp.json['total'] == 1

        # 修改操作
        data = {
            'comment_id': comment_id,
            'content': 'testtest'
        }
        resp = auth_clnt.post('/comments/modify', json=data)
        assert resp.status_code == 201
        assert resp.json['comment']['content'] == 'testtest'

        # 删除操作
        resp = auth_clnt.delete(f'/replies/{reply_id}')
        assert resp.status_code == 201
        resp = clnt.get(f'/comments/{comment_id}/replies')
        assert resp.json['total'] == 0

        resp = auth_clnt.delete(f'/articles/{article_id}')
        assert resp.status_code == 201
        assert Comment.query.count() == 0

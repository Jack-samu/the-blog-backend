import pytest
from faker import Faker
from app.models import Post, Draft, Category



class TestArticle:
    def test_save_draft(self, auth_clnt, session):
        f = Faker()
        data = {
            'title': f.sentence(),
            'content': f.text(max_nb_chars=200),
            'excerpt': f.sentence()
        }
        
        resp = auth_clnt.post('/articles/save', json=data)
        assert resp.status_code == 201
        assert Draft.query.count() == 1

        # 继续保存草稿，不过是添加更多细节
        data['id'] = resp.json.get('id')
        data['category'] = f.word()
        data['tags'] = f.words()
        resp = auth_clnt.post('/articles/save', json=data)
        assert resp.status_code == 201
        assert Draft.query.count() == 1

        # 草稿获取
        resp = auth_clnt.get('/articles/draft')
        assert resp.status_code == 200
        assert len(resp.json['drafts']) == 1

        # 已发表获取
        resp = auth_clnt.get('/articles/publish')
        assert resp.status_code == 200
        assert len(resp.json['publishedArticles']) == 0

    def test_publish_article(self, clnt, auth_clnt, session):

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
        assert Post.query.count() == 1

        resp = auth_clnt.get(f'/articles/{resp.json['id']}')
        assert resp.status_code == 200
        assert resp.json['article']['title'] == data['title']

        # 草稿获取
        resp = auth_clnt.get('/articles/draft')
        assert resp.status_code == 200
        assert len(resp.json['drafts']) == 0

        resp = auth_clnt.get('/articles/publish')
        assert resp.status_code == 200
        assert len(resp.json['publishedArticles']) == 1

        # 文章列表
        resp = clnt.get('/articles')
        assert resp.status_code == 200
        assert len(resp.json['articles']) == 1
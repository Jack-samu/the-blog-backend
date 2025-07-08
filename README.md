# Flask 博客后台系统架构文档

## 系统概述

基于 Flask 的 RESTful API 服务，为博客应用提供完整的数据存储和业务逻辑处理能力，支持文章管理、用户认证、评论互动等核心功能。

## 架构设计

### 分层架构

| 层级 | 模块 | 职责 | 关键组件 |
|------|------|------|----------|
| **表示层** | 路由蓝图 | 接收HTTP请求，返回JSON响应 | AuthBlueprint, ArticleBlueprint, CommentBlueprint |
| **服务层** | 业务服务 | 处理核心业务逻辑 | ArticleService |
| **数据层** | 数据模型 | 数据持久化与访问 | Article, User, Comment, Tag, Category |
| **核心模块** | 基础组件 | 提供系统基础能力 | Config, Extensions, Hooks |

### 核心模块说明

#### 1. 配置管理 (`config.py`)
- 多环境支持：开发/测试/生产环境独立配置
- 敏感信息通过环境变量加载
- 数据库连接、JWT密钥、邮件服务等全局配置

#### 2. 扩展集成 (`extensions.py`)
- 统一管理第三方扩展初始化：
  - Flask-SQLAlchemy (数据库ORM)
  - Flask-Migrate (数据库迁移)
  - Flask-Cors (跨域请求)

#### 3. 请求拦截 (`hooks.py`)
- 认证拦截器：JWT令牌验证(todo but accomplish in another way)
- 请求日志记录
- 异常统一处理(todo)
- 命令自定义

#### 4. 数据库事件 (`events.py`)
- 图片清理
- 栏目和标签清理

## 数据模型设计

```mermaid
erDiagram
    User ||--o{ Article : "author"
    User ||--o{ Category : "owns"
    User ||--o{ Comment : "writes"
    
    Article ||--|{ Tag : "tags"
    Article ||--o{ Category : "belongs_to"
    Article ||--o{ Comment : "has"
    
    Comment ||--o{ Reply : "has_replies"
    Reply ||--o{ User : "reply_to"
```

## 关键业务流程

### 文章发布流程
```mermaid
sequenceDiagram
    participant Client
    participant ArticleAPI
    participant ArticleService
    participant DB
    
    Client->>ArticleAPI: POST /articles (with draft data)
    ArticleAPI->>ArticleService: publish(draft_id)
    ArticleService->>DB: 创建PublishedArticle记录
    ArticleService->>DB: 删除Draft记录
    ArticleService->>DB: 更新关联标签
    DB-->>ArticleService: 操作结果
    ArticleService-->>ArticleAPI: 发布结果
    ArticleAPI-->>Client: 201 Created
```

### 认证流程
```mermaid
sequenceDiagram
    participant Client
    participant AuthAPI
    participant AuthService
    participant DB
    
    Client->>AuthAPI: POST /auth/login (credentials)
    AuthAPI->>AuthService: authenticate(email, password)
    AuthService->>DB: 验证用户凭证
    alt 验证成功
        DB-->>AuthService: 用户数据
        AuthService->>AuthService: 生成访问令牌
        AuthService-->>AuthAPI: 令牌+用户数据
        AuthAPI-->>Client: 200 OK (with tokens)
    else 验证失败
        DB-->>AuthService: 错误
        AuthService-->>AuthAPI: 错误
        AuthAPI-->>Client: 401 Unauthorized
    end
```

## 部署指南

### 开发环境配置
```bash
# 克隆仓库
git clone https://github.com/Jack-samu/the-blog-backend.git
cd the-blog-backend

# 安装依赖
sudo pip3 install pipenv
pipenv install
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# mysql容器服务配置
sudo docker run -d --restart=unless-stopped \
  -p 3306:3306 \
  -v $(pwd)/db/init.sql:/docker-entrypoint-initdb.d/init.sql \
  --name mysql_service \
  -e MYSQL_ROOT_PASSWORD=123456 \
  -e TZ=Asia/Shanghai \
  mysql:8.0 \
  --character-set-server=utf8mb4 \
  --collation-server=utf8mb4_unicode_ci \
  --default-authentication-plugin=mysql_native_password

# 环境变量配置 (创建.env文件)
echo "FLASK_ENV=development" >> .env
echo "mysql+pymysql://guest:Guest123%40@localhost:3306/course?charset=utf8mb4&connect_timeout=20" >> .env
# 这里配置你的smtp服务，笔者用的是网易邮箱开放的，随便注册一个邮箱然后设置好就行
echo "MAIL_SERVER=your_smtp_server"
echo "MAIL_USERNAME=your_email_name"
echo "MAIL_PASSWORD=your_token"
echo "MAIL_PORT=your_smtp_service_port"

# 数据库初始化
flask db init
flask db migrate
flask db upgrade

# 初始化一些数据进去
sudo docker exec -it mysql_service mysql -u root -p123456 course < db/blog_data.sql

# 启动服务，密码重置链接会有局域网下外部主机访问需要，如果你用手机访问的话
flask run --host 0.0.0.0 --port 8088
```

### 生产环境部署 (Docker)
1. 创建Dockerfile
```dockerfile
FROM python:3.9

WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV FLASK_APP=run.py
ENV FLASK_ENV=production

# 如果需要，就进行容器内apt镜像添加，从而进行加速
RUN echo "deb http://mirrors.aliyun.com/debian/ bookworm main contrib non-free non-free-firmware" > /etc/apt/sources.list
RUN echo "deb http://mirrors.aliyun.com/debian/ bookworm-updates main contrib non-free non-free-firmware" >> /etc/apt/sources.list
RUN echo "deb http://mirrors.aliyun.com/debian-security bookworm-security main contrib non-free non-free-firmware" >> /etc/apt/sources.list
# 对原有apt源进行备份，也踢出apt源队列，防止update操作受其影响
RUN mv /etc/apt/sources.list.d/ /etc/apt/sources.list.d.bak

# 安装系统依赖
RUN pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple --upgrade pip

COPY requirements.txt .
RUN pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple -r requirements.txt 

# 环境配置
RUN echo "FLASK_ENV=development" >> .env
RUN echo "DATABASE_URI=mysql+pymysql://guest:Guest123%40@mysql_service:3306/course?charset=utf8mb4&connect_timeout=20" >> .env
# 这里配置你的smtp服务，笔者用的是网易邮箱开放的，随便注册一个邮箱然后设置好就行
RUN echo "MAIL_SERVER=your_smtp_server" >> .env
RUN echo "MAIL_USERNAME=your_email" >> .env
RUN echo "MAIL_PASSWORD=your_smtp_service_token" >> .env
RUN echo "MAIL_PORT=the_port" >> .env

# 复制项目文件（排除.dockerignore中指定的文件）
COPY . .

# 数据库初始化
RUN flask db init
RUN flask db migrate
RUN flask db upgrade
RUN mysql -hmysql_service -p 3306 -uroot -p123456 course < db/blog_data.sql

EXPOSE 8088
CMD ["flask", "run", "--host", "0.0.0.0", "--port", "8088"]
```

2. 构建并运行
```bash
# 在build这个backend镜像之前先准备好mysql服务
sudo docker run -d --restart=unless-stopped \
  -p 3306:3306 \
  -v $(pwd)/db/init.sql:/docker-entrypoint-initdb.d/init.sql \
  --name mysql_service \
  -e MYSQL_ROOT_PASSWORD=123456 \
  -e TZ=Asia/Shanghai \
  mysql:8.0 \
  --character-set-server=utf8mb4 \
  --collation-server=utf8mb4_unicode_ci \
  --default-authentication-plugin=mysql_native_password

# 创建flask后台服务image，喜欢的话也可以直接在Dockerfile中把mysql给一起添加进去，
# 省去外部创建mysql容器
sudo docker build -t backend .

# 创建flask-backend服务
sudo docker run -d --name flask-backend --link mysql_service:mysql -p 8088:8088 backend
```

## 系统特性

1. **完善的认证体系**
   - JWT令牌认证
   - 令牌自动刷新
   - 权限分级控制

2. **内容管理能力**
   - 草稿/发布双状态管理
   - 分类与标签系统

## 架构演进路线

1. **短期优化**
   - 增加Redis缓存层
   - 实现API限流机制
   - 完善监控指标

2. **中期规划**
   - 引入Celery异步任务队列
   - 支持多用户架构
   - 增加全文搜索功能

3. **长期愿景**
   - 微服务化拆分
   - 实现Serverless部署
   - 支持国际化和多语言

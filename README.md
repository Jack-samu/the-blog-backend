# Blog Backend

基于 Flask 的 RESTful API 服务，提供blog应用的数据存储和业务逻辑处理。

## 整体架构

这个Flask后台采用Blueprint模块化设计，分为三个主要模块：
* `auth.py` - 用户认证与个人资料管理
  ### 核心功能
  - 用户注册/登录/登出
  - 密码重置流程
  - JWT token刷新
  - 头像管理
  - 用户资料获取
  #### 亮点设计
    ```
    密码重置流程采用三阶段验证
    1. 发送验证码 -> 2. 验证码校验 -> 3. 重置链接
    ```
* `article.py` - 文章内容管理
  ### 核心功能
  - 文章CRUD
  - 草稿管理
  - 分类/标签管理
  - 文章点赞

* `comment.py` - 评论互动系统
  #### 核心功能
  - 多级评论系统
  - 评论点赞
  - 评论管理

## 现有数据结构
```mermaid
erDiagram
    User ||--o{ Article : "撰写"
    User ||--o{ Category : "创建"
    User ||--o{ Image : "上传"
    User ||--o{ Comment : "发表"
    User ||--o{ Reply : "发表"
    
    Article ||--o{ Category : "归属"
    Article ||--|| article_tags : "标记"
    Article ||--|{ Comment : "包含"
    Article ||--|{ Reply : "包含"
    
    Comment ||--o{ Article : "属于"
    Comment ||--|{ Reply : "包含"
    
    Reply ||--o{ Article : "属于"
    Reply ||--o{ Comment : "属于"
    Reply ||--|{ Reply : "回复"
    
    article_tags ||--o{ Tag : "标签"
```

## 已完成接口
| 模块       | 端点示例                  | 方法   | 描述                     |
|------------|---------------------------|--------|--------------------------|
| 用户认证   | `/auth/login`             | POST   | JWT 令牌签发             |
| 文章管理   | `/articles/{id}/comments` | GET    | 获取文章评论列表         |
| 文件上传   | `/upload/image`           | POST   | 头像/封面图上传          |

目前已实现的功能模块包含用户auth、文章article和评论comment。

## 部署指南
```bash
git clone https://github.com/Jack-samu/the-blog-backend.git

cd the-blog-backend
# 依赖安装
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 事先创建对应文件夹
sudo mkdir /opt/service
sudo mkdir /opt/service/mysql
sudo mkdir /opt/service/mysql/conf /opt/service/mysql/logs /opt/service/mysql/data

# 假定已经按照配置可用docker
sudo docker run -d --restart=unless-stopped \
  -p 3306:3306 \
  -p 33060:33060 \
  -v /opt/service/mysql/conf:/etc/mysql/conf.d \
  -v /opt/service/mysql/logs:/var/log/mysql \
  -v /opt/service/mysql/data:/var/lib/mysql \
  -v $(pwd)/init.sql:/docker-entrypoint-initdb.d/init.sql \
  --name mysql_service \
  -e MYSQL_ROOT_PASSWORD=123456 \
  -e MYSQL_DATABASE=course \
  -e MYSQL_USER=guest \
  -e MYSQL_PASSWORD=Guest123@ \
  mysql:8.0 \
  --character-set-server=utf8mb4 \
  --collation-server=utf8mb4_unicode_ci \
  --default-authentication-plugin=mysql_native_password
```

各种密钥都是在自定义.env中，只消配上对应邮箱配置和数据库配置即可，不多。

```bash
# 数据库初始化
flask db init
flask db migrate
flask db upgrade

# 数据库预操作，创建admin和已注销用户
flask init-db

# 针对用户密码修改的情况
flask run --host --port=8088 --debug
```

## 操作流程注
用户注销流程
```mermaid
sequenceDiagram
    participant Client
    participant Controller
    participant User
    participant Comment
    participant Reply
    
    Client->>Controller: 删除用户请求
    Controller->>User: delete_user(user_id)
    User->>Comment: transfer_to_deleted_user
    User->>Reply: transfer_to_deleted_user
    Comment->>DB: 批量UPDATE评论
    Reply->>DB: 批量UPDATE回复
    User->>DB: DELETE用户
    Controller-->>Client: 操作结果
```

token刷新流程
```mermaid
sequenceDiagram
    participant Request1
    participant Request2
    participant Interceptor
    participant AuthStore
    
    Request1->>Interceptor: 收到401
    Interceptor->>AuthStore: 开始刷新(token1)
    AuthStore-->>Interceptor: 返回刷新Promise
    
    Request2->>Interceptor: 收到401
    Interceptor->>AuthStore: 检测到已有刷新进行
    Interceptor-->>Request2: 加入等待队列
    
    AuthStore->>Backend: 刷新token
    Backend-->>AuthStore: 返回新token
    
    AuthStore->>Interceptor: 刷新完成
    Interceptor->>Request1: 用新token重试
    Interceptor->>Request2: 用新token重试
```
mysqldump: [Warning] Using a password on the command line interface can be insecure.
-- MySQL dump 10.13  Distrib 8.0.42, for Linux (x86_64)
--
-- Host: localhost    Database: course
-- ------------------------------------------------------
-- Server version	8.0.42

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Dumping data for table `alembic_version`
--

LOCK TABLES `alembic_version` WRITE;
/*!40000 ALTER TABLE `alembic_version` DISABLE KEYS */;
INSERT INTO `alembic_version` VALUES ('c5f9e976c565');
/*!40000 ALTER TABLE `alembic_version` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `categories`
--

LOCK TABLES `categories` WRITE;
/*!40000 ALTER TABLE `categories` DISABLE KEYS */;
INSERT INTO `categories` VALUES (2,'html','b465af5a-66d0-48ef-8795-786cac84d2ed'),(3,'全栈','b465af5a-66d0-48ef-8795-786cac84d2ed');
/*!40000 ALTER TABLE `categories` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `comment`
--

LOCK TABLES `comment` WRITE;
/*!40000 ALTER TABLE `comment` DISABLE KEYS */;
INSERT INTO `comment` VALUES (1,'正经测试😄',0,'2025-06-26 09:37:55','2025-06-26 09:37:55',8,'b465af5a-66d0-48ef-8795-786cac84d2ed'),(2,'正经测试x2',1,'2025-06-26 09:38:11','2025-06-26 10:58:39',8,'b465af5a-66d0-48ef-8795-786cac84d2ed');
/*!40000 ALTER TABLE `comment` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `draft_tags`
--

LOCK TABLES `draft_tags` WRITE;
/*!40000 ALTER TABLE `draft_tags` DISABLE KEYS */;
INSERT INTO `draft_tags` VALUES (9,4),(9,5);
/*!40000 ALTER TABLE `draft_tags` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `drafts`
--

LOCK TABLES `drafts` WRITE;
/*!40000 ALTER TABLE `drafts` DISABLE KEYS */;
INSERT INTO `drafts` VALUES (9,'markdown转html后代码高亮实现','html代码高亮方案','# Markdown 转换后 HTML 代码高亮美化方案 (使用 Prism.js)\n\n针对 Markdown 转换后的 HTML 代码高亮美化，特别是使用 Prism.js 进行处理，需要考虑多种情况和处理方式。以下是全面的解决方案：\n\n## 一、Markdown 中代码块的常见情况\n\n1. **标准代码块** (围栏式)\n   :::markdown\n   ```python\n   def hello():\n       print(\"Hello World\")\n   ```\n   :::\n\n2. **缩进式代码块**\n   ```markdown\n       def hello():\n           print(\"Hello World\")\n   ```\n\n3. **行内代码**\n   ```markdown\n   这是`行内代码`的例子\n   ```\n\n4. **带特殊属性的代码块** (某些 Markdown 扩展)\n   ```markdown\n   ```python {linenos highlight-lines=\"2\"}\n   def hello():\n       print(\"Hello World\")\n   ```\n   ```\n\n## 二、使用 Prism.js 的处理方案\n\n### 基础处理方式\n\n```html\n<!DOCTYPE html>\n<html>\n<head>\n  <!-- 引入 Prism.js 核心 CSS -->\n  <link href=\"https://cdn.jsdelivr.net/npm/prismjs@1.29.0/themes/prism.min.css\" rel=\"stylesheet\" />\n  \n  <!-- 引入 Prism.js 核心 JS -->\n  <script src=\"https://cdn.jsdelivr.net/npm/prismjs@1.29.0/prism.min.js\"></script>\n  \n  <!-- 引入语言支持 (按需) -->\n  <script src=\"https://cdn.jsdelivr.net/npm/prismjs@1.29.0/components/prism-python.min.js\"></script>\n  <script src=\"https://cdn.jsdelivr.net/npm/prismjs@1.29.0/components/prism-javascript.min.js\"></script>\n</head>\n<body>\n  <!-- Markdown 转换后的 HTML 内容 -->\n  <pre><code class=\"language-python\">def hello():\n      print(\"Hello World\")</code></pre>\n  \n  <!-- 初始化 Prism.js -->\n  <script>Prism.highlightAll();</script>\n</body>\n</html>\n```\n\n### 针对不同情况的处理\n\n#### 1. 标准代码块处理\n\n转换后的 HTML:\n```html\n<pre><code class=\"language-python\">def hello():\n    print(\"Hello World\")\n</code></pre>\n```\n\nPrism.js 会自动识别 `language-xxx` 类名进行高亮。\n\n#### 2. 缩进式代码块处理\n\nMarkdown 转换器可能生成:\n```html\n<pre><code>def hello():\n    print(\"Hello World\")\n</code></pre>\n```\n\n解决方案:\n- 在转换时强制添加语言类\n- 或使用 JS 自动检测:\n  ```javascript\n  document.querySelectorAll(\'pre code:not([class])\').forEach(code => {\n    code.classList.add(\'language-none\');\n  });\n  ```\n\n#### 3. 行内代码处理\n\n转换后的 HTML:\n```html\n<p>这是<code>行内代码</code>的例子</p>\n```\n\n解决方案:\n```css\n/* 为行内代码添加基本样式 */\ncode:not([class]) {\n  background: #f5f2f0;\n  padding: 0.2em 0.4em;\n  border-radius: 3px;\n  font-family: monospace;\n}\n```\n\n#### 4. 带特殊属性的代码块\n\n转换后的 HTML (需要 Markdown 解析器支持):\n```html\n<pre class=\"line-numbers\" data-line=\"2\"><code class=\"language-python\">def hello():\n    print(\"Hello World\")\n</code></pre>\n```\n\n需要额外插件:\n```html\n<!-- 引入行号插件 -->\n<link href=\"https://cdn.jsdelivr.net/npm/prismjs@1.29.0/plugins/line-numbers/prism-line-numbers.min.css\" rel=\"stylesheet\" />\n<script src=\"https://cdn.jsdelivr.net/npm/prismjs@1.29.0/plugins/line-numbers/prism-line-numbers.min.js\"></script>\n\n<!-- 引入高亮行插件 -->\n<script src=\"https://cdn.jsdelivr.net/npm/prismjs@1.29.0/plugins/highlight-keywords/prism-highlight-keywords.min.js\"></script>\n```\n\n### 三、高级处理方案\n\n#### 1. 动态加载语言\n\n```javascript\nfunction loadPrismLanguage(lang) {\n  return new Promise((resolve) => {\n    if (Prism.languages[lang]) return resolve();\n    \n    const script = document.createElement(\'script\');\n    script.src = `https://cdn.jsdelivr.net/npm/prismjs@1.29.0/components/prism-${lang}.min.js`;\n    script.onload = resolve;\n    document.head.appendChild(script);\n  });\n}\n\ndocument.querySelectorAll(\'pre code[class^=\"language-\"]\').forEach(async code => {\n  const lang = code.className.replace(\'language-\', \'\');\n  await loadPrismLanguage(lang);\n  Prism.highlightElement(code);\n});\n```\n\n#### 2. 自定义主题和样式\n\n```css\n/* 自定义代码块样式 */\npre[class*=\"language-\"] {\n  border-radius: 8px;\n  box-shadow: 0 2px 10px rgba(0,0,0,0.1);\n  margin: 1em 0;\n}\n\n/* 自定义行内代码样式 */\n:not(pre) > code[class*=\"language-\"] {\n  padding: 0.1em 0.3em;\n  border-radius: 3px;\n  white-space: normal;\n}\n```\n\n#### 3. 支持不常见语言\n\n```javascript\n// 注册自定义语言\nPrism.languages.myLang = {\n  \'keyword\': /\\b(if|else|for|while)\\b/,\n  // 更多语法规则...\n};\n```\n\n## 四、完整实现示例\n\n```html\n<!DOCTYPE html>\n<html>\n<head>\n  <title>Markdown 代码高亮</title>\n  <!-- Prism.js 核心 -->\n  <link href=\"https://cdn.jsdelivr.net/npm/prismjs@1.29.0/themes/prism-tomorrow.min.css\" rel=\"stylesheet\" />\n  <script src=\"https://cdn.jsdelivr.net/npm/prismjs@1.29.0/prism.min.js\"></script>\n  \n  <!-- 插件 -->\n  <link href=\"https://cdn.jsdelivr.net/npm/prismjs@1.29.0/plugins/line-numbers/prism-line-numbers.min.css\" rel=\"stylesheet\" />\n  <script src=\"https://cdn.jsdelivr.net/npm/prismjs@1.29.0/plugins/line-numbers/prism-line-numbers.min.js\"></script>\n  \n  <style>\n    /* 自定义样式 */\n    pre[class*=\"language-\"] {\n      border-radius: 8px;\n      margin: 1.5em 0;\n    }\n    \n    :not(pre) > code {\n      background: #f5f2f0;\n      padding: 0.2em 0.4em;\n      border-radius: 3px;\n      font-family: monospace;\n    }\n  </style>\n</head>\n<body>\n  <!-- Markdown 转换后的内容 -->\n  <div id=\"content\">\n    <h1>代码示例</h1>\n    \n    <p>这是<code>行内代码</code>的例子</p>\n    \n    <pre class=\"line-numbers\"><code class=\"language-javascript\">function hello() {\n  console.log(\"Hello World\");\n}</code></pre>\n    \n    <pre><code class=\"language-python\">def hello():\n    print(\"Hello World\")</code></pre>\n    \n    <pre><code>这是未指定语言的代码块</code></pre>\n  </div>\n  \n  <script>\n    // 处理未指定语言的代码块\n    document.querySelectorAll(\'pre code:not([class])\').forEach(code => {\n      code.classList.add(\'language-none\');\n    });\n    \n    // 初始化 Prism\n    Prism.highlightAll();\n  </script>\n</body>\n</html>\n```\n\n## 五、最佳实践建议\n\n1. **服务端预处理**：\n   - 在 Markdown 转换阶段就确保正确的 `language-xxx` 类名\n   - 处理特殊属性转换为 Prism.js 支持的格式\n\n2. **按需加载**：\n   - 只加载需要的语言组件\n   - 使用动态加载减少初始负载\n\n3. **性能优化**：\n   - 对于大量代码块，考虑虚拟滚动\n   - 使用 Web Worker 进行高亮处理\n\n4. **无障碍访问**：\n   - 确保代码块有适当的 ARIA 属性\n   - 提供代码复制功能\n\n通过以上方案，您可以全面处理 Markdown 转换后 HTML 中的各种代码高亮需求，并利用 Prism.js 实现美观的代码展示效果。','8c45724eb15742539cb74ed72e091fd5.png','2025-06-26 13:35:36','2025-06-26 13:35:36','b465af5a-66d0-48ef-8795-786cac84d2ed',2,NULL);
/*!40000 ALTER TABLE `drafts` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `image`
--

LOCK TABLES `image` WRITE;
/*!40000 ALTER TABLE `image` DISABLE KEYS */;
INSERT INTO `image` VALUES (1,'16d389634be74500ad96ad35a6d9380a.png',1,'2025-06-23 14:41:30','b465af5a-66d0-48ef-8795-786cac84d2ed'),(10,'8c45724eb15742539cb74ed72e091fd5.png',0,'2025-06-25 12:40:39','b465af5a-66d0-48ef-8795-786cac84d2ed'),(11,'4ff74f0f709b4644b43aca55dacbe8ba.png',0,'2025-06-26 13:53:22','b465af5a-66d0-48ef-8795-786cac84d2ed');
/*!40000 ALTER TABLE `image` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `likes`
--

LOCK TABLES `likes` WRITE;
/*!40000 ALTER TABLE `likes` DISABLE KEYS */;
INSERT INTO `likes` VALUES ('b465af5a-66d0-48ef-8795-786cac84d2ed','comment',2,'2025-06-26 10:58:39'),('b465af5a-66d0-48ef-8795-786cac84d2ed','reply',1,'2025-06-26 10:52:43'),('b465af5a-66d0-48ef-8795-786cac84d2ed','reply',2,'2025-06-26 10:02:51');
/*!40000 ALTER TABLE `likes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `post_tags`
--

LOCK TABLES `post_tags` WRITE;
/*!40000 ALTER TABLE `post_tags` DISABLE KEYS */;
INSERT INTO `post_tags` VALUES (8,4),(8,5),(9,6),(9,7),(9,8);
/*!40000 ALTER TABLE `post_tags` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `posts`
--

LOCK TABLES `posts` WRITE;
/*!40000 ALTER TABLE `posts` DISABLE KEYS */;
INSERT INTO `posts` VALUES (8,'markdown转html后代码高亮实现','html代码高亮方案','# Markdown 转换后 HTML 代码高亮美化方案 (使用 Prism.js)\n\n针对 Markdown 转换后的 HTML 代码高亮美化，特别是使用 Prism.js 进行处理，需要考虑多种情况和处理方式。以下是全面的解决方案：\n\n## 一、Markdown 中代码块的常见情况\n\n1. **标准代码块** (围栏式)\n   :::markdown\n   ```python\n   def hello():\n       print(\"Hello World\")\n   ```\n   :::\n\n2. **缩进式代码块**\n   ```markdown\n       def hello():\n           print(\"Hello World\")\n   ```\n\n3. **行内代码**\n   ```markdown\n   这是`行内代码`的例子\n   ```\n\n4. **带特殊属性的代码块** (某些 Markdown 扩展)\n   ```markdown\n   ```python {linenos highlight-lines=\"2\"}\n   def hello():\n       print(\"Hello World\")\n   ```\n   ```\n\n## 二、使用 Prism.js 的处理方案\n\n### 基础处理方式\n\n```html\n<!DOCTYPE html>\n<html>\n<head>\n  <!-- 引入 Prism.js 核心 CSS -->\n  <link href=\"https://cdn.jsdelivr.net/npm/prismjs@1.29.0/themes/prism.min.css\" rel=\"stylesheet\" />\n  \n  <!-- 引入 Prism.js 核心 JS -->\n  <script src=\"https://cdn.jsdelivr.net/npm/prismjs@1.29.0/prism.min.js\"></script>\n  \n  <!-- 引入语言支持 (按需) -->\n  <script src=\"https://cdn.jsdelivr.net/npm/prismjs@1.29.0/components/prism-python.min.js\"></script>\n  <script src=\"https://cdn.jsdelivr.net/npm/prismjs@1.29.0/components/prism-javascript.min.js\"></script>\n</head>\n<body>\n  <!-- Markdown 转换后的 HTML 内容 -->\n  <pre><code class=\"language-python\">def hello():\n      print(\"Hello World\")</code></pre>\n  \n  <!-- 初始化 Prism.js -->\n  <script>Prism.highlightAll();</script>\n</body>\n</html>\n```\n\n### 针对不同情况的处理\n\n#### 1. 标准代码块处理\n\n转换后的 HTML:\n```html\n<pre><code class=\"language-python\">def hello():\n    print(\"Hello World\")\n</code></pre>\n```\n\nPrism.js 会自动识别 `language-xxx` 类名进行高亮。\n\n#### 2. 缩进式代码块处理\n\nMarkdown 转换器可能生成:\n```html\n<pre><code>def hello():\n    print(\"Hello World\")\n</code></pre>\n```\n\n解决方案:\n- 在转换时强制添加语言类\n- 或使用 JS 自动检测:\n  ```javascript\n  document.querySelectorAll(\'pre code:not([class])\').forEach(code => {\n    code.classList.add(\'language-none\');\n  });\n  ```\n\n#### 3. 行内代码处理\n\n转换后的 HTML:\n```html\n<p>这是<code>行内代码</code>的例子</p>\n```\n\n解决方案:\n```css\n/* 为行内代码添加基本样式 */\ncode:not([class]) {\n  background: #f5f2f0;\n  padding: 0.2em 0.4em;\n  border-radius: 3px;\n  font-family: monospace;\n}\n```\n\n#### 4. 带特殊属性的代码块\n\n转换后的 HTML (需要 Markdown 解析器支持):\n```html\n<pre class=\"line-numbers\" data-line=\"2\"><code class=\"language-python\">def hello():\n    print(\"Hello World\")\n</code></pre>\n```\n\n需要额外插件:\n```html\n<!-- 引入行号插件 -->\n<link href=\"https://cdn.jsdelivr.net/npm/prismjs@1.29.0/plugins/line-numbers/prism-line-numbers.min.css\" rel=\"stylesheet\" />\n<script src=\"https://cdn.jsdelivr.net/npm/prismjs@1.29.0/plugins/line-numbers/prism-line-numbers.min.js\"></script>\n\n<!-- 引入高亮行插件 -->\n<script src=\"https://cdn.jsdelivr.net/npm/prismjs@1.29.0/plugins/highlight-keywords/prism-highlight-keywords.min.js\"></script>\n```\n\n### 三、高级处理方案\n\n#### 1. 动态加载语言\n\n```javascript\nfunction loadPrismLanguage(lang) {\n  return new Promise((resolve) => {\n    if (Prism.languages[lang]) return resolve();\n    \n    const script = document.createElement(\'script\');\n    script.src = `https://cdn.jsdelivr.net/npm/prismjs@1.29.0/components/prism-${lang}.min.js`;\n    script.onload = resolve;\n    document.head.appendChild(script);\n  });\n}\n\ndocument.querySelectorAll(\'pre code[class^=\"language-\"]\').forEach(async code => {\n  const lang = code.className.replace(\'language-\', \'\');\n  await loadPrismLanguage(lang);\n  Prism.highlightElement(code);\n});\n```\n\n#### 2. 自定义主题和样式\n\n```css\n/* 自定义代码块样式 */\npre[class*=\"language-\"] {\n  border-radius: 8px;\n  box-shadow: 0 2px 10px rgba(0,0,0,0.1);\n  margin: 1em 0;\n}\n\n/* 自定义行内代码样式 */\n:not(pre) > code[class*=\"language-\"] {\n  padding: 0.1em 0.3em;\n  border-radius: 3px;\n  white-space: normal;\n}\n```\n\n#### 3. 支持不常见语言\n\n```javascript\n// 注册自定义语言\nPrism.languages.myLang = {\n  \'keyword\': /\\b(if|else|for|while)\\b/,\n  // 更多语法规则...\n};\n```\n\n## 四、完整实现示例\n\n```html\n<!DOCTYPE html>\n<html>\n<head>\n  <title>Markdown 代码高亮</title>\n  <!-- Prism.js 核心 -->\n  <link href=\"https://cdn.jsdelivr.net/npm/prismjs@1.29.0/themes/prism-tomorrow.min.css\" rel=\"stylesheet\" />\n  <script src=\"https://cdn.jsdelivr.net/npm/prismjs@1.29.0/prism.min.js\"></script>\n  \n  <!-- 插件 -->\n  <link href=\"https://cdn.jsdelivr.net/npm/prismjs@1.29.0/plugins/line-numbers/prism-line-numbers.min.css\" rel=\"stylesheet\" />\n  <script src=\"https://cdn.jsdelivr.net/npm/prismjs@1.29.0/plugins/line-numbers/prism-line-numbers.min.js\"></script>\n  \n  <style>\n    /* 自定义样式 */\n    pre[class*=\"language-\"] {\n      border-radius: 8px;\n      margin: 1.5em 0;\n    }\n    \n    :not(pre) > code {\n      background: #f5f2f0;\n      padding: 0.2em 0.4em;\n      border-radius: 3px;\n      font-family: monospace;\n    }\n  </style>\n</head>\n<body>\n  <!-- Markdown 转换后的内容 -->\n  <div id=\"content\">\n    <h1>代码示例</h1>\n    \n    <p>这是<code>行内代码</code>的例子</p>\n    \n    <pre class=\"line-numbers\"><code class=\"language-javascript\">function hello() {\n  console.log(\"Hello World\");\n}</code></pre>\n    \n    <pre><code class=\"language-python\">def hello():\n    print(\"Hello World\")</code></pre>\n    \n    <pre><code>这是未指定语言的代码块</code></pre>\n  </div>\n  \n  <script>\n    // 处理未指定语言的代码块\n    document.querySelectorAll(\'pre code:not([class])\').forEach(code => {\n      code.classList.add(\'language-none\');\n    });\n    \n    // 初始化 Prism\n    Prism.highlightAll();\n  </script>\n</body>\n</html>\n```\n\n## 五、最佳实践建议\n\n1. **服务端预处理**：\n   - 在 Markdown 转换阶段就确保正确的 `language-xxx` 类名\n   - 处理特殊属性转换为 Prism.js 支持的格式\n\n2. **按需加载**：\n   - 只加载需要的语言组件\n   - 使用动态加载减少初始负载\n\n3. **性能优化**：\n   - 对于大量代码块，考虑虚拟滚动\n   - 使用 Web Worker 进行高亮处理\n\n4. **无障碍访问**：\n   - 确保代码块有适当的 ARIA 属性\n   - 提供代码复制功能\n\n通过以上方案，您可以全面处理 Markdown 转换后 HTML 中的各种代码高亮需求，并利用 Prism.js 实现美观的代码展示效果。',0,0,'8c45724eb15742539cb74ed72e091fd5.png','2025-06-25 12:40:39','2025-06-25 12:40:39','b465af5a-66d0-48ef-8795-786cac84d2ed',2),(9,'HttpOnly Cookie实现的前后端分离token认证方案','HttpOnly Cookie实现的前后端分离token认证方案','<font face=\"楷体\">\n\n在 Vue + Flask 前后端分离项目中，使用 `HttpOnly Cookie` 实现 Token 认证可显著提升安全性，避免 XSS 攻击窃取 Token。以下是完整的技术方案，包含服务端配置、前端交互和安全策略：\n\n\n### **一、服务端（Flask）实现**\n#### **1. 生成与设置 HttpOnly Cookie**\n在用户登录成功后，通过 Flask 设置 `HttpOnly Cookie`，将 Token 存入其中，并禁止 JavaScript 访问。\n\n```python\n# Flask 后端代码（auth.py）\nfrom flask import make_response, jsonify\nfrom datetime import timedelta\n\n@auth_bp.route(\'/login\', methods=[\'POST\'])\ndef login():\n    try:\n        form = request.get_json()\n        username = form.get(\'username\')\n        password = form.get(\'password\')\n        user = User.query.filter_by(username=username).first()\n        \n        if not user or not user.check_pwd(password):\n            return jsonify({\'err\': \'用户名或密码错误\'}), 401\n        \n        # 生成访问令牌（JWT）\n        access_token = generate_jwt_token(user.id, timedelta(hours=1))\n        \n        # 创建响应对象，设置 HttpOnly Cookie\n        response = make_response(jsonify({\n            \'userInfo\': {\n                \'id\': user.id,\n                \'username\': user.username\n            }\n        }))\n        response.set_cookie(\n            key=\'access_token\',          # Cookie 名称\n            value=access_token,          # Token 值\n            max_age=3600,                # 过期时间（秒）\n            httponly=True,               # 禁止 JavaScript 访问\n            secure=True,                 # 仅通过 HTTPS 传输\n            samesite=\'Lax\'               # 防御 CSRF 攻击\n        )\n        return response, 200\n    \n    except Exception as e:\n        return jsonify({\'err\': \'服务器错误\'}), 500\n```\n\n#### **2. 校验 Cookie 中的 Token**\n通过自定义装饰器校验请求中的 `access_token` Cookie，并解析用户身份。\n\n```python\n# 自定义 Token 校验装饰器\nfrom functools import wraps\nfrom flask import request, jsonify, current_app\nimport jwt\nfrom app.auth.model import User\n\ndef token_required(f):\n    @wraps(f)\n    def decorated(*args, **kwargs):\n        # 从 Cookie 中获取 Token\n        token = request.cookies.get(\'access_token\')\n        if not token:\n            return jsonify({\'err\': \'未提供有效 Token\'}), 401\n        \n        try:\n            # 校验 JWT\n            payload = jwt.decode(\n                token,\n                current_app.config[\'JWT_SECRET_KEY\'],\n                algorithms=[\'HS256\'],\n                options={\'verify_exp\': True}\n            )\n            user = User.query.get(payload[\'sub\'])\n            if not user:\n                return jsonify({\'err\': \'用户不存在\'}), 404\n            \n            # 将用户对象传入视图函数\n            return f(user, *args, **kwargs)\n        \n        except jwt.ExpiredSignatureError:\n            return jsonify({\'err\': \'Token 已过期\'}), 401\n        except jwt.InvalidTokenError:\n            return jsonify({\'err\': \'无效 Token\'}), 401\n    \n    return decorated\n```\n\n#### **3. 退出登录（清除 Cookie）**\n用户登出时，通过设置 Cookie 过期时间为过去，强制清除 Token。\n\n```python\n@auth_bp.route(\'/logout\', methods=[\'POST\'])\n@token_required\ndef logout(user):\n    response = make_response(jsonify({\'msg\': \'退出成功\'}))\n    # 设置 Cookie 过期时间为 0，立即清除\n    response.set_cookie(\'access_token\', \'\', max_age=0, httponly=True, secure=True)\n    return response, 200\n```\n\n\n### **二、前端（Vue）实现**\n#### **1. 登录时自动存储 Cookie**\n前端无需手动处理 Cookie，浏览器会自动接收并存储服务端返回的 `HttpOnly Cookie`。\n\n```vue\n<!-- Vue 登录组件 -->\n<template>\n  <div>\n    <input v-model=\"username\" placeholder=\"用户名\" />\n    <input v-model=\"password\" type=\"password\" placeholder=\"密码\" />\n    <button @click=\"handleLogin\">登录</button>\n  </div>\n</template>\n\n<script setup>\nimport { ref } from \'vue\';\nimport axios from \'axios\';\n\nconst username = ref(\'\');\nconst password = ref(\'\');\n\nconst handleLogin = async () => {\n  try {\n    const response = await axios.post(\'http://localhost:5000/auth/login\', {\n      username: username.value,\n      password: password.value\n    });\n    if (response.status === 200) {\n      // 登录成功，浏览器自动存储 Cookie\n      console.log(\'登录成功\');\n      // 跳转至首页\n      window.location.href = \'/home\';\n    }\n  } catch (error) {\n    console.error(\'登录失败:\', error.response.data.err);\n  }\n};\n</script>\n```\n\n#### **2. 发起请求时自动携带 Cookie**\nAxios 会自动将同源 Cookie 附加到请求头中，无需手动添加 Token。\n\n```javascript\n// Vue 全局 Axios 配置（axios.js）\nimport axios from \'axios\';\n\nconst instance = axios.create({\n  baseURL: \'http://localhost:5000\',\n  withCredentials: true, // 允许携带 Cookie（跨域场景需配合 CORS）\n});\n\n// 请求拦截器（可选，如需额外处理）\ninstance.interceptors.request.use(config => {\n  // 无需手动添加 Token，浏览器自动处理\n  return config;\n});\n\nexport default instance;\n```\n\n#### **3. 处理 Token 过期逻辑**\n通过 Axios 响应拦截器捕获过期错误，引导用户重新登录。\n\n```javascript\n// axios.js 响应拦截器\ninstance.interceptors.response.use(\n  response => response,\n  error => {\n    if (error.response && error.response.status === 401) {\n      if (error.response.data.err.includes(\'Token 已过期\')) {\n        // 清除无效状态（虽无法操作 HttpOnly Cookie，但可重置前端状态）\n        localStorage.removeItem(\'userInfo\');\n        // 跳转登录页\n        window.location.href = \'/login\';\n      }\n    }\n    return Promise.reject(error);\n  }\n);\n```\n\n\n### **三、跨域场景配置（CORS）**\n若前端与后端部署在不同域名下（如前端：`http://localhost:8080`，后端：`http://localhost:5000`），需配置 CORS 允许携带 Cookie。\n\n#### **Flask 后端配置（添加 CORS 中间件）**\n```python\n# Flask 配置文件（app.py）\nfrom flask_cors import CORS\n\napp = Flask(__name__)\nCORS(app, supports_credentials=True)  # 允许携带 Cookie\n\n# 关键配置：允许前端域名和 Cookie\napp.config[\'CORS_HEADERS\'] = \'Content-Type\'\napp.config[\'SESSION_COOKIE_SAMESITE\'] = \'None\'  # 跨域时需设置为 None\napp.config[\'SESSION_COOKIE_SECURE\'] = True       # 生产环境必须为 True（HTTPS）\n```\n\n#### **前端 Axios 配置**\n```javascript\n// 确保 withCredentials 为 true\nconst instance = axios.create({\n  withCredentials: true,\n});\n```\n\n\n### **四、安全增强策略**\n#### **1. Cookie 属性优化**\n- **`HttpOnly`**：禁止 JavaScript 访问，防御 XSS。\n- **`Secure`**：仅通过 HTTPS 传输，防止中间人攻击（生产环境必须启用）。\n- **`SameSite`**：\n  - `Lax`：允许跨站 GET 请求携带 Cookie（如链接跳转）。\n  - `Strict`：仅同源请求携带 Cookie（安全性更高）。\n  - `None`：跨域场景需设置，但必须配合 `Secure`。\n\n```python\n# 设置 Cookie 时添加完整属性\nresponse.set_cookie(\n    \'access_token\',\n    access_token,\n    max_age=3600,\n    httponly=True,\n    secure=True,\n    samesite=\'Lax\'  # 根据需求选择\n)\n```\n\n#### **2. 刷新 Token 机制（可选）**\n- **方案**：将刷新 Token 存储在 `HttpOnly Cookie` 或 `localStorage` 中，当访问 Token 过期时，自动请求新的 Token。\n- **示例流程**：\n  1. 服务端返回 `access_token`（短时效，如 1 小时）和 `refresh_token`（长时效，如 1 天）。\n  2. 前端通过 `refresh_token` 请求新的 `access_token`（存储于 `HttpOnly Cookie`）。\n\n#### **3. 防御 CSRF 攻击**\n- 在敏感操作（如修改密码）中，要求前端携带额外的 CSRF Token（存储于普通 Cookie 或请求头）。\n- Flask 可使用 `flask-wtf` 生成 CSRF Token：\n  ```python\n  from flask_wtf.csrf import CSRFProtect\n\n  csrf = CSRFProtect(app)\n  ```\n\n\n### **五、生产环境注意事项**\n1. **强制使用 HTTPS**：确保 `Secure` 属性生效，避免明文传输 Token。\n2. **限制 Cookie 作用域**：通过 `Domain` 和 `Path` 属性缩小 Cookie 生效范围：\n   ```python\n   response.set_cookie(\'access_token\', ..., domain=\'your-domain.com\', path=\'/api\')\n   ```\n3. **监控 Token 异常**：记录 Token 校验失败日志，及时发现攻击行为。\n\n\n### **六、总结流程**\n1. **用户登录**：后端生成 Token，通过 `HttpOnly Cookie` 返回给前端。\n2. **请求验证**：前端发起请求时自动携带 Cookie，后端校验 Token 并返回数据。\n3. **Token 过期**：后端返回 401 错误，前端跳转登录页。\n4. **安全防护**：通过 `HttpOnly`、`Secure`、`SameSite` 等属性提升安全性。\n\n此方案充分利用 `HttpOnly Cookie` 的安全特性，适合对安全性要求较高的前后端分离项目。',0,0,'','2025-06-26 13:58:06','2025-06-26 13:58:06','b465af5a-66d0-48ef-8795-786cac84d2ed',3);
/*!40000 ALTER TABLE `posts` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `replies`
--

LOCK TABLES `replies` WRITE;
/*!40000 ALTER TABLE `replies` DISABLE KEYS */;
INSERT INTO `replies` VALUES (1,'次级测试x2',1,'2025-06-26 10:01:21','2025-06-26 10:52:43',8,2,'b465af5a-66d0-48ef-8795-786cac84d2ed',NULL),(2,'guest what螺丝钉看见分厘卡',1,'2025-06-26 10:02:12','2025-06-26 10:18:12',8,2,'b465af5a-66d0-48ef-8795-786cac84d2ed',1);
/*!40000 ALTER TABLE `replies` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `tags`
--

LOCK TABLES `tags` WRITE;
/*!40000 ALTER TABLE `tags` DISABLE KEYS */;
INSERT INTO `tags` VALUES (8,'flask'),(4,'html'),(5,'Markdown'),(7,'vue'),(6,'全栈');
/*!40000 ALTER TABLE `tags` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `user`
--

LOCK TABLES `user` WRITE;
/*!40000 ALTER TABLE `user` DISABLE KEYS */;
INSERT INTO `user` VALUES ('2ceb941c-5caf-4c59-ae74-485ec799782f',NULL,'已注销','deleted@aba.com','$2b$12$dIxHfd7FP.RThrr/gZe4JOOG1nysfQVv9VtQXEwzxEp20QUK7Ex5q','deleted','2025-06-23 10:39:23',0,0,'2025-06-23 10:39:23','2025-06-23 10:39:23'),('8ca5c46a-34ab-4e2b-b395-08decccd5816',NULL,'admin','admin@secure.com','$2b$12$PQrFzHRslTs.9XDLXjAfzufX9gY4CnOqF1pzGBY9Xm16CR/jKZ.6K','admin','2025-06-23 10:39:22',0,1,'2025-06-23 10:39:22','2025-06-23 10:39:22'),('b465af5a-66d0-48ef-8795-786cac84d2ed',NULL,'阿巴','3464198485@qq.com','$2b$12$cO71AHSaLNn.bNSMJPqjZ.r5U4N3SF6XHD5UwTD73fLbkSq2Q3sm.','normal','2025-06-26 09:48:57',0,1,'2025-06-23 14:41:30','2025-06-26 09:48:57');
/*!40000 ALTER TABLE `user` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-06-26 12:47:39

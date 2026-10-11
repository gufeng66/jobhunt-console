# 求职作战台

单用户投递记录和看板。接口以运行中的 `/docs` 为准。

```text
browser -> Vite /api 或 nginx /api -> FastAPI -> MySQL
```

## 本地启动

1. MySQL 里准备库 `jobhunt` 和独立账号，不要用 root。
2. 复制 `.env.example` 为 `.env`，填上数据库连接、`INITIAL_PASSWORD`、`JWT_SECRET`。
3. 后端：

```text
cd backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

4. 前端：

```text
cd frontend
npm install
npm run dev
```

打开 Vite 地址。登录用户来自 `.env` 的 `APP_USERNAME`（默认 `admin`）和 `INITIAL_PASSWORD`。改密码后重启后端即可。

## 环境变量

| 变量 | 作用 |
| --- | --- |
| `DATABASE_URL` | SQLAlchemy 连接串 |
| `APP_USERNAME` | 预置用户名，默认 `admin` |
| `INITIAL_PASSWORD` | 预置密码，必填 |
| `JWT_SECRET` | access token 签名 |
| `UPLOAD_DIR` | 附件目录 |

局域网部署：`docker compose up --build`，浏览器访问 `http://<主机>:8080`。容器时区是 `Asia/Shanghai`。

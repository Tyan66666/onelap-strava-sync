# OneLap 到 Strava 同步

本地一键 Python 工具，用于从 OneLap 导出 FIT 文件并逐步上传到 Strava。

项目采用直接 OneLap HTTP + Strava HTTP 适配器运行。

## 设置

1. 创建并激活虚拟环境
2. 安装依赖：
   - `pip install -r requirements-dev.txt`
3. 复制 `.env.example` 到 `.env` 并填充所需的值

运行时必需的 `.env` 键：

- `ONELAP_USERNAME`
- `ONELAP_PASSWORD`
- `STRAVA_CLIENT_ID`
- `STRAVA_CLIENT_SECRET`
- `STRAVA_REFRESH_TOKEN`
- `STRAVA_ACCESS_TOKEN`
- `STRAVA_EXPIRES_AT`
- `DEFAULT_LOOKBACK_DAYS`

## OneLap 账户设置

- 一次性 OneLap 凭证初始化：`onelap-sync --onelap-auth-init`
- 交互式提示输入用户名和密码（密码输入被隐藏）
- 将 `ONELAP_USERNAME` 和 `ONELAP_PASSWORD` 保存到 `.env`

## Strava OAuth 首次运行

1. 创建 Strava API 应用并获取 `client_id` + `client_secret`
2. 完成 OAuth 授权流程以获取 `refresh_token`
3. 在 `.env` 中保存凭证

- 一次性 Strava 认证初始化：`onelap-sync --strava-auth-init`
- 此流程请求 `read,activity:write` 权限并将令牌写入 `.env`
- 在正常运行中，刷新的 Strava 令牌会自动保存回 `.env`

## 一键运行

- OneLap HTTP 前置条件：
  - OneLap 账户可在 `https://www.onelap.cn` 登录
  - Strava OAuth 令牌在 `.env` 中有效
- 推荐全局命令安装：
  - `pipx install onelap-strava-sync`
- 默认回溯运行：
  - `onelap-sync`
- 使用明确的开始日期运行：
  - `onelap-sync --since 2026-03-01`

### 仅下载模式

- 从 OneLap 下载 FIT 文件而不上传到 Strava：
  - `onelap-sync --download-only --since 2026-03-01`
- 在此模式下，不需要 Strava 密钥
- 示例输出：
  - `2026-03-09T08:00:00Z  a2.fit`
  - `download-only fetched X -> downloaded Y -> failed Z`

## --since 使用方法

- 使用 ISO 日期格式：`YYYY-MM-DD`
- 示例：`onelap-sync --since 2026-03-01`

仓库本地备用命令：`python run_sync.py`

## 技能分发

- 运行时代码保留在根源目录中
- 分发友好的技能工件位于 `skills/onelap-strava-sync/`
- 技能工件和运行时入口点之间的映射：`docs/skills-mapping.md`
- 开发者维护指南：`CONTRIBUTING.md`

## 故障排除

- 如果发生导入错误，请确认活动虚拟环境中已安装依赖项
- 如果 Strava 上传因 5xx 失败，请重试；可重试错误使用有界退避
- 如果同步报告上传失败，请检查 `logs/sync.log`；每条失败行包括 Strava `status` 和 `error` 详情
- 如果 OneLap 风险控制触发，请等待后重试
- 如果 OneLap HTTP 返回 401，请验证 `.env` 中的用户名/密码
- 如果 OneLap HTTP 持续返回 4xx/5xx，请验证端点可达性并稍后重试

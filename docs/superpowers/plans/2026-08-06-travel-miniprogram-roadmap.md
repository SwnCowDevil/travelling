# 旅行推荐小程序实施路线图

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 按四个可独立验证的阶段交付个人旅行推荐微信小程序。

**Architecture:** 微信原生小程序只访问 FastAPI；FastAPI 使用 SQLite 保存用户、目的地、推荐和足迹，外部 AI 与天气均通过后端适配器调用。规则引擎保证可靠筛选，AI 只在候选集合内重排并按需生成攻略。

**Tech Stack:** 微信原生小程序、Vant Weapp、Python 3.12、FastAPI、Pydantic 2、SQLAlchemy 2、Alembic、SQLite、httpx、pytest。

## Global Constraints

- 第一版数据库固定使用 SQLite WAL，FastAPI 使用单应用进程。
- 前端不得保存系统 AI Token、微信 AppSecret 或天气密钥。
- 默认天气服务为 Open-Meteo，个人非商业使用无需 Key。
- AI 默认端点为 `https://www.packyapi.com/v1`，模型 ID 必须可配置。
- AI 不能引入目的地库之外的推荐，不能突破硬约束。
- 所有密钥只通过环境变量或加密字段保存，禁止进入仓库和日志。
- 未实现功能不展示空入口。

---

## 执行顺序

1. [项目基础与后端核心](./2026-08-06-phase-1-backend-foundation.md)
2. [推荐、AI、天气与攻略](./2026-08-06-phase-2-recommendation-ai-weather.md)
3. [足迹、到访记录与地图聚合](./2026-08-06-phase-3-footprints-map.md)
4. [微信小程序前端、联调与部署](./2026-08-06-phase-4-miniprogram-deployment.md)

每一阶段必须通过其完整测试和验收后，才开始下一阶段。


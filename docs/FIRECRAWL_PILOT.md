# Firecrawl 本机小样本试验

## 当前交付与边界

这是默认关闭的可选适配器，不是生产部署，也不是微信互动数据源。
本轮没有安装 Docker、启动服务、改动 GitHub Actions 或接入付费 API。
只通过标准库 HTTP 接口连接自部署服务，没有复制 Firecrawl 的 AGPL 源码或引入其 SDK。

## 已有本机实例时如何运行

1. 自行确认实例仅绑定本机，未配置收费代理、云端引擎、LLM 或其他计费服务。
   客户端限制不能约束你自行配置的服务内部行为。
2. 在 `config/firecrawl-local.example.json` 中把 `enabled` 改为 `true`，
   `urls` 填入 10–20 条实际可公开访问的公众号文章链接。不要填验证码页或带登录凭据的链接。
3. 从项目目录运行下方命令。输出写入独立目录，不覆盖正式 `reports/latest.*`。

```bash
PYTHONPATH=src python -m wechat_hot_radar run \
  --config config/firecrawl-local.example.json \
  --date today --timezone Asia/Shanghai --top 50 \
  --output /tmp/wechat-hot-radar-firecrawl-pilot
```

测试历史文章时，把日期改为文章所属日期。输出仍会按目标日期过滤，
“采集成功数量”和“当日保留数量”可能不同，不应混为抓取失败。
关闭时把 `enabled` 改回 `false`；生产默认配置没有新增该来源。
没有本机实例时不要启用。此项目不自动安装 Docker，也不提供免费云端替代地址。

## 资源与故障控制

- 仅接受 `http://127.0.0.1:端口` 或 `http://[::1]:端口`；默认端口 3002。
- 不使用环境代理、不跟随客户端重定向、不读取 API Key。
- 最多 20 个输入 URL，去重后顺序执行；无无限重试或后台轮询。
- 每次请求最多约 20 秒，整轮预算 120 秒，响应最多 2 MiB。
- 传输故障打开本轮熔断，停止后续请求；其他来源仍由现有流水线独立处理。
- `maxAge=0`、`storeInCache=false`，但来源自己的更新时间仍可能未知。
- 同时检查 Firecrawl API 成功状态、目标页面 HTTP 状态、来源 URL、原始 HTML 和文章字段。
- 常见验证页结构会被拒绝；不能据此声称识别了所有反爬或伪装页面。

输出包含本次获取时间及原始 HTML 字符串的 SHA-256，不发布文章全文。
哈希不证明内容真实性；`source_updated_at=null` 表示没有取得来源更新时间。
服务可能在内部跟随目标页面重定向，因此本机服务本身仍须配置出站访问限制。

## 验收时必须分别报告

| 检查 | 不能替代的检查 |
|---|---|
| 单元测试通过 | Firecrawl 真实服务可用 |
| Firecrawl 心跳正常 | 目标文章获取成功 |
| 文章元信息获取成功 | 真实转发/点赞证据获取成功 |
| 配置来源内有 50 条 | 全微信公众号前 50 |

本轮没有 Docker，未做真实 Firecrawl/微信样本测试；不得填报成功率、费用或运行时长。
接通真实来源后，记录样本 URL、日期、运行版本、文章成功数、指标证据成功数、
错误类别、总时长和资源使用，与现有采集方式对照后再决定是否启用。

## 官方依据（2026-09-08 查阅）

- [Scrape：响应状态、rawHtml、缓存](https://docs.firecrawl.dev/features/scrape)
- [自部署：能力差异、持久化和安全边界](https://docs.firecrawl.dev/contributing/self-host)

升级应固定并审查版本，先在隔离环境验证，再人工决定是否切换；不做无人审核的自更新。

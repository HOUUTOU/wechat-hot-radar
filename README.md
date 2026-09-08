# WeChat Hot Radar｜微信公众号真实热榜

[![CI](https://github.com/HOUUTOU/wechat-hot-radar/actions/workflows/ci.yml/badge.svg)](https://github.com/HOUUTOU/wechat-hot-radar/actions/workflows/ci.yml)

一个**免费、按需运行、证据优先**的微信公众号文章筛选框架。目标是从公开可验证的数据中生成当日热榜，严格按照：

> 可验证转发量 ↓ → 可验证点赞量 ↓ → 发布时间 ↓

系统不把阅读量、在看数、推荐数或转载文章数量冒充转发量，也不会把 `10万+` 推算成虚假的精确数字。

## 最简单的使用方法

1. 点击右上角 **Fork**，复制到自己的 GitHub。
2. 进入 **Actions**。
3. 选择 **Manual WeChat Hot Radar**。
4. 点击 **Run workflow**。日期留空表示“今天”，仓库默认时区为 `Asia/Tokyo`；其他地区可直接修改。
5. 运行结束后查看 `reports/latest.md`；也可以下载 CSV/JSON artifact。

没有定时任务，不需要 API Key，也没有付费服务依赖。

本地运行：

```bash
git clone https://github.com/HOUUTOU/wechat-hot-radar.git
cd wechat-hot-radar
PYTHONPATH=src python -m wechat_hot_radar run --date today --timezone Asia/Tokyo --top 50
```

## 输出如何理解

| 状态 | 含义 |
|---|---|
| `PASS` | 找到至少 50 条具有可验证转发数据的当日文章 |
| `PARTIAL` | 有可验证转发数据，但不足 50 条 |
| `ABSTAIN` | 没有足够转发证据，系统拒绝生成伪 Top 50 |

报告包含两张明确分开的榜：

- **转发证据主榜**：只有转发指标可验证的文章。
- **点赞候选榜**：转发数据未公开，不能与主榜直接比较。

## 当前能力边界

### 安全修订：字段齐全不等于已核验

旧版本仅凭数值、证据 URL 和时间齐全就标记 `verified`，不足以证明真实性。
现在将其分为 `evidence_present`（字段齐全）和 `verified`（通过来源核验）。
外部 JSON 中自报的 `verified`、`source_verified` 或“官方”等级不会授予核验资格。

**目前还没有接通经过审查的真实转发/点赞核验器。** 因此导入 JSON 仅作为待核验资料，
不进入主榜或点赞候选榜；当前标准运行将返回 `ABSTAIN`。这不是完整热榜服务已经上线。
单元测试中的内部已核验对象是合成测试材料，不代表正式数据。

本项目尚未取得覆盖全平台的免费实时转发数据源。程序提供文章发现、字段检查、去重、分类、排序、来源健康检查和报告生成，但无法保证上游一直公开互动数据或服务永久可用。

因此，本项目保证的是：

- 有证据才排名；
- 无数据就标记缺失；
- 数据不足就 `PARTIAL` 或 `ABSTAIN`；
- 来源失效不会偷偷改用含义不同的指标；
- 每次运行记录来源状态与生成时间。

它不承诺：

- 覆盖微信全部公众号；
- 免费取得任意第三方文章的真实转发量；
- 绕过登录、验证码、反爬或微信访问控制。

## 数据源与持续扩展

默认启用两类来源：

1. `bing-wechat-discovery`：发现公开微信文章并回到原文核验文章身份；只负责发现，不产生互动指标。
2. `verified-json-inbox`：保留原有配置 ID，读取待核验记录；名字不代表已通过核验，不能仅凭导入进入主榜。

配置中还预留了 `rss_wechat` 和 `json_url`：前者可以连接自建 RSSHub/其他标准 RSS，后者可以连接遵守数据契约的公开 JSON 地址。示例默认关闭，填写真实 HTTPS 地址后即可启用。

所有来源均为独立 adapter。平台页面、字段或接口发生变化时，只需替换对应 adapter，不改排序、分类和报告核心。详见：

- [数据源契约](docs/SOURCE_CONTRACT.md)
- [适配器开发指南](docs/ADAPTER_GUIDE.md)
- [系统架构](docs/ARCHITECTURE.md)

## 数据文件

把公开、可复核的数据文件放入 `data/inbox/*.json`。原始显示值、证据 URL 与观察时间只是核验的必要条件，不是充分条件；文件字段不能自行证明真实性。

## 可选 Firecrawl 本机试验

新增 `firecrawl_local` 适配器，**默认关闭**，不改变现有工作流。只允许本机 IP，
不调用 Firecrawl Cloud、不使用 API Key、不启用 LLM 提取，也不自动安装或启动服务。
它仅提取文章信息，不产生转发量或点赞量。

已有经过配置检查的免费自部署实例时，按 [试验指南](docs/FIRECRAWL_PILOT.md) 操作。
当前 Firecrawl 测试使用模拟响应；真实微信公众号成功率、资源消耗和长期稳定性尚未实测。

运行不依赖付费 API，但自部署设备、电力与维护仍有成本；不能承诺第三方平台永远免费。

## 开发与验证

```bash
python -m compileall -q src tests
PYTHONPATH=src python -m unittest discover -s tests -v
```

项目只使用 Python 标准库。支持 Python 3.11 及以上版本。

## License

MIT。欢迎增加合法、公开、可审计的数据源 adapter。

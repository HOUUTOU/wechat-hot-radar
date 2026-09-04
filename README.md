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

微信没有向公众提供覆盖全平台的免费实时转发排行榜。开源程序可以稳定完成文章发现、校验、去重、分类、排序、来源健康检查和报告生成，但无法保证上游一直公开互动数据。

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
2. `verified-json-inbox`：读取符合证据契约的公开数据记录，可进入主榜。

配置中还预留了 `rss_wechat` 和 `json_url`：前者可以连接自建 RSSHub/其他标准 RSS，后者可以连接遵守数据契约的公开 JSON 地址。示例默认关闭，填写真实 HTTPS 地址后即可启用。

所有来源均为独立 adapter。平台页面、字段或接口发生变化时，只需替换对应 adapter，不改排序、分类和报告核心。详见：

- [数据源契约](docs/SOURCE_CONTRACT.md)
- [适配器开发指南](docs/ADAPTER_GUIDE.md)
- [系统架构](docs/ARCHITECTURE.md)

## 数据文件

把公开、可复核的数据文件放入 `data/inbox/*.json`，再运行工作流。指标必须包含原始显示值、证据 URL 与观察时间；缺少其中任一项都不会被视为已验证。

## 开发与验证

```bash
python -m compileall -q src tests
PYTHONPATH=src python -m unittest discover -s tests -v
```

项目只使用 Python 标准库。支持 Python 3.11 及以上版本。

## License

MIT。欢迎增加合法、公开、可审计的数据源 adapter。

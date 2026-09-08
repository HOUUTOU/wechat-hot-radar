# 免费来源与开源组件审查：2026-09-08

## 本轮结论

正式验收仍为 **BLOCKED_SOURCE_ACCESS / ABSTAIN**。
本轮没有取得任何可进入主榜的转发证据，也没有取得可进入点赞候选榜的证据。
这是本轮有限样本的结果，不能推断所有公众号都没有公开指标。

- 匿名 RSS GET 样本：3 个，均返回 HTTP 403，成功解析 0 个。
- 未取得文章正文和条目列表；条目数量、更新时间、转发/点赞字段均为未知，不是数值 0。
- 浏览器网页读取器先因不支持 application/xml 无法解析；这属于工具格式限制，不是源站停服证明。
- 对第一个 URL 的 curl HEAD 曾返回 HTTP 200，但后续实际 GET 返回 403。
  因此，HEAD 可达不等于正文可读，更不等于热度指标可用。
- 遇到 403 后停止这三个目标的抓取；没有更换代理、伪装登录态、提取 cookie 或绕过访问控制。
- 原始结构化检查结果见 [RSS_PROBE_20260908.json](RSS_PROBE_20260908.json)。
- 未新增付费依赖，未安装外部 skill，未改动 main、生产配置、工作流或正式榜单。

## 有限范围的项目筛选

| 项目 | 本轮看到的第一方证据 | 当前决策 |
|---|---|---|
| [wechat-article-exporter](https://github.com/wechat-article/wechat-article-exporter) | 维护者 2026-07-30 公告停止维护，称核心上游接口关闭；文档所列转发量导出需要 credentials | 不作为核心依赖；不能把旧功能清单当当前可用性 |
| [wewe-rss](https://github.com/cooderl/wewe-rss) | GitHub archived=true，页面显示 2026-05-11 归档；需微信读书扫码，文档还列出中转服务 | 不作为长期核心依赖；可以研究其 RSS 输出结构 |
| [we-mp-rss](https://github.com/rachelos/we-mp-rss/blob/main/README.zh-CN.md) | MIT；提供公众号订阅、正文、RSS、授权过期提醒；使用步骤要求扫码，默认启用定时任务 | 仅为文章发现候选；没有证明能提供符合本项目要求的匿名真实转发量；不安装/授权/开启定时任务 |
| [Wechat2RSS](https://github.com/ttttmr/Wechat2RSS) | 部分公众号有免费公开 RSS；私有部署为付费产品；免费源说明仅尽力在 24 小时内收录 | 免费公开源可候选，但本轮三个 GET 被拒绝；不接入其付费私有部署，不把 RSS 称为实时热榜 |
| [Read Buddy / read-rss-aggregator](https://github.com/SpaceZephyr/read-buddy/blob/main/read-rss-aggregator/SKILL.md) | skill 输出标题、作者、摘要、时间、链接；没有声明提供微信转发指标。根目录未见 LICENSE，GitHub license=null | 可参考来源列表与内容整理思路；许可证未澄清前不复制代码/安装，不据此推断微信热度 |
| [weixin_crawler](https://github.com/wonderfulsuccess/weixin_crawler) | 作者说明 2019 年更名为 wcplusPro 后不再免费提供源码；旧源码可能不能直接运行 | 排除商业版；不依赖旧代码的可运行性 |

补充证据：
- [exporter 停止维护公告](https://github.com/wechat-article/wechat-article-exporter/issues/200)：
  这是维护者对其所依赖接口的说明，不代表本项目独立证实所有微信接口均不可用。
- [Wechat2RSS 免费源说明](https://wechat2rss.xlab.app/list/)与[公开列表](https://wechat2rss.xlab.app/list/all)。
- GitHub 仓库元数据只证明观察时的归档/许可证识别状态，不证明项目安全、可用或未来维护。
  exporter 的 README 宣布停止维护，但本轮 API archived=false；两者分别记录，不混称“已归档”。

## 质量、免费与稳定性约束

1. 代码免费不等于上游数据免费；不引入订阅、收费 API 或额度用尽自动付费的回退。
2. 外部 skill 的公开可读不等于具备可复用许可证；安装脚本、权限、联网去向需另行审查。
3. “文章获取”“指标证据获取”“来源身份核验”“排名覆盖范围”独立验收。
4. 来源进入正式配置前，至少验证指标含义、文章映射、时间戳及实际匿名可读性。
5. 抓取失败报告失败，不用旧缓存冒充当下，不用阅读/在看/转载数冒充转发量。
6. 不承诺任何第三方源永久免费或永不故障；可控目标是零收费依赖、故障隔离、可回退和可审计。

## 下一步真实数据门槛

需要一个允许匿名访问、确实显示对应文章转发或点赞指标的来源，或另行明确授权的采集环境。
当前没有证明符合这些条件的数据源，不能继续宣称“真实 Top 50 已可用”。
不为绕过本次阻断而购买服务、提取凭据或改变既定排序规则。

## 复核方法

本轮对公开列表中的三个 URL，使用 Python 标准库 urllib.request.urlopen：
单 URL timeout=20 秒，读取上限 8 MiB，串行、无重试，不携带登录凭据。
仅在成功读到 XML 后才会解析 item 与字段；本轮全部在 HTTP 层被拒绝，所以没有计算条目或指标数量。
本轮只新增审查资料，没有修改生产 Python 文件，未重跑代码测试。
上一阶段 39 项本地单元测试的结果不能替代本次真实来源验收。

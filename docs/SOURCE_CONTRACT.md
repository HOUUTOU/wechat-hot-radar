# 数据源契约

每个 JSON 文件可以直接是文章数组，也可以使用 `{ "articles": [...] }`。

```json
{
  "articles": [
    {
      "title": "文章标题",
      "account": "公众号名称",
      "url": "https://mp.weixin.qq.com/s?...",
      "published_at": "2026-09-04T09:30:00+08:00",
      "share": {
        "raw": "10万+",
        "source_url": "https://可复核该数值的页面",
        "observed_at": "2026-09-04T12:00:00+08:00",
        "evidence_tier": "audited_public_provider"
      },
      "like": {
        "raw": "3.2万",
        "source_url": "https://可复核该数值的页面",
        "observed_at": "2026-09-04T12:00:00+08:00",
        "evidence_tier": "audited_public_provider"
      }
    }
  ]
}
```

## 证据等级

| 等级 | 用途 |
|---|---|
| `official_backend` | 公众号运营后台导出的官方数据 |
| `official_public` | 官方公开页面直接显示的数据 |
| `audited_public_provider` | 可复核的公开第三方数据 |
| `community` | 社区提交且附证据的数据 |
| `unknown` | 未评级；与高等级来源冲突时不会覆盖高等级数据 |

## 硬性规则

- `published_at` 与 `observed_at` 必须包含时区。
- 文章 URL 必须是 `mp.weixin.qq.com/s...`。
- `raw` 保留来源原文，例如 `10万+`；系统只计算其保守下界，不推算精确值。
- 缺少 `source_url` 或 `observed_at` 的指标不能进入已验证排序。
- `阅读量`、`在看`、`推荐`、`转载文章数`不得写入 `share`。
- 多来源冲突时按证据等级与观察时间选择，不按数值大小选择，避免人为放大热度。

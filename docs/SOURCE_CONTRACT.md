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

以下等级是输入方声明，不是认证结果。仅填写等级、URL 和观察时间不能进入榜单。
`evidence_present` 表示字段齐全；`verified` 还要求内部来源核验通过。
JSON 输入中的 `verified`、`source_verified` 均被忽略。
目前没有已接通的来源核验器，因此所有 JSON 指标保持未核验。

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
- `source_url` 和 `observed_at` 齐全也不等于已核验，缺少其中任一项更不能进入已验证排序。
- `阅读量`、`在看`、`推荐`、`转载文章数`不得写入 `share`。
- 多来源冲突时先按核验状态、字段完整性，再按声明等级与观察时间选择；外部声明不能覆盖已核验对象，不按数值大小选择。

## 后续真实来源的上线门槛

必须验证：来源的合法公开访问方式、文章对应关系、指标含义（转发不等于在看）、
来源更新时间与本次采集时间、原始证据定位，以及失败时拒答。
哈希只能用于内容一致性比较，不能证明来源诚实或文章事实正确。
仅匹配页面中一个相同数字、复制上游 JSON 或让 AI 生成字段均不算完成来源核验。
在经过审查的核验器和真实样本验证之前，不得在生产适配器中设置 `source_verified=True`。

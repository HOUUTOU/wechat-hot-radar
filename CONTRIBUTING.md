# Contributing

欢迎提交新的合法公开数据源、解析修复、分类词表和测试。

提交前请运行：

```bash
python -m compileall -q src tests
PYTHONPATH=src python -m unittest discover -s tests -v
```

任何指标采集都必须说明字段的真实含义和证据来源。以下修改不会被接受：

- 把阅读、在看、推荐或转载文章数替代转发量；
- 绕过登录、验证码、访问限制或反爬系统；
- 提交账号凭据、Cookie、Token 或截获的数据；
- 为凑满 50 条而填充推测值。

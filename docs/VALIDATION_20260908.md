# 2026-09-08 安全补强与 Firecrawl 本机适配验证

- 上游基线：`781b7fa8cc55c8f04ab9a2e6679e655ddbe99d0e`。
- 基线单元测试：本环境复现 17/17 通过。
- 修改后单元测试：39/39 通过，具体输出见下方。
- `python -m py_compile`（5 个修改/新增生产 Python 文件）：通过。
- `python -m compileall -q src tests`：通过。
- `git diff --check`：通过。
- 使用默认关闭的 Firecrawl 示例配置实际执行 CLI：退出码 0，`ABSTAIN`，发现 0，主榜 0。
  这是无网络调用的空配置烟雾测试，不是真实采集成功。
- Firecrawl HTTP 请求使用模拟响应验证；没有运行真实 Firecrawl 实例。
- 当前环境没有 Docker。未安装依赖、启动服务、配置凭据或修改 GitHub Actions。
- 正式 `main`、`config/sources.json`、已有报告与工作流保持不变。此修订只在隔离分支交付。

## 行为变化与风险

原先仅字段齐全的 JSON 指标将不再进入主榜/点赞候选榜，保留为待核验资料。
当前尚无真实来源核验器；本修订不代表获得了微信转发量，也不保证第三方来源真实。
`source_verified` 是内部接口，不是防恶意代码的安全边界；生产代码尚不设置该标记。

真实性缺口、真实页面成功率、资源成本、长期稳定性均未完成验证。
后续上线须先接通可信指标来源，完成真实样本试验及独立审查，再决定是否合并。
回退方式：保留 main 不变；不启用可选来源即可。未修改用户数据。

## 本轮单元测试原始输出

```text
test_json_url_keeps_evidence_requirements (test_adapters.AdapterTests.test_json_url_keeps_evidence_requirements) ... ok
test_json_url_rejects_plain_http (test_adapters.AdapterTests.test_json_url_rejects_plain_http) ... ok
test_rss_extracts_only_direct_wechat_articles (test_adapters.AdapterTests.test_rss_extracts_only_direct_wechat_articles) ... ok
test_external_official_tier_does_not_override_internal_verified_metric (test_evidence_policy.EvidencePolicyTests.test_external_official_tier_does_not_override_internal_verified_metric) ... ok
test_forged_fifty_articles_abstain (test_evidence_policy.EvidencePolicyTests.test_forged_fifty_articles_abstain) ... ok
test_import_cannot_self_certify (test_evidence_policy.EvidencePolicyTests.test_import_cannot_self_certify) ... ok
test_malformed_source_url_does_not_crash (test_evidence_policy.EvidencePolicyTests.test_malformed_source_url_does_not_crash) ... ok
test_source_flag_alone_is_insufficient (test_evidence_policy.EvidencePolicyTests.test_source_flag_alone_is_insufficient) ... ok
test_api_success_does_not_override_page_failure (test_firecrawl_local.FirecrawlLocalTests.test_api_success_does_not_override_page_failure) ... ok
test_bad_firecrawl_config_does_not_break_other_source (test_firecrawl_local.FirecrawlLocalTests.test_bad_firecrawl_config_does_not_break_other_source) ... ok
test_challenge_rejected_even_with_article_metadata (test_firecrawl_local.FirecrawlLocalTests.test_challenge_rejected_even_with_article_metadata) ... ok
test_cloud_and_non_loopback_endpoints_rejected (test_firecrawl_local.FirecrawlLocalTests.test_cloud_and_non_loopback_endpoints_rejected) ... ok
test_disabled_source_never_constructs_client (test_firecrawl_local.FirecrawlLocalTests.test_disabled_source_never_constructs_client) ... ok
test_http_redirect_not_followed (test_firecrawl_local.FirecrawlLocalTests.test_http_redirect_not_followed) ... ok
test_malformed_json_is_rejected (test_firecrawl_local.FirecrawlLocalTests.test_malformed_json_is_rejected) ... ok
test_missing_html_and_metadata_fail_closed (test_firecrawl_local.FirecrawlLocalTests.test_missing_html_and_metadata_fail_closed) ... ok
test_non_article_targets_rejected (test_firecrawl_local.FirecrawlLocalTests.test_non_article_targets_rejected) ... ok
test_oversized_response_rejected (test_firecrawl_local.FirecrawlLocalTests.test_oversized_response_rejected) ... ok
test_request_is_fresh_raw_html_with_no_auth_or_cloud_options (test_firecrawl_local.FirecrawlLocalTests.test_request_is_fresh_raw_html_with_no_auth_or_cloud_options) ... ok
test_run_budget_skips_without_request (test_firecrawl_local.FirecrawlLocalTests.test_run_budget_skips_without_request) ... ok
test_source_mismatch_and_redirect_rejected (test_firecrawl_local.FirecrawlLocalTests.test_source_mismatch_and_redirect_rejected) ... ok
test_success_produces_discovery_only_with_hash (test_firecrawl_local.FirecrawlLocalTests.test_success_produces_discovery_only_with_hash) ... ok
test_timeout_opens_circuit (test_firecrawl_local.FirecrawlLocalTests.test_timeout_opens_circuit) ... ok
test_transport_failure_opens_circuit_without_leaking_error (test_firecrawl_local.FirecrawlLocalTests.test_transport_failure_opens_circuit_without_leaking_error) ... ok
test_url_budget_and_deduplication (test_firecrawl_local.FirecrawlLocalTests.test_url_budget_and_deduplication) ... ok
test_decimal_unit (test_metrics.MetricTests.test_decimal_unit) ... ok
test_exact_integer (test_metrics.MetricTests.test_exact_integer) ... ok
test_invalid_text_is_not_verified (test_metrics.MetricTests.test_invalid_text_is_not_verified) ... ok
test_missing_evidence_is_not_verified (test_metrics.MetricTests.test_missing_evidence_is_not_verified) ... ok
test_naive_observation_is_not_verified (test_metrics.MetricTests.test_naive_observation_is_not_verified) ... ok
test_ten_thousand_plus_keeps_band (test_metrics.MetricTests.test_ten_thousand_plus_keeps_band) ... ok
test_unitless_decimal_is_rejected (test_metrics.MetricTests.test_unitless_decimal_is_rejected) ... ok
test_filters_date_and_requires_wechat_url (test_pipeline.PipelineTests.test_filters_date_and_requires_wechat_url) ... ok
test_tracking_parameters_are_removed (test_pipeline.PipelineTests.test_tracking_parameters_are_removed) ... ok
test_like_breaks_share_tie (test_ranking.RankingTests.test_like_breaks_share_tie) ... ok
test_no_metrics_is_discovery_only (test_ranking.RankingTests.test_no_metrics_is_discovery_only) ... ok
test_share_is_primary (test_ranking.RankingTests.test_share_is_primary) ... ok
test_unknown_share_is_separate (test_ranking.RankingTests.test_unknown_share_is_separate) ... ok
test_empty_result_abstains_and_writes_all_outputs (test_report.ReportTests.test_empty_result_abstains_and_writes_all_outputs) ... ok

----------------------------------------------------------------------
Ran 39 tests in 0.044s

OK
```

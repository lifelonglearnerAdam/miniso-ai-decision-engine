# MINISO 公开用户之声（VoC）样本与用户洞察

本数据包服务于飞书 AI 比赛命题“AI 驱动的产品开发智能决策引擎”，覆盖趋势感知、产品创意、SKU 选择、上市前验证和上市后反馈回写。

## 内容

- `report/miniso_user_insight_report_zh.md`：可直接在 GitHub 阅读的完整研究报告；
- `report/miniso_user_insight_report_zh.docx`：可编辑 Word 版；
- `report/miniso_user_insight_report_zh.pdf`：固定版式 PDF；
- `data/miniso_voc_dataset.csv`：124 条公开样本主表；
- `data/miniso_voc_dataset.xlsx`：含概览、样本库、小红书评论证据和字段说明；
- `data/miniso_xhs_comment_evidence.csv`：13 条小红书详情页评论主题证据；
- `data/miniso_voc_codebook.csv`：字段和编码口径；
- `data/miniso_voc_summary.json`：机器可读统计；
- `DATA_ETHICS.md`：采集边界、偏差与使用限制。
- `scripts/`：数据集、工作簿和报告生成脚本（不含账号凭证）。

## 数据概览

- 总样本：124 条；进入分析：119 条；检索噪声：5 条；
- 小红书：75 条，其中 13 条读取公开详情页与公开评论主题；
- 其他来源：哔哩哔哩、抖音、微博、Reddit、Trustpilot、Google Reviews 聚合页、BBB Reviews；
- 产品开发高相关样本：91 条；严重度 4-5 级样本：25 条；
- 采集日期：2026-07-18。

## 推荐使用方式

1. 将 `data/miniso_voc_dataset.csv` 导入飞书多维表格；
2. 以 `sample_id` 作为主键，以 `source_url` 作为证据回链；
3. 用 `primary_theme`、`category_ip`、`journey`、`severity_1_5` 和 `evidence_level` 建立筛选视图；
4. 将 VoC 样本关联到趋势事件、产品概念、SKU 评分、试销和上市结果；
5. 模型输出应同时显示爆款潜力、失败风险和证据置信度。

## 重要限制

本数据为目的性公开采样，不是随机抽样，不能用来估计总体满意度或市场份额。平台互动口径不同，不应把播放、点赞、收藏、评论和星级直接相加。搜索结果、公开页面和互动量可能随时间变化或失效。

本项目不含登录凭证、Cookie、私信、非公开个人信息或完整评论批量转载。评论只保留主题归纳，展示名仅用于公开证据回溯。

# 贡献指南 / Contributing Guide

## 团队分工 Team Roles

| 角色 | 负责人 | 主要负责 |
|------|--------|---------|
| **队友 A** | TBD | Agent 架构、Prompt Chain、时光机回测 Protocol |
| **队友 B** | TBD | 回测实验、Precision@20/Lift/NDCG 实现 |
| **队友 C** | TBD | 行业分析、竞品对标、Granger 因果、DFM 规则库、文献 |

## 分支策略 Branch Strategy

```
main          — 稳定版本，需 PR review 后合并
├── feat/     — 新功能 (feat/backtest-engine, feat/evolution-engine)
├── fix/      — 修复
└── docs/     — 文档更新
```

## 开发流程 Workflow

1. `git checkout -b feat/your-feature-name`
2. 编写代码 + 测试
3. `git push origin feat/your-feature-name`
4. 在 GitHub 上创建 Pull Request
5. @ 相关队友 Review

## 代码规范 Code Style

- Python: 遵循 PEP 8，使用 `black` 格式化
- 所有函数需有 Type Hint + Docstring
- 关键算法需有单元测试

## 提交信息规范 Commit Message

```
<type>(<scope>): <description>

feat(backtest): 实现滚动时间窗回测
fix(panel): 方差修正除零错误
docs(analysis): 更新 Granger 因果结果
```

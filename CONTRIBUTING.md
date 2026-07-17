# 贡献指南

感谢参与。项目优先级是**可验证、可复现、口径真实**。

## 本地流程

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements-dev.txt
ruff check src scripts tests
pytest -q
```

## 分支与提交

- `feat/...`：功能；`fix/...`：修复；`docs/...`：文档；
- 提交格式：`type(scope): description`；
- Pull Request 说明动机、证据、风险和回滚；
- 算法改动必须包含测试和可复现实验；
- 指标改动必须说明数据、窗口、基线和统计口径。

## 证据规则

- 合成数据结果必须标注 `synthetic_demo`；
- 不得把目标值写成已实现 KPI；
- 不得提交真实个人信息、未发布商品、供应商报价、合同或凭据；
- 引用应能定位到原始论文、官方报告或标准；
- Granger 不写成结构因果，LLM persona 不写成真实人群代表。

## 代码要求

- Python 3.10+，类型提示和简洁 docstring；
- 随机过程使用显式种子；
- 不静默吞掉评估错误；
- 数据列要区分特征、标签和未来结果；
- 高影响写操作不得直接接入 Agent。

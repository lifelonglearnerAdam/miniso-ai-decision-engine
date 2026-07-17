# 样例数据说明

项目不提交真实消费者、未发布商品、供应商或销售明细。演示数据由 `src/pipeline/data_generator.py` 在本地确定性生成：

```bash
python -m src.pipeline.data_generator
```

每行代表一个产品决策。`social_score`、`trend_score`、产品属性和成本估计在决策时可见；`is_hit`、`sales_90d` 和 `realized_margin` 是未来结果，回测引擎会在候选评分前删除。

所有演示行带 `data_provenance=synthetic-demo-v2`。这些数据只能验证代码和评估协议，不能用于推断名创优品真实业务表现。

真实数据接入必须使用受控存储和数据目录，不应提交到 Git。字段定义、敏感级别、事件时间、可用时间、保留期和 owner 见技术白皮书第 4 章。

window.MINISO_DEMO_DATA = {
  meta: {
    batch: "2026-W29-demo",
    evidenceLevel: "synthetic_and_algorithm_demo",
    generatedAt: "2026-07-18T06:54:11+00:00",
    disclaimer: "合成 / 算法演示，仅验证系统路径与证据约束，不代表名创优品真实业务指标。"
  },
  signals: [
    {
      id: "S-101",
      name: "国潮轻户外",
      alias: "合成趋势信号 A",
      momentum: 82,
      change: "+18.4%",
      bestLag: 4,
      pValue: "< 0.001",
      direction: "双向显著，需业务事件复核",
      decision: "进入候选",
      state: "success",
      description: "在演示时间序列中，社媒动量对后续结果具有预测领先性；反向关系同样显著，因此不解释为结构因果。",
      correlations: [0.72, 0.79, 0.92, 0.79, 0.70, 0.61, 0.49]
    },
    {
      id: "S-118",
      name: "随行收纳",
      alias: "合成趋势信号 B",
      momentum: 71,
      change: "+11.2%",
      bestLag: 2,
      pValue: "0.018",
      direction: "单期领先，稳定性待观察",
      decision: "继续观察",
      state: "review",
      description: "演示信号在较短滞后下通过单次检验，但跨窗口稳定性不足，暂不独立触发创意生成。",
      correlations: [0.58, 0.74, 0.62, 0.51, 0.43, 0.36, 0.29]
    },
    {
      id: "S-126",
      name: "情绪陪伴小物",
      alias: "合成趋势信号 C",
      momentum: 65,
      change: "+7.8%",
      bestLag: 0,
      pValue: "0.280",
      direction: "未发现预测领先性",
      decision: "不进入",
      state: "danger",
      description: "热度上升不等于领先销量。该演示信号未通过领先性门槛，保留记录但不进入本轮候选。",
      correlations: [0.36, 0.31, 0.28, 0.22, 0.19, 0.15, 0.11]
    }
  ],
  candidates: [
    {
      id: "C-042",
      name: "国潮随行美妆收纳",
      short: "美妆 · 中价 · 国潮 · 白领",
      category: "美妆",
      priceTier: "中价",
      style: "国潮",
      audience: "白领",
      material: "硅胶",
      features: ["环保", "IP 联名", "限量版", "防水"],
      objectives: { demand: 0.92, dfm: 1.0, novelty: 0.5 },
      status: "pareto",
      riskLevel: "review",
      icon: "briefcase-business",
      color: "red",
      source: "端到端算法演示快照 mutant_000838；名称为结构化属性的人类可读表达。",
      risks: [
        { level: "review", title: "IP 授权边界", detail: "进入企业验证前确认授权范围与成本空间。" },
        { level: "success", title: "DFM 演示规则", detail: "当前规则集未发现阻断项。" }
      ],
      validation: {
        score: 0.74,
        lower: 0.62,
        upper: 0.84,
        summary: "在合成锚定条件下表现为较强弱信号，但区间仍跨越企业决策阈值，建议进入真实历史盲测。",
        segments: [
          { name: "都市白领", note: "核心受众", score: 0.78, lower: 0.65, upper: 0.87 },
          { name: "Z 世代", note: "风格增量", score: 0.72, lower: 0.59, upper: 0.84 },
          { name: "礼赠场景", note: "需验证", score: 0.63, lower: 0.50, upper: 0.75 }
        ]
      }
    },
    {
      id: "C-057",
      name: "环保防水毛绒挂件",
      short: "玩具 · 低价 · 国潮 · Z 世代",
      category: "玩具",
      priceTier: "低价",
      style: "国潮",
      audience: "Z 世代",
      material: "布料",
      features: ["防水", "环保", "便携", "IP 联名"],
      objectives: { demand: 0.92, dfm: 1.0, novelty: 0.5 },
      status: "pareto",
      riskLevel: "review",
      icon: "package",
      color: "green",
      source: "端到端算法演示快照 mutant_000874；名称为结构化属性的人类可读表达。",
      risks: [
        { level: "review", title: "低价 IP 成本", detail: "授权费与目标价格带的空间需供应链确认。" },
        { level: "success", title: "材料可制造性", detail: "当前演示规则集未发现阻断项。" }
      ],
      validation: {
        score: 0.71,
        lower: 0.59,
        upper: 0.82,
        summary: "演示信号显示 Z 世代与礼赠场景存在潜力，但低价带的授权和防水工艺需要先行验证。",
        segments: [
          { name: "Z 世代", note: "核心受众", score: 0.79, lower: 0.66, upper: 0.88 },
          { name: "亲子人群", note: "安全敏感", score: 0.67, lower: 0.53, upper: 0.78 },
          { name: "礼赠场景", note: "节日波动", score: 0.65, lower: 0.49, upper: 0.77 }
        ]
      }
    },
    {
      id: "C-063",
      name: "模块化桌面香氛灯",
      short: "家居 · 中价 · 简约 · 白领",
      category: "家居",
      priceTier: "中价",
      style: "简约",
      audience: "白领",
      material: "玻璃",
      features: ["模块化", "氛围灯", "礼盒装"],
      objectives: { demand: 0.79, dfm: 0.76, novelty: 0.83 },
      status: "candidate",
      riskLevel: "risk",
      icon: "lamp-desk",
      color: "blue",
      source: "用于展示非支配筛选的对照候选，属于概念演示数据。",
      risks: [
        { level: "danger", title: "玻璃运输风险", detail: "包装跌落测试和破损率基线尚未接入。" },
        { level: "review", title: "香氛合规", detail: "配方、标签与区域法规需质量团队复核。" }
      ],
      validation: {
        score: 0.68,
        lower: 0.52,
        upper: 0.80,
        summary: "新颖性较高，但运输与合规风险扩大了决策不确定性，当前不建议优先进入打样。",
        segments: [
          { name: "都市白领", note: "桌面场景", score: 0.75, lower: 0.60, upper: 0.85 },
          { name: "学生人群", note: "价格敏感", score: 0.58, lower: 0.42, upper: 0.72 },
          { name: "礼赠场景", note: "包装敏感", score: 0.70, lower: 0.54, upper: 0.82 }
        ]
      }
    },
    {
      id: "C-071",
      name: "便携降温防晒喷雾瓶",
      short: "美妆 · 低价 · 日系 · 学生",
      category: "美妆",
      priceTier: "低价",
      style: "日系",
      audience: "学生",
      material: "塑料",
      features: ["便携", "雾化", "防水"],
      objectives: { demand: 0.85, dfm: 0.68, novelty: 0.46 },
      status: "candidate",
      riskLevel: "risk",
      icon: "spray-can",
      color: "amber",
      source: "用于展示 DFM 风险门槛的对照候选，属于概念演示数据。",
      risks: [
        { level: "danger", title: "低价雾化工艺", detail: "目标成本与喷头稳定性存在冲突。" },
        { level: "review", title: "功效表述", detail: "防晒相关内容必须经过法规与功效测试。" }
      ],
      validation: {
        score: 0.66,
        lower: 0.51,
        upper: 0.78,
        summary: "需求弱信号尚可，但 DFM 与功效合规均未过门槛，应先补充工程和法规证据。",
        segments: [
          { name: "学生人群", note: "核心受众", score: 0.73, lower: 0.57, upper: 0.84 },
          { name: "户外人群", note: "功效敏感", score: 0.64, lower: 0.48, upper: 0.77 },
          { name: "通勤人群", note: "便携场景", score: 0.68, lower: 0.53, upper: 0.79 }
        ]
      }
    }
  ],
  audit: [
    {
      type: "system",
      title: "决策包生成",
      detail: "4 个候选、2 个前沿解、2 项 DFM 待办已写入 demo-v2。",
      time: "2026-07-18 14:54"
    },
    {
      type: "evidence",
      title: "证据边界检查通过",
      detail: "合成指标未标记为真实 KPI；采购与上架动作保持禁用。",
      time: "2026-07-18 14:53"
    },
    {
      type: "model",
      title: "校准诊断完成",
      detail: "加权 ECE 0.016，区间覆盖率 91.9%，证据等级为 synthetic_demo。",
      time: "2026-07-18 14:52"
    }
  ]
};

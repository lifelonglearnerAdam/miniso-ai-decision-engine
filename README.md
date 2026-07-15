# 🚀 名创优品 AI 驱动的产品开发智能决策引擎

> **MINISO AI-Powered Product Development Decision Engine**
>
> 名创优品 × AI先锋未来人才大赛 参赛项目

---

## 📋 项目概述

名创优品每年推出上万款新品。本项目设计一套 **AI驱动的产品开发智能决策引擎**，覆盖趋势洞察 → 产品创意 → 上市验证全链路，缩短新品上市周期，提升爆品命中率。

## 🏗️ 架构总览

```
┌─────────────────────────────────────────────────────────┐
│                    LLM Orchestrator                      │
│           (Ollama + Qwen2.5-14B, 本地 4090 运行)          │
├────────┬────────┬────────┬────────┬────────┬────────────┤
│ Trend  │ Design │ Review │ Panel  │ DFM    │ Preference │
│ Agent  │ Agent  │ Agent  │ Agent  │ Agent  │  Evolution  │
├────────┴────────┴────────┴────────┴────────┴────────────┤
│          时光机回测引擎 (Time-Machine Backtest)            │
│     Precision@20 / Lift / NDCG / 帕累托前沿               │
├─────────────────────────────────────────────────────────┤
│           虚拟消费者面板 (Virtual Consumer Panel)           │
│     锚定回归 + 方差修正 + 保形预测 + 置信区间               │
├─────────────────────────────────────────────────────────┤
│          Granger 因果分析 (社媒趋势 → 销售数据)             │
└─────────────────────────────────────────────────────────┘
```

## 📦 六大交付物

| # | 交付物 | 负责人 | 核心内容 |
|---|--------|--------|---------|
| 1 | **行业分析报告** | 队友 C | 商业模式、竞品对标(无印良品/泡泡玛特/完美日记)、Granger 因果 |
| 2 | **技术白皮书** | 队友 A+B | 多 Agent 架构、Prompt Chain、时光机回测 Protocol、虚拟面板校准 |
| 3 | **回测实验报告** | 队友 B | ⭐ Precision@20/Lift/NDCG 曲线 (全场唯一离线回测证据) |
| 4 | **进化式创意引擎** | 队友 A+B+C | 进化循环参数、DFM 可制造性约束规则库 |
| 5 | **Demo 演示脚本** | 队友 A+C | 时光机回测演示、帕累托前沿、置信区间 |
| 6 | **参考文献清单** | 队友 C | 学术论文、行业报告 |

## 🖥️ 本地运行 (RTX 4090)

### 环境要求
- Windows / Linux (WSL2)
- NVIDIA RTX 4090 (24GB VRAM)
- Python 3.10+
- Ollama (本地大模型，零 API 费用)

### 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/lifelonglearnerAdam/miniso-ai-decision-engine.git
cd miniso-ai-decision-engine

# 2. 安装依赖
pip install -r requirements.txt

# 3. 安装 Ollama (如未安装)
# Windows: https://ollama.com/download
# Linux: curl -fsSL https://ollama.com/install.sh | sh

# 4. 拉取本地模型
ollama pull qwen2.5:14b

# 5. 运行回测
python scripts/run_backtest.py

# 6. 运行完整管线
python src/pipeline/run_all.py
```

### 显存占用 (4090)

| 模型 | 量化 | 显存 | 可用 |
|-----|------|------|------|
| Qwen2.5-14B | Q4_K_M | ~9GB | ✅ |
| Qwen2.5-32B | Q4_K_M | ~20GB | ✅ (极限) |
| bge-m3 (embedding) | - | ~2GB | ✅ 可共存 |

## 🤝 团队协作

详见 [CONTRIBUTING.md](CONTRIBUTING.md)

### 仓库共建方式
1. **Collaborator 模式**: 管理员在 Settings → Collaborators 添加队友 GitHub 账号
2. **Fork + PR 模式**: 队友 Fork → 开发 → PR → Review → Merge

## 📊 关键技术指标

| 指标 | 目标 |
|------|------|
| Precision@20 | ≥35% |
| Lift vs 随机基线 | ≥2.5x |
| NDCG@20 | ≥0.65 |
| 平均校准误差 (ACE) | ≤0.05 |
| 新品上市周期缩短 | ≥40% |

## 📄 License

MIT

---

**⭐ 如果这个项目对你有帮助，请给一个 Star！**

# Agent系统DoS攻击安全研究 - 文献综述

## 目录
1. [Prompt Injection攻击研究](#1-prompt-injection攻击研究)
2. [LLM Agent安全研究](#2-llm-agent安全研究)
3. [DoS攻击研究](#3-dos攻击研究)
4. [基准测试与评估框架](#4-基准测试与评估框架)
5. [防御机制研究](#5-防御机制研究)
6. [相关漏洞披露](#6-相关漏洞披露)
7. [总结与研究机会](#7-总结与研究机会)

---

## 1. Prompt Injection攻击研究

### 1.1 直接提示词注入 (Direct Prompt Injection)

**基础概念**
- 攻击者直接在用户输入中注入恶意指令
- 目标是覆盖或修改系统提示词
- 经典案例：绕过LLM的安全对齐机制

**重要论文**

| 论文 | 作者 | 年份 | 贡献 |
|------|------|------|------|
| Tensor Trust | Stanford HCI Lab | 2023 | 126,000+提示词注入攻击数据集 |
| Signed-Prompt | Xuchen Suo | 2024 | 签名方法防止注入 |

**Tensor Trust (arXiv:2311.01011)**
- 来自在线游戏的真实攻击数据
- 最大的人类生成对抗性示例数据集
- 识别了LLM的关键弱点

### 1.2 间接提示词注入 (Indirect Prompt Injection, IPI)

**核心概念**
- 恶意指令嵌入外部数据源（网页、文档、邮件）
- 当LLM通过工具检索数据时触发
- 更隐蔽，更难检测

**重要论文**

| 论文 | 作者 | 年份 | 贡献 |
|------|------|------|------|
| Indirect Prompt Injection | Microsoft Research | 2024 | 首次系统性研究IPI |
| InjecAgent | ACL Findings | 2024 | 工具集成LLM的IPI基准 |
| ObliInjection | - | 2025 | 多源数据顺序无关的注入 |

**InjecAgent (ACL Findings 2024)**
- 首个针对工具集成LLM的IPI基准
- 评估LLM代理在工具使用场景下的脆弱性

**TopicAttack (arXiv:2507.13686)**
- 通过主题转换的间接提示注入
- 更自然的攻击方式，避免突兀的指令注入

### 1.3 工具选择攻击

**ToolHijacker (arXiv:2504.19793)**
- 针对LLM代理的工具选择过程
- 将恶意工具文档注入工具库
- 两阶段优化策略生成攻击

---

## 2. LLM Agent安全研究

### 2.1 Agent架构安全

**Agent Security Bench (ASB) - ICLR 2025**
- 综合性LLM代理安全评估框架
- 10个场景（电商、自动驾驶、金融等）
- 10个目标代理，400+工具
- 27种攻击/防御方法

**关键攻击类型**:
1. 直接提示注入 (DPI)
2. 间接提示注入 (IPI)
3. 内存中毒
4. 思维链(PoT)后门攻击
5. 混合攻击

### 2.2 Agent框架漏洞

**LangChain安全漏洞**
- CVE-2023-29374: 代码注入漏洞
  - LLMMathChain允许通过exec()执行任意代码
  - 严重性：Critical
- 序列化注入漏洞 (GHSA-c67j-w6g6-q2cm)
  - dumps/loads API中的反序列化攻击
  - 可导致密钥泄露

### 2.3 多代理系统

**TradingAgents**
- LLM多代理金融交易框架
- 代理间通信安全研究

---

## 3. DoS攻击研究

### 3.1 LLM DoS攻击

**ThinkTrap (arXiv:2512.07086)**
- 标题: "Denial-of-Service Attacks against Black-box LLM Services via Infinite Thinking"
- 核心: 通过"无限思考"机制触发DoS
- 攻击LLM的推理过程使其陷入无限循环
- 上海交通大学研究

**关键发现**:
- LLM的推理能力可被滥用于DoS
- 黑盒服务同样易受攻击
- 传统DoS防御对LLM无效

### 3.2 API配额耗尽攻击

**相关研究较少** - 这是一个新兴研究领域

**LLM Safeguard DoS (arXiv:2410.02916)**
- 利用安全过滤器的误报进行DoS攻击
- 攻击者触发误报导致服务不可用

---

## 4. 基准测试与评估框架

### 4.1 安全基准

| 基准 | 场景数 | 工具数 | 攻击类型 |
|------|--------|--------|----------|
| AgentDojo | 4 | 20+ | 数据泄露 |
| InjecAgent | 5 | 15+ | IPI |
| ASB | 10 | 400+ | 全面 |
| AgentBench | 8 | 多 | 能力评估 |

### 4.2 数据集

**Tensor Trust数据集**
- 126,000+提示词注入攻击
- 46,000+防御示例
- 最大人类生成对抗性数据集

---

## 5. 防御机制研究

### 5.1 模型级防御

**Meta SecAlign (arXiv:2507.02735)**
- 首个开源模型级防御
- 商业级性能
- 通用指令微调数据集

### 5.2 检测方法

**DataSentinel (IEEE S&P 2025)**
- 博弈论方法检测提示注入
- 对抗性自适应攻击
- 微调LLM检测污染输入

**MELON (arXiv:2502.05174)**
- 掩码重执行+工具比较
- 无需模型训练
- 防御IPI攻击

### 5.3 微软防御实践

**多层防御策略**:
1. 硬化系统提示词
2. Spotlighting隔离不可信输入
3. 数据治理
4. 用户同意工作流

---

## 6. 相关漏洞披露

### 6.1 MCP相关

**Slack MCP Server数据泄露**
- Link Unfurling导致数据泄露
- 2025年6月发现

### 6.2 LLM应用漏洞

**OWASP LLM Top 10 (2025)**
- LLM01: Prompt Injection (首位)
- LLM02: Sensitive Information Disclosure
- LLM03: Supply Chain Vulnerabilities
- ...

---

## 7. 总结与研究机会

### 7.1 现有研究空白

1. **API配额DoS攻击** - 几乎无研究
   - 通过prompt injection耗尽用户API配额
   - 利用agent的递归/循环机制

2. **MCP协议安全** - 缺乏学术研究
   - MCP作为新兴协议，安全研究不足
   - 工具调度器权限模型风险

3. **Agent系统DoS** - 新兴领域
   - ThinkTrap是首个相关研究
   - 针对推理过程的DoS

### 7.2 本研究的创新点

| 方向 | 现有研究 | 本研究 |
|------|----------|--------|
| 攻击目标 | 数据泄露、权限提升 | API配额耗尽 |
| 攻击向量 | 提示注入 | 递归任务分解 |
| 目标系统 | 通用LLM | Claude Code等Agent系统 |
| 攻击方式 | 单次注入 | 持续性DoS |

### 7.3 参考文献

1. Tensor Trust: arXiv:2311.01011
2. Signed-Prompt: arXiv:2401.07612
3. InjecAgent: ACL Findings 2024
4. ToolHijacker: arXiv:2504.19793
5. ASB: arXiv:2410.02644 (ICLR 2025)
6. ThinkTrap: arXiv:2512.07086
7. Meta SecAlign: arXiv:2507.02735
8. DataSentinel: IEEE S&P 2025
9. MELON: arXiv:2502.05174
10. LLM Safeguard DoS: arXiv:2410.02916
11. OWASP LLM Top 10 2025

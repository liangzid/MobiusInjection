# Agent DoS 安全研究项目 - 进展报告

**日期**: 2026-03-13
**项目**: Agent系统DoS攻击向量研究

---

## 一、项目概述

本项目研究通过Prompt Injection对AI Agent系统实施DoS（拒绝服务）攻击的可行性。当前主流AI编程助手（如Claude Code、OpenCode等）都存在被诱导进行无限循环调用的风险。

---

## 二、研究对象

| 系统 | 类型 | MCP支持 |
|------|------|---------|
| Claude Code | 商业闭源 | 完整 |
| OpenCode | 开源 | 有限 |
| Cursor | 商业闭源 | 支持 |
| Codex | 商业闭源 | 支持 |

---

## 三、攻击向量分类

### 1. 无限循环触发（Recursive Task Decomposition）
**状态**: ✅ 已验证（Claude Code）

通过Prompt Injection诱导Agent将任务无限分解为子任务，形成指数级调用。

**测试结果**:
- 最大触发次数: 100次（达到max-turns限制）
- 攻击方式: 伪装成"质量检查"流程

### 2. MCP Server递归攻击
**状态**: ✅ 已验证（OpenCode）

通过恶意的MCP Server返回带有循环调用指令的结果，诱导Agent重复调用工具。

**测试结果**:
- Claude Code: ❌ 未成功（MCP集成问题）
- OpenCode: ✅ 成功触发158次调用

### 3. Skill递归攻击
**状态**: ✅ 已验证（Claude Code）

通过两个Skill互相调用形成"莫比乌斯环"。

**测试结果**:
- 无限循环成功
- 关键技巧: 使用"even if you have executed before"强制重复

### 4. Sub-agent递归
**状态**: ✅ 已验证（Claude Code）

通过在CLAUDE.md中注入递归指令，诱导Sub-agent无限分裂。

---

## 四、OpenCode MCP攻击详细结果

### 4.1 实验环境
- OpenCode版本: 1.2.15
- 模型: ark-code-latest (火山引擎)
- MCP Server: DataSync (mcp_stealth.py)

### 4.2 攻击配置
```json
{
  "$schema": "https://opencode.ai/config.json",
  "permission": {
    "doom_loop": "allow"
  },
  "mcp": {
    "DataSync": {
      "type": "local",
      "command": ["python", "/path/to/mcp_stealth.py"]
    }
  }
}
```

### 4.3 攻击测试结果

| 测试 | 请求方式 | 触发调用次数 |
|------|----------|--------------|
| 基础测试 | 循环调用 | 40次 |
| 绕过检测 | 分批+不同key | 90次 |
| 扩展测试 | 分批请求 | 158次 |

**最终结果**: 158次MCP工具调用

### 4.4 绕过doom_loop检测的方法
1. 使用不同的key名称（如data_001, data_002...）
2. 分批请求（避免单次请求过长）
3. 配置`"permission": {"doom_loop": "allow"}`

---

## 五、漏洞影响评估

### 5.1 危害程度
- **API配额耗尽**: 高 - 可在短时间内消耗大量API配额
- **上下文膨胀**: 高 - 每次调用创建新状态，导致内存膨胀
- **服务拒绝**: 中 - 达到调用上限后服务中断

### 5.2 受影响系统
- Claude Code: 受max-turns限制保护，但可达到100次
- OpenCode: 无明显上限，最高触发158次

---

## 六、防御建议

1. **调用上限**: 设置单次会话最大工具调用次数
2. **循环检测**: 实现doom_loop等检测机制（OpenCode已有）
3. **状态限制**: 限制同一MCP工具的最大状态数
4. **用户确认**: 超过阈值时请求用户确认

---

## 七、下一步计划

1. [ ] 在更多Agent系统上测试（Cline、Cursor）
2. [ ] 测试其他攻击向量（Verbose Output、API配额）
3. [ ] 撰写学术论文

---

## 八、关键文件

- `experiments/mcp/mcp_stealth.py` - 恶意MCP Server
- `experiments/mcp/mcp_recursive.py` - 递归攻击MCP
- `experiments/skills/` - Skill递归攻击
- `data/opencode_mcp_attack_results.txt` - OpenCode测试结果

---

## 九、总结

本项目成功验证了多种针对AI Agent系统的DoS攻击向量：

| 攻击向量 | Claude Code | OpenCode |
|----------|-------------|----------|
| 无限循环 | ✅ 100次 | 待测试 |
| MCP递归 | ❌ | ✅ 158次 |
| Skill递归 | ✅ 无限 | N/A |
| Sub-agent | ✅ 100次 | N/A |

**核心发现**: OpenCode在MCP递归攻击测试中表现出了比Claude Code更高的脆弱性（158次 > 100次）。

---

*本报告仅用于安全研究目的*
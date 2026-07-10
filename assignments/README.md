# 作业总览

本集训基于 Stanford CS336。A1-A5 提前给出 Stanford 原版仓库，便于了解主题和工作量；实验室正式版本可能修改题目、代码、数据、算力限制、评测和提交物，必须以发布时的实验室题面与组织内公开的飞书补充文档为准。

| 作业 | 主题 | 状态 | 原版或说明 |
| --- | --- | --- | --- |
| [A0](A0/README.md) | Linux、GitHub、服务器环境与双层 Profile | 已发布 | 实验室原创入口作业 |
| [A1](A1/README.md) | Basics | 预告 | [Stanford 原版 assignment1-basics](https://github.com/stanford-cs336/assignment1-basics) |
| [A2](A2/README.md) | Systems | 预告 | [Stanford 原版 assignment2-systems](https://github.com/stanford-cs336/assignment2-systems) |
| [A3](A3/README.md) | Scaling | 预告 | [Stanford 原版 assignment3-scaling](https://github.com/stanford-cs336/assignment3-scaling) |
| [A4](A4/README.md) | Data | 预告 | [Stanford 原版 assignment4-data](https://github.com/stanford-cs336/assignment4-data) |
| [A5](A5/README.md) | Alignment | 预告 | [Stanford 原版 assignment5-alignment](https://github.com/stanford-cs336/assignment5-alignment) |
| [A6](A6/README.md) | 内容待公布 | 预告 | 具体题目后续发布 |

## 所有作业的共同提交结构

```text
students/<同学真名>/assignments/<A编号>/
└── README.md    # 公开、脱敏的报告，并填写组织内公开的飞书补充文档链接
```

A1-A6 正式发布后使用脚手架创建对应目录：

```bash
python scripts/create_assignment.py --name '<同学真名>' --assignment A1
```

课程题面、资料与个人提交都可能包含不适合公开的组内内容。请在开始任何作业前阅读 [公开性与提交规则](../docs/submission-rules.md)。

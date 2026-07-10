# A0：基础环境、GitHub 与双层 Profile

## 目标

A0 是后续 A1-A6 的入口作业。完成后，你应当能够：

1. 使用 Git 和 GitHub 完成 Fork、分支、commit、push 与 PR。
2. 通过 SSH 使用实验室分配的个人 CPU 服务器，完成基本 Linux 操作和用户级 Python 环境管理。
3. 安装 `gpustat`，实际运行 `nvidia-smi` 与 `gpustat`，正确解释有 GPU、无 GPU或驱动不可用时的状态。
4. 建立公开 GitHub profile 与组织内公开的飞书 profile。
5. 区分公开材料、组内材料和机密凭据，避免把实验室内部信息或密钥提交到 GitHub。

## 开始前

- 已获得实验室分配的个人 CPU 服务器账号和 SSH 登录方式。
- 已有 GitHub 账号和实验室飞书账号。
- 已阅读 [公开性与提交规则](../../docs/submission-rules.md)。
- 已在 [新生 GitHub ID 收集表](https://fudan-nlp.feishu.cn/base/VaJ4b0k62aVqqdsXYF8cSTMpn9f) 登记真实姓名和 GitHub ID。

服务器、账号、内部 IP、主机名和登录方式属于组内信息。不要写入公开 GitHub 文件。

如果服务器账号、Python 包源或实验室网络阻塞任务，请立即联系课程助教并在组内文档记录阻塞。平台或管理员原因不扣分；不要绕过权限、借用他人凭据或自行修改系统级驱动。

## 提交目录

使用脚手架创建个人目录：

```bash
python scripts/create_student.py --name '<同学真名>' --github '<GitHub ID>'
```

脚手架将创建：

```text
students/<同学真名>/
├── PROFILE.md
└── assignments/
    └── A0/
        └── README.md
```

`<同学真名>` 必须是真实中文姓名或日常使用的完整真实姓名，不使用 GitHub ID、拼音、昵称或英文缩写，也不包含空格。

## 任务 1：完成 GitHub 基本操作

1. Fork 本仓库并 clone 到个人服务器。
2. 添加实验室仓库为 `upstream`。
3. 从最新 `upstream/main` 创建 `a0/<GitHub ID>` 分支。
4. 只在 `students/<同学真名>/` 中完成 A0。
5. 使用 Conventional Commits 提交并向上游仓库创建 PR。

建议命令见 [标准 PR 流程](../../docs/submission-rules.md#3-一次作业的标准-pr-流程)。

公开 `students/<同学真名>/assignments/A0/README.md` 中记录你的分支名和一段简短的 Git 操作总结。PR 链接由 GitHub 本身保存，不要在报告中维护会过期的 commit hash 或 PR URL；也不要记录服务器地址、内部仓库凭据或 SSH 配置。

## 任务 2：完成 Linux 与 Python 环境操作

通过 SSH 登录个人服务器，在自己的 home 目录下完成以下操作：

1. 查看当前用户、工作目录、操作系统、CPU、内存和 home 分区空间。
2. 创建 `~/openmoss-a0` 工作目录。
3. 创建用户级 Python virtual environment，不使用 `sudo pip`。
4. 创建一个模拟密钥文件并把权限设置为仅当前用户可读写，以理解敏感配置文件的权限要求。
5. 查看当前用户进程，并选择一种可在 SSH 断开后继续运行进程的方式。

参考命令：

```bash
whoami
pwd
uname -srm
cat /etc/os-release
lscpu
free -h
df -h "$HOME"

mkdir -p ~/openmoss-a0
python3 -m venv ~/.venvs/openmoss-a0
source ~/.venvs/openmoss-a0/bin/activate
python -m pip install --upgrade pip

touch ~/openmoss-a0/example.env
chmod 600 ~/openmoss-a0/example.env
stat -c '%a %n' ~/openmoss-a0/example.env
ps -u "$USER" -o pid,stat,etime,comm
```

组内飞书文档也只保留审核所需且已经检查、脱敏的最小输出，不上传环境变量、完整命令行、其他用户进程或凭据页面。公开 GitHub 报告只写操作系统类型、Python 版本和权限检查结论，并删除用户名、主机名、IP、内部路径、硬件容量和进程参数。

## 任务 3：安装并检查 `gpustat`

在上一步的 virtual environment 中安装：

```bash
source ~/.venvs/openmoss-a0/bin/activate
python -m pip install gpustat
python -m pip show gpustat
```

然后分别运行 `nvidia-smi` 和 `gpustat`，记录命令输出与退出码：

```bash
set +e

nvidia-smi
nvidia_smi_exit_code=$?
printf 'nvidia-smi exit_code=%s\n' "$nvidia_smi_exit_code"

gpustat
gpustat_exit_code=$?
printf 'gpustat exit_code=%s\n' "$gpustat_exit_code"
```

个人服务器可能没有 NVIDIA GPU，`nvidia-smi` 也可能不存在或无法连接驱动。A0 不要求命令必须成功；验收重点是你确实执行了两个命令、保留退出码，并能解释看到的状态。不要为了让命令成功而安装内核驱动或使用 `sudo` 修改系统环境。

提交要求：

- 公开 GitHub 报告：写出两个命令的退出码、状态类别及你的解释。不要公开 GPU 型号、数量、UUID、利用率、进程或服务器容量。
- 组内飞书文档：保存助教核验所需的最小脱敏输出；删除进程区、主机名、用户名、内部路径、UUID 和无关硬件信息。

以下状态均可获得同等分数：命令成功、命令不存在、未检测到设备、NVML/驱动不可用。前提是你真实执行、记录退出码，并能区分“没有 GPU”和“当前无法检查”。安装包源或实验室网络故障按基础设施问题联系助教处理。

## 任务 4：建立双层个人 Profile

填写公开 `PROFILE.md`。模板覆盖个人简介、研究兴趣、公开经历、CS336 学习计划、技能，以及可选的特长和日常信息；完整写法可参考 [`PROFILE.example.md`](../../students/_template/PROFILE.example.md)。示例中的人物和经历均为虚构内容，不要复制为自己的经历。

家乡、生日、MBTI、饮食、游戏、学校和导师等字段均为可选项，不填写不影响 A0 评分。填写前应确认自己愿意让这些信息长期公开；详细联系方式、完整生日、住址、个人账号凭据和其他敏感信息不得提交到 GitHub。

创建一个组织内公开的飞书文档或 Wiki 主页，作为更完整的组内 profile，并把链接与权限状态写入 `PROFILE.md`。飞书主页建议包括：

- 个人简介和研究兴趣。
- 项目与学习经历。
- 课程笔记和后续作业索引。
- 希望在组织内持续维护的课程材料索引。

GitHub profile 是公开的；飞书 profile 设置为组织内公开，不得开启互联网公开访问，也不能把组织内 profile 正文复制到 GitHub。

## 完成后填写提交表格

完成 A0 的 GitHub、Linux、GPU 状态检查和双层 Profile 后，填写 [A0 完成登记表](https://fudan-nlp.feishu.cn/share/base/form/shrcnlJtPIL2M6NIEyWyPqlicAb)。

A0 不再要求创建、部署或验收飞书机器人，也不进行 `/ping`、随机 nonce、常驻进程或重启验证。仓库中的飞书机器人 starter 仅作为可选资料，不属于 A0 提交物或评分项。

## 公开提交物

- `students/<同学真名>/PROFILE.md`
- `students/<同学真名>/assignments/A0/README.md`

## 组内提交物

A0 飞书补充文档应包含组织内公开、最小必要且已经脱敏的：

- Linux 命令与环境检查记录。
- `nvidia-smi` 和 `gpustat` 关键输出、退出码及解释。
- 遇到的问题、排查过程和最终状态。

## 验收标准

| 项目 | 比例 | 验收重点 |
| --- | ---: | --- |
| GitHub 与 PR | 25% | Fork、分支、commit、PR 与修改范围正确 |
| Linux 与 GPU 状态 | 35% | 完成基本操作，安装 `gpustat`，真实记录两个命令及退出码；无 GPU/命令失败可同等得分 |
| 双层 Profile | 30% | GitHub 与飞书个人资料完整，公开范围和权限正确 |
| 安全与可读性 | 10% | 无密钥、无内部地址、公开报告脱敏、飞书证据可由助教读取 |

完成登记表为 A0 提交流程的必需步骤，不单独计分。

以下任一情况会要求修正后再审核：

- 提交任何 Secret、Token、Cookie、密码或私钥。
- 在 GitHub 暴露内部服务器地址、主机名、账号或组内材料。
- 飞书文档设置为互联网公开，或未设置为组织内公开。
- 未实际运行 `nvidia-smi` 与 `gpustat`，只写预期结果。
- 完成后未填写 A0 完成登记表。

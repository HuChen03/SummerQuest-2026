# A1 公开提交：胡宸

## 基本信息

- 作业题面版本：26.0.3
- 上游 starter commit：`a158843b20107949f1a8d7df1b05cd33b9166712`
- 本地工作仓库：`../assignment1-basics`
- 完成范围：byte-level BPE tokenizer、Transformer LM、训练组件、checkpoint、数据编码、训练脚本、生成脚本、TinyStories 实验、架构消融、learning-rate sweep、batch-size sweep、OWT 训练与生成。
- 未提交内容：数据文件、tokenized `.bin`、tokenizer 产物和 checkpoint 均保存在 `../assignment1-basics/runs/`，不进入公开 PR。

## 实现说明

真实实现位于 `submission/cs336_basics/`：

- `model.py`：Linear、Embedding、RMSNorm、SwiGLU、SiLU FFN、RoPE、masked scaled dot-product attention、causal MHA、Transformer block、Transformer LM、stable softmax、cross-entropy。
- `tokenizer.py`：GPT-2 regex pre-tokenization、byte-level BPE 训练、special token 边界处理、encode/decode、streaming `encode_iterable`。
- `optim.py`：from-scratch AdamW。
- `training.py`：random token batch、cosine schedule、global gradient clipping。
- `serialization.py`：model/optimizer/iteration checkpoint 保存与恢复。

`submission/tests/adapters.py` 保留公共测试的 21 个 adapter 函数签名，只转发到真实实现。

## 复现脚本

基础脚本：

- `submission/scripts/train_tokenizer.py`：训练 BPE tokenizer。
- `submission/scripts/encode.py`：把文本编码成 `uint16`/`uint32` token id 文件。
- `submission/scripts/train_lm.py`：训练 Transformer LM，支持 mmap、validation、checkpoint、resume 和 ablation 参数。
- `submission/scripts/generate.py`：temperature + top-p 自回归生成。
- `submission/scripts/evaluate_lm.py`：checkpoint 评估和生成样例。

实验入口：

- `submission/scripts/run_tinystories_gpu_experiments.sh`：TinyStories baseline、四个架构消融、LR sweep、batch-size sweep 和样例生成。
- `submission/scripts/run_tinystories_target45_experiments.sh`：TinyStories valid loss 1.45 目标改进实验。
- `submission/scripts/run_owt_gpu_full_experiment.sh`：OWT tokenizer/encode/full-model train/generate 链路。
- `submission/scripts/run_required_gpu_experiments.sh`：顺序执行 TinyStories 实验、OWT encode、OWT 训练。
- `submission/scripts/run_cpu_training.sh`、`run_cpu_eval.sh`、`run_full_cpu_experiment.sh`：CPU smoke 和低资源复现入口。

公共测试：

```bash
cd ../assignment1-basics
uv run pytest
```

最新结果见 `logs/public-tests.md`：`47 passed, 1 xpassed in 123.31s`。

## Tokenizer 与编码

| 数据集 | tokenizer vocab | train raw bytes | train tokens | train bytes/token | valid raw bytes | valid tokens | valid bytes/token |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| TinyStories | 10,000 | 2,227,753,162 | 540,793,471 | 4.119 | 22,502,601 | 5,461,167 | 4.120 |
| OpenWebText | 32,000 | 11,920,511,059 | 262,963,181 | 45.331 | 289,998,753 | 66,401,098 | 4.367 |

TinyStories tokenizer 训练约 9.2 分钟；train split 编码约 60.3 分钟，valid split 编码约 39 秒。OWT 32K tokenizer 训练从 2026-07-14 11:45:06 UTC 到 2026-07-15 05:03:40 UTC，约 17.3 小时；OWT train/valid 编码后的 `.bin` 文件用于后续 GPU 训练。

说明：不同 tokenizer 和不同数据集的 per-token loss 不直接可比。OWT train split 的 bytes/token 明显高于 valid split，报告中只把它作为本次产物统计和复现实验记录，不作为 tokenizer 质量的单独结论。

## 模型规模与计算

TinyStories/OWT full-model 架构相同：context length 256，`d_model=512`，`d_ff=1344`，4 layers，16 heads，RoPE theta 10000，Pre-Norm RMSNorm，SwiGLU FFN。实现使用 untied token embedding 和 LM head。

| 配置 | vocab | 参数量 | fp32 参数内存 | AdamW 训练状态估算 |
| --- | ---: | ---: | ---: | ---: |
| TinyStories full model | 10,000 | 22,696,448 | 86.6 MiB | 0.338 GiB |
| OWT full model | 32,000 | 45,224,448 | 172.5 MiB | 0.674 GiB |

参数公式：

```text
2 * vocab_size * d_model
+ num_layers * (4 * d_model^2 + 3 * d_model * d_ff + 2 * d_model)
+ d_model
```

AdamW 训练状态按 fp32 参数、梯度、一阶矩和二阶矩估算，即约 `16 * num_parameters` bytes，不含 activations、temporary tensors 和 allocator overhead。

矩阵乘法 FLOPs 采用 `2mnp` 估算。对 GPT-2 family 形状，按 tied embedding、context 1024、MLP width `4d`、每层 attention+MLP 近似估算：

| GPT-2 shape | layers | d_model | heads | 参数量估算 | AdamW 状态估算 | B=1,T=1024 forward FLOPs 估算 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| small | 12 | 768 | 12 | 124.3M | 1.85 GiB | 0.292 TFLOPs |
| medium | 24 | 1024 | 16 | 354.6M | 5.28 GiB | 0.827 TFLOPs |
| large | 36 | 1280 | 20 | 773.5M | 11.53 GiB | 1.775 TFLOPs |
| XL | 48 | 1600 | 25 | 1,556.8M | 23.20 GiB | 3.507 TFLOPs |

## TinyStories 训练结果

主目标配置：`batch_size=128`，`context_length=256`，`steps=10000`，processed tokens `327,680,000`。

| run | steps | batch | LR | train loss | valid loss | elapsed | tokens/sec | 结论 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `tinystories_gpu_baseline` | 10,000 | 128 | 3e-4 -> 3e-5 | 1.5004 | 1.5109 | 1014.2s | 323k | baseline 未达到 1.45 |
| `tinystories_gpu_target45_continue20k` | 20,000 | 128 | continued | 1.5047 | 1.4552 | 1024.0s | - | 接近但仍高于 1.45 |
| `tinystories_gpu_target45_highlr10k` | 10,000 | 128 | 3e-3 -> 3e-4 | 1.3377 | 1.3517 | 817.8s | 321k | 达到 1.45 目标 |

`target45_highlr10k` 从 `tinystories_gpu_lr_3em3.pt` 的 2000-step checkpoint 续训到 10000 step，因此表中 tokens/sec 按新增 8000 step 计算。其 validation loss 1.3517 是本次 TinyStories 主结果。

## 必做实验

完整实验日志见 `logs/gpu-experiments.md`。

架构消融均使用 TinyStories full-model 设置，除被测变量外保持 baseline 配置：

| run | 改动 | valid loss | 相对 baseline |
| --- | --- | ---: | ---: |
| baseline | Pre-Norm + RMSNorm + RoPE + SwiGLU | 1.5109 | 0.0000 |
| no RMSNorm | 删除 RMSNorm | 1.5400 | +0.0291 |
| post norm | Pre-Norm 改 Post-Norm | 1.5114 | +0.0006 |
| no RoPE | RoPE 改 NoPE | 1.6039 | +0.0930 |
| SiLU FFN | 参数量近似匹配的 SiLU FFN (`silu_d_ff=2016`) | 1.5481 | +0.0372 |

LR sweep 包含一个发散/不稳定 run：

| max LR | steps | valid loss | 观察 |
| ---: | ---: | ---: | --- |
| 1e-4 | 2,000 | 2.4335 | 明显欠训练 |
| 3e-4 | 2,000 | 1.9387 | 稳定但慢 |
| 1e-3 | 2,000 | 1.6411 | 更快收敛 |
| 3e-3 | 2,000 | 1.5629 | 本 sweep 最好，并作为 high-LR 续训 seed |
| 1e-1 | 2,000 | 3.8268 | 不稳定/发散 |

Batch sweep 覆盖 1 到 128，包括 64 和 128。batch 1-32 只跑 1000 steps；batch 64/128 跑 10000 steps，所以两组不能直接按最终 loss 比较：

| batch | steps | processed tokens | valid loss |
| ---: | ---: | ---: | ---: |
| 1 | 1,000 | 256,000 | 3.6470 |
| 2 | 1,000 | 512,000 | 3.2888 |
| 4 | 1,000 | 1,024,000 | 3.0544 |
| 8 | 1,000 | 2,048,000 | 2.8968 |
| 16 | 1,000 | 4,096,000 | 2.6904 |
| 32 | 1,000 | 8,192,000 | 2.5129 |
| 64 | 10,000 | 163,840,000 | 1.5675 |
| 128 | 10,000 | 327,680,000 | 1.5109 |

## OWT 训练与生成

OWT 使用相同 Transformer 架构，vocab size 改为 32,000，`batch_size=32`，`steps=10000`，processed tokens `81,920,000`。

| run | train tokens | valid tokens | train loss | valid loss | elapsed | tokens/sec |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `owt_gpu_full` | 262,963,181 | 66,401,098 | 4.6059 | 4.6234 | 395.2s | 207k |

生成样例见 `logs/generation-samples.md`。TinyStories 样例语法通顺、儿童故事结构明显，但结尾因果关系有轻微不一致；OWT 样例更像新闻/百科文本，局部短语流畅，但事实和篇章连贯性较弱。影响生成质量的因素包括数据域、tokenizer、训练 token 数、模型容量、采样 temperature/top-p 和 validation loss。

## 提交文件清单

- `README.md`：本报告。
- `submission/cs336_basics/`：真实实现。
- `submission/tests/adapters.py`：公共测试 adapter。
- `submission/scripts/`：训练、编码、生成和实验脚本。
- `logs/public-tests.md`：公共测试结果。
- `logs/gpu-experiments.md`：TinyStories/OWT 训练实验摘要。
- `logs/generation-samples.md`：生成样例和分析。

所有提交文件均为文本小文件；未复制数据、checkpoint、tokenizer JSON/merges 或二进制 token 文件。

## 飞书补充文档

- 链接：https://fudan-nlp.feishu.cn/wiki/L1SJwDyfci6fbgkuo4xcrzDnnsc?from=from_copylink

本次公开 README 和 `logs/` 已包含主要实验结果；飞书入口用于组织内补充说明。

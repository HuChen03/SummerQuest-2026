# A1 实现梳理

## 目标

这份文档用于记录 A1 的实现过程，以及 `submission/` 中各个函数和脚本的作用。原始提交说明仍保留在 `README.md`。

## 目录结构

```text
submission/
├── cs336_basics/
│   ├── model.py
│   ├── tokenizer.py
│   ├── optim.py
│   ├── training.py
│   ├── serialization.py
│   └── pretokenization_example.py
├── tests/
│   └── adapters.py
└── scripts/
    ├── train_tokenizer.py
    ├── encode.py
    ├── train_lm.py
    └── generate.py
```

`submission/tests/adapters.py` 保留公共测试要求的 21 个函数签名，只做薄转发；真实逻辑全部放在 `submission/cs336_basics/`。

## 实现过程

1. 先阅读 A1 README 和公共测试，确认必须实现的稳定 ABI 是 `tests/adapters.py` 中的 21 个 adapter 函数。
2. 将实现按功能拆到 `cs336_basics/`：
   - `model.py` 负责神经网络基本算子和 Transformer LM。
   - `tokenizer.py` 负责 byte-level BPE tokenizer 和 BPE 训练。
   - `optim.py` 负责 AdamW。
   - `training.py` 负责训练辅助函数。
   - `serialization.py` 负责 checkpoint。
3. 实现模型数值算子时，不使用 `nn.Linear`、`nn.Embedding`、`torch.nn.functional.softmax`、`torch.nn.functional.cross_entropy` 等现成实现；只使用 `torch.nn.Module`、`ModuleList`、`Parameter` 和 `torch.optim.Optimizer` 基类。
4. 实现 tokenizer 时，使用 GPT-2 风格预分词正则，先把文本切成 pre-token，再在每个 pre-token 内做 byte-level BPE；special token 单独匹配，不参与普通 merge。
5. BPE 训练一开始使用全量重算 pair counts 的写法，正确但速度不够；之后改成维护 `pair_counts` 和 `pair_to_words`，每次 merge 只更新受影响的 pre-token，满足公共测试的速度要求。
6. 实现 adapter 后运行公共测试，修正数值、RoPE、特殊 token 和 BPE 性能问题，最终通过公共测试。
7. 使用 `scripts/sync_a1_submission.py --name '胡宸'` 将兄弟仓库中的实现同步到本提交目录。

## Transformer 与训练部分

### `model.py`

#### 基础函数

- `linear(x, weight)`：执行无 bias 线性层，计算 `x @ weight.T`。公共测试通过给定权重验证输出。
- `embedding(token_ids, weight)`：根据 token id 从 embedding 矩阵中取向量。
- `silu(x)`：实现 SiLU 激活函数 `x * sigmoid(x)`。
- `rmsnorm(x, weight, eps)`：实现 RMSNorm。先在最后一维计算均方根归一化，再乘可学习缩放参数。
- `swiglu(x, w1_weight, w2_weight, w3_weight)`：实现 SwiGLU 前馈网络，形式为 `W2(SiLU(W1x) * W3x)`。
- `softmax(x, dim)`：数值稳定 softmax。先减去指定维度最大值，再指数归一化。
- `cross_entropy(logits, targets)`：实现平均交叉熵。使用 log-sum-exp 思路避免大 logits 溢出。

#### Attention 和 RoPE

- `scaled_dot_product_attention(q, k, v, mask)`：计算 `softmax(QK^T / sqrt(d_k))V`。如果传入 mask，则把不可见位置置为极小值。
- `rope(x, theta, max_seq_len, token_positions)`：实现 rotary positional embedding。对偶数/奇数维成对旋转，使 query/key 注入位置信息。
- `_split_heads(x, num_heads)`：把最后一维 `d_model` 拆成 `(num_heads, head_dim)`，供多头注意力使用。
- `_combine_heads(x)`：把多头注意力输出重新合并回 `d_model`。
- `multihead_self_attention(...)`：一次性做 Q/K/V 投影、分头、可选 RoPE、因果 mask attention 和输出投影。

#### Transformer 前向

- `transformer_block(x, num_heads, max_seq_len, theta, weights)`：实现 pre-norm Transformer block。流程是 `x + attention(RMSNorm(x))`，再 `x + SwiGLU(RMSNorm(x))`。
- `transformer_lm(in_indices, num_layers, num_heads, context_length, rope_theta, weights)`：实现完整 Transformer LM 前向。流程是 token embedding、多层 block、final RMSNorm、LM head。

#### 可训练模块类

- `Linear`：无 bias 线性层模块，内部参数名为 `weight`。
- `Embedding`：embedding 模块，内部参数名为 `weight`。
- `RMSNorm`：RMSNorm 模块，内部参数名为 `weight`。
- `SwiGLU`：由 `w1`、`w2`、`w3` 三个 `Linear` 组成的前馈模块。
- `MultiheadSelfAttention`：可训练多头自注意力模块，包含 `q_proj`、`k_proj`、`v_proj`、`output_proj`。
- `TransformerBlock`：可训练 Transformer block，包含 attention、两个 RMSNorm 和 SwiGLU。
- `TransformerLM`：可训练语言模型，包含 token embedding、多层 Transformer block、final norm 和 LM head。

### `training.py`

- `get_batch(dataset, batch_size, context_length, device)`：从一维 token id 数组中随机采样 batch。返回 `x` 和右移一位的 `y`。
- `clip_gradients(parameters, max_l2_norm)`：计算所有参数梯度的全局 L2 norm。如果超过阈值，按比例原地缩放梯度。
- `cosine_lr_schedule(it, max_learning_rate, min_learning_rate, warmup_iters, cosine_cycle_iters)`：实现 warmup + cosine decay 学习率。warmup 阶段线性升高，之后余弦衰减，到周期结束后保持最小学习率。

### `optim.py`

- `AdamW`：从 `torch.optim.Optimizer` 基类实现 AdamW。维护一阶矩 `exp_avg`、二阶矩 `exp_avg_sq` 和 step，先做 decoupled weight decay，再做 Adam 更新。

### `serialization.py`

- `save_checkpoint(model, optimizer, iteration, out)`：保存模型 state dict、优化器 state dict 和当前 iteration。
- `load_checkpoint(src, model, optimizer)`：加载 checkpoint，恢复模型和优化器状态，并返回保存时的 iteration。

## Tokenizer 部分

### `tokenizer.py`

- `GPT2_PRETOKEN_PATTERN`：GPT-2 风格预分词正则。用于把文本切成单词、数字、标点、空白等 pre-token。
- `_special_pattern(special_tokens)`：把 special token 列表编译成正则。按长度从长到短排序，避免重叠 special token 被短 token 先匹配。
- `_split_on_specials(text, special_tokens)`：把文本切成普通文本片段和 special token 片段。返回 `(piece, is_special)`。
- `_pretoken_bytes(text)`：对普通文本片段做 GPT-2 风格预分词，并把每个 pre-token 编码成 UTF-8 bytes。
- `_merge_word(word, pair)`：给 tokenizer 编码阶段使用，把一个 token 序列中的指定相邻 pair 合并。
- `train_bpe(input_path, vocab_size, special_tokens)`：训练 byte-level BPE。初始词表包含 256 个单 byte token 和 special tokens；随后统计 pre-token 内的相邻 pair，反复选择最高频 pair 合并，频率相同时选择字典序更大的 pair。
- `Tokenizer`：BPE tokenizer 类，负责编码、流式编码和解码。

### `Tokenizer` 方法

- `Tokenizer.__init__(vocab, merges, special_tokens)`：保存词表、反向词表、merge rank 和 special token id。
- `Tokenizer.from_files(vocab_filepath, merges_filepath, special_tokens)`：从脚本保存的 tokenizer 文件中恢复 tokenizer。
- `Tokenizer._encode_bytes(token_bytes)`：对一个 pre-token 的 byte 序列按 merge rank 反复合并，输出 token ids。
- `Tokenizer.encode(text)`：把完整字符串编码为 token id 列表。special token 保持为一个整体，普通文本走预分词和 BPE。
- `Tokenizer.encode_iterable(iterable)`：对文本迭代器逐块编码，适合大文件。
- `Tokenizer.decode(ids)`：把 token id 序列拼接回 bytes，再按 UTF-8 解码成字符串。

## Adapter 函数作用

`submission/tests/adapters.py` 中的函数是公共测试入口：

- `run_linear`：调用 `linear`，测试线性层。
- `run_embedding`：调用 `embedding`，测试 embedding 查表。
- `run_swiglu`：调用 `swiglu`，测试 SwiGLU 前馈网络。
- `run_scaled_dot_product_attention`：调用 `scaled_dot_product_attention`，测试 attention 核心计算。
- `run_multihead_self_attention`：调用不带 RoPE 的 `multihead_self_attention`。
- `run_multihead_self_attention_with_rope`：调用带 RoPE 的 `multihead_self_attention`。
- `run_rope`：调用 `rope`，单独测试旋转位置编码。
- `run_transformer_block`：调用 `transformer_block`，测试单层 Transformer block。
- `run_transformer_lm`：调用 `transformer_lm`，测试完整 LM 前向。
- `run_rmsnorm`：调用 `rmsnorm`，测试 RMSNorm。
- `run_silu`：调用 `silu`，测试 SiLU 激活。
- `run_get_batch`：调用 `get_batch`，测试数据采样和 device 处理。
- `run_softmax`：调用 `softmax`，测试数值稳定 softmax。
- `run_cross_entropy`：调用 `cross_entropy`，测试平均交叉熵。
- `run_gradient_clipping`：调用 `clip_gradients`，测试全局梯度裁剪。
- `get_adamw_cls`：返回 `AdamW` 类，供公共测试实例化优化器。
- `run_get_lr_cosine_schedule`：调用 `cosine_lr_schedule`，测试学习率曲线。
- `run_save_checkpoint`：调用 `save_checkpoint`，测试 checkpoint 保存。
- `run_load_checkpoint`：调用 `load_checkpoint`，测试 checkpoint 加载。
- `get_tokenizer`：构造并返回 `Tokenizer`。
- `run_train_bpe`：调用 `train_bpe`，测试 BPE 训练结果和速度。

## 脚本作用

- `submission/scripts/train_tokenizer.py`：读取文本语料，调用 `train_bpe` 训练 tokenizer，并保存 vocab 和 merges。
- `submission/scripts/encode.py`：读取 tokenizer 文件和文本文件，调用 `Tokenizer.encode`，输出二进制 token id 文件。
- `submission/scripts/train_lm.py`：读取二进制 token id 数据，构造 `TransformerLM`，用 AdamW 和 cross-entropy 训练，定期记录 train / validation loss，并保存 checkpoint。
- `submission/scripts/evaluate_lm.py`：加载 checkpoint，在 validation token ids 上估计 loss，并可用 tokenizer 生成文本样例。
- `submission/scripts/generate.py`：加载 tokenizer 和 LM checkpoint，从 prompt 开始做自回归生成，支持 temperature 和 top-p sampling。
- `submission/scripts/run_cpu_training.sh`：CPU 一键训练链路，包含 tokenizer 训练、数据编码、LM 训练和日志保存。
- `submission/scripts/run_cpu_eval.sh`：CPU 一键评测链路，自动读取同一 run 的配置、checkpoint 和 tokenizer。

## 测试结果

- 公共测试日志：`logs/public-tests.md`
- 结果：`47 passed, 1 xpassed`
- `xpassed` 用例是公共测试中标记为 xfail 的 tokenizer 内存测试，本实现实际通过。

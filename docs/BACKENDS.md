# Search Backends

项目保留三个搜索后端，不互相覆盖。

## 1. `python`

人类可读版。

用途：

- 规则调试。
- UI 对局。
- 复盘和日志验证。
- Renju 禁手调试。
- VCF/VCT 正确性基准。

特点：

- 可读性最高。
- 容易加中文注释。
- 性能一般。
- 不追求 24 核吃满。

命令：

```bash
python main.py benchmark --backend python --time-limit 0.05
python main.py play --human black --engine python
python main.py selfplay --games 1 --engine python
python main.py play --human black --engine numba_bitboard
python main.py selfplay --games 1 --engine numba_bitboard
```

## 2. `numba`

Numba 矩阵版。

用途：

- 验证 Numba JIT。
- 验证根节点 `prange` 并行。
- 做 CPU 线程数和 NPS 压测。
- 作为进入 4xuint64 前的中间版本。

特点：

- 使用 `int8[15,15]` 棋盘。
- 比 Python 版快很多。
- 比 4xuint64 版更容易理解。
- 当前 benchmark 已可接近千万 NPS。

命令：

```bash
python main.py benchmark --backend numba --threads 24 --depth 5 --scenario midgame
```

限制：

- 当前只接入 benchmark。
- 尚未接入 `play` / `selfplay` 的真实对局引擎。

## 3. `numba_bitboard`

Numba bitboard 极限版。

用途：

- 最终性能优化。
- 4xuint64 棋盘。
- 减少递归分配。
- 为置换表和更深搜索做准备。

特点：

- 可读性最低。
- 代码更接近底层数值计算。
- 不直接替代 Python 可读版。
- 必须通过测试和 benchmark 逐步接入。

命令：

```bash
python main.py benchmark --backend numba_bitboard --threads 24 --depth 5 --scenario midgame
```

限制：

- 当前已经接入 CLI benchmark 后端。
- 已接入 `play` / `selfplay` 的 `--engine numba_bitboard`。
- Renju 黑棋会回退 Python 引擎保证禁手合法性。

## 原则

- 不删除 `python` 后端。
- 不用极限版承载规则解释。
- 先保证三版本结果大体一致，再比较性能。
- 任何 4xuint64 优化都必须有测试。

# Extreme Run

这份文件只放 freestyle 极限测试命令。`ROBUST_RUN.md` 是默认 mild 模式；这里统一使用 `--mode extreme`、`--ai-depth 16`、`--time-limit 30` 和 `--threads 24`。

## 人机 UI 极限测试

自由五子棋，人类执黑：

```bash
python main.py play --human black --rule freestyle --engine numba_bitboard --mode extreme --ai-depth 16 --time-limit 30 --threads 24
```

自由五子棋，人类执白：

```bash
python main.py play --human white --rule freestyle --engine numba_bitboard --mode extreme --ai-depth 16 --time-limit 30 --threads 24
```

## 机机 UI 极限测试

自由五子棋，可观看 UI：

```bash
python main.py selfplay --games 1 --rule freestyle --engine numba_bitboard --mode extreme --ai-depth 16 --time-limit 30 --threads 24
```

自由五子棋，可观看 UI，限制最多 120 手：

```bash
python main.py selfplay --games 1 --rule freestyle --max-moves 120 --engine numba_bitboard --mode extreme --ai-depth 16 --time-limit 30 --threads 24
```

## 无 UI 稳定性测试

自由五子棋，快速验证命令链路：

```bash
python main.py selfplay --games 1 --max-moves 6 --rule freestyle --engine numba_bitboard --mode extreme --ai-depth 16 --time-limit 30 --threads 24 --no-ui
```

自由五子棋，批量稳定性测试：

```bash
python main.py selfplay --games 10 --max-moves 120 --rule freestyle --engine numba_bitboard --mode extreme --ai-depth 16 --time-limit 30 --threads 24 --no-ui
```

## Benchmark 极限参考

Numba bitboard extreme，24 线程，中盘：

```bash
python main.py benchmark --backend numba_bitboard --rule freestyle --mode extreme --threads 24 --depth 16 --time-limit 30 --scenario midgame
```

Numba bitboard extreme，24 线程，空盘：

```bash
python main.py benchmark --backend numba_bitboard --rule freestyle --mode extreme --threads 24 --depth 16 --time-limit 30 --scenario empty
```

## 测试

全量测试：

```bash
python3 -B -m pytest -q -p no:cacheprovider
```

只测 CLI / AI worker / UI 统计：

```bash
python3 -B -m pytest -q -p no:cacheprovider tests/test_cli.py tests/test_ai_worker.py tests/test_ui_stats.py
```

## 参数说明

- `--mode extreme`：启用 freestyle 极限搜索模式。内部使用递归 VCF、bitboard 极限候选裁剪和迭代加深，优先返回已完整完成的最深结果。
- `--mode mild`：默认模式，也就是 `ROBUST_RUN.md` 使用的稳定运行模式。
- `--engine numba_bitboard`：当前默认高性能对局引擎。
- `--ai-depth 16`：extreme 推荐目标深度。
- `--time-limit 30`：extreme 推荐单步时间预算。
- `--threads 24`：面向 M2 Ultra 24 核。
- `--rule freestyle`：自由五子棋，无 Renju 黑棋禁手，适合极限搜索。
- `--no-ui`：关闭 Pygame，用于批量稳定性测试。

## 为什么没有 Renju Extreme

Renju 的黑棋三三、四四、长连禁手需要严格判定有效活三和有效四。这个规则很复杂，不能用粗糙模式硬判。当前 extreme 模式专门面向 freestyle；如果强行把 Renju 放进 16 层 extreme，会因为每层候选都要做高成本禁手过滤而明显变慢，也更容易出现规则误判。Renju 先走 `ROBUST_RUN.md` 的 mild 模式，等禁手检测完全搬进高速 bitboard 后再开放 Renju extreme。

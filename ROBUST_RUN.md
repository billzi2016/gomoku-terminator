# Robust Run

这份文件只放“强度测试 / 稳定性测试”命令。日常完整说明看 `QUICKSTART.md`。

## 人机 UI 最终测试

Renju，人类执黑：

```bash
python main.py play --human black --rule renju --engine numba_bitboard --ai-depth 10 --time-limit 10 --threads 24
```

Renju，人类执白：

```bash
python main.py play --human white --rule renju --engine numba_bitboard --ai-depth 10 --time-limit 10 --threads 24
```

自由五子棋，人类执黑：

```bash
python main.py play --human black --rule freestyle --engine numba_bitboard --ai-depth 10 --time-limit 10 --threads 24
```

自由五子棋，人类执白：

```bash
python main.py play --human white --rule freestyle --engine numba_bitboard --ai-depth 10 --time-limit 10 --threads 24
```

## 机机 UI 最终测试

Renju，可观看 UI：

```bash
python main.py selfplay --games 1 --rule renju --engine numba_bitboard --ai-depth 10 --time-limit 10 --threads 24
```

自由五子棋，可观看 UI：

```bash
python main.py selfplay --games 1 --rule freestyle --engine numba_bitboard --ai-depth 10 --time-limit 10 --threads 24
```

Renju，可观看 UI，限制最多 120 手：

```bash
python main.py selfplay --games 1 --rule renju --max-moves 120 --engine numba_bitboard --ai-depth 10 --time-limit 10 --threads 24
```

自由五子棋，可观看 UI，限制最多 120 手：

```bash
python main.py selfplay --games 1 --rule freestyle --max-moves 120 --engine numba_bitboard --ai-depth 10 --time-limit 10 --threads 24
```

## 无 UI 稳定性短测

Renju，快速验证命令链路：

```bash
python main.py selfplay --games 1 --max-moves 6 --rule renju --engine numba_bitboard --ai-depth 10 --time-limit 10 --threads 24 --no-ui
```

自由五子棋，快速验证命令链路：

```bash
python main.py selfplay --games 1 --max-moves 6 --rule freestyle --engine numba_bitboard --ai-depth 10 --time-limit 10 --threads 24 --no-ui
```

Renju，批量稳定性测试：

```bash
python main.py selfplay --games 10 --max-moves 120 --rule renju --engine numba_bitboard --ai-depth 10 --time-limit 10 --threads 24 --no-ui
```

自由五子棋，批量稳定性测试：

```bash
python main.py selfplay --games 10 --max-moves 120 --rule freestyle --engine numba_bitboard --ai-depth 10 --time-limit 10 --threads 24 --no-ui
```

## Benchmark 强度参考

Numba bitboard，24 线程，中盘：

```bash
python main.py benchmark --backend numba_bitboard --threads 24 --depth 6 --scenario midgame
```

Numba bitboard，24 线程，空盘：

```bash
python main.py benchmark --backend numba_bitboard --threads 24 --depth 6 --scenario empty
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

- `--engine numba_bitboard`：当前默认高性能对局引擎。
- `--ai-depth 10`：最终测试建议深度，不是硬上限。
- `--time-limit 10`：最终测试建议单步时间，不是硬上限。
- `--threads 24`：面向 M2 Ultra 24 核。
- `--rule renju`：连珠规则，黑棋有禁手，棋盘会显示红色 X。
- `--rule freestyle`：自由五子棋，无 Renju 黑棋禁手。
- `--no-ui`：关闭 Pygame，用于批量稳定性测试。


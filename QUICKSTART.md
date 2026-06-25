# Quickstart

本文件只放命令和必要说明，方便直接复制执行。

## 1. 安装

### venv 环境

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 不使用 venv

```bash
pip install -r requirements.txt
```

### 检查入口

```bash
python main.py --help
```

## 2. 查看帮助

```bash
python main.py --help
python main.py play --help
python main.py selfplay --help
python main.py replay --help
python main.py benchmark --help
```

## 2.1 默认参数

不写参数时，当前默认值如下：

| 参数 | 默认值 | 含义 |
| --- | --- | --- |
| `--rule` | `renju` | 默认使用连珠规则，黑棋有禁手，棋盘显示红色 X。 |
| `--time-limit` | `5.0` | 单步最大思考时间默认 5 秒。 |
| `--threads` | `24` | 默认线程数 24，面向 M2 Ultra。 |
| `--opening-book` | `data/opening_book.json` | 默认开局库路径。 |
| `--log-dir` | `data/game_logs` | 默认对局日志目录。 |
| `--no-ui` | `false` | 默认开启 UI；只有显式写 `--no-ui` 才后台运行。 |
| `play --human` | `black` | 人机模式默认人类执黑，AI 执白。 |
| `selfplay --games` | `1` | 机机模式默认跑 1 局。 |
| `selfplay --max-moves` | `225` | 机机模式默认最多 225 手。 |
| `benchmark --backend` | `python` | benchmark 默认使用人类可读 Python 后端。 |
| `benchmark --depth` | `5` | benchmark 默认深度参数为 5；Python 后端内部当前最多取到 3。 |
| `benchmark --scenario` | `midgame` | benchmark 默认使用中盘压测局面。 |

也就是说，下面这条：

```bash
python main.py play
```

等价于：

```bash
python main.py play --human black --rule renju --time-limit 5 --threads 24
```

下面这条：

```bash
python main.py selfplay
```

等价于开启可观看 UI 的机机对战：

```bash
python main.py selfplay --games 1 --max-moves 225 --rule renju --time-limit 5 --threads 24
```

下面这条：

```bash
python main.py benchmark
```

等价于：

```bash
python main.py benchmark --backend python --rule renju --time-limit 5 --threads 24 --depth 5 --scenario midgame
```

## 3. 人机 UI

参数含义：

- `--human black`：人类玩家执黑，AI 执白。
- `--human white`：人类玩家执白，AI 执黑。
- `--rule renju`：使用连珠规则，黑棋有三三、四四、长连禁手，棋盘会显示黑棋禁手红色 X。
- `--rule freestyle`：使用自由五子棋规则，不启用 Renju 黑棋禁手。
- 默认规则是 `renju`。也就是说，不写 `--rule` 时就是连珠规则。

### 人类执黑，Renju 规则

```bash
python main.py play --human black --rule renju
```

含义：你下黑棋，AI 下白棋；规则是 Renju，黑棋禁手会显示红色 X，黑棋不能下禁手点。

### 人类执白，Renju 规则

```bash
python main.py play --human white --rule renju
```

含义：你下白棋，AI 下黑棋；规则是 Renju，AI 作为黑棋也不能下禁手点。

### 人类执黑，Renju 规则，AI 最多思考 5 秒

```bash
python main.py play --human black --rule renju --time-limit 5
```

### 自由五子棋规则

```bash
python main.py play --human black --rule freestyle --time-limit 5
```

### 指定线程数

```bash
python main.py play --human black --threads 24
```

### 指定日志文件

```bash
python main.py play --human black --log-file data/game_logs/human_black.json
python main.py play --human white --log-file data/game_logs/human_white.json
```

## 4. 机机自博弈

默认不加 `--no-ui` 时，会打开 Pygame 棋盘观看 AI vs AI。加上 `--no-ui` 时，才是后台批量跑。

### 可观看机机对战 UI

```bash
python main.py selfplay --games 1 --time-limit 1
```

### 可观看机机对战 UI，限制最多 80 手

```bash
python main.py selfplay --games 1 --max-moves 80 --time-limit 1
```

### 后台跑 1 局，无 UI

```bash
python main.py selfplay --games 1 --time-limit 5 --no-ui
```

### 快速跑 4 手，用于验证日志

```bash
python main.py selfplay --games 1 --max-moves 4 --time-limit 0.01 --no-ui
```

### 后台跑 10 局

```bash
python main.py selfplay --games 10 --time-limit 1 --no-ui
```

### 后台跑 100 局

```bash
python main.py selfplay --games 100 --time-limit 1 --no-ui
```

### 指定日志目录

```bash
python main.py selfplay --games 10 --time-limit 1 --log-dir data/game_logs --no-ui
```

### 限制每局最多手数

```bash
python main.py selfplay --games 10 --max-moves 80 --time-limit 1 --no-ui
```

## 5. 复盘

### 打开对局日志

```bash
python main.py replay data/game_logs/example.json
```

复盘 UI 支持：

- 进度条拖拽。
- `Prev` / `Next` 相邻按钮。
- 按任意步数重建棋盘。
- 继续显示黑棋禁手红色 X。

## 6. Python 后端 benchmark

Python 后端是人类可读搜索路径，适合调试规则和搜索行为。

```bash
python main.py benchmark --backend python
python main.py benchmark --backend python --time-limit 0.05
python main.py benchmark --backend python --depth 2 --time-limit 0.1
python main.py benchmark --backend python --rule renju --time-limit 1
python main.py benchmark --backend python --rule freestyle --time-limit 1
```

## 7. Numba 后端 benchmark

Numba 后端用于 CPU 并行压测。

### 24 线程，中盘场景，推荐日常压测

```bash
python main.py benchmark --backend numba --threads 24 --depth 5 --scenario midgame
```

### 使用环境变量指定线程数

```bash
NUMBA_NUM_THREADS=24 python main.py benchmark --backend numba --threads 24 --depth 5 --scenario midgame
```

### 空棋盘场景

```bash
python main.py benchmark --backend numba --threads 24 --depth 5 --scenario empty
```

注意：空棋盘只有天元一个根分支，不适合压满 24 核。

### 中盘压力测试

```bash
python main.py benchmark --backend numba --threads 24 --depth 6 --scenario midgame
```

注意：`depth 6` 节点数很大，可能明显耗时。日常建议先用 `depth 5`。

### 不同线程数对比

```bash
python main.py benchmark --backend numba --threads 1 --depth 5 --scenario midgame
python main.py benchmark --backend numba --threads 4 --depth 5 --scenario midgame
python main.py benchmark --backend numba --threads 8 --depth 5 --scenario midgame
python main.py benchmark --backend numba --threads 16 --depth 5 --scenario midgame
python main.py benchmark --backend numba --threads 24 --depth 5 --scenario midgame
```

## 8. 测试

### 全量测试

```bash
python3 -B -m pytest -q -p no:cacheprovider
```

### 单独测试坐标和 bitboard

```bash
python3 -B -m pytest -q -p no:cacheprovider tests/test_coordinates.py tests/test_bitboard.py
```

### 单独测试规则

```bash
python3 -B -m pytest -q -p no:cacheprovider tests/test_win_check.py tests/test_forbidden.py
```

### 单独测试搜索

```bash
python3 -B -m pytest -q -p no:cacheprovider tests/test_engine.py tests/test_evaluator.py tests/test_move_ordering.py tests/test_tactics.py
```

### 单独测试 Numba

```bash
python3 -B -m pytest -q -p no:cacheprovider tests/test_numba_search.py
```

### 单独测试日志和复盘加载

```bash
python3 -B -m pytest -q -p no:cacheprovider tests/test_game_log.py
```

### 单独测试 CLI

```bash
python3 -B -m pytest -q -p no:cacheprovider tests/test_cli.py
```

## 9. Docker

### 构建镜像

```bash
docker build -t gomoku-terminator .
```

### 查看帮助

```bash
docker run --rm gomoku-terminator
```

### Docker 内跑 Python benchmark

```bash
docker run --rm gomoku-terminator python main.py benchmark --backend python
```

### Docker 内跑测试

```bash
docker run --rm gomoku-terminator python3 -B -m pytest -q -p no:cacheprovider
```

Pygame UI 需要宿主机图形环境。Docker 内跑 UI 需要额外配置显示转发，不建议作为默认方式。

## 10. 脚本

### 构建开局库骨架

```bash
python scripts/build_opening_book.py
```

### 下载开局来源资料占位脚本

```bash
python scripts/download_opening_sources.py
```

### 搜索 profile 占位脚本

```bash
python scripts/profile_search.py
```

### benchmark 脚本入口

```bash
python scripts/benchmark_engine.py
```

## 11. 常用组合

### 本地开发最常用

```bash
python3 -B -m pytest -q -p no:cacheprovider
python main.py benchmark --backend python --time-limit 0.05
python main.py benchmark --backend numba --threads 24 --depth 5 --scenario midgame
```

### UI 对局最常用

```bash
python main.py play --human black --rule renju --time-limit 5
```

### 快速验证 selfplay 和日志

```bash
python main.py selfplay --games 1 --max-moves 4 --time-limit 0.01 --no-ui
```

### 观看一局机机对战

```bash
python main.py selfplay --games 1 --max-moves 80 --time-limit 1
```

### 生成一批自博弈日志

```bash
python main.py selfplay --games 100 --time-limit 1 --log-dir data/game_logs --no-ui
```

### 压 M2 Ultra CPU

```bash
NUMBA_NUM_THREADS=24 python main.py benchmark --backend numba --threads 24 --depth 5 --scenario midgame
```

### 重压力测试

```bash
NUMBA_NUM_THREADS=24 python main.py benchmark --backend numba --threads 24 --depth 6 --scenario midgame
```

## 12. 输出文件

默认对局日志目录：

```text
data/game_logs/
```

日志格式：

```text
*.json
```

JSON 文件使用 `indent=2`，便于人工阅读和复盘调试。

## 13. 当前注意事项

- `backend=python` 是人类可读版，适合调试。
- `backend=numba` 是性能压测版，适合看 NPS 和 CPU 利用率。
- 当前 Numba 后端还是矩阵版，不是最终 4xuint64 bitboard 版。
- 高质量开局库还需要继续补。
- Renju 禁手规则还需要继续用标准局面打磨。
- 完整递归 VCF/VCT 还需要继续增强。

## 14. 命令矩阵

这一节把有意义的排列组合集中列出来。不要把所有参数乱拼，下面这些是当前项目支持且有实际用途的组合。

### 14.1 人机 UI：Renju 规则

```bash
# 人类执黑，AI 执白，Renju 规则
python main.py play --human black --rule renju

# 人类执白，AI 执黑，Renju 规则
python main.py play --human white --rule renju

# 人类执黑，AI 最多思考 1 秒
python main.py play --human black --rule renju --time-limit 1

# 人类执黑，AI 最多思考 5 秒
python main.py play --human black --rule renju --time-limit 5

# 人类执白，AI 最多思考 1 秒
python main.py play --human white --rule renju --time-limit 1

# 人类执白，AI 最多思考 5 秒
python main.py play --human white --rule renju --time-limit 5

# 人类执黑，指定日志文件
python main.py play --human black --rule renju --time-limit 5 --log-file data/game_logs/human_black_renju.json

# 人类执白，指定日志文件
python main.py play --human white --rule renju --time-limit 5 --log-file data/game_logs/human_white_renju.json
```

### 14.2 人机 UI：自由五子棋规则

```bash
# 人类执黑，自由五子棋
python main.py play --human black --rule freestyle

# 人类执白，自由五子棋
python main.py play --human white --rule freestyle

# 人类执黑，自由五子棋，AI 最多思考 5 秒
python main.py play --human black --rule freestyle --time-limit 5

# 人类执白，自由五子棋，AI 最多思考 5 秒
python main.py play --human white --rule freestyle --time-limit 5

# 人类执黑，自由五子棋，指定日志文件
python main.py play --human black --rule freestyle --time-limit 5 --log-file data/game_logs/human_black_freestyle.json

# 人类执白，自由五子棋，指定日志文件
python main.py play --human white --rule freestyle --time-limit 5 --log-file data/game_logs/human_white_freestyle.json
```

### 14.3 可观看机机 UI

```bash
# 观看一局 Renju 机机对战
python main.py selfplay --games 1 --rule renju --time-limit 1

# 观看一局自由五子棋机机对战
python main.py selfplay --games 1 --rule freestyle --time-limit 1

# 观看一局 Renju 机机对战，最多 80 手
python main.py selfplay --games 1 --rule renju --max-moves 80 --time-limit 1

# 观看一局自由五子棋机机对战，最多 80 手
python main.py selfplay --games 1 --rule freestyle --max-moves 80 --time-limit 1

# 观看机机对战并指定日志文件
python main.py selfplay --games 1 --rule renju --max-moves 80 --time-limit 1 --log-file data/game_logs/watch_selfplay.json
```

### 14.4 后台机机自博弈

```bash
# 后台跑 1 局 Renju
python main.py selfplay --games 1 --rule renju --time-limit 1 --no-ui

# 后台跑 1 局自由五子棋
python main.py selfplay --games 1 --rule freestyle --time-limit 1 --no-ui

# 后台快速跑 4 手 Renju，用于验证日志
python main.py selfplay --games 1 --rule renju --max-moves 4 --time-limit 0.01 --no-ui

# 后台快速跑 4 手自由五子棋，用于验证日志
python main.py selfplay --games 1 --rule freestyle --max-moves 4 --time-limit 0.01 --no-ui

# 后台跑 10 局 Renju
python main.py selfplay --games 10 --rule renju --time-limit 1 --no-ui

# 后台跑 10 局自由五子棋
python main.py selfplay --games 10 --rule freestyle --time-limit 1 --no-ui

# 后台跑 100 局 Renju
python main.py selfplay --games 100 --rule renju --time-limit 1 --no-ui

# 后台跑 100 局自由五子棋
python main.py selfplay --games 100 --rule freestyle --time-limit 1 --no-ui

# 后台跑 100 局 Renju，最多 120 手
python main.py selfplay --games 100 --rule renju --max-moves 120 --time-limit 1 --no-ui

# 后台跑 100 局，指定日志目录
python main.py selfplay --games 100 --rule renju --time-limit 1 --log-dir data/game_logs --no-ui
```

### 14.5 复盘命令

```bash
# 打开一份对局日志
python main.py replay data/game_logs/example.json

# 打开人机对局日志
python main.py replay data/game_logs/human_black_renju.json

# 打开机机对局日志
python main.py replay data/game_logs/watch_selfplay.json
```

### 14.6 Python benchmark：规则组合

```bash
# Python 后端，Renju 默认规则
python main.py benchmark --backend python

# Python 后端，Renju 规则
python main.py benchmark --backend python --rule renju

# Python 后端，自由五子棋规则
python main.py benchmark --backend python --rule freestyle

# Python 后端，Renju，限制 0.05 秒
python main.py benchmark --backend python --rule renju --time-limit 0.05

# Python 后端，自由五子棋，限制 0.05 秒
python main.py benchmark --backend python --rule freestyle --time-limit 0.05

# Python 后端，深度 1
python main.py benchmark --backend python --depth 1 --time-limit 0.05

# Python 后端，深度 2
python main.py benchmark --backend python --depth 2 --time-limit 0.05

# Python 后端，深度 3
python main.py benchmark --backend python --depth 3 --time-limit 0.1
```

### 14.7 Numba benchmark：线程组合

```bash
# 单线程
python main.py benchmark --backend numba --threads 1 --depth 5 --scenario midgame

# 4 线程
python main.py benchmark --backend numba --threads 4 --depth 5 --scenario midgame

# 8 线程
python main.py benchmark --backend numba --threads 8 --depth 5 --scenario midgame

# 16 线程
python main.py benchmark --backend numba --threads 16 --depth 5 --scenario midgame

# 24 线程
python main.py benchmark --backend numba --threads 24 --depth 5 --scenario midgame
```

### 14.8 Numba benchmark：场景和深度组合

```bash
# 空棋盘，深度 5，不适合压满 24 核
python main.py benchmark --backend numba --threads 24 --depth 5 --scenario empty

# 中盘，深度 4，较快
python main.py benchmark --backend numba --threads 24 --depth 4 --scenario midgame

# 中盘，深度 5，推荐日常压测
python main.py benchmark --backend numba --threads 24 --depth 5 --scenario midgame

# 中盘，深度 6，重压力测试
python main.py benchmark --backend numba --threads 24 --depth 6 --scenario midgame

# 用环境变量指定线程数
NUMBA_NUM_THREADS=24 python main.py benchmark --backend numba --threads 24 --depth 5 --scenario midgame
```

### 14.9 测试命令组合

```bash
# 全量测试
python3 -B -m pytest -q -p no:cacheprovider

# CLI 测试
python3 -B -m pytest -q -p no:cacheprovider tests/test_cli.py

# 棋盘底层测试
python3 -B -m pytest -q -p no:cacheprovider tests/test_coordinates.py tests/test_bitboard.py

# 规则测试
python3 -B -m pytest -q -p no:cacheprovider tests/test_win_check.py tests/test_forbidden.py

# 搜索测试
python3 -B -m pytest -q -p no:cacheprovider tests/test_engine.py tests/test_evaluator.py tests/test_move_ordering.py tests/test_tactics.py

# Numba 测试
python3 -B -m pytest -q -p no:cacheprovider tests/test_numba_search.py

# 开局库测试
python3 -B -m pytest -q -p no:cacheprovider tests/test_opening_book.py tests/test_symmetry.py

# 日志测试
python3 -B -m pytest -q -p no:cacheprovider tests/test_game_log.py

# 对局状态测试
python3 -B -m pytest -q -p no:cacheprovider tests/test_game_session.py
```

### 14.10 Docker 命令组合

```bash
# 构建镜像
docker build -t gomoku-terminator .

# 查看帮助
docker run --rm gomoku-terminator

# Docker 内跑 Python benchmark
docker run --rm gomoku-terminator python main.py benchmark --backend python

# Docker 内跑 Numba benchmark
docker run --rm gomoku-terminator python main.py benchmark --backend numba --threads 4 --depth 5 --scenario midgame

# Docker 内跑测试
docker run --rm gomoku-terminator python3 -B -m pytest -q -p no:cacheprovider
```

### 14.11 脚本命令组合

```bash
# 构建开局库骨架
python scripts/build_opening_book.py

# 下载开局来源资料占位脚本
python scripts/download_opening_sources.py

# 搜索 profile 占位脚本
python scripts/profile_search.py

# benchmark 脚本入口
python scripts/benchmark_engine.py
```

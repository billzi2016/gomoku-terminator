# Gomoku Terminator

CPU-only 五子棋 / 连珠 AI 项目。

目标是构建一个不依赖 CNN、不使用 MPS、不跑 PyTorch 主模型推理的本地五子棋 AI。当前项目保留三条搜索路径：

- `python` 后端：人类可读版，方便调试规则、UI、日志、复盘和搜索逻辑。
- `numba` 后端：高性能 CPU benchmark 路径，使用 Numba JIT 和矩阵棋盘根节点并行。
- `numba_bitboard` 后端：当前最高效 benchmark 和默认 UI 对局路径，使用 4xuint64 bitboard。

当前状态：已经具备可运行 MVP，包括 Pygame 人机模式、机机自博弈、JSON 复盘日志、复盘 UI、基础 Renju 禁手可视化接口、基础 Alpha-Beta 搜索、棋形评估、即时成五/防五、基础 VCF/双威胁检测，以及 Numba 并行 benchmark。

注意：当前人机 UI 和机机自博弈默认使用 `--engine numba_bitboard`，也就是 4xuint64 Numba bitboard 对局引擎。`--engine python` 仍保留用于规则调试。`--backend numba` 和 `--backend numba_bitboard` 是 benchmark 参数，不要和 UI 的 `--engine` 混淆。

开局库：`data/opening_book.json` 已经包含 Renju 26 个标准开局形和保守前几手推荐，并支持加载时 8 向对称扩展。来源、重建命令和当前边界写在 [data/README.md](/Users/bizi/Desktop/GitHub/gomoku-terminator/data/README.md)。注意它还不是完整职业深度定式库，后续深库必须从许可证清楚的 SGF/RenLib 数据源导入。

## Quickstart

### 1. 创建环境

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

如果你使用系统 Python，也可以直接：

```bash
pip install -r requirements.txt
```

### 2. 查看命令帮助

```bash
python main.py --help
python main.py play --help
python main.py selfplay --help
python main.py replay --help
python main.py benchmark --help
```

### 3. 启动人机 UI

人类执黑：

```bash
python main.py play --human black
```

显式指定当前 UI 引擎：

```bash
python main.py play --human black --engine python
python main.py play --human black --engine numba_bitboard
```

人类执白：

```bash
python main.py play --human white
```

指定规则和思考时间：

```bash
python main.py play --human black --rule renju --time-limit 5
```

指定日志文件：

```bash
python main.py play --human black --log-file data/game_logs/manual_game.json
```

说明：

- Pygame 主线程负责 UI。
- AI 在后台线程思考。
- UI 右侧显示 AI 思考统计，包括落点、深度、节点数、NPS、耗时、评分。
- 黑棋禁手点会通过红色 X 覆盖层显示。
- 人机模式支持悔棋一步。
- 日志保存为普通 JSON，使用 `indent=2`。

### 4. 机机自博弈

跑一局完整自博弈：

```bash
python main.py selfplay --games 1 --time-limit 5 --no-ui
```

快速跑 4 手，用于测试日志链路：

```bash
python main.py selfplay --games 1 --max-moves 4 --time-limit 0.01 --no-ui
```

批量跑 100 局：

```bash
python main.py selfplay --games 100 --time-limit 1 --no-ui
```

指定日志目录：

```bash
python main.py selfplay --games 10 --log-dir data/game_logs --time-limit 1 --no-ui
```

### 5. 复盘

打开一份 JSON 对局日志：

```bash
python main.py replay data/game_logs/example.json
```

复盘 UI 支持：

- 进度条拖拽。
- `Prev` / `Next` 相邻按钮。
- 按任意步数重建棋盘。
- 继续显示黑棋禁手红色 X。

### 6. Python 后端 benchmark

```bash
python main.py benchmark --backend python --time-limit 0.05
```

输出示例字段：

- `backend`
- `rule`
- `time_limit`
- `threads`
- `best_move`
- `score`
- `depth`
- `nodes`
- `elapsed_ms`
- `nps`

### 7. Numba 并行 benchmark

使用 24 线程：

```bash
python main.py benchmark --backend numba --threads 24 --depth 5 --scenario midgame
```

也可以通过环境变量指定：

```bash
NUMBA_NUM_THREADS=24 python main.py benchmark --backend numba --threads 24 --depth 5 --scenario midgame
```

当前 Numba benchmark 会先 warmup 一次 JIT 编译，再正式计时。它的目的不是替代人类可读搜索，而是验证 CPU 并行路径、线程数和 NPS。

4xuint64 bitboard 后端：

```bash
python main.py benchmark --backend numba_bitboard --threads 24 --depth 5 --scenario midgame
```

可选场景：

```bash
python main.py benchmark --backend numba --threads 24 --depth 5 --scenario empty
python main.py benchmark --backend numba --threads 24 --depth 5 --scenario midgame
```

建议：

- `--scenario empty` 只有天元一个根分支，不适合压 24 核。
- `--scenario midgame` 有更多根候选，适合观察 CPU 并行性能。
- `--depth 5` 适合日常性能检查。
- `--depth 6` 是压力测试，可能耗时明显变长。

### 8. 运行测试

```bash
python3 -B -m pytest -q -p no:cacheprovider
```

### 9. Docker

构建镜像：

```bash
docker build -t gomoku-terminator .
```

查看帮助：

```bash
docker run --rm gomoku-terminator
```

运行 benchmark：

```bash
docker run --rm gomoku-terminator python main.py benchmark --backend python
```

注意：Pygame UI 需要宿主机图形环境，Docker 内运行 UI 需要额外配置显示转发。

## 基础命令

```bash
python main.py --help
python main.py play --human black
python main.py play --human white
python main.py selfplay --games 1 --no-ui
python main.py selfplay --games 1 --max-moves 4 --time-limit 0.01 --no-ui
python main.py replay data/game_logs/example.json
python main.py benchmark --backend python --time-limit 0.05
python3 -B -m pytest -q -p no:cacheprovider
```

## 进阶命令

```bash
python main.py play --human black --rule renju --time-limit 5 --threads 24
python main.py play --human white --rule renju --time-limit 5 --log-file data/game_logs/human_white.json
python main.py selfplay --games 100 --time-limit 1 --threads 24 --log-dir data/game_logs --no-ui
python main.py benchmark --backend numba --threads 24 --depth 5 --scenario midgame
NUMBA_NUM_THREADS=24 python main.py benchmark --backend numba --threads 24 --depth 5 --scenario midgame
python main.py benchmark --backend numba --threads 24 --depth 6 --scenario midgame
python scripts/build_opening_book.py
python scripts/download_opening_sources.py
python scripts/profile_search.py
docker build -t gomoku-terminator .
docker run --rm gomoku-terminator python main.py benchmark --backend python
```

## 当前实现边界

已经完成：

- Pygame 人机 UI。
- 机机自博弈。
- JSON `indent=2` 对局日志。
- 复盘 UI。
- 人类可读 Python 搜索。
- 棋形评估。
- 即时成五 / 防五。
- 基础 VCF / 双威胁检测。
- Numba 根节点并行 benchmark。
- Numba bitboard benchmark。
- Renju 26 标准开局形 JSON 库。

仍需继续强化：

- 高质量 Renju 深度开局库，也就是 4/5/6 手以后带来源和评分的职业变化。
- 职业级三三 / 四四 / 长连禁手判定。
- 完整递归 VCF / VCT。
- 完善 Numba bitboard 的 Renju 黑棋禁手高速过滤，减少回退 Python 的情况。
- 置换表。
- 更强 move ordering。
- UI 实机细节打磨。

## 日志格式

对局日志保存在 `data/game_logs/*.json`，结构如下：

```json
{
  "version": 1,
  "moves": [
    {
      "game_id": "...",
      "move_number": 1,
      "player": "black",
      "row": 7,
      "col": 7,
      "index": 112,
      "rule": "renju",
      "is_forbidden": false,
      "forbidden_points": [],
      "search_depth": 2,
      "nodes": 34,
      "nps": 1200.0,
      "score": 0,
      "time_ms": 28.0,
      "engine": "negamax",
      "timestamp": 0.0
    }
  ]
}
```

## 设计原则

- 不使用 CNN。
- 不使用 MPS。
- 不使用 PyTorch 主模型推理。
- 保留人类可读 Python 版作为规则和调试基准。
- Numba 版专注性能，不替代可读版。
- 开局库是胜负关键资产，不能使用来路不明的低质量数据。

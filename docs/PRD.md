# 极速 CPU 算力流五子棋 AI PRD

## 1. 项目定位

本项目目标是实现一个本地运行的高性能五子棋 / 连珠 AI 引擎，核心路线是纯算法搜索，不依赖 CNN，不使用 MPS，不走深度学习模型推理流水线。

目标硬件是 Apple Silicon M2 Ultra 24 核 CPU。引擎侧通过位棋盘、Numba JIT、根节点并行、Alpha-Beta 剪枝、置换表、VCF/VCT 杀棋搜索尽量压榨 CPU 算力。界面侧使用 Pygame 作为轻量显示器和鼠标交互棋盘，不让 UI 阻塞搜索线程。

## 2. 核心目标

- CPU-only，高性能本地运行。
- 不使用 CNN。
- 不使用 MPS。
- 不使用 PyTorch / TensorFlow 作为主搜索或评估模型流水线。
- Pygame 只负责棋盘显示、鼠标输入、落子反馈。
- 搜索核心使用 NumPy / Numba / 位运算。
- 优先支持 15 x 15 标准棋盘。
- 支持连珠规则下的黑棋禁手检测。
- 支持开局库、常规搜索、VCF/VCT 杀棋模块。
- 单步响应目标为 1 到 2 秒内返回当前最佳落子。
- 在 M2 Ultra 上允许配置 24 个 Numba worker 线程。

## 3. 非目标

本项目第一阶段明确不做以下内容：

- 不训练神经网络。
- 不接入 CNN policy/value network。
- 不接入 MPS 推理。
- 不用 PyTorch 跑主模型。
- 不做复杂 3D UI。
- 不依赖远程 API。
- 不以图形界面复杂度为优先目标。
- 不优先实现网络对战、账号系统、棋谱云同步。

如果未来需要做神经网络实验，必须作为单独分支或实验模块隔离，不能污染 CPU-only 主线。

## 4. 推荐目录树

```text
gomoku-terminator/
├── main.py
├── docs/
│   └── PRD.md
├── data/
│   ├── opening_book.json
│   ├── game_logs/
│   └── sgf/
├── scripts/
│   ├── build_opening_book.py
│   ├── benchmark_engine.py
│   ├── download_opening_sources.py
│   └── profile_search.py
├── src/
│   └── gomoku_terminator/
│       ├── __init__.py
│       ├── board/
│       │   ├── __init__.py
│       │   ├── bitboard.py
│       │   ├── coordinates.py
│       │   └── zobrist.py
│       ├── rules/
│       │   ├── __init__.py
│       │   ├── win_check.py
│       │   └── renju_forbidden.py
│       ├── opening/
│       │   ├── __init__.py
│       │   ├── book.py
│       │   └── symmetry.py
│       ├── engine/
│       │   ├── __init__.py
│       │   ├── evaluator.py
│       │   ├── move_ordering.py
│       │   ├── negamax.py
│       │   ├── parallel_search.py
│       │   ├── transposition_table.py
│       │   └── time_control.py
│       ├── tactical/
│       │   ├── __init__.py
│       │   ├── vcf.py
│       │   └── vct.py
│       ├── ui/
│       │   ├── __init__.py
│       │   ├── pygame_app.py
│       │   ├── board_view.py
│       │   ├── forbidden_overlay.py
│       │   ├── ai_worker.py
│       │   └── replay_view.py
│       ├── logging/
│       │   ├── __init__.py
│       │   ├── game_log.py
│       │   └── replay_loader.py
│       └── cli.py
├── tests/
│   ├── test_bitboard.py
│   ├── test_coordinates.py
│   ├── test_win_check.py
│   ├── test_forbidden.py
│   ├── test_opening_book.py
│   ├── test_game_log.py
│   ├── test_replay_loader.py
│   ├── test_vcf.py
│   └── test_engine.py
└── pyproject.toml
```

## 5. 技术栈

### 5.1 必选技术

- Python 3.11+
- NumPy
- Numba
- Pygame
- pytest

### 5.2 可选技术

- orjson：加速开局库 JSON 加载。
- rich：命令行 benchmark 输出。
- line_profiler / py-spy：性能分析。

### 5.3 禁用技术

- CNN。
- MPS 推理。
- PyTorch 主模型推理。
- TensorFlow 主模型推理。

## 6. 总体架构

```text
Pygame UI
  |
  | mouse click -> row, col
  v
Game Controller
  |
  | row, col -> bit index
  v
Bitboard State
  |
  +--> Rule Check
  |      ├── win check
  |      └── forbidden check
  |
  +--> Opening Book
  |
  +--> AI Worker Thread
         |
         +--> VCF / VCT Search
         |
         +--> Parallel Negamax Search
                ├── move ordering
                ├── alpha-beta
                ├── transposition table
                └── time control
```

Pygame 主线程只处理窗口、绘制、输入和状态展示。AI 搜索必须放入后台 worker，避免搜索 1 到 2 秒时 UI 卡死。

程序入口统一放在仓库根目录 `main.py`。`main.py` 只负责 argparse 参数解析和模式分发，具体实现调用 `src/gomoku_terminator/` 内部模块，避免把业务逻辑堆在入口文件里。

运行模式分为两类：

- 人机模式：人类通过 Pygame 点击落子，AI 后台线程搜索后返回落子。
- 机机模式：两个 AI 自动对弈，用于压测搜索、生成对局日志、比较参数强度。

每局都应保存结构化 log。复盘命令读取 log 后打开复盘界面，提供进度条拖拽、上一步、下一步。上一步和下一步按钮必须相邻放置，不能分别放在界面两侧。

## 7. 模块设计

### 7.0 程序入口与参数解析

仓库根目录必须提供 `main.py`，作为唯一推荐启动入口。

职责：

- 解析所有命令行参数。
- 分发到人机、机机、复盘、benchmark 等模式。
- 设置运行时配置，例如线程数、单步时间限制、规则类型、日志路径。
- 不直接实现搜索算法和 UI 细节。

推荐命令：

```bash
python main.py play --human black --time-limit 5 --threads 24
python main.py selfplay --games 100 --time-limit 5 --threads 24 --log-dir data/game_logs
python main.py replay data/game_logs/example.json
python main.py benchmark --position tests/fixtures/midgame.json --time-limit 5 --threads 24
```

核心参数：

- `mode`：`play`、`selfplay`、`replay`、`benchmark`。
- `--human`：人机模式下人类执黑或执白。
- `--rule`：`freestyle` 或 `renju`。
- `--time-limit`：单步最大思考秒数，默认 5 秒。
- `--threads`：Numba 线程数，M2 Ultra 推荐 24。
- `--opening-book`：开局库路径，默认 `data/opening_book.json`。
- `--log-dir`：对局日志目录，默认 `data/game_logs`。
- `--log-file`：指定单局日志文件。
- `--no-ui`：无 UI 运行，主要用于机机压测。

### 7.1 Bitboard 棋盘模块

15 x 15 棋盘一共 225 个点。底层使用 4 个 `uint64` 保存一方棋子位置。

```text
black_bits: uint64[4]
white_bits: uint64[4]
```

坐标转换：

```text
index = row * 15 + col
word = index // 64
offset = index % 64
mask = 1 << offset
```

落子逻辑：

- 判断 `black_bits[word] | white_bits[word]` 对应位是否已占用。
- 未占用时，将当前颜色对应 bit 置 1。
- 搜索内部优先传递紧凑的 bitboard 数据。

设计要求：

- 搜索热点路径不得使用二维 Python list。
- Pygame 展示层可以维护只读快照或轻量矩阵，但不能作为搜索真源。
- 真源状态必须是 bitboard。
- 坐标转换必须有单元测试。

### 7.2 胜负检测模块

胜负检测需要支持 4 个方向：

- 横向。
- 纵向。
- 左上到右下。
- 右上到左下。

初期可以先实现清晰可靠版本，再逐步替换为位运算优化版本。

验收要求：

- 任意方向五连能正确识别。
- 边界位置不越界。
- 黑白双方互不干扰。
- 长连在普通五子棋和连珠规则中能区分处理。

### 7.3 Renju 禁手模块

黑棋需要检查：

- 三三禁手。
- 四四禁手。
- 长连禁手。

要求：

- 仅黑棋需要禁手过滤。
- 白棋无禁手。
- 黑棋候选点如果构成禁手，直接判为非法点。
- 禁手检测必须在搜索候选点生成阶段执行。
- 禁手检测必须有专门测试局面。
- Pygame 棋盘上需要持续显示黑棋禁手点，用红色 X 标注。
- 红色 X 对人类和机器人都生效：只要当前规则判定该点为黑棋禁手，就显示并禁止黑棋落在该点。
- 白棋回合可以继续显示黑棋禁手提示，但白棋不受禁手限制。
- 所有棋盘视图都必须显示该覆盖层：人机实战、机机实时观看、机机日志复盘都一样。

注意：

- 连珠规则细节复杂，不能只靠粗糙模式匹配。
- 三三和四四需要判断有效活三、有效四。
- 黑棋五连获胜和长连禁手必须按规则严格区分。
- UI 层的红色 X 只是规则结果的可视化，不能作为规则真源；真源必须来自 `rules/renju_forbidden.py`。

### 7.4 Opening Book 开局库

文件：

```text
data/opening_book.json
```

开局库是胜负关键资产，不是普通配置文件。它的质量会直接决定 AI 前 8 到 12 手是否进入职业可下局面，因此必须按核心数据资产管理。

功能：

- 存储标准连珠开局和常见变着。
- 使用落子序列生成 key。
- 命中后直接返回推荐落点。
- 未命中时切换常规搜索。
- 加载时自动扩展 8 种对称变换。

数据来源策略：

- 第一优先级：标准连珠 26 开局资料，来源链接写入 PRD 和生成脚本注释。
- 推荐参考链接：https://www.renju.net/study/openings.php
- 如果找不到可信现成 JSON，不直接依赖随机 GitHub 开局库。
- 使用 `scripts/download_opening_sources.py` 下载或缓存公开资料。
- 使用 `scripts/build_opening_book.py` 将来源资料转换为项目内部 `data/opening_book.json`。
- `opening_book.json` 必须保存来源 URL、生成时间、坐标系统说明和对称扩展状态。

质量要求：

- 不能只收录一个推荐点，必须支持主线和常见变着。
- 每条记录必须包含来源、可信等级、适用规则、落子序列、推荐落点。
- 高质量条目优先来自标准连珠开局资料、职业棋谱、比赛棋谱或人工校验定式。
- 低可信来源只能进入候选池，不能直接进入默认开局库。
- 开局库变更必须有测试：旋转、翻转、命中、非法点过滤、禁手兼容。
- 开局库需要版本号，例如 `book_version` 和 `source_version`。
- 人工维护条目必须带注释字段说明为什么推荐该点。

推荐 JSON 元数据：

```json
{
  "book_version": "0.1.0",
  "board_size": 15,
  "rule": "renju",
  "coordinate": "row_col_zero_based",
  "sources": [
    {
      "name": "RenjuNet standard openings",
      "url": "https://www.renju.net/study/openings.php",
      "trust": "reference"
    }
  ],
  "entries": []
}
```

对称变换：

- 原始。
- 旋转 90 度。
- 旋转 180 度。
- 旋转 270 度。
- 水平翻转。
- 垂直翻转。
- 主对角线翻转。
- 副对角线翻转。

验收要求：

- 同一开局的旋转、翻转局面能命中同一推荐。
- 开局库不存在时引擎仍能正常搜索。
- JSON 格式错误时给出明确错误信息。
- `data/opening_book.json` 不是人工随手写死的散乱坐标，必须能追溯到来源资料或生成脚本。

### 7.5 常规搜索引擎

核心算法：

- Negamax。
- Alpha-Beta 剪枝。
- Iterative Deepening。
- Move Ordering。
- Transposition Table。
- Time Control。

搜索流程：

```text
1. 检查开局库。
2. 检查己方一步胜。
3. 检查对方一步胜并强制防守。
4. 尝试 VCF / VCT。
5. 进入 iterative deepening negamax。
6. 超时返回当前最佳落子。
```

候选点生成：

- 只生成已有棋子邻域内的空点。
- 优先半径为 2。
- 棋盘极空时优先天元或开局库。
- 禁手点不进入黑棋候选列表。

落子排序：

- 立即成五。
- 必须防守对方成五。
- 冲四。
- 活三。
- 双威胁。
- 靠近已有棋子。
- 中央偏好。

### 7.6 M2 Ultra 24 核并行策略

并行层级优先放在根节点：

```text
root candidate moves -> prange -> each worker searches one branch
```

要求：

- 使用 `@njit(nogil=True, parallel=True)`。
- 使用 `numba.prange` 分发根节点候选。
- 通过环境变量配置线程数：

```bash
export NUMBA_NUM_THREADS=24
```

实现原则：

- 不在 `prange` 内创建复杂 Python 对象。
- 不在搜索热点里访问 Pygame 对象。
- 不在搜索热点里打印日志。
- 搜索状态使用基础数值类型和 NumPy 数组。
- bitboard 复制成本控制在极小范围内。

置换表：

- 使用一维 NumPy 数组。
- 初期允许 lock-free 覆盖写。
- 表项至少包括 zobrist key、depth、score、flag、best_move。
- 需要 benchmark 验证并发写入收益和稳定性。

### 7.7 VCF / VCT 杀棋模块

VCF：

- 只搜索连续冲四。
- 对方只允许防守。
- 分支极小，可以搜索 30 层以上。

VCT：

- 搜索活三、冲四和连续威胁。
- 分支比 VCF 更大，需要更严格排序。
- 初期目标深度 16 到 24，后续优化到更深。

触发策略：

- 每步 AI 搜索前优先启动战术检查。
- 如果找到必胜路径，直接返回首步。
- 如果没有找到，进入常规搜索。

输出要求：

- 返回首步坐标。
- 返回杀棋路径。
- 返回搜索深度和节点数，方便调试。

### 7.8 Pygame UI 模块

Pygame 只做显示和鼠标交互，不参与 AI 计算。

棋盘规格：

- 15 x 15。
- 标准五个星位。
- 鼠标点击映射到最近交叉点。
- 黑白棋子绘制。
- 显示当前轮到谁。
- 显示 AI 思考状态。

核心坐标映射：

```text
col = round((mouse_x - margin) / grid_size)
row = round((mouse_y - margin) / grid_size)
```

坐标合法范围：

```text
0 <= row < 15
0 <= col < 15
```

UI 状态流：

```text
human click
  -> validate move
  -> update bitboard
  -> start AI worker thread
  -> UI keeps rendering
  -> worker returns AI move
  -> main thread applies AI move
```

### 7.9 AI Worker 异步模块

Pygame 主线程不能直接调用耗时搜索，否则窗口会卡死。

设计要求：

- 使用 `threading.Thread` 或 `concurrent.futures.ThreadPoolExecutor` 启动 AI 搜索。
- 主线程只轮询搜索状态。
- worker 只接收棋盘快照，不直接修改 UI 状态。
- worker 返回 `(row, col, score, info)`。
- 主线程验证 AI 返回点合法后再落子。

状态示例：

```text
IDLE
HUMAN_TURN
AI_THINKING
AI_DONE
GAME_OVER
```

并发注意：

- Numba 搜索释放 GIL 后可以使用 CPU 多核。
- Python UI 线程继续刷新。
- 不要从 worker 线程调用 Pygame 绘图 API。

### 7.10 对局模式模块

项目必须支持两种核心对局模式。

人机模式：

- Pygame 打开棋盘。
- 人类通过鼠标点击落子。
- 可选择人类执黑或执白。
- 人类执黑时，禁手红色 X 必须阻止点击落子。
- AI 思考时 UI 不冻结。
- AI 返回非法点时主线程必须拒绝，并记录错误。
- 支持人类悔棋一步：撤销最近一轮人类落子和 AI 应手，回到人类落子前局面。
- 如果 AI 尚未落子完成，只允许取消本次人类落子并中止或忽略当前 AI 搜索结果。

机机模式：

- 两个 AI 自动对弈。
- 可开启 UI 观看，也可 `--no-ui` 后台批量跑。
- 开启 UI 观看时，棋盘必须持续显示黑棋禁手红色 X，便于分析 AI 为什么不能走某些点。
- 用于 benchmark、参数比较、回归测试和生成训练外的纯算法对局数据。
- 每步都必须记录搜索信息。
- 支持连续多局运行。

### 7.11 对局日志模块

每一局都需要保存结构化 log，默认目录：

```text
data/game_logs/
```

推荐格式为普通 JSON 文件，使用 `indent=2`，便于人工查看、复盘调试和版本比较。

每条记录至少包含：

- `game_id`。
- `move_number`。
- `player`。
- `row`。
- `col`。
- `index`。
- `rule`。
- `is_forbidden`。
- `forbidden_points`。
- `search_depth`。
- `nodes`。
- `nps`。
- `score`。
- `time_ms`。
- `engine`。
- `timestamp`。

日志要求：

- 人机和机机都保存 log。
- 非法点击、AI 返回非法点、超时截断都要写入 log。
- log 必须足够复盘完整棋局，不依赖运行时内存状态。
- 后续可以从 log 重放到任意一步，并重建该步后的 bitboard。

### 7.12 复盘模块

复盘命令：

```bash
python main.py replay data/game_logs/example.json
```

复盘 UI 要求：

- 打开 Pygame 复盘棋盘。
- 显示当前步数和总步数。
- 提供进度条。
- 进度条可以拖拽跳转到任意手数。
- 提供上一步、下一步按钮。
- 上一步和下一步按钮必须相邻放在一起。
- 复盘时可以显示每步的搜索信息：耗时、深度、节点数、评分。
- 复盘时继续显示黑棋禁手红色 X，用于分析当时哪些点不能走。
- 机机对局 log 的复盘同样必须显示黑棋禁手红色 X。

复盘状态必须由 log 重建，不能依赖原对局时残留的进程状态。

## 8. 性能目标

### 8.1 初期目标

- UI 帧率保持 30 FPS 以上。
- 鼠标落子无明显延迟。
- 合法落子检查小于 0.1 ms。
- 基础胜负检测小于 0.05 ms。
- AI 默认尽量 1 到 2 秒内返回。
- AI 单步硬上限为 5 秒，超过 5 秒必须截断并返回当前最佳落子。
- 支持固定深度搜索和固定时间搜索。

### 8.2 进阶目标

- M2 Ultra 上可配置 24 个 Numba worker 线程。
- 根节点并行搜索稳定运行。
- VCF 深度 30+。
- VCT 深度 20+。
- 常规搜索深度 10 到 14 层，具体以 benchmark 为准。
- 搜索节点数、剪枝率、置换表命中率可统计。

### 8.3 Benchmark 指标

每次 benchmark 至少输出：

- 搜索深度。
- 总节点数。
- 每秒节点数。
- Alpha-Beta 剪枝次数。
- 置换表命中次数。
- VCF/VCT 命中情况。
- 总耗时。
- 最佳落子。

## 9. 开发阶段

### Phase 1: 工程骨架

- 建立目录结构。
- 建立根目录 `main.py`。
- 实现 argparse 参数入口。
- 建立 `pyproject.toml`。
- 加入基础 pytest。
- 加入 Pygame UI 原型。

### Phase 2: Bitboard 底座

- 坐标转换。
- bitboard 落子。
- bitboard 占用检测。
- bitboard 转 UI 快照。
- 基础胜负检测。

### Phase 3: 规则系统

- 普通五子棋胜负。
- 连珠禁手检测。
- 黑棋非法点过滤。
- Pygame 红色 X 禁手覆盖层。
- 禁手测试集。

### Phase 4: 基础搜索

- 候选点生成。
- 静态评估函数。
- 单线程 Negamax。
- Alpha-Beta 剪枝。
- Iterative Deepening。
- 时间控制。

### Phase 5: 并行搜索

- Numba JIT 改造热点函数。
- 根节点 `prange` 并行。
- 置换表。
- M2 Ultra 24 线程 benchmark。

### Phase 6: VCF / VCT

- VCF 搜索。
- VCT 搜索。
- 必胜路径输出。
- 与主搜索融合。

### Phase 7: 开局库

- SGF 解析。
- JSON opening book。
- 开局来源下载和缓存脚本。
- 标准 26 开局骨架。
- 高质量职业定式条目导入。
- 8 方向对称扩展。
- 开局命中测试。

### Phase 8: 对弈体验

- Pygame 主界面完善。
- AI 思考状态。
- 人机模式。
- 机机模式。
- 人机悔棋一步。
- 重新开始。
- 棋谱导出。
- JSON 对局日志，使用 `indent=2`。
- 复盘命令。
- 复盘进度条拖拽。
- 上一步 / 下一步相邻按钮。

## 10. 风险与约束

- Numba 在 Apple Silicon 上的并行收益必须实测，不能只按核心数线性估算。
- 24 线程搜索可能受分支不均衡影响，根节点并行需要良好 move ordering。
- lock-free 置换表可能带来非确定性，需要测试稳定性。
- Renju 禁手规则复杂，需要大量局面测试。
- Pygame UI 必须和搜索线程隔离。
- Python 层时间控制不能过于频繁进入 JIT 热点，否则会拖慢搜索。
- 开局库质量不足会显著影响胜率，必须作为核心资产持续维护，不能只做格式正确的空壳。

## 11. 验收标准

第一版可验收标准：

- 能启动 Pygame 15 x 15 棋盘。
- 能通过鼠标点击落子。
- 能将点击坐标转成 bitboard index。
- 能检测横、竖、斜四方向五连。
- 能区分黑白棋。
- 能阻止重复落子。
- 能在后台线程启动 AI 搜索，UI 不冻结。
- 能在指定时间内返回 AI 落子。
- AI 单步超过 5 秒必须截断。
- 能通过 `main.py` 解析参数并启动指定模式。
- 能启动人机模式。
- 能启动机机模式。
- 人机模式能悔棋一步，撤销最近一轮人类落子和 AI 应手。
- 能保存对局 log。
- 能用复盘命令打开 log。
- 复盘界面有可拖拽进度条。
- 复盘界面的上一步和下一步按钮相邻。
- 黑棋禁手点能用红色 X 持续显示。
- 黑棋不能落在红色 X 标注位置。
- 不依赖 CNN。
- 不依赖 MPS。
- 不依赖 PyTorch 主模型推理。

进阶验收标准：

- 支持黑棋三三、四四、长连禁手。
- 支持高质量开局库命中。
- 开局库条目可追溯来源和版本。
- 开局库支持标准 26 开局和常见变着。
- 支持 VCF/VCT 必胜搜索。
- 支持 Numba 根节点并行。
- 可在 M2 Ultra 上配置 `NUMBA_NUM_THREADS=24`。
- benchmark 能输出节点数和每秒节点数。

## 12. 第一版实现建议

第一版不要直接追求完整 24 核杀棋引擎。建议按下面顺序推进：

```text
1. main.py 参数入口和最小工程骨架。
2. Pygame 棋盘和鼠标坐标映射。
3. bitboard 坐标转换和落子。
4. 基础胜负检测。
5. Renju 禁手检测和红色 X 覆盖层。
6. 人机模式和 Pygame 异步 AI worker。
7. 对局 JSON 日志，使用 `indent=2`。
8. 复盘命令、进度条、上一步 / 下一步按钮。
9. 简单候选点生成。
10. 单线程 Alpha-Beta。
11. Numba 优化热点。
12. 根节点并行。
13. VCF/VCT。
14. 高质量开局库：标准 26 开局、常见变着、来源追溯、对称扩展。
```

这样可以保证每一步都有可运行结果，避免一开始就把 UI、规则、并行、杀棋、开局库全部耦合在一起。

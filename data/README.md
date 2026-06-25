# Data 目录说明

这个目录保存五子棋 / 连珠 AI 的本地数据资产。当前最重要的是 `opening_book.json`。

## 当前开局库

`opening_book.json` 目前是 Renju 标准开局骨架库，不是完整职业深度定式库。

它已经包含：

- Renju 26 个标准开局形。
- Direct / Indirect 两类标准开局。
- 每个开局的英文名、日文/中文汉字名、简要评估标签。
- 保守的前几手推荐：
  - 空棋盘走天元 `(7, 7)`。
  - 黑棋天元后，白棋走 direct second `(6, 7)`。
  - direct 二手后，黑棋走 `3D Sosei / 疎星`。
  - indirect 二手后，黑棋走 `1I Chosei / 長星`。
- 对标记了 `expand_symmetry` 的条目，加载时自动做 8 向旋转/翻转扩展。

为什么 JSON 里没有把所有镜像都摊平写出来：

- 同一个定番的 8 向旋转/翻转会产生大量重复字段。
- 磁盘文件只保存 canonical 条目，便于人工审核和减少空间浪费。
- `OpeningBook.load()` 会在内存里展开 8 向 key，所以实战查询能匹配各种旋转、镜像、对角线变化。
- 测试 `tests/test_opening_book.py` 覆盖了全部 8 种变换。

它还没有包含：

- 大量职业 SGF 对局抽取出的 4/5/6 手深度变化。
- RenLib 私有库转换结果。
- 每个开局下不同规则体系的候选 5th move offer。
- 胜率统计或 engine 自博弈打分。

这个边界很重要：当前库能防止开局乱走，并让引擎进入标准定番骨架；但还不能冒充完整职业开局数据库。

## 来源

当前标准开局形参考：

- RenjuNet 26 Renju Openings: https://www.renju.net/openings/
- RenjuNet Starting the Game: https://www.renju.net/starting/
- Direct opening diagram: https://www.renju.net/upload/staticfiles/direct_openings.png
- Indirect opening diagram: https://www.renju.net/upload/staticfiles/indirect_openings.png

注意：RenjuNet 页面标注 All rights reserved。因此本仓库只记录标准开局事实、来源 URL 和坐标化结果，不再分发网页图片，也不抓取未明确授权的深度棋谱内容。

## 坐标系统

项目统一使用 0-based row/col：

- 左上角是 `(0, 0)`。
- 右下角是 `(14, 14)`。
- 天元是 `(7, 7)`。
- `index = row * 15 + col`。

`opening_book.json`、对局日志、UI、bitboard 都使用同一套坐标。

## 重建开局库

从仓库根目录运行：

```bash
python scripts/build_opening_book.py
```

这个命令会重建：

```text
data/opening_book.json
```

构建脚本必须保留。以后导入 SGF、RenLib 或其他许可证清楚的数据源时，也应该扩展这个脚本，而不是手工编辑 JSON。

## 查看来源清单

```bash
python scripts/download_opening_sources.py
```

当前脚本只打印来源和许可边界，不自动下载未授权素材。

## 在对局中使用

默认 CLI 参数已经指向：

```bash
--opening-book data/opening_book.json
```

人机模式：

```bash
python main.py play --human black --rule renju --engine numba_bitboard --opening-book data/opening_book.json
```

机机模式：

```bash
python main.py selfplay --games 1 --rule renju --engine numba_bitboard --opening-book data/opening_book.json
```

无 UI 机机批量：

```bash
python main.py selfplay --games 100 --rule renju --engine numba_bitboard --opening-book data/opening_book.json --no-ui
```

## 命中逻辑

搜索前会先按当前棋谱历史生成 key，例如：

```text
B7,7|W6,7
```

如果开局库命中，并且该点未被占用、不是 Renju 黑棋禁手，就直接返回该落子。命中开局库时搜索结果的 `nodes=0`，表示没有消耗搜索节点。

如果未命中，或者命中点非法，则自动回退到当前搜索引擎。

支持的 8 向变换：

- `identity`
- `rot90`
- `rot180`
- `rot270`
- `flip_h`
- `flip_v`
- `diag_main`
- `diag_anti`

## 后续深库方案

下一步要做真正强的开局库，建议按这个顺序：

1. 找许可证清楚的 SGF / RenLib / Gomocup opening 数据源。
2. 写导入器，把外部坐标转换成项目 0-based row/col。
3. 保留来源 URL、许可证、导入时间、原始文件校验值。
4. 对所有导入条目做 8 向对称扩展。
5. 用当前引擎批量复核候选点，过滤明显非法点和 Renju 黑棋禁手。
6. 给每条开局分配 `trust`、`depth`、`source`、`score` 等字段。
7. 加测试局面，确保关键定番能稳定命中。

# Elden Ring Ascended：平衡与新版内容兼容测试

本仓库记录基于用户所持 Ascended MOD 的平衡测试迭代。当前主线为 **v0.4 兼容测试版**；区域随机化尚未开始。v0.3 在玩家的 1.17.1 环境中加载参数文件时出现存档损坏提示，v0.4 改用原版 `11711000` 参数容器。

实机更新：v0.4 完整包仍报存档提示，**紧凑重建且使用官方封装方式的参数文件已能启动**。目前正在整合 [`v0.5 待测改动`](docs/v0.5-pending.md)，等待后续反馈后统一交付完整包。

| 版本 | 逐项记录 | 实际调整 |
|---|---|---|
| v0.1 | [`changes/v0.1.csv`](changes/v0.1.csv) · [`docs/v0.1.md`](docs/v0.1.md) | 581 项 FP 消耗；一处公共事件效果 ID `530373 → 530273`。 |
| v0.2 | [`changes/v0.2.csv`](changes/v0.2.csv) · [`docs/v0.2.md`](docs/v0.2.md) | 9,259 项玩家倍率、护符、敌人血量／抗性／失衡／攻击和近战接触弹反参数改动；继承 v0.1。 |
| v0.3 | [`changes/v0.3_manifest.json`](changes/v0.3_manifest.json) · [`docs/v0.3.md`](docs/v0.3.md) | 在 v0.2 上导入 27 张参数表的 426 个新版独有行；其中 82 行为新武器及强化阶段，2 行为新增开局职业选择。去掉 31 个旧版玩家动作或文字覆盖以供兼容测试。 |
| v0.4 | [`changes/v0.4_manifest.json`](changes/v0.4_manifest.json) · [`docs/v0.4.md`](docs/v0.4.md) | 基于官方 1.17.1 原生容器重建，移植可直接映射的 Ascended 参数行；10 张布局变化的表暂用原版值。 |

## 从何处开始

- 阅读 [`CHANGELOG.md`](CHANGELOG.md) 了解每版决策、验证与未解决问题。
- 阅读 [`docs/initial-comparison.md`](docs/initial-comparison.md) 了解跨版本参数对照的方法及局限。
- 逐项 CSV 含参数表、行 ID、字段中英文说明、原值、原版参考值与调整后值。v0.3 JSON 包含每个新增行 ID、被移除的覆盖路径和测试包哈希。

### 复现参数构建

仓库不提供游戏或 MOD 原包。v0.3 需要自己的 v0.2 完整 ZIP 和官方 1.17.1 已解密 BND4。v0.4 另需自己的 v0.3 完整 ZIP、v0.3 manifest 和官方 1.17.1 加密 `regulation.bin`。可运行：

```bash
python3 -m pip install zstandard cryptography
python3 scripts/unpack_regulation.py /path/to/official/decrypted_regulation.dcx inputs/vanilla_1.17.1.bnd
cp /path/to/Ascended_优化版_v0.2_完整包.zip inputs/
python3 scripts/build_v03.py
cp /path/to/Ascended_优化版_v0.3_新版武器职业测试包.zip inputs/
cp /path/to/v03_manifest.json inputs/
cp /path/to/current/game/regulation.bin inputs/vanilla_1.17.1_regulation.bin
python3 scripts/build_v04.py
```

生成文件位于 `output/`。v0.4 对可兼容表逐行回读验证，并保留原版新行和 Ascended 独有行。10 张布局变化表的旧字段暂未迁移。v0.1/v0.2 的历史精确改动由 CSV 和说明记录，历史构建脚本未包含在此仓库中。

**测试包须在新 MOD 文件夹使用。** 直接覆盖旧文件夹不会删除旧版玩家动作和 `item/menu.msgbnd.dcx`，这会遮住新版资源。新增职业和装备依赖玩家自己安装的游戏版本与 Tarnished Pack 权限；本仓库不含 DLC 内容，也不解除授权。

## 文件边界

`changes/`、`docs/` 与 `scripts/` 仅保存本项目生成的文本、代码和逐项记录。原版与 Ascended 的 `regulation.bin`、地图、动画、脚本、消息文件、完整测试 ZIP 都不进入 Git。Paramdex 字段资料属于 [soulsmods/Paramdex](https://github.com/soulsmods/Paramdex)，这里不复制其内容。

已核对的完整包 SHA-256：v0.2 `82aad1d33353e4bcb4345ca104b889abd429d3222d7f93e7178114c4568bb888`；v0.3 `311171fe4da27f325681e2b6c7e767217d283418b23d63264c18b251972fe3bc`；v0.4 `f8b1f085e6409b9ce6dce3c147d3597b0f287d0886e0bdd938448341f4c97c80`。加密文件含随机 IV，所以重建的 ZIP 哈希会不同，应按解密后的参数行核对。

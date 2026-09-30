# Elden Ring Ascended：平衡与新版内容兼容测试

本仓库记录基于用户所持 Ascended MOD 的平衡测试迭代。当前主线停在 **v0.3 测试版**；区域随机化尚未开始。原版 1.17.1 参数仅用于数值参照及新增行的测试接入，Ascended 参数容器仍是 `11601000`。目前只有静态验证，**没有完成游戏内测试**。

| 版本 | 逐项记录 | 实际调整 |
|---|---|---|
| v0.1 | [`changes/v0.1.csv`](changes/v0.1.csv) · [`docs/v0.1.md`](docs/v0.1.md) | 581 项 FP 消耗；一处公共事件效果 ID `530373 → 530273`。 |
| v0.2 | [`changes/v0.2.csv`](changes/v0.2.csv) · [`docs/v0.2.md`](docs/v0.2.md) | 9,259 项玩家倍率、护符、敌人血量／抗性／失衡／攻击和近战接触弹反参数改动；继承 v0.1。 |
| v0.3 | [`changes/v0.3_manifest.json`](changes/v0.3_manifest.json) · [`docs/v0.3.md`](docs/v0.3.md) | 在 v0.2 上导入 27 张参数表的 426 个新版独有行；其中 82 行为新武器及强化阶段，2 行为新增开局职业选择。去掉 31 个旧版玩家动作或文字覆盖以供兼容测试。 |

## 从何处开始

- 阅读 [`CHANGELOG.md`](CHANGELOG.md) 了解每版决策、验证与未解决问题。
- 阅读 [`docs/initial-comparison.md`](docs/initial-comparison.md) 了解跨版本参数对照的方法及局限。
- 逐项 CSV 含参数表、行 ID、字段中英文说明、原值、原版参考值与调整后值。v0.3 JSON 包含每个新增行 ID、被移除的覆盖路径和测试包哈希。

### 复现 v0.3 参数构建

仓库不提供游戏或 MOD 原包。准备你自己的 v0.2 完整 ZIP，以及用兼容工具解密得到的官方 1.17.1 DCX 或 BND4（原版加密 `regulation.bin` 使用另一密钥，本脚本不能直接解密它）。可运行：

```bash
python3 -m pip install zstandard cryptography
python3 scripts/unpack_regulation.py /path/to/official/decrypted_regulation.dcx inputs/vanilla_1.17.1.bnd
cp /path/to/Ascended_优化版_v0.2_完整包.zip inputs/
python3 scripts/build_v03.py
```

生成文件位于 `output/`。脚本核验 v0.2 已有行完全保留，新增行对应官方原版；新武器常驻效果补上 v0.2 的 `6202065`。脚本只重建 v0.3 参数与测试包；v0.1/v0.2 的历史精确改动由 CSV 和说明记录，历史构建脚本未包含在此仓库中。

**测试包须在新 MOD 文件夹使用。** 直接覆盖旧文件夹不会删除旧版玩家动作和 `item/menu.msgbnd.dcx`，这会遮住新版资源。新增职业和装备依赖玩家自己安装的游戏版本与 Tarnished Pack 权限；本仓库不含 DLC 内容，也不解除授权。

## 文件边界

`changes/`、`docs/` 与 `scripts/` 仅保存本项目生成的文本、代码和逐项记录。原版与 Ascended 的 `regulation.bin`、地图、动画、脚本、消息文件、完整测试 ZIP 都不进入 Git。Paramdex 字段资料属于 [soulsmods/Paramdex](https://github.com/soulsmods/Paramdex)，这里不复制其内容。

已核对的完整包 SHA-256：v0.2 `82aad1d33353e4bcb4345ca104b889abd429d3222d7f93e7178114c4568bb888`；v0.3 `311171fe4da27f325681e2b6c7e767217d283418b23d63264c18b251972fe3bc`。v0.3 的加密文件含随机 IV，所以重新运行脚本所生成 ZIP 哈希会不同，应按解密后的参数行核对。

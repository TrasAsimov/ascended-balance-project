# Simplified Chinese item text patch / 简体中文道具文本补丁

The current v0.10.4 release includes English item descriptions. This source patch translates the modified talisman effects, 21 ordinary remembrance effects, and the starter **Empowered Soul** into Simplified Chinese while keeping the rest of your game's own Chinese text.

当前 v0.10.4 安装包含英文道具说明。本补丁会翻译改动过的护符、21 种普通追忆及开局道具 **Empowered Soul（强化之魂）**，其余简中内容沿用你自己游戏版本的文本。

## Build / 生成

Use the **two Simplified Chinese archives from your installed 1.17.1 game with DLC**. Supply `Game/msg/zhocn/item_dlc01.msgbnd.dcx` and `Game/msg/zhocn/item_dlc02.msgbnd.dcx` as input; do not use the old Ascended 1.16 Chinese archives. If the game archives use Kraken compression, unpack each archive to a raw `BND4` file first with a game-compatible tool and your legally installed `oo2core_6_win64.dll`. The script supports raw BND4 or DFLT DCX input and emits DFLT DCX overlays.

使用**与你当前 1.17.1 游戏和 DLC 一致的两份简中文本包**：`Game/msg/zhocn/item_dlc01.msgbnd.dcx` 与 `Game/msg/zhocn/item_dlc02.msgbnd.dcx`。不要使用 Ascended 1.16 旧简中包。如文件采用 Kraken 压缩，请先借助兼容游戏格式的工具及自己游戏目录中的 `oo2core_6_win64.dll` 解成原始 `BND4`；脚本接受 BND4 或 DFLT DCX，输出 DFLT DCX 覆盖文件。

```powershell
py -3 scripts/build_zhocn_patch.py "D:\EldenRing\Game\msg\zhocn\item_dlc01.msgbnd.dcx" "D:\EldenRing\Game\msg\zhocn\item_dlc02.msgbnd.dcx" "D:\Ascended\ModEngine\mod"
```

If you unpacked the two archives, substitute their BND4 file paths. Copy the resulting `msg/zhocn/item_dlc01.msgbnd.dcx` and `msg/zhocn/item_dlc02.msgbnd.dcx` into the same mod folder as the v0.10.4 test build. The script refuses unknown compression or an occupied Empowered Soul ID instead of silently replacing unrelated text.

如先行解压，请把上述命令中的两个输入路径换成 BND4 文件路径。生成的两份 `msg/zhocn/*.msgbnd.dcx` 会落在所指定的 MOD 目录内。脚本遇到未知压缩格式或被其他道具占用的“强化之魂”ID 会停止，避免误覆盖。

This repository does not contain a prebuilt Chinese archive because it lacks the matching official 1.17.1 Chinese input archives. The script was structurally checked against the current release's English DLC01 and DLC02 archives: all 21 remembrance captions, eight talisman captions, and three Empowered Soul fields survive packing and unpacking in both variants. In-game Chinese display has not yet been tested. Please provide the two matching official Chinese archives if you want a ready-to-install binary patch assembled here.

仓库尚无可直接安装的简中二进制包，因为缺少同版本的官方简中输入包。脚本已用当前 Release 的英文 DLC01、DLC02 包校验结构：两份输出都保留了 21 条普通追忆、8 条护符说明及 3 条强化之魂字段；**简中游戏内显示尚未实测**。若希望由项目直接提供可安装补丁，请提供上述两份同版本官方简中包。

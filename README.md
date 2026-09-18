# 桌面宠物

一个透明的桌面宠物程序，住在你的桌面上，会撒娇、会打哈欠、陪你打字、帮你查单词。

> English version: [README_EN.md](README_EN.md)

![Preview](docs/preview.png)

> 上图用的是**作者自绘的形象**（素材原文件不随仓库分发）。仓库另带一套占位形象，clone 后复制一下就能跑 —— 见下方「自备素材」。

---

## 下载

不想配环境？直接从 Releases 拿打包好的版本：

👉 **[Releases · v6.9](https://github.com/owdeky017-ui/desktop-pet/releases/tag/v6.9)**

发布包分中英两个版本，各自独立，**界面、菜单、设置和宠物台词完全用各自语言**：

| 版本 | 压缩包 | 主程序 | 界面语言 | 附带说明 |
| --- | --- | --- | --- | --- |
| 中文版 | `DesktopPet-v69-windows.zip` | `DesktopPet_v69.exe` | 中文 | `使用说明.txt` |
| 英文版 | `DesktopPet-v69-windows-en.zip` | `DesktopPet_v69_en.exe` | 英文 | `Instructions.txt` |

解压到同一个文件夹，双击对应版本的 exe 即可，免安装。两个版本可以放在同一个文件夹里，互不干扰。

压缩包里除了主程序和说明，还有 6 张占位形象：

| 文件 | 说明 |
| --- | --- |
| `pet_transparent.png`<br>`mini_1.png` ~ `mini_5.png` | 默认的占位形象 PNG —— 直接改这些图就能换形象，改完放回 exe 旁边 |

> **注意：下载下来看到的不是上面的预览图。** 预览图是作者自绘的成品形象（仅作示意），发布包内嵌的是占位形象（粉色小熊），要把占位图换成作者那套或你自己的图，看压缩包里的说明文件。

---

## 功能

- **透明无边框窗口** —— 真正「住」在桌面上，不抢任务栏位置
- **多种交互** —— 单击、双击、长按、悬停抚摸、滚轮缩放、拖拽
- **会自己动** —— 随机踱步、伸懒腰、打哈欠、左右看；闲置久了会睡着
- **攀附屏幕/应用窗口** —— 拖到窗口边上会被吸附过去，歪头「抱住」它
- **打字陪伴 & 实时翻译** —— 监听键盘，敲得多有反应；复制英文自动翻译
- **查单词 & 生词本** —— 右键查词，自动保存进生词本，可导出为可编辑的 HTML
- **截图工具** —— 全屏或区域截图，可选保存/复制
- **系统托盘** —— 隐藏、设置、自启动、退出
- **自定义台词库** —— JSON 文件里改台词，支持可视化编辑

---

## 快速开始

需要 Python 3.10+ 和 Windows（程序用了 Windows 特定的 API：键盘 hook、注册表自启动、Win32 窗口枚举）。

```bash
# 克隆仓库
git clone https://github.com/owdeky017-ui/desktop-pet.git
cd desktop-pet

# 创建虚拟环境
python -m venv venv
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 运行
python main.py
```

### 打包成 exe

```bash
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --name DesktopPet_v69 ^
  --add-data "placeholder\pet_transparent.png;." ^
  --add-data "placeholder\mini_1.png;." ^
  --add-data "placeholder\mini_2.png;." ^
  --add-data "placeholder\mini_3.png;." ^
  --add-data "placeholder\mini_4.png;." ^
  --add-data "placeholder\mini_5.png;." ^
  main.py
```

> **`--add-data` 不能省。** 素材没打进 exe 时程序照样能启动，但形象是空白的 —— `QPixmap` 加载失败只返回空图，不抛异常、不报错，很容易被当成「打包成功」。Windows 上分隔符用 `;`，macOS/Linux 用 `:`。

想内嵌自己的素材，把上面 `placeholder\` 换成你自己的文件路径即可（见下节）。

打包完成后 `DesktopPet_v69.exe` 单独一个文件就能跑（素材已内嵌）。想让别人也能换图，就把 PNG 一并放进压缩包 —— 见下节。

### 打包英文版

界面语言由**打包时内嵌的 `lang.txt`** 决定，不是运行时切换的：里面写 `en` 就是英文版，没有这个文件（或写 `zh`）就是中文版。

```bash
# 准备语言标记文件
mkdir build_lang_en
echo en > build_lang_en\lang.txt

# 打包英文版：多一行 --add-data 把 lang.txt 放进包根目录
pyinstaller --noconfirm --onefile --windowed --name DesktopPet_v69_en ^
  --add-data "build_lang_en\lang.txt;." ^
  --add-data "placeholder\pet_transparent.png;." ^
  ...（其余 5 张 mini 同上）...
  main.py
```

> 文件名必须是 `lang.txt`（`--add-data` 的目标目录不会重命名文件），所以中文版和英文版要分别放在不同目录下准备。

> **台词库按语言分文件**：中文版写 `data/lines.json`，英文版写 `data/lines_en.json`。两个版本很可能被解压到同一个文件夹里共用 `data/`，如果共用一个文件，谁先运行谁的语言就会把另一个版本也带偏（英文版会开始说中文台词）。英文版第一次启动时，如果发现旧的 `lines.json` 内容确实属于英文（和默认台词有交集），会自动接过来，不会丢用户改过的台词。

代码里的做法是：所有界面文案都写成 `T("中文原文")`，`T()` 在中文版原样返回、英文版查 `EN` 表替换。台词库、菜单、设置面板、气泡、生词本导出页都走这一层。**中文版的输出与加入多语言之前逐字一致。**

---

## 自备素材

仓库自带一套**程序生成的占位形象**（`placeholder/`），clone 下来就能先跑起来看效果：

```bash
copy placeholder\*.png .
python main.py
```

想换成自己的素材时，把下面这些文件放到仓库根目录（或 exe 同目录）覆盖掉即可：

| 文件 | 用途 |
| --- | --- |
| `pet_transparent.png` | 主形象 + 系统托盘图标（透明背景） |
| `mini_1.png` ~ `mini_5.png` | 双击时从天上掉下来的小人 |

> `pet.png` 代码里没有引用 —— 托盘图标用的是 `pet_transparent.png`（`QIcon(PET_IMAGE)`）。

可选用 `pet_<name>.png` 命名添加更多皮肤，在右键菜单 → 设置 → 形象里切换。

---

## 数据存放

运行时生成的文件放在 **exe 同目录的 `data/` 文件夹**里，不会污染你的工作目录。窗口位置、缩放、各类开关单独写在 **exe 旁边的 `pet_config.json`**（不在 `data/` 里），方便查找和直接编辑。

```
DesktopPet_v69.exe
├── pet_config.json    # 窗口位置、缩放、各类开关（直接放在 exe 旁边方便编辑）
├── (你的 PNGs)        # pet_transparent.png / mini_*.png / pet_xxx.png
└── data/
    ├── vocab.json          # 生词本
    ├── lines.json          # 自定义台词（中文版；首次运行自动生成）
    ├── lines_en.json       # 自定义台词（英文版；同上）
    ├── typing_log.txt      # 调试日志（按需生成）
    ├── translation_log.txt # 调试日志（按需生成）
    └── screenshots/        # 截图保存目录
```

### 改宠物名

台词里的 `{name}` 是占位符，运行时替换成 `pet_name`，**默认未命名**（此时宠物自称「我」）。改名有两种方式：

**1. 设置面板（推荐）** —— 右键 → 设置 → 在「宠物名」输入框里改 → 确定。立即生效，不用重启，托盘提示和台词会同步更新。

**2. 直接改配置文件** —— 打开 `pet_config.json`，改 `"pet_name"`：

```json
{ "pet_name": "小豆丁" }
```

> 输入框留空的话，宠物会自称「我」（台词里的 `{name}` 替换成「我」）。

---

## 自启动

右键 → 开机自启动，会在注册表 `HKCU\Software\Microsoft\Windows\CurrentVersion\Run` 写一条 `DesktopPet_Pet`。

> 旧版本（≤ v6.9 早期构建）用的是 `DesktopPet_Hana`。程序写入新键时会自动把旧键删掉，不会出现两条自启动项重复拉起。

---

## 托盘

**默认启动时宠物窗口是隐藏的，只在系统托盘显示图标** —— 不会一开机就占着桌面。想让它出来有两种方式：

- 单击托盘图标
- 右键托盘图标 → 显示/隐藏宠物

不想要这个行为，就：右键 → 设置 → 取消勾选「启动时隐藏窗口（只在托盘显示）」，下次启动会直接显示宠物窗口。

> **托盘图标找不到？** Windows 会把不常用的图标折叠进任务栏的「隐藏的图标」（向上箭头）里。点箭头就能看到；想让它一直显示在外面：**设置 → 个性化 → 任务栏 → 任务栏角溢出**（或「选择哪些图标显示在任务栏上」）→ 把桌面宠物设为「开」。这一步是 Windows 的系统行为，程序无法替你设置。

---

## 项目结构

```
.
├── main.py              # 全部代码（透明窗口、动画、气泡、生词本、截图、翻译……）
├── requirements.txt     # 依赖
├── .gitignore           # 排除 venv / .exe / 根目录真实素材 / 运行时 data 目录
├── placeholder/         # 占位形象（程序生成，clone 后复制到根目录即可运行）
├── docs/preview.png     # README 顶部效果图
├── pet_config.json      # 配置示例（运行时会被覆盖成你自己的）
├── vocab.json           # 生词本（空起步）
├── 生词本.html          # 导出生词本的样例输出（演示用，无真实数据）
├── README.md            # 本文件（中文）
├── README_EN.md         # 英文说明
├── 使用说明.txt         # 中文版发布包附带的说明
└── Instructions.txt     # 英文版发布包附带的说明
```

---

## 已知限制

- 仅 Windows：键盘 hook、注册表自启动、Win32 窗口枚举都是 Windows 专属。
- 全屏独占游戏会把宠物盖住，没法置顶到 DirectX 表面。
- 翻译走 MyMemory 免费 API，超过额度会失败（程序会安静地提示一下）。

---

## License

MIT — 见 [LICENSE](LICENSE)。

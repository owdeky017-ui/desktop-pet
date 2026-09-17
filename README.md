# 桌面宠物 · Desktop Pet

一个透明的桌面宠物程序，住在你的桌面上，会撒娇、会打哈欠、陪你打字、帮你查单词。

A transparent desktop companion that talks back, naps on your screen, and looks up words while you work.

![Preview](docs/preview.png)

> 上图用的是**作者自绘的形象**（素材原文件不随仓库分发）。仓库另带一套占位形象，clone 后复制一下就能跑 —— 见下方「自备素材」。
> The screenshot shows the **author's own artwork** (source PNGs aren't redistributed). The repo also ships placeholder sprites so it runs right after cloning — see [Bring your own sprites](#bring-your-own-sprites).

---

## 下载 · Download

不想配环境？直接从 Releases 拿打包好的版本：

Prefer to just run it? Grab the packaged build from the releases page:

👉 **[Releases · v6.9](https://github.com/owdeky017-ui/desktop-pet/releases/tag/v6.9)** — 下 `DesktopPet-v69-windows.zip`，解压到同一个文件夹，双击 `DesktopPet_v69.exe` 即可，免安装。

压缩包里有三样东西：

The zip contains three things:

| 文件 · File | 说明 · What it is |
| --- | --- |
| `DesktopPet_v69.exe` | 主程序（已内嵌占位形象，单独双击就能跑）<br>The app — placeholder sprites are embedded, so it runs on its own |
| `pet_transparent.png`<br>`mini_1.png` ~ `mini_5.png` | 默认的占位形象 PNG —— 直接改这些图就能换形象，改完放回 exe 旁边<br>Placeholder sprite PNGs — edit these to reskin the pet, then put them next to the exe |
| `使用说明.txt` | 换图、改宠物名等操作步骤<br>Step-by-step: swapping sprites, renaming the pet, etc. |

> **注意：下载下来看到的不是上面的预览图。** 预览图是作者自绘的成品形象（仅作示意），发布包内嵌的是占位形象（粉色小熊），要把占位图换成作者那套或你自己的图，看压缩包里的 `使用说明.txt`。
>
> **The pet in the download won't look like the screenshot above.** The screenshot is a finished illustration of the author's own art (just for show); the release actually ships a placeholder sprite (a pink bear). To swap in the author's art or your own, see `使用说明.txt` in the zip.

Download the zip, unzip everything into one folder, and double-click `DesktopPet_v69.exe`. No installer. To use your own art, see [自备素材 · Bring your own sprites](#自备素材--bring-your-own-sprites).

---

## 功能 · Features

- **透明无边框窗口** — 真正"住"在桌面上，不抢任务栏位置
  Truly transparent, frameless window that stays out of your way.
- **多种交互** — 单击、双击、长按、悬停抚摸、滚轮缩放、拖拽
  Single click, double click, long press, hover petting, scroll-zoom, drag to move.
- **会自己动** — 随机踱步、伸懒腰、打哈欠、左右看；闲置久了会睡着
  Idles on its own — walks, stretches, yawns, looks around, then naps when ignored.
- **攀附屏幕/应用窗口** — 拖到窗口边上会被吸附过去，歪头"抱住"它
  Drags onto a window edge to cling on with a tilted pose.
- **打字陪伴 & 实时翻译** — 监听键盘，敲得多有反应；复制英文自动翻译
  Reacts to your typing pace and auto-translates English you copy to the clipboard.
- **查单词 & 生词本** — 右键查词，自动保存进生词本，可导出为可编辑的 HTML
  Right-click to look up words. Saved into a personal vocab book, exportable as editable HTML.
- **截图工具** — 全屏或区域截图，可选保存/复制
  Full-screen or region screenshots, with save / copy choices.
- **系统托盘** — 隐藏、设置、自启动、退出
  System tray with show/hide, settings, autostart, exit.
- **自定义台词库** — JSON 文件里改台词，支持可视化编辑
  Customizable dialogue in a JSON file with an in-app visual editor.

---

## 快速开始 · Quick start

需要 Python 3.10+ 和 Windows（程序用了 Windows 特定的 API：键盘 hook、注册表自启动、Win32 窗口枚举）。

Requires Python 3.10+ on Windows (uses Win32 APIs for the keyboard hook, autostart registry, and window enumeration).

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

### 打包成 exe · Build the exe

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

> **`--add-data` 不能省。** 素材没打进 exe 时程序照样能启动，但形象是空白的 —— `QPixmap` 加载失败只返回空图，不抛异常、不报错，很容易被当成"打包成功"。Windows 上分隔符用 `;`，macOS/Linux 用 `:`。
>
> Don't skip `--add-data`. Without bundled sprites the app still launches but renders nothing — `QPixmap` fails silently and returns a null pixmap, which looks exactly like a successful build. Use `;` on Windows, `:` on macOS/Linux.

想内嵌自己的素材，把上面 `placeholder\` 换成你自己的文件路径即可（见下节）。

打包完成后 `DesktopPet_v69.exe` 单独一个文件就能跑（素材已内嵌）。想让别人也能换图，就把 PNG 一并放进压缩包 —— 见下节。

To embed your own art, swap `placeholder\` for your own paths (see below). The resulting `DesktopPet_v69.exe` runs standalone with sprites embedded. If you want users to be able to swap sprites, ship the PNGs alongside it in the zip — see below.

---

## 自备素材 · Bring your own sprites

仓库自带一套**程序生成的占位形象**（`placeholder/`），clone 下来就能先跑起来看效果：

The repo ships with **generated placeholder sprites** (`placeholder/`) so it runs right after cloning:

```bash
copy placeholder\*.png .
python main.py
```

想换成自己的素材时，把下面这些文件放到仓库根目录（或 exe 同目录）覆盖掉即可：

When you're ready to swap in your own art, drop these files into the repo root (or the directory next to the exe):

| 文件 · File | 用途 · Used for |
| --- | --- |
| `pet_transparent.png` | 主形象 + 系统托盘图标（透明背景）<br>Main sprite **and** system tray icon — the tray reuses this same file, transparent background |
| `mini_1.png` ~ `mini_5.png` | 双击时从天上掉下来的小人<br>Mini characters that drop from the sky on double-click |

> `pet.png` 代码里没有引用 —— 托盘图标用的是 `pet_transparent.png`（`QIcon(PET_IMAGE)`）。
> `pet.png` is never referenced — the tray loads `pet_transparent.png` via `QIcon(PET_IMAGE)`.

可选用 `pet_<name>.png` 命名添加更多皮肤，在右键菜单 → 设置 → 形象里切换。

Optionally add more skins by naming them `pet_<name>.png`. Switch between them in the right-click menu → Settings → Skin.

---

## 数据存放 · Where data lives

运行时生成的文件放在 **exe 同目录的 `data/` 文件夹**里，不会污染你的工作目录。窗口位置、缩放、各类开关单独写在 **exe 旁边的 `pet_config.json`**（不在 `data/` 里），方便查找和直接编辑。

All runtime files (vocab, dialogue library, logs, screenshots) live in a **`data/` folder next to the program**. Window position, scale, and toggles are written to **`pet_config.json` next to the exe** — kept outside `data/` so it's easy to find and edit.

```
DesktopPet_v69.exe
├── pet_config.json    # 窗口位置、缩放、各类开关（直接放在 exe 旁边方便编辑）
├── (你的 PNGs)        # pet_transparent.png / mini_*.png / pet_xxx.png
└── data/
    ├── vocab.json          # 生词本
    ├── lines.json          # 自定义台词（首次运行自动生成）
    ├── typing_log.txt      # 调试日志（按需生成）
    ├── translation_log.txt # 调试日志（按需生成）
    └── screenshots/        # 截图保存目录
```

### 改宠物名 · Rename your pet

台词里的 `{name}` 是占位符，运行时替换成 `pet_name`，默认是「花枝」。改名有两种方式：

Dialogue lines contain a `{name}` placeholder that resolves at runtime from `pet_name` (defaults to 花枝). Two ways to rename:

**1. 设置面板（推荐）** —— 右键 → 设置 → 在「宠物名」输入框里改 → 确定。立即生效，不用重启，托盘提示和台词会同步更新。

Through the UI: right-click the pet → Settings → type a new name in the box → OK. Takes effect immediately; tray tooltip and dialogue update live.

**2. 直接改配置文件** —— 打开 `pet_config.json`，改 `"pet_name"`：

Or edit `pet_config.json` directly:

```json
{ "pet_name": "小豆丁" }
```

> 输入框留空的话，会回到默认名字「花枝」。
> Leaving the box empty reverts to the default name 花枝.

---

## 自启动 · Autostart on login

右键 → 开机自启动，会在注册表 `HKCU\Software\Microsoft\Windows\CurrentVersion\Run` 写一条 `DesktopPet_Hana`。

Right-click → Autostart writes a `DesktopPet_Hana` entry under `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`.

---

## 项目结构 · Project layout

```
.
├── main.py              # 全部代码（透明窗口、动画、气泡、生词本、截图、翻译……）
├── requirements.txt     # 依赖
├── .gitignore            # 排除 venv / .exe / 根目录真实素材 / 运行时 data 目录
├── placeholder/          # 占位形象（程序生成，clone 后复制到根目录即可运行）
├── docs/preview.png      # README 顶部效果图
├── pet_config.json      # 配置示例（运行时会被覆盖成你自己的）
├── vocab.json           # 生词本（空起步）
├── 生词本.html           # 导出生词本的样例输出（演示用，无真实数据）
└── README.md
```

---

## 已知限制 · Known limits

- 仅 Windows：键盘 hook、注册表自启动、Win32 窗口枚举都是 Windows 专属。
  Windows only — the keyboard hook, autostart registry, and window enumeration are Win32-specific.
- 全屏独占游戏会把宠物盖住，没法置顶到 DirectX 表面。
  Fullscreen-exclusive games will cover the pet; there's no way to draw on top of a DirectX surface.
- 翻译走 MyMemory 免费 API，超过额度会失败（程序会安静地提示一下）。
  Translation uses the free MyMemory API and will fail past the daily quota.

---

## License

MIT — 见 [LICENSE](LICENSE)。

MIT — see [LICENSE](LICENSE).
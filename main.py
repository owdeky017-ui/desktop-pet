# -*- coding: utf-8 -*-
"""
桌面宠物主程序（PySide6 增强版）
功能：
  1. 透明无边框窗口，显示宠物形象
  2. 左键拖动移动，鼠标滚轮缩放
  3. 右键菜单（重置、透明度、穿透、气泡、退出）
  4. 鼠标穿透（透明区域穿透）
  5. 随机自主动作（踱步、发呆、休眠）
  6. 点击交互（单击抖动+台词、双击弹跳+台词）
  7. 触碰反馈（悬停放大、长按缩小、拖拽倾斜）
  8. 气泡台词（圆角+半透明+小尾巴+胡萝卜装饰）
  9. 透明度调节（手动+智能）
  10. 系统托盘（显示/隐藏、重启、退出、快捷键）
  11. 攀附窗口边缘（抱树姿势）
"""

import sys
import os
import json
import math
import random
import time
import threading
import ctypes
from ctypes import wintypes
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
from PySide6.QtWidgets import (QApplication, QWidget, QLabel, QMenu, QSystemTrayIcon,
                               QSlider, QVBoxLayout, QHBoxLayout, QDialog, QPushButton, QInputDialog, QCheckBox, QComboBox, QTextEdit, QMessageBox, QLineEdit)
from PySide6.QtGui import QPixmap, QPainter, QColor, QBrush, QPen, QFont, QFontMetrics, QPainterPath, QIcon, QCursor
from PySide6.QtCore import Qt, QTimer, QPoint, QRect, QSize, Signal, QEvent, QPropertyAnimation, QThread

# ============ 路径处理 ============
def get_resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)


def get_data_dir():
    """Return the writable data directory, creating it if missing.

    Frozen builds use the directory next to the .exe; source runs use
    the directory next to main.py.
    """
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base, "data")
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


# ============ 可配置参数 ============
PET_IMAGE = get_resource_path("pet_transparent.png")
MINI_IMAGE_NAMES = [f"mini_{i}.png" for i in range(1, 6)]


def get_mini_images():
    """小人图片：优先用 exe 同目录下的（方便用户替换），没有再回退到内嵌资源。

    Mini-character sprites: prefer copies sitting next to the exe so users can
    swap them, falling back to the ones bundled into the build.
    """
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    paths = []
    for name in MINI_IMAGE_NAMES:
        custom = os.path.join(base, name)
        paths.append(custom if os.path.exists(custom) else get_resource_path(name))
    return paths
DEFAULT_PET_NAME = ""  # 默认未命名；留空时台词里的 {name} 自称「我」，用户可在设置里改名
MIN_SCALE = 0.1
MAX_SCALE = 1.0
DEFAULT_SCALE = 0.5  # 0.1 对 placeholder（256px）太不友好；首启缩到 26px 用户看不到。改为 0.5 后占位图 128px 可见。已有 config 用户的 scale 不受这个值影响
BUBBLE_DURATION = 4000  # 气泡显示时长ms
IDLE_ACTION_MIN = 30000  # 闲置动作最小间隔ms
IDLE_ACTION_MAX = 60000  # 闲置动作最大间隔ms
SLEEP_AFTER = 120000  # 闲置多久后休眠ms

# 配置文件路径（exe同目录）
if getattr(sys, 'frozen', False):
    CONFIG_PATH = os.path.join(os.path.dirname(sys.executable), "pet_config.json")
else:
    CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pet_config.json")

# 数据目录：vocab、台词库、日志、截图都放这里
DATA_DIR = get_data_dir()
VOCAB_PATH = os.path.join(DATA_DIR, "vocab.json")
LINES_PATH = os.path.join(DATA_DIR, "lines.json")

# 默认台词库
DEFAULT_LINES = {
    "idle": [
        "（探头）哈喽呀～你终于来啦，{name}等你好久了啊啊啊💗",
        "哦哈哟～今天也要元气满满哦，{name}给你注入能量！੧ᐛ੭",
        "（歪头）咦你回来啦，快过来让{name}看看有没有好好吃饭◐⩊◑",
        "嘤嘤嘤人家好无聊，有没有人来陪{name}聊聊天嘛（）",
        "（戳戳你）在看什么呢在看什么呢，让{name}也看看嘛～",
        "呜呜呜你都不理{name}，{name}要黑化了哦💢（才不会，理我一下嘛）",
        "{name}提醒您，该次饭啦🍚再不吃饭饭就要凉了哦",
        "（打哈欠）好困哦... 但是还想再陪你一会儿...zzz",
        "工作加油哦！{name}在旁边给你应援！！✊🏻摸鱼也可以的（小声）",
        "唉今天也是摸鱼的一天呢，不过摸鱼好快乐啊哈哈哈哈🤪",
        "报一丝报一丝，刚才不小心把你的零食吃掉了（x）真的只吃了一口",
        "（突然凑近）悄悄告诉你，{name}今天也超级喜欢你呀💗",
        "系不系今天也很辛苦呀，来，给你抱抱🤗",
        "你说... 爱就爱不爱就不爱，可爱是什么意思呀😠",
        "想不想跟{name}回武汉七热干面呀，{name}请客（才怪，你请）",
        "（递上一颗糖）给你吃，吃完就要开心起来哦,不开心{name}会心疼的 TT",
        "没关系的啦，天塌下来有{name}顶着（虽然{name}也顶不住），一切都会好的ʔ・̫͡・ʕ",
        "在相册翻翻捡捡... 发现有你的每一天都是独一无二的幸福🌸",
        "哎呀不小心打翻水杯了...（收拾中）就当是给地板洗个澡吧（）",
        "（一本正经）人类已经无法阻止{name}了！（下一秒）啊好饿，次饭去",
    ],
    "click": [
        "（探头）哈喽呀～你终于来啦，{name}等你好久了啊啊啊💗",
        "哦哈哟～今天也要元气满满哦，{name}给你注入能量！੧ᐛ੭",
        "（歪头）咦你回来啦，快过来让{name}看看有没有好好吃饭◐⩊◑",
        "嘤嘤嘤人家好无聊，有没有人来陪{name}聊聊天嘛（）",
        "（戳戳你）在看什么呢在看什么呢，让{name}也看看嘛～",
        "呜呜呜你都不理{name}，{name}要黑化了哦💢（才不会，理我一下嘛）",
        "系不系今天也很辛苦呀，来，给你抱抱🤗",
        "你说... 爱就爱不爱就不爱，可爱是什么意思呀😠",
        "（突然凑近）悄悄告诉你，{name}今天也超级喜欢你呀💗",
        "（递上一颗糖）给你吃，吃完就要开心起来哦,不开心{name}会心疼的 TT",
    ],
    "double": [
        "哎呀不小心打翻水杯了...（收拾中）就当是给地板洗个澡吧（）",
        "（一本正经）人类已经无法阻止{name}了！（下一秒）啊好饿，次饭去",
        "报一丝报一丝，刚才不小心把你的零食吃掉了（x）真的只吃了一口",
        "唉今天也是摸鱼的一天呢，不过摸鱼好快乐啊哈哈哈哈🤪",
        "想不想跟{name}回武汉七热干面呀，{name}请客（才怪，你请）",
        "工作加油哦！{name}在旁边给你应援！！✊🏻摸鱼也可以的（小声）",
    ],
    "typing_long": [
        "哇，你打了好多字呀，辛苦了～",
        "认真工作的样子好帅！{name}给你捶捶背🤗",
        "这么多内容，是在写什么重要的东西吗～",
    ],
    "typing_medium": [
        "嗯嗯，{name}在旁边安静陪着你～",
        "加油加油！{name}为你应援✊",
        "打字打得好认真呀，要不要休息一下～",
    ],
    "typing_short": [
        "你在跟谁聊天呀～是不是在说{name}的好话😳",
        "在写什么呢在写什么呢，让{name}看看嘛～",
        "哦哦，又在忙啦，{name}不打扰你了",
        "打字啪啪啪的，好厉害呀！",
    ],
    "cling": [
        "抱住啦～{name}会乖乖陪着你的🥰",
        "嘿嘿，攀上来咯，这里视野不错呀～",
        "抱紧抱紧，不会掉下去的（才怪）",
    ],
    "eat": [
        "辛苦啦~我来帮你吃掉(๑•̀ㅂ•́)و✧",
    ],
    "greeting_morning": [
        "早上好呀～新的一天也要元气满满哦☀️",
        "早安早安，{name}已经等你好久啦～",
    ],
    "greeting_afternoon": [
        "下午好呀～要不要喝杯奶茶提提神🥤",
        "午安～工作辛苦了，休息一下吧",
    ],
    "greeting_evening": [
        "晚上好呀～今天也辛苦啦💗",
        "晚饭吃了吗？不吃饭{name}会担心的哦",
    ],
    "greeting_night": [
        "这么晚还不睡呀～{name}陪你熬夜🌙",
        "夜深了，要注意休息哦，{name}会心疼的",
    ],
}


def _load_lines_from_file():
    """从 DATA_DIR/lines.json 加载台词，不存在则创建默认文件"""
    try:
        data_dir = os.path.dirname(LINES_PATH)
        if not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)
        if not os.path.exists(LINES_PATH):
            with open(LINES_PATH, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_LINES, f, ensure_ascii=False, indent=2)
            return DEFAULT_LINES
        with open(LINES_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        # 合并默认值，确保所有key都存在
        result = {}
        for key, default_val in DEFAULT_LINES.items():
            result[key] = data.get(key, default_val)
            if not result[key]:
                result[key] = default_val
        return result
    except Exception:
        return DEFAULT_LINES


# 加载台词
LINES = _load_lines_from_file()
LINES_IDLE = LINES["idle"]
LINES_CLICK = LINES["click"]
LINES_DOUBLE = LINES["double"]


# ============ 气泡窗口 ============
class BubbleWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.text = ""
        self._full_text = ""
        self._displayed_count = 0
        self.tail_side = "bottom"
        self._anchor_x = 0
        self._anchor_y = 0
        self._lines = []
        self._text_w = 100
        self._text_h = 20
        font = QFont("Microsoft YaHei", 10)
        self._fm = QFontMetrics(font)
        # 打字机定时器
        self.type_timer = QTimer(self)
        self.type_timer.timeout.connect(self._type_next_char)
        self.hide()

    def _char_width(self, ch):
        """智能字符宽度：emoji修饰符不计宽，emoji基础字符估算，其余用horizontalAdvance"""
        cp = ord(ch)
        # emoji修饰符（肤色、变异选择符、ZWJ、组合键帽）不单独占宽度
        if (0x1F3FB <= cp <= 0x1F3FF or 0xFE00 <= cp <= 0xFE0F or
            cp == 0x200D or cp == 0x20E3):
            return 0
        # emoji基础字符，10号字体下约占20px
        if (0x1F000 <= cp <= 0x1FAFF or 0x2600 <= cp <= 0x27BF or
            0x2B00 <= cp <= 0x2BFF or 0x2300 <= cp <= 0x23FF or
            0x1F1E6 <= cp <= 0x1F1FF):
            return 20
        return self._fm.horizontalAdvance(ch)

    def _text_width(self, text):
        return sum(self._char_width(ch) for ch in text)

    def _type_next_char(self):
        if self._displayed_count < len(self._full_text):
            self._displayed_count += 1
            self.text = self._full_text[:self._displayed_count]
            self._recalc_lines()
            self.update()
        else:
            self.type_timer.stop()

    def _wrap_text(self, text):
        """按已有换行符分段，每段内再按宽度自动换行"""
        max_width = 260
        no_leading = set(" ，。、！？；：）】》」』～…—,.!?;:)]}")
        all_lines = []
        for segment in text.split("\n"):
            words = list(segment)
            current = ""
            for w in words:
                test = current + w
                if self._text_width(test) > max_width:
                    if w in no_leading:
                        all_lines.append(current + w)
                        current = ""
                    else:
                        all_lines.append(current)
                        current = w
                else:
                    current = test
            if current:
                all_lines.append(current)
            elif not words:
                # 空行（连续换行）
                all_lines.append("")
        return all_lines

    def _recalc_lines(self):
        # 根据当前已显示的文本重新计算换行
        self._lines = self._wrap_text(self.text)
        if self._lines:
            self._text_w = max(self._text_width(l) for l in self._lines)
        else:
            self._text_w = 100
        self._text_h = len(self._lines) * self._fm.height()

    def show_text(self, text, x, y, tail_side="bottom"):
        self._full_text = text
        self._displayed_count = 0
        self.text = ""
        self.tail_side = tail_side
        self._anchor_x = x
        self._anchor_y = y
        font = QFont("Microsoft YaHei", 10)
        self._fm = QFontMetrics(font)
        # 先按完整文本计算气泡大小（避免逐字时气泡跳动）
        lines = self._wrap_text(text)
        text_w = max(self._text_width(l) for l in lines) if lines else 100
        text_h = len(lines) * self._fm.height()
        self._text_w = text_w
        self._text_h = text_h
        self._lines = []
        padding = 18
        # 胡萝卜装饰占左侧约24px，需要额外留出空间
        carrot_extra = 24
        bw = int(text_w + padding * 2 + carrot_extra)
        bh = int(text_h + padding * 2)
        self.setFixedSize(bw, bh)
        # 定位
        screen = QApplication.primaryScreen().geometry()
        if tail_side == "bottom":
            bx = int(x - bw // 2)
            by = int(y - bh)
        elif tail_side == "top":
            bx = int(x - bw // 2)
            by = int(y)
        elif tail_side == "left":
            bx = int(x)
            by = int(y - bh // 2)
        else:  # right
            bx = int(x - bw)
            by = int(y - bh // 2)
        # 边界保护
        bx = max(0, min(bx, screen.width() - bw))
        by = max(0, min(by, screen.height() - bh))
        self.move(bx, by)
        self.setWindowOpacity(0.0)
        self.show()
        self.raise_()
        # 淡入动画
        self._fade_in = QPropertyAnimation(self, b"windowOpacity")
        self._fade_in.setDuration(200)
        self._fade_in.setStartValue(0.0)
        self._fade_in.setEndValue(1.0)
        self._fade_in.start()
        # 启动打字机效果，每60ms显示一个字
        self.type_timer.start(60)

    def follow(self, x, y):
        """跟随锚点移动（宠物移动时调用）"""
        if not self.isVisible():
            return
        self._anchor_x = x
        self._anchor_y = y
        bw, bh = self.width(), self.height()
        screen = QApplication.primaryScreen().geometry()
        if self.tail_side == "bottom":
            bx = int(x - bw // 2)
            by = int(y - bh)
        elif self.tail_side == "top":
            bx = int(x - bw // 2)
            by = int(y)
        elif self.tail_side == "left":
            bx = int(x)
            by = int(y - bh // 2)
        else:  # right
            bx = int(x - bw)
            by = int(y - bh // 2)
        bx = max(0, min(bx, screen.width() - bw))
        by = max(0, min(by, screen.height() - bh))
        self.move(bx, by)

    def fade_out_and_hide(self):
        """淡出后隐藏"""
        self._fade_out = QPropertyAnimation(self, b"windowOpacity")
        self._fade_out.setDuration(200)
        self._fade_out.setStartValue(self.windowOpacity())
        self._fade_out.setEndValue(0.0)
        self._fade_out.finished.connect(self.hide)
        self._fade_out.start()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w = self.width()
        h = self.height()
        tail_h = 12
        # 气泡主体区域
        if self.tail_side == "bottom":
            rect = QRect(0, 0, w, h - tail_h)
        elif self.tail_side == "top":
            rect = QRect(0, tail_h, w, h - tail_h)
        elif self.tail_side == "left":
            rect = QRect(tail_h, 0, w - tail_h, h)
        else:
            rect = QRect(0, 0, w - tail_h, h)

        # 画圆角矩形背景（白色半透明）
        path = QPainterPath()
        radius = 12
        path.addRoundedRect(rect, radius, radius)
        # 画小尾巴
        center_x = w // 2
        center_y = h // 2
        if self.tail_side == "bottom":
            path.moveTo(center_x - 8, h - tail_h)
            path.lineTo(center_x, h)
            path.lineTo(center_x + 8, h - tail_h)
        elif self.tail_side == "top":
            path.moveTo(center_x - 8, tail_h)
            path.lineTo(center_x, 0)
            path.lineTo(center_x + 8, tail_h)
        elif self.tail_side == "left":
            path.moveTo(tail_h, center_y - 8)
            path.lineTo(0, center_y)
            path.lineTo(tail_h, center_y + 8)
        else:
            path.moveTo(w - tail_h, center_y - 8)
            path.lineTo(w, center_y)
            path.lineTo(w - tail_h, center_y + 8)
        path.closeSubpath()

        p.fillPath(path, QBrush(QColor(255, 255, 255, 230)))
        p.setPen(QPen(QColor(200, 200, 200, 180), 1))
        p.drawPath(path)

        # 画胡萝卜装饰（左上角）
        car_x = rect.left() + 8
        car_y = rect.top() + 6
        # 胡萝卜身体（橙色三角形）
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(QColor(255, 140, 0)))
        from PySide6.QtGui import QPolygon
        carrot = QPolygon([
            QPoint(car_x, car_y),
            QPoint(car_x + 14, car_y + 2),
            QPoint(car_x + 7, car_y + 16),
        ])
        p.drawPolygon(carrot)
        # 胡萝卜叶子（绿色）
        p.setBrush(QBrush(QColor(34, 139, 34)))
        leaf1 = QPolygon([
            QPoint(car_x + 3, car_y),
            QPoint(car_x + 5, car_y - 6),
            QPoint(car_x + 7, car_y),
        ])
        leaf2 = QPolygon([
            QPoint(car_x + 7, car_y),
            QPoint(car_x + 9, car_y - 5),
            QPoint(car_x + 11, car_y),
        ])
        p.drawPolygon(leaf1)
        p.drawPolygon(leaf2)

        # 画文字
        p.setPen(QColor(60, 60, 60))
        font = QFont("Microsoft YaHei", 10)
        p.setFont(font)
        text_x = rect.left() + 16
        text_y = rect.top() + 12
        # 胡萝卜占了左上角，文字往右挪一点
        text_x = max(text_x, car_x + 24)
        # 使用实际文字高度，避免底部空行
        text_rect = QRect(text_x, text_y, rect.right() - text_x - 4, self._text_h)
        p.drawText(text_rect, Qt.AlignLeft | Qt.AlignTop, "\n".join(self._lines))


# ============ 掉落小人 ============
class MiniCharacter(QWidget):
    """从天上掉落到宠物头顶的小人"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.pixmap = None
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.fall_timer = QTimer(self)
        self.fall_timer.timeout.connect(self._fall_step)
        self.life_timer = QTimer(self)
        self.life_timer.setSingleShot(True)
        self.life_timer.timeout.connect(self._start_fade)
        self.fade_timer = QTimer(self)
        self.fade_timer.timeout.connect(self._fade_step)
        self.jump_timer = QTimer(self)
        self.jump_timer.timeout.connect(self._jump_step)
        self.target_y = 0
        self.current_y = 0
        self.velocity = 0
        self.gravity = 1.2
        self.bounce_count = 0
        self.fade_opacity = 1.0
        self._jump_count = 0
        self._base_x = 0
        self._base_y = 0

    def spawn(self, image_path, target_x, target_y, size):
        """在指定位置上方生成小人并掉落到target_y"""
        self.pixmap = QPixmap(image_path)
        if self.pixmap.isNull():
            self.close()
            return
        scaled = self.pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.label.setPixmap(scaled)
        self.resize(scaled.width(), scaled.height())
        self.label.resize(scaled.width(), scaled.height())
        # 初始位置：目标点正上方，屏幕外
        self.current_y = -self.height() - 50
        self.target_y = target_y
        self.velocity = 0
        self.bounce_count = 0
        self.move(target_x - self.width() // 2, int(self.current_y))
        self.show()
        self.fall_timer.start(16)  # 约60fps

    def _fall_step(self):
        self.velocity += self.gravity
        self.current_y += self.velocity
        if self.current_y >= self.target_y:
            # 落地
            self.current_y = self.target_y
            if self.bounce_count < 2:
                # 弹两下
                self.bounce_count += 1
                self.velocity = -self.velocity * 0.4
            else:
                # 稳定，开始在头顶跳跃玩耍
                self.fall_timer.stop()
                self._base_x = self.x()
                self._base_y = self.target_y
                self._jump_count = 0
                self.jump_timer.start(400)
        self.move(self.x(), int(self.current_y))

    def _jump_step(self):
        """在头顶左右跳跃玩耍"""
        self._jump_count += 1
        if self._jump_count <= 4:
            # 跳4次，左右交替
            offset_x = 15 if self._jump_count % 2 == 0 else -15
            self.move(self._base_x + offset_x, self._base_y - 12)
            QTimer.singleShot(150, lambda: self.move(self._base_x + offset_x, self._base_y))
        else:
            # 跳完回到中间，站6秒后淡出
            self.jump_timer.stop()
            self.move(self._base_x, self._base_y)
            self.life_timer.start(6000)

    def _start_fade(self):
        self.fade_opacity = 1.0
        self.fade_timer.start(30)

    def _fade_step(self):
        self.fade_opacity -= 0.05
        if self.fade_opacity <= 0:
            self.fade_timer.stop()
            self.close()
        else:
            self.setWindowOpacity(self.fade_opacity)

    def update_position(self, target_x, target_y):
        """跟随宠物移动时更新位置"""
        if not self.fall_timer.isActive():
            # 已经落地，跟随移动
            self.target_y = target_y
            self.current_y = target_y
            self.move(target_x - self.width() // 2, int(self.current_y))


# ============ 透明度设置对话框 ============
class RegionSelector(QWidget):
    """全屏半透明区域选择器，用于区域截图"""
    region_selected = Signal(QRect)
    canceled = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setCursor(Qt.CrossCursor)
        self._start_pos = QPoint()
        self._end_pos = QPoint()
        self._selecting = False
        # 全屏覆盖
        screen = QApplication.primaryScreen()
        self.setGeometry(screen.geometry())

    def paintEvent(self, event):
        painter = QPainter(self)
        # 半透明黑色背景
        painter.fillRect(self.rect(), QColor(0, 0, 0, 120))
        if self._selecting:
            rect = QRect(self._start_pos, self._end_pos).normalized()
            # 挖空选区（显示原图）
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
            painter.fillRect(rect, Qt.transparent)
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            # 选区边框
            pen = QPen(QColor(255, 105, 180), 2)
            painter.setPen(pen)
            painter.drawRect(rect)
            # 尺寸提示
            painter.setPen(QColor(255, 255, 255))
            painter.setFont(QFont("Microsoft YaHei", 9))
            painter.drawText(rect.x(), rect.y() - 5, f"{rect.width()} x {rect.height()}")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._start_pos = event.position().toPoint()
            self._end_pos = self._start_pos
            self._selecting = True
            self.update()

    def mouseMoveEvent(self, event):
        if self._selecting:
            self._end_pos = event.position().toPoint()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._selecting:
            self._end_pos = event.position().toPoint()
            rect = QRect(self._start_pos, self._end_pos).normalized()
            self.close()
            if rect.width() > 5 and rect.height() > 5:
                self.region_selected.emit(rect)
            else:
                self.canceled.emit()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
            self.canceled.emit()


class OpacityDialog(QDialog):
    opacity_changed = Signal(int)
    def __init__(self, current=100, parent=None):
        super().__init__(parent)
        self.setWindowTitle("透明度设置")
        self.setFixedSize(280, 100)
        layout = QVBoxLayout()
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(20, 100)
        self.slider.setValue(current)
        self.label = QLabel(f"透明度：{current}%")
        self.slider.valueChanged.connect(lambda v: self.label.setText(f"透明度：{v}%"))
        self.slider.valueChanged.connect(self.opacity_changed.emit)
        layout.addWidget(self.label)
        layout.addWidget(self.slider)
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self.accept)
        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        layout.addLayout(btn_layout)
        self.setLayout(layout)


LINE_CATEGORIES = [
    ("idle", "闲置/日常"),
    ("click", "单击"),
    ("double", "双击"),
    ("typing_long", "打字(长)"),
    ("typing_medium", "打字(中)"),
    ("typing_short", "打字(短)"),
    ("cling", "攀附"),
    ("eat", "吃文件"),
    ("greeting_morning", "问候(早上)"),
    ("greeting_afternoon", "问候(下午)"),
    ("greeting_evening", "问候(傍晚)"),
    ("greeting_night", "问候(深夜)"),
]


class LinesEditorDialog(QDialog):
    """台词库可视化编辑器"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("台词库编辑")
        self.setFixedSize(420, 480)
        # 加载当前台词
        try:
            with open(LINES_PATH, "r", encoding="utf-8") as f:
                self.lines_data = json.load(f)
        except Exception:
            self.lines_data = dict(DEFAULT_LINES)
        # 确保所有key存在
        for key, _ in LINE_CATEGORIES:
            if key not in self.lines_data or not self.lines_data[key]:
                self.lines_data[key] = DEFAULT_LINES.get(key, [])

        layout = QVBoxLayout()
        # 类型选择
        cat_layout = QHBoxLayout()
        cat_layout.addWidget(QLabel("台词类型："))
        self.category_combo = QComboBox()
        for key, name in LINE_CATEGORIES:
            self.category_combo.addItem(name, key)
        self.category_combo.currentIndexChanged.connect(self._on_category_changed)
        cat_layout.addWidget(self.category_combo, 1)
        layout.addLayout(cat_layout)
        # 提示
        hint = QLabel("每行一条台词，留空行将被忽略")
        hint.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(hint)
        # 台词编辑区
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("在此输入台词，每行一条...")
        layout.addWidget(self.text_edit, 1)
        # 统计
        self.count_label = QLabel("共 0 条")
        self.count_label.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(self.count_label)
        # 按钮
        btn_layout = QHBoxLayout()
        reset_btn = QPushButton("恢复默认")
        reset_btn.clicked.connect(self._on_reset)
        btn_layout.addWidget(reset_btn)
        btn_layout.addStretch()
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self._on_save)
        save_btn.setDefault(True)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)
        self.setLayout(layout)
        # 加载第一个类型
        self._current_key = LINE_CATEGORIES[0][0]
        self._load_category(self._current_key)

    def _load_category(self, key):
        lines = self.lines_data.get(key, [])
        self.text_edit.setPlainText("\n".join(lines))
        self.count_label.setText(f"共 {len(lines)} 条")

    def _save_current(self):
        text = self.text_edit.toPlainText()
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        self.lines_data[self._current_key] = lines

    def _on_category_changed(self, index):
        self._save_current()
        self._current_key = self.category_combo.itemData(index)
        self._load_category(self._current_key)

    def _on_reset(self):
        key = self._current_key
        self.lines_data[key] = list(DEFAULT_LINES.get(key, []))
        self._load_category(key)

    def _on_save(self):
        self._save_current()
        try:
            with open(LINES_PATH, "w", encoding="utf-8") as f:
                json.dump(self.lines_data, f, ensure_ascii=False, indent=2)
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "保存失败", str(e))


class SettingsDialog(QDialog):
    """统一设置面板"""
    settings_changed = Signal(dict)  # 发送所有设置变更

    def __init__(self, pet, parent=None):
        super().__init__(parent)
        self.pet = pet
        self.setWindowTitle(f"{pet.pet_name}设置")
        self.setFixedSize(340, 545)

        layout = QVBoxLayout()
        layout.setSpacing(8)

        # === 显示设置 ===
        layout.addWidget(QLabel("🎨 显示设置"))

        # 透明度
        opacity_layout = QHBoxLayout()
        opacity_layout.addWidget(QLabel("透明度："))
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(20, 100)
        self.opacity_slider.setValue(int(pet.manual_opacity * 100))
        self.opacity_label = QLabel(f"{int(pet.manual_opacity * 100)}%")
        self.opacity_slider.valueChanged.connect(lambda v: self.opacity_label.setText(f"{v}%"))
        opacity_layout.addWidget(self.opacity_slider, 1)
        opacity_layout.addWidget(self.opacity_label)
        layout.addLayout(opacity_layout)

        # 缩放
        scale_layout = QHBoxLayout()
        scale_layout.addWidget(QLabel("缩放比例："))
        self.scale_slider = QSlider(Qt.Horizontal)
        self.scale_slider.setRange(10, 100)
        self.scale_slider.setValue(int(pet.target_scale * 100))
        self.scale_label = QLabel(f"{pet.target_scale:.1f}x")
        self.scale_slider.valueChanged.connect(lambda v: self.scale_label.setText(f"{v/100:.1f}x"))
        scale_layout.addWidget(self.scale_slider, 1)
        scale_layout.addWidget(self.scale_label)
        layout.addLayout(scale_layout)

        layout.addSpacing(5)

        # === 功能开关 ===
        layout.addWidget(QLabel("⚙️ 功能开关"))

        self.chk_smart_opacity = QCheckBox("智能透明度（闲置自动变淡）")
        self.chk_smart_opacity.setChecked(pet.smart_opacity)
        layout.addWidget(self.chk_smart_opacity)

        self.chk_mouse_through = QCheckBox("鼠标穿透（透明区不拦截点击）")
        self.chk_mouse_through.setChecked(pet.mouse_through)
        layout.addWidget(self.chk_mouse_through)

        self.chk_bubble = QCheckBox("显示气泡台词")
        self.chk_bubble.setChecked(pet.bubble_enabled)
        layout.addWidget(self.chk_bubble)

        self.chk_typing = QCheckBox("打字实时反应")
        self.chk_typing.setChecked(pet.typing_enabled)
        layout.addWidget(self.chk_typing)

        self.chk_translate = QCheckBox("实时翻译（复制英文自动翻译）")
        self.chk_translate.setChecked(pet.translation_enabled)
        layout.addWidget(self.chk_translate)

        self.chk_autostart = QCheckBox("开机自启动")
        self.chk_autostart.setChecked(pet.auto_start)
        layout.addWidget(self.chk_autostart)

        self.chk_start_hidden = QCheckBox("启动时隐藏窗口（只在托盘显示）")
        self.chk_start_hidden.setChecked(pet.start_hidden)
        self.chk_start_hidden.setToolTip("勾选后程序启动时不弹宠物窗口，只在系统托盘显示图标，点托盘图标再叫它出来")
        layout.addWidget(self.chk_start_hidden)

        self.chk_sound = QCheckBox("互动音效")
        self.chk_sound.setChecked(pet.sound_enabled)
        layout.addWidget(self.chk_sound)

        # 音量
        vol_layout = QHBoxLayout()
        vol_layout.addWidget(QLabel("音量："))
        self.vol_slider = QSlider(Qt.Horizontal)
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setValue(pet.sound_volume)
        self.vol_label = QLabel(f"{pet.sound_volume}%")
        self.vol_slider.valueChanged.connect(lambda v: self.vol_label.setText(f"{v}%"))
        vol_layout.addWidget(self.vol_slider, 1)
        vol_layout.addWidget(self.vol_label)
        layout.addLayout(vol_layout)

        layout.addSpacing(5)

        # === 外观设置 ===
        layout.addWidget(QLabel("👗 外观设置"))

        # 宠物名（台词里的 {name} 会替换成它）
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("宠物名："))
        self.name_edit = QLineEdit(pet.pet_name)
        self.name_edit.setPlaceholderText("未命名（留空则自称「我」）")
        name_layout.addWidget(self.name_edit, 1)
        layout.addLayout(name_layout)

        skin_layout = QHBoxLayout()
        skin_layout.addWidget(QLabel("形象："))
        self.skin_combo = QComboBox()
        self._skins = pet._get_available_skins()
        for skin in self._skins:
            display = skin.replace("pet_", "").replace(".png", "")
            if display == "transparent":
                display = "默认"
            self.skin_combo.addItem(display, skin)
        # 设置当前选中
        idx = self.skin_combo.findData(pet.current_skin)
        if idx >= 0:
            self.skin_combo.setCurrentIndex(idx)
        skin_layout.addWidget(self.skin_combo, 1)
        layout.addLayout(skin_layout)

        layout.addSpacing(5)

        # === 快捷操作 ===
        layout.addWidget(QLabel("🔧 快捷操作"))
        btn_row = QHBoxLayout()
        btn_reset_pos = QPushButton("重置位置")
        btn_reset_pos.clicked.connect(pet._reset_position)
        btn_row.addWidget(btn_reset_pos)
        btn_reset_size = QPushButton("重置大小")
        btn_reset_size.clicked.connect(pet._reset_size)
        btn_row.addWidget(btn_reset_size)
        btn_edit_lines = QPushButton("编辑台词")
        btn_edit_lines.clicked.connect(self._open_lines_file)
        btn_row.addWidget(btn_edit_lines)
        layout.addLayout(btn_row)

        layout.addStretch()

        # === 底部按钮 ===
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self._on_accept)
        btn_layout.addWidget(ok_btn)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def _open_lines_file(self):
        """打开台词库可视化编辑器"""
        dlg = LinesEditorDialog(self)
        if dlg.exec() == QDialog.Accepted:
            if hasattr(self, 'pet') and self.pet:
                self.pet._reload_lines()

    def _on_accept(self):
        # 收集所有设置变更
        changes = {
            "manual_opacity": self.opacity_slider.value() / 100.0,
            "target_scale": self.scale_slider.value() / 100.0,
            "smart_opacity": self.chk_smart_opacity.isChecked(),
            "mouse_through": self.chk_mouse_through.isChecked(),
            "bubble_enabled": self.chk_bubble.isChecked(),
            "typing_enabled": self.chk_typing.isChecked(),
            "translation_enabled": self.chk_translate.isChecked(),
            "auto_start": self.chk_autostart.isChecked(),
            "sound_enabled": self.chk_sound.isChecked(),
            "sound_volume": self.vol_slider.value(),
            "current_skin": self.skin_combo.currentData(),
            "pet_name": self.name_edit.text().strip() or DEFAULT_PET_NAME,
            "start_hidden": self.chk_start_hidden.isChecked(),
        }
        self.settings_changed.emit(changes)
        self.accept()


# ============ 单词查询线程 ============
class _LookupThread(QThread):
    lookup_done = Signal(str, str, str)  # word, phonetic, meaning

    def __init__(self, word, pet):
        super().__init__()
        self.word = word
        self.pet = pet

    def run(self):
        phonetic, meaning = self.pet._query_word(self.word)
        self.lookup_done.emit(self.word, phonetic, meaning)


class _TranslationThread(QThread):
    translation_done = Signal(str, str)  # original, translated

    def __init__(self, text):
        super().__init__()
        self.text = text

    def run(self):
        result = ""
        try:
            import urllib.request
            import urllib.parse
            import json
            # MyMemory 免费翻译API（英译中）
            url = "https://api.mymemory.translated.net/get?q=" + urllib.parse.quote(self.text) + "&langpair=en|zh-CN"
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            status = data.get("responseStatus")
            if status == 200:
                result = data["responseData"]["translatedText"]
            else:
                result = ""
        except Exception as e:
            result = ""
        self.translation_done.emit(self.text, result)


# ============ 桌面宠物主窗口 ============
class DesktopPet(QWidget):
    def __init__(self):
        super().__init__()
        # 窗口设置
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAutoFillBackground(False)
        self.setAcceptDrops(True)  # 接受文件拖放

        # 加载图片（支持多形象切换）
        self.current_skin = "pet_transparent.png"
        self._load_skin(self.current_skin)
        self.current_scale = DEFAULT_SCALE
        self.target_scale = DEFAULT_SCALE

        # 宠物显示label
        self.pet_label = QLabel(self)
        self.pet_label.setPixmap(self.original_pixmap)
        self.pet_label.setAlignment(Qt.AlignCenter)
        self.pet_label.resize(self.base_w, self.base_h)
        self.pet_label.setAttribute(Qt.WA_TranslucentBackground)
        self.pet_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setMouseTracking(True)

        # 状态变量
        self.dragging = False
        self.drag_offset = QPoint()
        self.mouse_press_pos = QPoint()
        self.press_time = 0
        self.is_long_press = False
        self.long_press_timer = QTimer(self)
        self.long_press_timer.setSingleShot(True)
        self.long_press_timer.timeout.connect(self._on_long_press)

        self.last_interaction_time = time.time()
        self.is_sleeping = False
        self.is_walking = False
        self.walk_dx = 0
        self.walk_dy = 0
        self.walk_timer = QTimer(self)
        self.walk_timer.timeout.connect(self._walk_step)

        self.anim_scale = 1.0  # 动画缩放倍率
        self.anim_rotation = 0.0  # 动画旋转角度
        self.anim_offset = QPoint(0, 0)  # 动画偏移
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._anim_step)
        self.anim_timer.start(30)
        self.float_angle = 0.0
        self._hug_angle = 0.0  # 抱树晃动角度
        self._drag_history = []  # 拖拽历史，用于惯性计算
        self._inertia_timer = QTimer(self)
        self._inertia_timer.timeout.connect(self._inertia_step)

        self.mouse_through = False
        self._alpha_image = None
        self.bubble_enabled = True
        self.auto_start = False
        self.manual_opacity = 1.0
        self.smart_opacity = True
        self.current_opacity = 1.0
        self._click_pending = False
        self._just_double_clicked = False
        self._last_click_time = 0
        self._last_line = ""

        # 攀附相关
        self.attached_window = None
        self.attached_side = None
        self._pending_attach = None  # 拖拽时的候选吸附目标
        self.attach_timer = QTimer(self)
        self.attach_timer.timeout.connect(self._sync_attached_window)

        # 气泡
        self.bubble = BubbleWindow()
        self.current_mini = None  # 当前头顶的小人
        self.bubble_timer = QTimer(self)
        self.bubble_timer.setSingleShot(True)
        self.bubble_timer.timeout.connect(self._hide_bubble)

        # 闲置动作定时器
        self.idle_timer = QTimer(self)
        self.idle_timer.setSingleShot(True)
        self.idle_timer.timeout.connect(self._trigger_idle_action)
        self._schedule_idle()

        # 智能透明度检测
        self.opacity_timer = QTimer(self)
        self.opacity_timer.timeout.connect(self._update_opacity)
        self.opacity_timer.start(1000)

        # 宠物名（托盘提示会用到，必须早于 _create_tray；稍后由配置覆盖）
        self.pet_name = DEFAULT_PET_NAME

        # 系统托盘
        self._create_tray()

        # 配置默认值（必须在菜单创建前初始化）
        self.translation_enabled = False
        self.typing_enabled = True
        self.sound_enabled = True
        self.sound_volume = 50
        self.start_hidden = True
        self._last_translated_text = ""
        self._translation_threads = []  # 保存翻译线程引用，防止被GC回收导致崩溃
        self._lookup_threads = []       # 保存查单词线程引用

        # 右键菜单
        self._create_context_menu()

        # 快捷键（Ctrl+Alt+H 隐藏/显示）
        self.hotkey_timer = QTimer(self)
        self.hotkey_timer.timeout.connect(self._check_hotkey)
        self.hotkey_timer.start(100)
        self._last_hotkey_state = False

        # 加载配置
        cfg = self._load_config()
        self.auto_start = cfg.get("auto_start", False)
        self.smart_opacity = cfg.get("smart_opacity", True)
        self.mouse_through = cfg.get("mouse_through", True)
        self.bubble_enabled = cfg.get("bubble_enabled", True)
        self.manual_opacity = cfg.get("manual_opacity", 1.0)
        self.translation_enabled = cfg.get("translation_enabled", False)
        self.typing_enabled = cfg.get("typing_enabled", True)
        self.sound_enabled = cfg.get("sound_enabled", True)
        self.sound_volume = cfg.get("sound_volume", 50)
        self.current_skin = cfg.get("current_skin", "pet_transparent.png")
        self.pet_name = cfg.get("pet_name", DEFAULT_PET_NAME)
        self.start_hidden = cfg.get("start_hidden", True)
        self._last_translated_text = ""
        # 加载选择的形象
        self._load_skin(self.current_skin)
        # 旧版本配置迁移：无版本号的旧配置重置缩放为新默认值
        if cfg.get("config_version", 0) < 2:
            self.target_scale = DEFAULT_SCALE
        else:
            self.target_scale = cfg.get("scale", DEFAULT_SCALE)
        self.current_scale = self.target_scale

        # 初始位置（从配置恢复，或默认右上角）
        screen = QApplication.primaryScreen().geometry()
        init_x = cfg.get("x", screen.width() - self.width() - 100)
        init_y = cfg.get("y", 100)
        # 确保在屏幕内
        init_x = max(0, min(init_x, screen.width() - self.width()))
        init_y = max(0, min(init_y, screen.height() - self.height()))
        self.move(init_x, init_y)

        self._apply_scale()
        self._apply_auto_start()
        # 启动3秒后时间段问候
        QTimer.singleShot(3000, self._greeting_by_time)
        # 启动生词本HTTP服务（供HTML删除同步）
        self._start_vocab_server()
        # 启动全局键盘监听（整句实时反应）
        if self.typing_enabled:
            self._start_keyboard_hook()
        # 初始化实时翻译（如果已开启）
        if self.translation_enabled:
            QTimer.singleShot(1000, self._init_translation_clipboard)
        # 初始化鼠标穿透状态
        self._apply_mouse_through()

    # ----------------------------------------------------------------
    # 缩放
    # ----------------------------------------------------------------
    def _apply_scale(self):
        w = int(self.base_w * self.current_scale)
        h = int(self.base_h * self.current_scale)
        self.setFixedSize(w, h)
        self.pet_label.setFixedSize(w, h)
        scaled = self.original_pixmap.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.pet_label.setPixmap(scaled)
        self._update_click_mask()

    # ----------------------------------------------------------------
    # 鼠标事件
    # ----------------------------------------------------------------
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.mouse_press_pos = event.globalPosition().toPoint()
            self.press_time = time.time()
            self.is_long_press = False
            self.long_press_timer.start(500)
            self.last_interaction_time = time.time()
            self._detach()
        elif event.button() == Qt.RightButton:
            self.context_menu.exec(event.globalPosition().toPoint())

    def mouseMoveEvent(self, event):
        if self.dragging:
            # 检测是否移动了，移动了就不算长按
            moved = (event.globalPosition().toPoint() - self.mouse_press_pos).manhattanLength()
            if moved > 5:
                self.long_press_timer.stop()
                self.is_long_press = False
            if moved >= 10:
                # 正常拖拽
                new_pos = event.globalPosition().toPoint() - self.drag_offset
                self.move(new_pos)
                self._check_attach()
                # 记录移动历史用于惯性
                now = time.time()
                self._drag_history.append((new_pos.x(), new_pos.y(), now))
                if len(self._drag_history) > 5:
                    self._drag_history.pop(0)
            else:
                # 按住小范围移动：抚摸反应
                self._pet_angle = getattr(self, '_pet_angle', 0) + 0.3
                self.anim_scale = 1.03 + math.sin(self._pet_angle) * 0.01
                rel_x = event.position().x() / self.width()
                self.anim_rotation = (rel_x - 0.5) * 6
        else:
            # 不按鼠标，悬停移动：轻微抚摸反应
            self.last_interaction_time = time.time()
            self._pet_angle = getattr(self, '_pet_angle', 0) + 0.2
            self.anim_scale = 1.04 + math.sin(self._pet_angle) * 0.01
            rel_x = event.position().x() / self.width()
            self.anim_rotation = (rel_x - 0.5) * 4

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.long_press_timer.stop()
            self.anim_rotation = 0.0
            self.anim_scale = 1.0
            press_duration = time.time() - self.press_time
            moved = (event.globalPosition().toPoint() - self.mouse_press_pos).manhattanLength()
            # 如果移动距离较大，视为拖拽，检查是否吸附到窗口
            if moved >= 10:
                attached = self._do_attach()
                if not attached:
                    # 计算惯性速度
                    self._start_inertia()
                self._save_config()
            elif not self.is_long_press and press_duration < 0.5 and not self._just_double_clicked:
                # 延迟200ms触发单击，等待判断是否为双击
                self._click_pending = True
                QTimer.singleShot(200, self._do_click_if_pending)
            self.last_interaction_time = time.time()

    def _do_click_if_pending(self):
        if self._click_pending:
            self._click_pending = False
            self._handle_click()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._click_pending = False  # 取消待执行的单击
            self._just_double_clicked = True
            QTimer.singleShot(300, self._reset_double_click_flag)
            self._handle_double_click()

    def _reset_double_click_flag(self):
        self._just_double_clicked = False

    # ----------------------------------------------------------------
    # 文件拖放储存
    # ----------------------------------------------------------------
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        import os
        import shutil
        urls = event.mimeData().urls()
        files = [u.toLocalFile() for u in urls if u.toLocalFile()]
        if not files:
            return
        # 目标文件夹
        target_dir = DATA_DIR
        try:
            os.makedirs(target_dir, exist_ok=True)
        except Exception as e:
            self._show_bubble("呜…文件夹建不了吖(>﹏<)")
            return
        # 显示储存中的台词
        self._play_sound("eat")
        self._show_bubble(random.choice(LINES["eat"]))
        # 复制文件
        saved_count = 0
        for src in files:
            if not os.path.exists(src):
                continue
            fname = os.path.basename(src)
            dst = os.path.join(target_dir, fname)
            # 重名自动加序号
            if os.path.exists(dst):
                base, ext = os.path.splitext(fname)
                i = 1
                while os.path.exists(dst):
                    dst = os.path.join(target_dir, f"{base}_{i}{ext}")
                    i += 1
            try:
                shutil.move(src, dst)
                saved_count += 1
            except Exception as e:
                pass
        self.last_interaction_time = time.time()
        # 延迟显示完成提示
        if saved_count > 0:
            QTimer.singleShot(2500, lambda: self._show_bubble(
                f"吃掉{saved_count}个啦~都存在我的小窝里咯(≧∇≦)ﾉ"))

    def _handle_click(self):
        self.last_interaction_time = time.time()
        # 抖动动画
        self._shake_animation()
        self._play_sound("click")
        if self.bubble_enabled:
            self._show_bubble(self._pick_line(LINES_CLICK))

    def _handle_double_click(self):
        self.last_interaction_time = time.time()
        self._play_sound("double_click")
        # 关掉之前的小人
        if self.current_mini:
            self.current_mini.close()
            self.current_mini = None
        # 随机选一个小人
        mini_img = random.choice(get_mini_images())
        # 小人大约为宠物宽度的0.5倍
        mini_size = max(40, int(self.width() * 0.5))
        # 头顶位置（皇冠顶部）
        head_top_y = self.y() + int(self.height() * 0.05)
        target_x = self.x() + self.width() // 2
        target_y = head_top_y - mini_size  # 小人底部落在头顶
        self.current_mini = MiniCharacter()
        self.current_mini.spawn(mini_img, target_x, target_y, mini_size)
        if self.bubble_enabled:
            self._show_bubble(self._pick_line(LINES_DOUBLE))

    def _on_long_press(self):
        self.is_long_press = True
        # 长按缩小动画
        self._shrink_animation()

    def enterEvent(self, event):
        self.last_interaction_time = time.time()
        # 悬停放大
        self.anim_scale = 1.05

    def leaveEvent(self, event):
        self.anim_scale = 1.0

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if delta > 0:
            self.target_scale = min(MAX_SCALE, self.target_scale + 0.1)
        else:
            self.target_scale = max(MIN_SCALE, self.target_scale - 0.1)
        self.last_interaction_time = time.time()
        self._save_config()

    # ----------------------------------------------------------------
    # 动画
    # ----------------------------------------------------------------
    def _shake_animation(self):
        self._shake_count = 0
        self._shake_max = 6
        def shake_step():
            self._shake_count += 1
            if self._shake_count <= self._shake_max:
                offset = 5 if self._shake_count % 2 == 0 else -5
                self.anim_offset = QPoint(offset, 0)
                QTimer.singleShot(40, shake_step)
            else:
                self.anim_offset = QPoint(0, 0)
        shake_step()

    def _bounce_animation(self):
        # 自然的上下跳动：跳起来→落下，重复2次
        self._bounce_count = 0
        self._bounce_max = 6
        jump_height = 35
        def bounce_step():
            self._bounce_count += 1
            if self._bounce_count <= self._bounce_max:
                c = self._bounce_count
                if c == 1:
                    self.anim_offset = QPoint(0, -jump_height)  # 第一次跳起
                elif c == 2:
                    self.anim_offset = QPoint(0, 0)  # 落下
                elif c == 3:
                    self.anim_offset = QPoint(0, -jump_height)  # 第二次跳起
                elif c == 4:
                    self.anim_offset = QPoint(0, 0)  # 落下
                elif c == 5:
                    self.anim_offset = QPoint(0, -jump_height // 2)  # 第三次小跳
                elif c == 6:
                    self.anim_offset = QPoint(0, 0)  # 落地
                QTimer.singleShot(120, bounce_step)
            else:
                self.anim_offset = QPoint(0, 0)
        bounce_step()

    def _shrink_animation(self):
        self.anim_scale = 0.7
        QTimer.singleShot(300, lambda: setattr(self, 'anim_scale', 1.0))

    def _anim_step(self):
        # 丝滑缩放插值
        if abs(self.current_scale - self.target_scale) > 0.001:
            # 记录缩放前中心点
            center_x = self.x() + self.width() // 2
            center_y = self.y() + self.height() // 2
            # 平滑插值（每帧移动差值的15%）
            self.current_scale += (self.target_scale - self.current_scale) * 0.15
            self._apply_scale()
            # 保持中心点不变
            self.move(center_x - self.width() // 2, center_y - self.height() // 2)
        # 呼吸浮动
        self.float_angle += 0.05
        float_y = math.sin(self.float_angle) * 3
        # 应用动画变换
        scale = self.anim_scale
        # 吸附预览提示：靠近可吸附窗口时轻微放大
        if self._pending_attach:
            scale *= 1.12
        rot = self.anim_rotation
        # 攀附抱树晃动
        if self.attached_window:
            self._hug_angle += 0.08
            rot += math.sin(self._hug_angle) * 2.0
        w = int(self.base_w * self.current_scale * scale)
        h = int(self.base_h * self.current_scale * scale)
        if w > 0 and h > 0:
            scaled = self.original_pixmap.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            # 旋转
            if rot != 0:
                from PySide6.QtGui import QTransform
                t = QTransform()
                t.rotate(rot)
                scaled = scaled.transformed(t, Qt.SmoothTransformation)
            self.pet_label.setPixmap(scaled)
            self.pet_label.resize(scaled.width(), scaled.height())
            # 居中偏移
            ox = (self.width() - scaled.width()) // 2 + self.anim_offset.x()
            oy = (self.height() - scaled.height()) // 2 + int(float_y) + self.anim_offset.y()
            self.pet_label.move(ox, oy)
        # 头顶小人跟随
        if self.current_mini and self.current_mini.isVisible():
            mini_size = self.current_mini.width()
            head_top_y = self.y() + int(self.height() * 0.05)
            target_x = self.x() + self.width() // 2
            target_y = head_top_y - mini_size
            self.current_mini.update_position(target_x, target_y)
        # 气泡跟随宠物移动
        if self.bubble and self.bubble.isVisible():
            rose_x = self.x() + int(self.width() * 0.14)
            rose_y = self.y() + int(self.height() * 0.35)
            self.bubble.follow(rose_x, rose_y)

    # ----------------------------------------------------------------
    # 气泡
    # ----------------------------------------------------------------
    def _pick_line(self, lines):
        """选台词，避免和上一次重复"""
        if len(lines) <= 1:
            return lines[0]
        result = random.choice(lines)
        tries = 0
        while result == self._last_line and tries < 10:
            result = random.choice(lines)
            tries += 1
        self._last_line = result
        return result

    def _show_bubble(self, text):
        # 台词里的 {name} 占位符换成宠物名；未命名时自称「我」
        text = text.replace("{name}", self.pet_name or "我")
        # 气泡显示在宠物左侧，尾巴指向玫瑰花（避开头顶小人掉落区域）
        rose_x = self.x() + int(self.width() * 0.14)
        rose_y = self.y() + int(self.height() * 0.35)
        self.bubble.show_text(text, rose_x, rose_y, "right")
        # 根据文本长度动态计算显示时间：打字时间 + 阅读时间，最长12秒
        text_len = len(text)
        type_time = text_len * 60  # 打字机每字60ms
        read_time = max(3000, text_len * 180)  # 每字180ms阅读，最少3秒
        duration = min(type_time + read_time, 12000)
        self.bubble_timer.start(duration)

    def _hide_bubble(self):
        self.bubble.type_timer.stop()
        self.bubble.fade_out_and_hide()

    def _start_inertia(self):
        """根据拖拽历史计算速度，启动惯性滑动"""
        if len(self._drag_history) < 2:
            self._drag_history = []
            return
        # 用最后两次移动计算速度
        x1, y1, t1 = self._drag_history[-2]
        x2, y2, t2 = self._drag_history[-1]
        dt = max(t2 - t1, 0.001)
        self._inertia_vx = (x2 - x1) / dt * 16  # 每帧位移
        self._inertia_vy = (y2 - y1) / dt * 16
        # 限制最大速度
        max_v = 30
        self._inertia_vx = max(-max_v, min(max_v, self._inertia_vx))
        self._inertia_vy = max(-max_v, min(max_v, self._inertia_vy))
        self._drag_history = []
        if abs(self._inertia_vx) > 1 or abs(self._inertia_vy) > 1:
            self._inertia_timer.start(16)

    def _inertia_step(self):
        """惯性移动一帧，速度衰减"""
        screen = QApplication.primaryScreen().geometry()
        new_x = self.x() + int(self._inertia_vx)
        new_y = self.y() + int(self._inertia_vy)
        # 边界限制
        new_x = max(0, min(new_x, screen.width() - self.width()))
        new_y = max(0, min(new_y, screen.height() - self.height()))
        self.move(new_x, new_y)
        # 速度衰减
        self._inertia_vx *= 0.88
        self._inertia_vy *= 0.88
        if abs(self._inertia_vx) < 0.5 and abs(self._inertia_vy) < 0.5:
            self._inertia_timer.stop()
            self._save_config()

    # ----------------------------------------------------------------
    # 闲置动作
    # ----------------------------------------------------------------
    def _schedule_idle(self):
        delay = random.randint(IDLE_ACTION_MIN, IDLE_ACTION_MAX)
        self.idle_timer.start(delay)

    def _trigger_idle_action(self):
        if self.dragging:
            self._schedule_idle()
            return
        idle_time = (time.time() - self.last_interaction_time) * 1000
        if idle_time > SLEEP_AFTER:
            # 进入休眠
            self.is_sleeping = True
            self._start_sleeping()
        else:
            # 随机动作
            action = random.choice(["walk", "look_around", "idle_bubble", "stretch", "yawn"])
            if action == "walk":
                self._start_walking()
            elif action == "look_around":
                self._look_around()
            elif action == "stretch":
                self._do_stretch()
            elif action == "yawn":
                self._do_yawn()
            elif action == "idle_bubble" and self.bubble_enabled:
                self._show_bubble(self._pick_line(LINES_IDLE))
        self._schedule_idle()

    def _start_walking(self):
        if self.attached_window:
            return
        self.is_walking = True
        self.walk_dx = random.choice([-2, -1, 1, 2])
        self.walk_dy = random.choice([-1, 0, 1])
        self.walk_timer.start(30)
        # 走一段距离后停
        QTimer.singleShot(random.randint(2000, 5000), self._stop_walking)

    def _walk_step(self):
        if not self.is_walking:
            return
        screen = QApplication.primaryScreen().geometry()
        new_x = self.x() + self.walk_dx
        new_y = self.y() + self.walk_dy
        # 碰边界转向
        if new_x < 0 or new_x + self.width() > screen.width():
            self.walk_dx = -self.walk_dx
            new_x = self.x() + self.walk_dx
        if new_y < 0 or new_y + self.height() > screen.height():
            self.walk_dy = -self.walk_dy
            new_y = self.y() + self.walk_dy
        self.move(new_x, new_y)

    def _stop_walking(self):
        self.is_walking = False
        self.walk_timer.stop()

    def _look_around(self):
        # 左右摇头
        self._look_count = 0
        def look_step():
            self._look_count += 1
            if self._look_count <= 4:
                self.anim_rotation = 10 if self._look_count % 2 == 0 else -10
                QTimer.singleShot(300, look_step)
            else:
                self.anim_rotation = 0
        look_step()

    def _do_stretch(self):
        # 伸懒腰：放大再还原，配合轻微旋转
        self.anim_scale = 1.0
        steps = [1.05, 1.1, 1.15, 1.12, 1.08, 1.0]
        rots = [3, 6, 0, -3, -1, 0]
        def stretch_step(i=0):
            if i < len(steps):
                self.anim_scale = steps[i]
                self.anim_rotation = rots[i]
                QTimer.singleShot(120, lambda: stretch_step(i + 1))
            else:
                self.anim_scale = 1.0
                self.anim_rotation = 0
        stretch_step()

    def _do_yawn(self):
        # 打哈欠：缩小再还原，说困的台词
        steps = [0.97, 0.93, 0.9, 0.92, 0.96, 1.0]
        def yawn_step(i=0):
            if i < len(steps):
                self.anim_scale = steps[i]
                QTimer.singleShot(150, lambda: yawn_step(i + 1))
            else:
                self.anim_scale = 1.0
        yawn_step()
        if self.bubble_enabled:
            QTimer.singleShot(300, lambda: self._show_bubble("（打哈欠）好困哦... 但是还想再陪你一会儿...zzz"))

    def _start_sleeping(self):
        # 休眠：透明度降低，缓慢浮动
        pass  # 由_update_opacity处理

    # ----------------------------------------------------------------
    # 透明度
    # ----------------------------------------------------------------
    def _update_opacity(self):
        idle_time = time.time() - self.last_interaction_time
        if self.smart_opacity and idle_time > 10 and not self.dragging:
            # 闲置变淡
            target = 0.4 if idle_time > 30 else 0.7
        else:
            target = self.manual_opacity
        # 平滑过渡
        self.current_opacity += (target - self.current_opacity) * 0.1
        self.setWindowOpacity(self.current_opacity)

    # ----------------------------------------------------------------
    # 鼠标穿透
    # ----------------------------------------------------------------
    def _toggle_mouse_through(self):
        self.mouse_through = not self.mouse_through
        self._apply_mouse_through()
        self._save_config()

    def _apply_mouse_through(self):
        """应用鼠标穿透状态：用setMask设置可点击区域，透明区域自动穿透"""
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        if self.mouse_through:
            self._update_click_mask()
        else:
            self.clearMask()
        self._update_context_menu()

    def _update_click_mask(self):
        """根据当前显示的图片更新可点击区域（攀附/旋转时整个窗口可点击）"""
        if not self.mouse_through:
            self.clearMask()
            return
        # 攀附或旋转状态下不设置mask，整个窗口可点击，避免旋转后区域不匹配
        if self.attached_window or self.anim_rotation != 0:
            self.clearMask()
            return
        try:
            pixmap = self.pet_label.pixmap()
            if pixmap and not pixmap.isNull():
                mask = pixmap.mask()
                if not mask.isEmpty():
                    mask.translate(self.pet_label.x(), self.pet_label.y())
                    self.setMask(mask)
                    return
        except Exception:
            pass
        self.clearMask()

    def _toggle_smart_opacity(self):
        self.smart_opacity = not self.smart_opacity
        self._update_context_menu()
        self._save_config()

    def _toggle_bubble(self):
        self.bubble_enabled = not self.bubble_enabled
        self._update_context_menu()
        self._save_config()

    def _toggle_auto_start(self):
        self.auto_start = not self.auto_start
        self._apply_auto_start()
        self._update_context_menu()
        self._save_config()

    def _apply_auto_start(self):
        """同步开机自启动注册表状态"""
        try:
            import winreg
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
            exe_path = sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(__file__)
            if self.auto_start:
                winreg.SetValueEx(key, "DesktopPet_Hana", 0, winreg.REG_SZ, f'"{exe_path}"')
            else:
                try:
                    winreg.DeleteValue(key, "DesktopPet_Hana")
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
        except:
            pass

    def _greeting_by_time(self):
        """启动时根据时间段说问候语（台词从外部JSON加载）"""
        if not self.bubble_enabled:
            return
        hour = time.localtime().tm_hour
        if 6 <= hour < 11:
            line = random.choice(LINES["greeting_morning"])
        elif 11 <= hour < 14:
            line = random.choice(LINES["greeting_afternoon"])
        elif 14 <= hour < 18:
            line = random.choice(LINES["greeting_afternoon"])
        elif 18 <= hour < 23:
            line = random.choice(LINES["greeting_evening"])
        else:
            line = random.choice(LINES["greeting_night"])
        self._show_bubble(line)

    # ----------------------------------------------------------------
    # 攀附窗口
    # ----------------------------------------------------------------
    def _get_visible_rect(self, hwnd):
        # 获取窗口实际可见矩形（去掉不可见的阴影边框）
        import win32gui
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        # Windows 10/11 普通窗口有不可见阴影边框，内缩后更接近可见边缘
        placement = win32gui.GetWindowPlacement(hwnd)
        if placement[1] != 3:  # 3 = SW_SHOWMAXIMIZED，非最大化才内缩
            left += 7
            right -= 7
            bottom -= 7
        return left, top, right, bottom

    def _check_attach(self):
        # 枚举所有可见窗口，找到宠物附近的可吸附窗口
        self._pending_attach = None
        try:
            import win32gui
        except ImportError:
            return

        candidates = []
        my_hwnd = int(self.winId())
        bubble_hwnd = int(self.bubble.winId()) if self.bubble else 0

        def enum_callback(hwnd, _):
            try:
                if not win32gui.IsWindowVisible(hwnd):
                    return
                if win32gui.IsIconic(hwnd):
                    return  # 跳过最小化
                placement = win32gui.GetWindowPlacement(hwnd)
                if placement[1] == 3:  # 3 = SW_SHOWMAXIMIZED，跳过最大化
                    return
                # 跳过自己和气泡
                if hwnd == my_hwnd or hwnd == bubble_hwnd:
                    return
                left, top, right, bottom = win32gui.GetWindowRect(hwnd)
                w = right - left
                h = bottom - top
                if w < 200 or h < 150:
                    return
                # 跳过桌面和系统窗口
                title = win32gui.GetWindowText(hwnd)
                if title in ("Program Manager", "Windows 输入体验",
                             "Microsoft Text Input Application", "Task Switching",
                             "Windows Shell Experience Host", "Start", "Search",
                             "桌面", "此电脑", "回收站",
                             "NVIDIA GeForce Overlay"):
                    return
                # 跳过没有标题且尺寸接近全屏的（可能是不可见的背景窗口）
                if not title and w > 1000 and h > 700:
                    return
                candidates.append((hwnd, left, top, right, bottom))
            except Exception:
                pass

        win32gui.EnumWindows(enum_callback, None)

        if not candidates:
            return

        px1, py1 = self.x(), self.y()
        px2, py2 = px1 + self.width(), py1 + self.height()
        threshold = 80  # 窗口吸附距离阈值

        best = None
        best_dist = threshold

        for hwnd, left, top, right, bottom in candidates:
            # 四条边距离
            d_left = abs(px2 - left)    # 宠物右边 → 窗口左边
            d_right = abs(px1 - right)  # 宠物左边 → 窗口右边
            d_top = abs(py2 - top)      # 宠物下边 → 窗口上边
            d_bottom = abs(py1 - bottom)  # 宠物上边 → 窗口下边

            # 重叠检测（放宽条件）
            v_overlap = py1 < bottom and py2 > top  # 垂直有重叠（左右吸附）
            h_overlap = px1 < right and px2 > left  # 水平有重叠（上下吸附）

            for side, d, overlap in [("left", d_left, v_overlap), ("right", d_right, v_overlap),
                                     ("top", d_top, h_overlap), ("bottom", d_bottom, h_overlap)]:
                if d < best_dist and overlap:
                    best_dist = d
                    best = (hwnd, side)

        if best:
            self._pending_attach = best
            return

        # 屏幕边缘吸附（工作区，排除任务栏）
        try:
            import win32gui, win32con
            monitor_info = win32gui.GetMonitorInfo(win32gui.MonitorFromWindow(self.winId(), win32con.MONITOR_DEFAULTTONEAREST))
            work_left, work_top, work_right, work_bottom = monitor_info["Work"]
            threshold = 30
            px1, py1 = self.x(), self.y()
            px2, py2 = px1 + self.width(), py1 + self.height()
            # 检测是否靠近屏幕边缘
            if abs(px1 - work_left) < threshold:
                self._pending_attach = ("screen", "left")
            elif abs(px2 - work_right) < threshold:
                self._pending_attach = ("screen", "right")
            elif abs(py1 - work_top) < threshold:
                self._pending_attach = ("screen", "top")
            elif abs(py2 - work_bottom) < threshold:
                self._pending_attach = ("screen", "bottom")
        except Exception:
            pass

    def _do_attach(self):
        # 松开鼠标时执行实际吸附
        if not self._pending_attach:
            return False
        hwnd, side = self._pending_attach
        self._pending_attach = None
        self.attached_window = hwnd
        self.attached_side = side
        self._apply_attach_position()
        if hwnd != "screen":
            self.attach_timer.start(100)
        # 抱树姿势：根据边调整倾斜角度
        if side == "left":
            self.anim_rotation = 12
        elif side == "right":
            self.anim_rotation = -12
        else:
            self.anim_rotation = 0
        # 吸附成功台词
        self._play_sound("cling")
        if self.bubble_enabled:
            self._show_bubble(random.choice(LINES["cling"]))
        return True

    def _apply_attach_position(self):
        # 根据依附的窗口和边，计算宠物位置（探出半个身子）
        if not self.attached_window or not self.attached_side:
            return
        w, h = self.width(), self.height()
        if self.attached_window == "screen":
            # 屏幕边缘吸附
            try:
                import win32gui, win32con
                monitor_info = win32gui.GetMonitorInfo(win32gui.MonitorFromWindow(self.winId(), win32con.MONITOR_DEFAULTTONEAREST))
                left, top, right, bottom = monitor_info["Work"]
            except Exception:
                return
            if self.attached_side == "left":
                self.move(left, (top + bottom) // 2 - h // 2)
            elif self.attached_side == "right":
                self.move(right - w, (top + bottom) // 2 - h // 2)
            elif self.attached_side == "top":
                self.move((left + right) // 2 - w // 2, top)
            elif self.attached_side == "bottom":
                self.move((left + right) // 2 - w // 2, bottom - h)
            return
        try:
            import win32gui
            left, top, right, bottom = win32gui.GetWindowRect(self.attached_window)
        except:
            self._detach()
            return
        if self.attached_side == "left":
            self.move(left, top + (bottom - top) // 2 - h // 2)
        elif self.attached_side == "right":
            self.move(right - w, top + (bottom - top) // 2 - h // 2)
        elif self.attached_side == "top":
            self.move(left + (right - left) // 2 - w // 2, top)
        elif self.attached_side == "bottom":
            self.move(left + (right - left) // 2 - w // 2, bottom - h)

    def _detach(self, say_goodbye=False):
        if say_goodbye and self.bubble_enabled and self.attached_window and self.attached_window != "screen":
            self._show_bubble("诶？窗口不见啦，{name}自己去玩咯～")
        self.attached_window = None
        self.attached_side = None
        self.attach_timer.stop()
        self.anim_rotation = 0.0
        self.anim_offset = QPoint(0, 0)

    def _sync_attached_window(self):
        # 跟随依附的窗口移动
        if not self.attached_window or self.attached_window == "screen":
            return
        try:
            import win32gui
            if not win32gui.IsWindow(self.attached_window):
                self._detach(say_goodbye=True)
                return
            # 检测窗口是否最小化
            if win32gui.IsIconic(self.attached_window):
                if self.isVisible():
                    self.hide()
                return
            else:
                if not self.isVisible():
                    self.show()
            self._apply_attach_position()
        except:
            self._detach(say_goodbye=True)

    # ----------------------------------------------------------------
    # 快捷键检测
    # ----------------------------------------------------------------
    def _check_hotkey(self):
        # 简化版：不实现全局热键，由托盘菜单控制
        pass

    # ----------------------------------------------------------------
    # 配置保存/加载
    # ----------------------------------------------------------------
    def _load_config(self):
        try:
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                return cfg
        except:
            pass
        return {}

    def _save_config(self):
        try:
            cfg = {
                "config_version": 2,
                "x": self.x(),
                "y": self.y(),
                "scale": self.target_scale,
                "manual_opacity": self.manual_opacity,
                "smart_opacity": self.smart_opacity,
                "mouse_through": self.mouse_through,
                "bubble_enabled": self.bubble_enabled,
                "auto_start": self.auto_start,
                "translation_enabled": self.translation_enabled,
                "typing_enabled": self.typing_enabled,
                "sound_enabled": self.sound_enabled,
                "sound_volume": self.sound_volume,
                "current_skin": self.current_skin,
                "pet_name": self.pet_name,
                "start_hidden": self.start_hidden,
            }
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
        except:
            pass

    # ----------------------------------------------------------------
    # 右键菜单
    # ----------------------------------------------------------------
    def _create_context_menu(self):
        self.context_menu = QMenu(self)
        self._update_context_menu()

    def _update_context_menu(self):
        self.context_menu.clear()
        act_settings = self.context_menu.addAction("⚙️ 设置...")
        act_settings.triggered.connect(self._show_settings_dialog)
        self.context_menu.addSeparator()
        act_through = self.context_menu.addAction("鼠标穿透")
        act_through.setCheckable(True)
        act_through.setChecked(self.mouse_through)
        act_through.triggered.connect(self._toggle_mouse_through)
        act_bubble = self.context_menu.addAction("显示气泡")
        act_bubble.setCheckable(True)
        act_bubble.setChecked(self.bubble_enabled)
        act_bubble.triggered.connect(self._toggle_bubble)
        act_autostart = self.context_menu.addAction("开机自启动")
        act_autostart.setCheckable(True)
        act_autostart.setChecked(self.auto_start)
        act_autostart.triggered.connect(self._toggle_auto_start)
        self.context_menu.addSeparator()
        act_lookup = self.context_menu.addAction("查单词...")
        act_lookup.triggered.connect(self._lookup_word)
        act_export = self.context_menu.addAction("导出生词本")
        act_export.triggered.connect(self._export_vocab)
        act_translate = self.context_menu.addAction("📖 实时翻译")
        act_translate.setCheckable(True)
        act_translate.setChecked(self.translation_enabled)
        act_translate.triggered.connect(self._toggle_translation)
        self.context_menu.addSeparator()
        act_screenshot = self.context_menu.addAction("📷 全屏截图")
        act_screenshot.triggered.connect(self._take_screenshot)
        act_region = self.context_menu.addAction("✂️ 区域截图")
        act_region.triggered.connect(self._take_region_screenshot)
        self.context_menu.addSeparator()
        act_hide = self.context_menu.addAction("隐藏到托盘")
        act_hide.triggered.connect(self.hide)
        act_exit = self.context_menu.addAction("退出")
        act_exit.triggered.connect(self._quit)

    def _get_available_skins(self):
        """扫描可用形象：内置pet_transparent.png + exe同目录下的pet_*.png"""
        skins = ["pet_transparent.png"]
        try:
            exe_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
            for f in os.listdir(exe_dir):
                if f.lower().startswith("pet_") and f.lower().endswith(".png") and f != "pet_transparent.png":
                    skins.append(f)
        except Exception:
            pass
        return skins

    def _load_skin(self, skin_name):
        """加载指定形象文件"""
        try:
            # 先尝试从exe同目录加载（用户自定义形象）
            exe_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
            custom_path = os.path.join(exe_dir, skin_name)
            if os.path.exists(custom_path):
                pixmap = QPixmap(custom_path)
            else:
                # 回退到内置资源
                pixmap = QPixmap(get_resource_path(skin_name))
            if pixmap.isNull():
                pixmap = QPixmap(PET_IMAGE)
            self.original_pixmap = pixmap
            self._alpha_image = pixmap.toImage()  # 用于鼠标穿透的像素透明度判断
            self.base_w = pixmap.width()
            self.base_h = pixmap.height()
            self.resize(self.base_w, self.base_h)
            if hasattr(self, 'pet_label') and self.pet_label:
                self.pet_label.setPixmap(pixmap)
                self.pet_label.resize(self.base_w, self.base_h)
            self.current_skin = skin_name
        except Exception:
            pass

    def _switch_skin(self, skin_name):
        """切换形象"""
        if skin_name == self.current_skin:
            return
        self._load_skin(skin_name)
        self._apply_scale()
        self._save_config()
        if self.bubble_enabled:
            self._show_bubble("换新衣服啦～好看吗💗")

    def _reset_position(self):
        self._detach()  # 先脱离攀附，避免被attach_timer拉回
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - self.width() - 100, 100)
        self._save_config()

    def _reset_size(self):
        self.target_scale = DEFAULT_SCALE
        self._save_config()

    def _reload_lines(self):
        """重新加载台词文件到全局变量"""
        global LINES, LINES_IDLE, LINES_CLICK, LINES_DOUBLE
        new_lines = _load_lines_from_file()
        LINES.update(new_lines)
        LINES_IDLE = LINES["idle"]
        LINES_CLICK = LINES["click"]
        LINES_DOUBLE = LINES["double"]

    # ----------------------------------------------------------------
    # 查单词 & 生词本
    # ----------------------------------------------------------------
    def _vocab_path(self):
        return VOCAB_PATH

    def _start_vocab_server(self):
        try:
            pet_ref = self
            class _Handler(BaseHTTPRequestHandler):
                def do_GET(self):
                    parsed = urllib.parse.urlparse(self.path)
                    self.send_response(200)
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Content-Type', 'text/plain; charset=utf-8')
                    self.end_headers()
                    if parsed.path == '/delete':
                        params = urllib.parse.parse_qs(parsed.query)
                        word = params.get('word', [''])[0].lower()
                        if word:
                            vocab = pet_ref._load_vocab()
                            if word in vocab:
                                del vocab[word]
                                pet_ref._save_vocab(vocab)
                        self.wfile.write(b'OK')
                    elif parsed.path == '/list':
                        vocab = pet_ref._load_vocab()
                        self.wfile.write(json.dumps(vocab, ensure_ascii=False).encode('utf-8'))
                    else:
                        self.wfile.write(b'unknown')
                def log_message(self, fmt, *args):
                    pass
            self._vocab_http = HTTPServer(('127.0.0.1', 0), _Handler)
            self._vocab_port = self._vocab_http.server_address[1]
            t = threading.Thread(target=self._vocab_http.serve_forever, daemon=True)
            t.start()
        except Exception:
            self._vocab_port = 0

    def _load_vocab(self):
        try:
            with open(self._vocab_path(), "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}

    def _save_vocab(self, vocab):
        try:
            os.makedirs(os.path.dirname(self._vocab_path()), exist_ok=True)
            with open(self._vocab_path(), "w", encoding="utf-8") as f:
                json.dump(vocab, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            self._show_bubble(f"生词本保存失败：{str(e)[:20]}")
            return False

    def _add_to_vocab(self, word, meaning):
        vocab = self._load_vocab()
        vocab[word.lower()] = {"meaning": meaning, "time": time.strftime("%Y-%m-%d %H:%M")}
        self._save_vocab(vocab)

    # ----------------------------------------------------------------
    # 全局键盘监听（整句实时反应，不储存）
    # ----------------------------------------------------------------
    def _toggle_typing(self):
        self.typing_enabled = not self.typing_enabled
        if self.typing_enabled:
            self._start_keyboard_hook()
            self._show_bubble("打字反应已开启～打字时{name}会陪你哦⌨️")
        else:
            self._stop_keyboard_hook()
            self._show_bubble("打字反应已关闭")
        self._update_context_menu()
        self._save_config()

    def _start_keyboard_hook(self):
        self._key_count = 0
        self._last_key_time = 0
        self._last_react_time = 0
        self._keyboard_hook = None
        try:
            # 使用 WinDLL + use_last_error 以便获取准确的错误码
            self._user32 = ctypes.WinDLL('user32', use_last_error=True)
            self._kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

            class _KBDLLHOOKSTRUCT(ctypes.Structure):
                _fields_ = [
                    ("vkCode", wintypes.DWORD),
                    ("scanCode", wintypes.DWORD),
                    ("flags", wintypes.DWORD),
                    ("time", wintypes.DWORD),
                    ("dwExtraInfo", ctypes.POINTER(wintypes.ULONG)),
                ]
            self._KBDLLHOOKSTRUCT = _KBDLLHOOKSTRUCT

            # 低级键盘钩子回调类型：nCode(int), wParam(WPARAM), lParam(LPARAM)
            self._hook_callback = ctypes.CFUNCTYPE(
                ctypes.c_int, ctypes.c_int, ctypes.c_size_t, ctypes.POINTER(_KBDLLHOOKSTRUCT)
            )(self._keyboard_proc)

            # 获取当前模块句柄
            h_mod = self._kernel32.GetModuleHandleW(None)
            self._log_typing(f"模块句柄: {h_mod}")

            # 安装低级全局键盘钩子 WH_KEYBOARD_LL=13
            # 注意：低级钩子回调在安装线程中执行，hMod传NULL也可工作
            # （某些环境下传GetModuleHandleW会报126错误，因为ctypes回调不在模块代码段）
            self._keyboard_hook = self._user32.SetWindowsHookExW(
                13, self._hook_callback, None, 0
            )
            self._log_typing(f"键盘钩子安装(传NULL): handle={self._keyboard_hook}")

            if not self._keyboard_hook:
                err = ctypes.get_last_error()
                self._log_typing(f"传NULL失败，错误码: {err}，重试传模块句柄")
                # 重试：传模块句柄
                self._keyboard_hook = self._user32.SetWindowsHookExW(
                    13, self._hook_callback, h_mod, 0
                )
                self._log_typing(f"键盘钩子安装(传模块句柄): handle={self._keyboard_hook}")

            if not self._keyboard_hook:
                err = ctypes.get_last_error()
                self._log_typing(f"钩子安装失败，错误码: {err}")
                return

            # 定时检测打字停顿
            self._typing_timer = QTimer(self)
            self._typing_timer.timeout.connect(self._check_typing_pause)
            self._typing_timer.start(500)
            self._log_typing("键盘钩子启动成功，定时器已开启")
        except Exception as e:
            self._log_typing(f"键盘钩子异常: {e}")
            import traceback
            self._log_typing(traceback.format_exc())

    def _log_typing(self, msg):
        try:
            log_path = os.path.join(DATA_DIR, "typing_log.txt")
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        except Exception:
            pass

    def _stop_keyboard_hook(self):
        try:
            if hasattr(self, '_typing_timer'):
                self._typing_timer.stop()
            if self._keyboard_hook:
                self._user32.UnhookWindowsHookEx(self._keyboard_hook)
                self._keyboard_hook = None
        except Exception:
            pass

    def _keyboard_proc(self, nCode, wParam, lParam):
        try:
            if nCode >= 0 and wParam in (0x0100, 0x0104):  # WM_KEYDOWN / WM_SYSKEYDOWN
                vk = lParam.contents.vkCode
                # 忽略纯功能键
                if vk not in (0x1B, 0x09, 0x10, 0x11, 0x12, 0x14, 0x2C, 0x2D, 0x2E,
                              0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28,
                              0x70, 0x71, 0x72, 0x73, 0x74, 0x75, 0x76, 0x77,
                              0x78, 0x79, 0x7A, 0x7B, 0x7C, 0x7D, 0x7E, 0x7F):
                    self._key_count += 1
                    self._last_key_time = time.time()
                    if self._key_count <= 3:
                        self._log_typing(f"按键: vk={vk}, count={self._key_count}")
                if vk == 0x0D:  # 回车
                    QTimer.singleShot(0, self._try_react_by_typing)
        except Exception as e:
            self._log_typing(f"按键回调异常: {e}")
        return self._user32.CallNextHookEx(self._keyboard_hook, nCode, wParam, lParam)

    def _check_typing_pause(self):
        """检测打字停顿：连续打字后停顿1秒以上则触发反应"""
        try:
            now = time.time()
            if self._key_count >= 5 and (now - self._last_key_time) >= 1.0:
                self._try_react_by_typing()
        except Exception:
            pass

    def _try_react_by_typing(self):
        now = time.time()
        count = self._key_count
        self._key_count = 0
        if count < 3:
            self._log_typing(f"触发检查: count={count} < 3，跳过")
            return
        if now - self._last_react_time < 6:
            self._log_typing(f"触发检查: count={count}，距上次反应{now - self._last_react_time:.1f}s < 6s，跳过")
            return
        self._last_react_time = now
        line = self._get_typing_reaction(count)
        if line:
            self._log_typing(f"触发反应: count={count}, line={line[:30]}")
            self._show_bubble(line)

    def _get_typing_reaction(self, count):
        # 根据打字量给不同反应（台词从外部JSON加载）
        if count >= 30:
            return random.choice(LINES["typing_long"])
        if count >= 15:
            return random.choice(LINES["typing_medium"])
        return random.choice(LINES["typing_short"])

    # ----------------------------------------------------------------
    # 实时翻译（剪贴板监听，复制英文自动翻译）
    # ----------------------------------------------------------------
    def _toggle_translation(self):
        self.translation_enabled = not self.translation_enabled
        self._save_config()
        self._apply_translation_state()

    def _apply_translation_state(self):
        """根据当前 translation_enabled 状态连接/断开剪贴板监听"""
        clipboard = QApplication.clipboard()
        if self.translation_enabled:
            try:
                clipboard.dataChanged.disconnect(self._on_clipboard_changed)
            except Exception:
                pass
            clipboard.dataChanged.connect(self._on_clipboard_changed, Qt.UniqueConnection)
            self._last_translated_text = clipboard.text()
            self._show_bubble("实时翻译已开启～复制英文就会翻译哦📖")
        else:
            try:
                clipboard.dataChanged.disconnect(self._on_clipboard_changed)
            except Exception:
                pass
            self._show_bubble("实时翻译已关闭")

    def _init_translation_clipboard(self):
        if self.translation_enabled:
            clipboard = QApplication.clipboard()
            try:
                clipboard.dataChanged.disconnect(self._on_clipboard_changed)
            except Exception:
                pass
            clipboard.dataChanged.connect(self._on_clipboard_changed, Qt.UniqueConnection)
            self._last_translated_text = clipboard.text()

    def _on_clipboard_changed(self):
        if not self.translation_enabled:
            return
        try:
            clipboard = QApplication.clipboard()
            text = clipboard.text().strip()
            self._log_translation(f"剪贴板变化: text={text[:50] if text else 'EMPTY'}, len={len(text) if text else 0}")
            if not text or len(text) > 500:
                self._log_translation("跳过: 空或过长")
                return
            if text == self._last_translated_text:
                self._log_translation("跳过: 与上次相同")
                return
            # 检测是否包含英文（至少有3个连续英文字母）
            import re
            if not re.search(r'[a-zA-Z]{3,}', text):
                self._log_translation("跳过: 不包含英文")
                return
            self._last_translated_text = text
            # 后台翻译（用列表保存引用，防止线程被GC回收导致崩溃）
            thread = _TranslationThread(text)
            thread.translation_done.connect(self._on_translation_done, Qt.QueuedConnection)
            self._translation_threads.append(thread)
            self._log_translation(f"启动翻译线程: {text[:30]}")
            thread.start()
        except Exception as e:
            self._log_translation(f"剪贴板处理异常: {e}")

    def _on_translation_done(self, original, translated):
        self._log_translation(f"翻译完成: original={original[:30]}, translated={translated[:30] if translated else 'EMPTY'}")
        if translated and translated != original:
            # 气泡显示原文和译文
            display = f"📖 {original}\n→ {translated}"
            self._show_bubble(display)
        elif not translated:
            self._show_bubble("翻译失败了，稍后再试试吧～")
        # 清理线程
        self._cleanup_translation_threads()

    def _log_translation(self, msg):
        try:
            log_path = os.path.join(DATA_DIR, "translation_log.txt")
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        except Exception:
            pass

    def _cleanup_translation_threads(self):
        """清理已完成的翻译线程"""
        try:
            remaining = []
            for t in self._translation_threads:
                if t.isFinished():
                    t.deleteLater()
                else:
                    remaining.append(t)
            self._translation_threads = remaining
        except Exception as e:
            self._log_translation(f"清理线程异常: {e}")

    def _query_word(self, word):
        """调用有道词典API查询单词，返回(音标, 释义)元组"""
        import urllib.request
        import urllib.parse
        url = "https://dict.youdao.com/jsonapi?q=" + urllib.parse.quote(word) + "&doctype=json"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            # 解析音标
            phonetic = ""
            word_data = data.get("ec", {}).get("word", [])
            if word_data:
                w = word_data[0]
                uk = w.get("ukphone", "")
                us = w.get("usphone", "")
                if uk and us:
                    phonetic = f"英 /{uk}/ 美 /{us}/"
                elif uk:
                    phonetic = f"英 /{uk}/"
                elif us:
                    phonetic = f"美 /{us}/"
            # 解析释义
            meanings = []
            trs = word_data[0].get("trs", []) if word_data else []
            for tr in trs:
                try:
                    m = tr.get("tr", [{}])[0].get("l", {}).get("i", [{}])[0]
                    if m:
                        meanings.append(m)
                except:
                    pass
            if not meanings:
                # 尝试web翻译
                web_trans = data.get("web_trans", {}).get("web-translation", [])
                if web_trans:
                    for t in web_trans[0].get("trans", []):
                        meanings.append(t.get("value", ""))
            return phonetic, "\n".join(meanings[:5]) if meanings else "未找到释义"
        except Exception as e:
            return "", f"查询失败：{str(e)[:30]}"

    def _lookup_word(self):
        # 用独立对话框，避免受宠物窗口鼠标穿透影响
        dlg = QInputDialog()
        dlg.setWindowFlags(dlg.windowFlags() | Qt.WindowStaysOnTopHint)
        dlg.setWindowTitle("查单词")
        dlg.setLabelText("输入要查询的单词：")
        dlg.setTextValue("")
        if dlg.exec() != QDialog.Accepted:
            return
        word = dlg.textValue().strip()
        if not word:
            return
        self._show_bubble(f"正在查询「{word}」...")
        # 用线程查询避免卡顿（用列表保存引用，防止被GC回收）
        thread = _LookupThread(word, self)
        thread.lookup_done.connect(self._on_lookup_done, Qt.QueuedConnection)
        self._lookup_threads.append(thread)
        thread.start()

    def _on_lookup_done(self, word, phonetic, meaning):
        text = f"{word}\n{meaning}"
        self._show_bubble(text)
        if meaning and "未找到释义" not in meaning and "查询失败" not in meaning:
            self._add_to_vocab(word, meaning)
        # 清理已完成的查单词线程
        try:
            remaining = []
            for t in self._lookup_threads:
                if t.isFinished():
                    t.deleteLater()
                else:
                    remaining.append(t)
            self._lookup_threads = remaining
        except Exception:
            pass

    def _show_vocab_book(self):
        vocab = self._load_vocab()
        if not vocab:
            self._show_bubble("生词本还是空的哦～快去查单词吧！")
            return
        # 按时间倒序
        items = sorted(vocab.items(), key=lambda x: x[1].get("time", ""), reverse=True)
        lines = [f"📖 生词本（共{len(items)}词）"]
        for w, info in items[:20]:
            m = info.get("meaning", "")[:40]
            lines.append(f"{w} — {m}")
        if len(items) > 20:
            lines.append(f"...还有{len(items)-20}个词")
        self._show_bubble("\n".join(lines))

    def _export_vocab(self):
        vocab = self._load_vocab()
        if not vocab:
            self._show_bubble("生词本还是空的哦～")
            return
        items = sorted(vocab.items(), key=lambda x: x[1].get("time", ""), reverse=True)
        html_path = os.path.join(os.path.dirname(VOCAB_PATH), "生词本.html")
        # 把数据嵌入JSON供JS使用
        vocab_json = json.dumps(vocab, ensure_ascii=False)
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>生词本</title>
<style>
body {{ font-family: "Microsoft YaHei", sans-serif; background: #fff5f8; margin: 0; padding: 30px; }}
h1 {{ color: #e91e63; text-align: center; }}
.container {{ max-width: 850px; margin: 0 auto; background: white; border-radius: 12px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
.count {{ text-align: center; color: #888; margin-bottom: 8px; }}
.filepath {{ text-align: center; color: #999; font-size: 12px; margin-bottom: 15px; word-break: break-all; }}
.toolbar {{ text-align: center; margin-bottom: 15px; }}
.btn {{ background: #e91e63; color: white; border: none; padding: 8px 20px; border-radius: 20px; cursor: pointer; font-size: 14px; margin: 0 5px; }}
.btn:hover {{ background: #c2185b; }}
.btn-gray {{ background: #999; }}
.btn-gray:hover {{ background: #777; }}
table {{ width: 100%; border-collapse: collapse; }}
th, td {{ padding: 10px 12px; text-align: left; border-bottom: 1px solid #f0f0f0; }}
th {{ background: #fce4ec; color: #c2185b; }}
.word {{ font-weight: bold; color: #333; font-size: 16px; }}
.time {{ color: #aaa; font-size: 12px; white-space: nowrap; }}
tr:hover {{ background: #fafafa; }}
.del-btn {{ background: #ffcdd2; color: #c62828; border: none; padding: 4px 10px; border-radius: 12px; cursor: pointer; font-size: 12px; }}
.del-btn:hover {{ background: #ef9a9a; }}
.tip {{ background: #fff3e0; padding: 10px 15px; border-radius: 8px; color: #e65100; font-size: 13px; margin-top: 15px; display: none; }}
.toast {{ position: fixed; top: 20px; left: 50%; transform: translateX(-50%); background: #4caf50; color: white; padding: 10px 25px; border-radius: 20px; display: none; z-index: 999; }}
</style>
</head>
<body>
<div class="toast" id="toast"></div>
<div class="container">
<h1>🌸 生词本</h1>
<p class="count" id="count">共 {len(items)} 个单词</p>
<p class="filepath">📁 生词本文件：{VOCAB_PATH}</p>
<div class="toolbar">
<button class="btn btn-gray" onclick="refresh()">↺ 刷新</button>
<button class="btn btn-gray" onclick="toggleAll()">☑ 全选</button>
<button class="btn" onclick="batchDelete()">🗑 批量删除</button>
</div>
<table>
<thead><tr><th><input type="checkbox" id="checkAll" onclick="toggleAll()"></th><th>#</th><th>单词</th><th>释义</th><th>添加时间</th><th>操作</th></tr></thead>
<tbody id="tbody">
</tbody>
</table>
</div>
<script>
let vocab = {vocab_json};

function render() {{
    let tbody = document.getElementById('tbody');
    tbody.innerHTML = '';
    let items = Object.entries(vocab).sort((a,b) => (b[1].time||'').localeCompare(a[1].time||''));
    items.forEach((item, i) => {{
        let w = item[0], info = item[1];
        let m = (info.meaning || '').replace(/\\n/g, '<br>');
        let t = info.time || '';
        let tr = document.createElement('tr');
        tr.innerHTML = `<td><input type="checkbox" class="word-check" data-word="${{w}}"></td><td>${{i+1}}</td><td class="word">${{w}}</td><td>${{m}}</td><td class="time">${{t}}</td><td><button class="del-btn" onclick="delWord('${{w.replace(/'/g,"\\\\'")}}')">删除</button></td>`;
        tbody.appendChild(tr);
    }});
    document.getElementById('count').textContent = '共 ' + items.length + ' 个单词';
}}

function delWord(w) {{
    if (!confirm('确定删除「' + w + '」吗？')) return;
    fetch('http://127.0.0.1:{self._vocab_port}/delete?word=' + encodeURIComponent(w))
        .then(() => {{
            delete vocab[w];
            render();
            showToast('已删除，下次导出自动生效 ✅');
        }})
        .catch(() => {{
            showToast('删除失败，请确保桌宠正在运行');
        }});
}}

function toggleAll() {{
    let checked = document.getElementById('checkAll').checked;
    document.querySelectorAll('.word-check').forEach(cb => cb.checked = checked);
}}

function batchDelete() {{
    let selected = Array.from(document.querySelectorAll('.word-check:checked')).map(cb => cb.dataset.word);
    if (selected.length === 0) {{ showToast('请先勾选要删除的单词'); return; }}
    if (!confirm('确定删除选中的 ' + selected.length + ' 个单词吗？')) return;
    let done = 0;
    selected.forEach(w => {{
        fetch('http://127.0.0.1:{self._vocab_port}/delete?word=' + encodeURIComponent(w))
            .then(() => {{
                delete vocab[w];
                done++;
                if (done === selected.length) {{
                    render();
                    document.getElementById('checkAll').checked = false;
                    showToast('已删除 ' + done + ' 个单词 ✅');
                }}
            }})
            .catch(() => showToast('删除失败，请确保桌宠正在运行'));
    }});
}}

function refresh() {{
    fetch('http://127.0.0.1:{self._vocab_port}/list')
        .then(r => r.json())
        .then(data => {{
            vocab = data;
            render();
            showToast('已刷新');
        }})
        .catch(() => showToast('刷新失败，请确保桌宠正在运行'));
}}

function showToast(msg) {{
    let t = document.getElementById('toast');
    t.textContent = msg;
    t.style.display = 'block';
    setTimeout(() => t.style.display = 'none', 2000);
}}

render();
</script>
</body>
</html>"""
        try:
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html)
            os.startfile(html_path)
            self._show_bubble(f"生词本已导出，共{len(items)}个词～")
        except Exception as e:
            self._show_bubble(f"导出失败：{str(e)[:20]}")

    def _take_screenshot(self):
        """全屏截图"""
        try:
            screen = QApplication.primaryScreen()
            pixmap = screen.grabWindow(0)
            self._handle_screenshot_result(pixmap)
        except Exception as e:
            self._show_bubble(f"截屏失败：{str(e)[:20]}")

    def _take_region_screenshot(self):
        """区域截图"""
        try:
            self.hide()  # 隐藏宠物避免被截到
            QTimer.singleShot(200, self._show_region_selector)
        except Exception as e:
            self.show()
            self._show_bubble(f"截屏失败：{str(e)[:20]}")

    def _show_region_selector(self):
        self._region_selector = RegionSelector()
        self._region_selector.region_selected.connect(self._on_region_selected)
        self._region_selector.canceled.connect(self._on_region_canceled)
        self._region_selector.show()

    def _on_region_selected(self, rect):
        try:
            screen = QApplication.primaryScreen()
            # 直接截取指定区域，避免高DPI下全屏裁剪坐标偏移
            pixmap = screen.grabWindow(0, rect.x(), rect.y(), rect.width(), rect.height())
            self.show()
            self._handle_screenshot_result(pixmap)
        except Exception as e:
            self.show()
            self._show_bubble(f"截屏失败：{str(e)[:20]}")

    def _on_region_canceled(self):
        self.show()

    def _handle_screenshot_result(self, pixmap):
        """截图后弹出选择菜单：保存/复制/都要"""
        menu = QMenu()
        act_save = menu.addAction("💾 仅保存")
        act_copy = menu.addAction("📋 仅复制")
        act_both = menu.addAction("💾📋 保存并复制")
        action = menu.exec(QCursor.pos())
        save_dir = os.path.join(DATA_DIR, "screenshots")
        saved = False
        copied = False
        if action in (act_save, act_both):
            os.makedirs(save_dir, exist_ok=True)
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filepath = os.path.join(save_dir, f"截图_{timestamp}.png")
            pixmap.save(filepath, "PNG")
            saved = True
        if action in (act_copy, act_both):
            QApplication.clipboard().setPixmap(pixmap)
            copied = True
        self._shake_animation()
        if saved and copied:
            self._show_bubble("咔嚓～已保存并复制到剪贴板📷")
        elif saved:
            self._show_bubble("咔嚓～截图已保存📷")
        elif copied:
            self._show_bubble("咔嚓～已复制到剪贴板📋")

    def _play_sound(self, sound_type):
        """播放音效（用winsound.Beep生成简单音效，独立线程避免阻塞）"""
        if not self.sound_enabled:
            return
        # 音效定义：频率(Hz)和时长(ms)的序列
        sounds = {
            "click": [(880, 70)],
            "double_click": [(880, 60), (1320, 80)],
            "eat": [(660, 70), (440, 100)],
            "cling": [(1040, 50), (1320, 50), (1560, 70)],
        }
        sequence = sounds.get(sound_type)
        if not sequence:
            return
        def _play():
            try:
                import winsound
                for freq, dur in sequence:
                    winsound.Beep(freq, dur)
            except Exception:
                pass
        threading.Thread(target=_play, daemon=True).start()

    def _show_opacity_dialog(self):
        dlg = OpacityDialog(int(self.manual_opacity * 100), self)
        dlg.opacity_changed.connect(self._on_opacity_changed)
        dlg.exec()

    def _show_settings_dialog(self):
        dlg = SettingsDialog(self, self)
        dlg.settings_changed.connect(self._apply_settings)
        dlg.exec()

    def _apply_settings(self, changes):
        """应用设置面板的所有变更"""
        # 透明度
        if "manual_opacity" in changes:
            self.manual_opacity = changes["manual_opacity"]
            self.current_opacity = self.manual_opacity
            self.setWindowOpacity(self.manual_opacity)
        # 缩放
        if "target_scale" in changes:
            self.target_scale = changes["target_scale"]
        # 智能透明度
        if "smart_opacity" in changes:
            self.smart_opacity = changes["smart_opacity"]
        # 鼠标穿透
        if "mouse_through" in changes and changes["mouse_through"] != self.mouse_through:
            self.mouse_through = changes["mouse_through"]
            self._apply_mouse_through()
        # 气泡
        if "bubble_enabled" in changes:
            self.bubble_enabled = changes["bubble_enabled"]
        # 打字反应
        if "typing_enabled" in changes and changes["typing_enabled"] != self.typing_enabled:
            self.typing_enabled = changes["typing_enabled"]
            if self.typing_enabled:
                self._start_keyboard_hook()
            else:
                self._stop_keyboard_hook()
        # 翻译
        if "translation_enabled" in changes and changes["translation_enabled"] != self.translation_enabled:
            self.translation_enabled = changes["translation_enabled"]
            self._apply_translation_state()
        # 开机自启
        if "auto_start" in changes and changes["auto_start"] != self.auto_start:
            self.auto_start = changes["auto_start"]
            self._apply_auto_start()
        # 音效
        if "sound_enabled" in changes:
            self.sound_enabled = changes["sound_enabled"]
        if "sound_volume" in changes:
            self.sound_volume = changes["sound_volume"]
        # 启动时是否只待在托盘
        if "start_hidden" in changes:
            self.start_hidden = changes["start_hidden"]
        # 形象切换
        if "current_skin" in changes and changes["current_skin"] != self.current_skin:
            self._switch_skin(changes["current_skin"])
        # 宠物名（台词里的 {name} 占位符运行时替换）
        if "pet_name" in changes and changes["pet_name"] != self.pet_name:
            self.pet_name = changes["pet_name"]
            self.tray.setToolTip(f"桌面宠物 - {self.pet_name}")
        self._update_context_menu()
        self._save_config()

    def _on_opacity_changed(self, value):
        self.manual_opacity = value / 100.0
        self.current_opacity = self.manual_opacity
        self.setWindowOpacity(self.manual_opacity)
        self._save_config()

    # ----------------------------------------------------------------
    # 系统托盘
    # ----------------------------------------------------------------
    def _create_tray(self):
        self.tray = QSystemTrayIcon(self)
        icon = QIcon(PET_IMAGE)
        self.tray.setIcon(icon)
        self.tray.setToolTip(f"桌面宠物 - {self.pet_name}")
        tray_menu = QMenu()
        act_settings = tray_menu.addAction("⚙️ 设置...")
        act_settings.triggered.connect(self._show_settings_dialog)
        act_show = tray_menu.addAction("显示/隐藏宠物")
        act_show.triggered.connect(self._toggle_visible)
        act_autostart = tray_menu.addAction("开机自启动")
        act_autostart.setCheckable(True)
        act_autostart.setChecked(self.auto_start)
        act_autostart.triggered.connect(self._toggle_auto_start)
        act_restart = tray_menu.addAction("重启")
        act_restart.triggered.connect(self._restart)
        tray_menu.addSeparator()
        act_exit = tray_menu.addAction("退出")
        act_exit.triggered.connect(self._quit)
        self.tray.setContextMenu(tray_menu)
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self._toggle_visible()

    def _toggle_visible(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.raise_()

    def _quit(self):
        self._save_config()
        self._stop_keyboard_hook()
        QApplication.instance().quit()

    def _restart(self):
        self._save_config()
        os.execl(sys.executable, sys.executable, *sys.argv)

    # ----------------------------------------------------------------
    # 绘制
    # ----------------------------------------------------------------
    def paintEvent(self, event):
        pass  # 透明背景，由label显示图片


# ============ 程序入口 ============
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    pet = DesktopPet()
    if pet.start_hidden:
        # 启动时只在托盘显示。Windows 可能把图标折叠进「隐藏的图标」，
        # 所以弹一次气泡告诉用户去哪找。
        pet.tray.showMessage(
            "桌面宠物",
            "我躲在任务栏托盘里啦～点一下托盘图标就能叫我出来",
            QSystemTrayIcon.Information,
            4000,
        )
    else:
        pet.show()
    sys.exit(app.exec())

# -*- encoding=utf8 -*-
"""
多语言卡拉比丘 UI 截图自动化工具

使用方式：
1. 在 config.py 中填写各语言启动器路径与参考语言
2. 运行本脚本
3. 程序自动启动参考语言客户端，开始记录你的鼠标操作
4. 手动操作进入目标页面，按 F9 拖选截图区域（可多次）
5. 按 F10 结束录制
6. 程序自动对其余语言重放所有操作并截图
"""

import os
import time
import threading
import tkinter as tk
import keyboard
import psutil
from typing import Optional
from pynput import mouse as pmouse
from pynput.mouse import Controller as MouseController, Button
from PIL import ImageGrab

# ─────────────────────────────────────────────
# 语言配置
# ─────────────────────────────────────────────
try:
    from config import LAUNCHER_PATHS, REFERENCE_LANG
except ImportError:
    raise SystemExit(
        "找不到 config.py，请先创建并填写各语言启动器路径。\n"
        "参考模板：config_template.py"
    )

LANGUAGES = ["zu", "zh-hant-tw", "pt-br", "fr", "es-419", "de", "zh", "en", "ja", "ru", "ko"]

# 以运行时间命名的输出根目录，每次运行独立存放
_run_ts = time.strftime("%Y%m%d_%H%M%S")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "screenshots", _run_ts)

# ─────────────────────────────────────────────
# 全局录制状态
# ─────────────────────────────────────────────
# 事件类型：
#   {"type": "click",      "x": int, "y": int, "button": str, "t": float}
#   {"type": "drag",       "x1": int, "y1": int, "x2": int, "y2": int, "button": str, "t": float}
#   {"type": "scroll",     "x": int, "y": int, "dx": int, "dy": int, "t": float}
#   {"type": "screenshot", "index": int, "region": (x1,y1,x2,y2), "t": float}
recorded_events = []
_recording = False
_record_start_time = 0.0
_event_lock = threading.Lock()
_stop_event = threading.Event()
_f9_pending = threading.Event()   # 通知主线程有 F9 待处理
_selecting = threading.Event()    # 拖选区域进行中，暂停一切鼠标录制


# ─────────────────────────────────────────────
# 区域选择覆盖层
# ─────────────────────────────────────────────

def select_region():
    """全屏透明覆盖层，拖选区域。返回 (x1,y1,x2,y2) 或 None。"""
    result = [None]
    start = [0, 0]

    root = tk.Tk()
    root.attributes("-fullscreen", True)
    root.attributes("-alpha", 0.25)
    root.attributes("-topmost", True)
    root.configure(bg="black")
    root.overrideredirect(True)

    canvas = tk.Canvas(root, cursor="cross", bg="black", highlightthickness=0)
    canvas.pack(fill=tk.BOTH, expand=True)
    rect_id = [None]

    def on_press(e):
        start[0], start[1] = e.x, e.y
        if rect_id[0]:
            canvas.delete(rect_id[0])
        rect_id[0] = canvas.create_rectangle(
            e.x, e.y, e.x, e.y, outline="red", width=2, fill=""
        )

    def on_drag(e):
        if rect_id[0]:
            canvas.coords(rect_id[0], start[0], start[1], e.x, e.y)

    def on_release(e):
        x1, y1 = min(start[0], e.x), min(start[1], e.y)
        x2, y2 = max(start[0], e.x), max(start[1], e.y)
        if x2 - x1 > 5 and y2 - y1 > 5:
            result[0] = (x1, y1, x2, y2)
        root.destroy()

    def on_escape(e):
        root.destroy()

    canvas.bind("<ButtonPress-1>", on_press)
    canvas.bind("<B1-Motion>", on_drag)
    canvas.bind("<ButtonRelease-1>", on_release)
    root.bind("<Escape>", on_escape)
    root.mainloop()
    return result[0]


def _capture_region(region: tuple):
    x1, y1, x2, y2 = region
    return ImageGrab.grab(bbox=(x1, y1, x2, y2))


def _save_screenshot(img, lang: str, index: int):
    folder = os.path.join(OUTPUT_DIR, lang)
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, f"{index:02d}.png")
    img.save(path)
    print(f"  [保存] {path}")


# ─────────────────────────────────────────────
# 启动器
# ─────────────────────────────────────────────

def kill_game(exe_name: str):
    """按 exe 文件名关闭所有匹配的进程。"""
    name = os.path.basename(exe_name).lower()
    killed = 0
    for proc in psutil.process_iter(["name", "pid"]):
        try:
            if proc.info["name"] and proc.info["name"].lower() == name:
                proc.kill()
                killed += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    if killed:
        print(f"  [关闭] 已终止 {killed} 个 {name} 进程")
    time.sleep(2)


def launch_game(lang: str):
    """用 os.startfile 启动 .lnk 快捷方式或 .exe。"""
    path = LAUNCHER_PATHS.get(lang, "")
    if not path:
        raise ValueError(f"未配置语言 [{lang}] 的启动器路径")
    if not path.lower().endswith((".lnk", ".exe")):
        path = path + ".lnk"
    if not os.path.exists(path):
        raise FileNotFoundError(f"启动器不存在: {path}")
    print(f"  [启动] {lang} → {path}")
    os.startfile(path)


# ─────────────────────────────────────────────
# 录制阶段
# ─────────────────────────────────────────────

def start_recording() -> int:
    """
    启动参考语言客户端，录制鼠标操作 + F9 截图事件。
    F10 结束录制，返回截图总数。
    """
    global _recording, _record_start_time

    # 启动参考语言
    launch_game(REFERENCE_LANG)

    startup_wait = getattr(__import__("config"), "STARTUP_WAIT", 15.0)
    print(f"[等待] {startup_wait}s 后开始录制，请等待游戏启动...")
    time.sleep(startup_wait)

    _recording = True
    _record_start_time = time.time()
    _stop_event.clear()

    screenshot_count = [0]
    _drag_start = {}   # button.name -> (x, y, t)

    # ── 鼠标监听 ──
    def on_click(x, y, button, pressed):
        if not _recording or _selecting.is_set():
            return
        t = time.time() - _record_start_time
        if pressed:
            _drag_start[button.name] = (x, y, t)
        else:
            if button.name in _drag_start:
                sx, sy, st = _drag_start.pop(button.name)
                dist = ((x - sx) ** 2 + (y - sy) ** 2) ** 0.5
                if dist > 5:
                    # 拖动
                    with _event_lock:
                        recorded_events.append({
                            "type": "drag",
                            "x1": sx, "y1": sy, "x2": x, "y2": y,
                            "button": button.name, "t": st,
                        })
                else:
                    # 普通点击（记录按下时刻）
                    with _event_lock:
                        recorded_events.append({
                            "type": "click", "x": sx, "y": sy,
                            "button": button.name, "t": st,
                        })

    def on_scroll(x, y, dx, dy):
        if not _recording or _selecting.is_set():
            return
        t = time.time() - _record_start_time
        with _event_lock:
            recorded_events.append({
                "type": "scroll", "x": x, "y": y,
                "dx": dx, "dy": dy, "t": t,
            })

    listener = pmouse.Listener(on_click=on_click, on_scroll=on_scroll)
    listener.start()

    # ── F9 处理（在主线程弹 tkinter 窗口）──
    def on_f9():
        if not _recording:
            return
        _f9_pending.set()

    def on_f10():
        global _recording
        _recording = False
        _stop_event.set()
        print(f"[F10] 录制结束，共截图 {screenshot_count[0]} 张")

    keyboard.add_hotkey("f9", on_f9, suppress=False)
    keyboard.add_hotkey("f10", on_f10, suppress=False)

    print("=" * 50)
    print("录制已开始（鼠标点击自动记录）")
    print("  F9  → 拖选截图区域（可多次）")
    print("  F10 → 结束录制并开始自动化")
    print("=" * 50)

    # 主循环：等待 F9 或 F10
    while not _stop_event.is_set():
        if _f9_pending.is_set():
            _f9_pending.clear()
            t_snap = time.time() - _record_start_time
            print("[F9] 请拖选截图区域（ESC 取消）...")
            _selecting.set()          # 暂停鼠标录制
            region = select_region()
            _selecting.clear()        # 恢复鼠标录制
            _drag_start.clear()       # 清除拖选期间残留状态
            if region:
                screenshot_count[0] += 1
                idx = screenshot_count[0]
                img = _capture_region(region)
                _save_screenshot(img, REFERENCE_LANG, idx)
                with _event_lock:
                    recorded_events.append({
                        "type": "screenshot",
                        "index": idx,
                        "region": region,
                        "t": t_snap,
                    })
                print(f"  [记录] 区域 {region} → 第 {idx} 张")
            else:
                print("  [取消] 未选择区域")
        time.sleep(0.05)

    listener.stop()
    keyboard.remove_hotkey("f9")
    keyboard.remove_hotkey("f10")

    return screenshot_count[0]


# ─────────────────────────────────────────────
# 回放阶段
# ─────────────────────────────────────────────

def replay_and_capture(lang: str, total_shots: int):
    """按录制的时间轴回放鼠标操作，并在对应时机截图。"""
    mouse = MouseController()

    # 分离点击事件与截图事件，按时间排序
    events = sorted(recorded_events, key=lambda e: e["t"])

    replay_start = time.time()
    shot_count = 0

    for event in events:
        # 等到该事件的时间点
        target = replay_start + event["t"]
        now = time.time()
        if target > now:
            time.sleep(target - now)

        if event["type"] == "click":
            mouse.position = (event["x"], event["y"])
            btn = Button.left if event["button"] == "left" else Button.right
            mouse.press(btn)
            time.sleep(0.05)
            mouse.release(btn)

        elif event["type"] == "drag":
            btn = Button.left if event["button"] == "left" else Button.right
            mouse.position = (event["x1"], event["y1"])
            time.sleep(0.05)
            mouse.press(btn)
            # 平滑移动到终点（20步）
            steps = 20
            for i in range(1, steps + 1):
                ix = event["x1"] + (event["x2"] - event["x1"]) * i // steps
                iy = event["y1"] + (event["y2"] - event["y1"]) * i // steps
                mouse.position = (ix, iy)
                time.sleep(0.01)
            mouse.release(btn)

        elif event["type"] == "scroll":
            mouse.position = (event["x"], event["y"])
            mouse.scroll(event["dx"], event["dy"])

        elif event["type"] == "screenshot":
            shot_count += 1
            idx = event["index"]
            region = event["region"]
            print(f"  [截图] {lang} #{idx}  区域 {region}")
            img = _capture_region(region)
            _save_screenshot(img, lang, idx)

    if shot_count != total_shots:
        print(f"  [警告] {lang} 实际截图 {shot_count} 张，预期 {total_shots} 张")


def run_all_languages(total_shots: int):
    target_langs = [l for l in LANGUAGES if l != REFERENCE_LANG]
    startup_wait = getattr(__import__("config"), "STARTUP_WAIT", 15.0)

    # 获取游戏 exe 文件名（从任意一个配置路径提取）
    sample_path = next((v for v in LAUNCHER_PATHS.values() if v), "")
    # .lnk 快捷方式无法直接拿到 exe 名，约定游戏进程名写在 config.py 的 GAME_EXE
    game_exe = getattr(__import__("config"), "GAME_EXE", "")

    prev_lang = REFERENCE_LANG

    for lang in target_langs:
        print(f"\n{'─' * 40}")
        print(f"开始处理语言: {lang}")
        try:
            # 关闭上一个语言的客户端
            if game_exe:
                print(f"  [关闭] 关闭上一个客户端 ({prev_lang})...")
                kill_game(game_exe)
            launch_game(lang)
            print(f"  [等待] {startup_wait}s 让游戏启动...")
            time.sleep(startup_wait)
            replay_and_capture(lang, total_shots)
            prev_lang = lang
        except (ValueError, FileNotFoundError) as e:
            print(f"  [跳过] {e}")

    print(f"\n{'=' * 50}")
    print("所有语言处理完毕！")
    print(f"截图保存目录: {OUTPUT_DIR}")


# ─────────────────────────────────────────────
# 入口
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("多语言卡拉比丘截图工具 启动")
    print(f"参考语言: {REFERENCE_LANG}")
    print(f"目标语言: {[l for l in LANGUAGES if l != REFERENCE_LANG]}\n")

    total = start_recording()

    if total == 0:
        print("[退出] 未截取任何截图，程序结束。")
    else:
        run_all_languages(total)

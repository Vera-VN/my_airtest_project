# -*- encoding=utf8 -*-
"""
多语言卡拉比丘 UI 截图自动化工具

使用方式：
1. 在 config.py 中填写各语言启动器路径
2. 运行本脚本，手动操作参考语言进入目标页面
3. 按 F9 截图（可多次），按 F10 结束录制
4. 脚本自动对其余语言重复相同步骤并截图
"""

import os
import time
import subprocess
import threading
import keyboard
from PIL import ImageGrab
from airtest.core.api import *
from airtest.core.helper import G

# ─────────────────────────────────────────────
# 语言配置（在 config.py 中维护启动器路径）
# ─────────────────────────────────────────────
try:
    from config import LAUNCHER_PATHS, REFERENCE_LANG
except ImportError:
    raise SystemExit(
        "找不到 config.py，请先创建并填写各语言启动器路径。\n"
        "参考模板：config_template.py"
    )

LANGUAGES = ["zu", "zh-hant-tw", "pt-br", "fr", "es-419", "de"]
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "screenshots")

# ─────────────────────────────────────────────
# 全局录制状态
# ─────────────────────────────────────────────
recorded_events = []   # 记录操作事件序列
screenshot_indices = []  # 记录第几个事件是截图点
_recording = False
_event_lock = threading.Lock()
_stop_event = threading.Event()


def _take_screenshot_to_buffer():
    """截取当前屏幕并返回 PIL Image。"""
    img = ImageGrab.grab()
    return img


def _save_screenshot(img, lang: str, index: int):
    """保存截图到对应语言文件夹。"""
    folder = os.path.join(OUTPUT_DIR, lang)
    os.makedirs(folder, exist_ok=True)
    filename = f"{lang}_{index:02d}.png"
    path = os.path.join(folder, filename)
    img.save(path)
    print(f"  [保存] {path}")
    return path


# ─────────────────────────────────────────────
# 录制阶段：监听 F9 / F10
# ─────────────────────────────────────────────

def start_recording():
    """
    进入录制模式：
    - F9 → 记录截图事件（同时截取参考截图）
    - F10 → 结束录制
    """
    global _recording
    _recording = True
    _stop_event.clear()

    ref_lang = REFERENCE_LANG
    ref_folder = os.path.join(OUTPUT_DIR, ref_lang)
    os.makedirs(ref_folder, exist_ok=True)

    screenshot_count = [0]

    def on_f9():
        if not _recording:
            return
        screenshot_count[0] += 1
        idx = screenshot_count[0]
        print(f"[F9] 截图 #{idx}")
        img = _take_screenshot_to_buffer()
        _save_screenshot(img, ref_lang, idx)
        with _event_lock:
            recorded_events.append({"type": "screenshot", "index": idx})

    def on_f10():
        global _recording
        _recording = False
        _stop_event.set()
        print(f"[F10] 录制结束，共截图 {screenshot_count[0]} 张")

    keyboard.add_hotkey("f9", on_f9, suppress=False)
    keyboard.add_hotkey("f10", on_f10, suppress=False)

    print("=" * 50)
    print("录制已启动")
    print("  F9  → 截取当前截图")
    print("  F10 → 结束录制并开始自动化")
    print("请手动操作参考语言客户端...")
    print("=" * 50)

    _stop_event.wait()

    keyboard.remove_hotkey("f9")
    keyboard.remove_hotkey("f10")

    return screenshot_count[0]


# ─────────────────────────────────────────────
# 自动化阶段：对其余语言重放
# ─────────────────────────────────────────────

def launch_game(lang: str):
    """启动指定语言的游戏客户端。"""
    exe_path = LAUNCHER_PATHS.get(lang)
    if not exe_path:
        raise ValueError(f"未配置语言 [{lang}] 的启动器路径，请检查 config.py")
    if not os.path.exists(exe_path):
        raise FileNotFoundError(f"启动器不存在: {exe_path}")

    print(f"  [启动] {lang} → {exe_path}")
    subprocess.Popen([exe_path])


def wait_and_capture(lang: str, total_shots: int, startup_wait: float = 15.0):
    """
    等待游戏启动后，在与参考语言相同的时机截图。

    :param lang: 目标语言代码
    :param total_shots: 需要截取的张数（与参考语言一致）
    :param startup_wait: 启动等待秒数（可在 config.py 中调整）
    """
    print(f"  [等待] 等待 {startup_wait}s 让游戏启动...")
    time.sleep(startup_wait)

    # 按照录制的事件序列回放
    shot_count = 0
    for event in recorded_events:
        if event["type"] == "screenshot":
            shot_count += 1
            idx = event["index"]
            print(f"  [截图] {lang} #{idx}")
            img = _take_screenshot_to_buffer()
            _save_screenshot(img, lang, idx)

    if shot_count != total_shots:
        print(f"  [警告] {lang} 实际截图 {shot_count} 张，预期 {total_shots} 张")


def run_all_languages(total_shots: int):
    """对除参考语言外的所有语言依次执行自动化截图。"""
    target_langs = [l for l in LANGUAGES if l != REFERENCE_LANG]

    startup_wait = getattr(__import__("config"), "STARTUP_WAIT", 15.0)

    for lang in target_langs:
        print(f"\n{'─' * 40}")
        print(f"开始处理语言: {lang}")
        try:
            launch_game(lang)
            wait_and_capture(lang, total_shots, startup_wait=startup_wait)
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

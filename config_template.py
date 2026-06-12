# -*- encoding=utf8 -*-
"""
配置模板 —— 复制此文件并重命名为 config.py，然后填写实际路径。
config.py 已被 .gitignore 排除，不会上传到仓库。
"""

# 你手动演示的参考语言（从下方6个代码中选一个）
# 可选: "zu" | "zh-hant-tw" | "pt-br" | "fr" | "es-419" | "de"
REFERENCE_LANG = "zh-hant-tw"

# 各语言启动器路径（填写实际路径，不使用的语言可留空字符串）
LAUNCHER_PATHS = {
    "zu":          r"",   # Zulu
    "zh-hant-tw":  r"",   # 中文繁体
    "pt-br":       r"",   # 葡萄牙语
    "fr":          r"",   # 法语
    "es-419":      r"",   # 西班牙语
    "de":          r"",   # 德语
    "zh":          r"",   # 中文简体
    "en":          r"",   # 英语
    "ja":          r"",   # 日语
    "ru":          r"",   # 俄语
    "ko":          r"",   # 韩语
}

# 启动游戏后等待进入界面的秒数
STARTUP_WAIT = 15.0

# 游戏进程的 exe 文件名（用于切换语言时关闭上一个客户端）
GAME_EXE = "YourGame.exe"

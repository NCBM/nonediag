from argparse import ArgumentParser
from os import path
import os
import sys

from .versions import HAS_PLUGIN_JSON_TOML, HAS_PYTHON311, NO_PYTHON37
from .models import check_builtin, default_state, duplicate_import, lack_module, no_export, not_implemented, port_used, type_subscription, warn_bad_import
from .base import noneversion, readlog, readbotpy, readtoml


def main(args):
    if sys.version_info < (3, 7):
        raise Exception("不受支持的 Python 版本，请使用更新版本 (>=3.7)")
    log = readlog()
    bothome: str = path.realpath(path.split(args.botfile)[0])
    os.chdir(bothome)
    if args.botfile.endswith(".toml"):
        info = {"adapters": [], "userload": [], "builtin": []}
        info.update(readtoml(path.split(args.botfile)[1]))
    else:
        info = readbotpy(path.split(args.botfile)[1])
        info.update(readtoml(info["toml"]))
    print("[DEBUG]", info)
    # print(sys.path)

    if (nv := noneversion()) is not None:
        print("[DEBUG] Found nonebot2 version", nv)
        if sys.version_info >= (3, 11) and nv < HAS_PYTHON311:
            print(f"当前的 nonebot2 {nv} 还不支持更新的 Python，请使用更低版本的 Python (>=3.7,<3.11)")
        if sys.version_info < (3, 8) and nv >= NO_PYTHON37:
            print(f"当前的 nonebot2 {nv} 已不支持更旧的 Python，请使用更新版本的 Python (>=3.8)")
    if "RuntimeError: Plugin already exists: " in log:
        if nv is not None and nv >= HAS_PLUGIN_JSON_TOML:
            duplicate_import(log, info)
        else:
            print(
                "警告：",
                "  我们无法在当前版本下分析重复导入",
                "  请自行排查 bot.py 中的重复导入",
                "",
                sep="\n"
            )
    if not info["adapters"]:
        print(
            "错误：",
            "  未找到可注册的适配器",
            "可能原因：",
            "  1. 使用 nb-cli 创建项目时未在适配器选择界面**按空格**选择需要的适配器",
            "  2. 使用了未识别的导入格式",
            "解决方案：",
            "  1. 使用 nb-cli 重新创建项目",
            "    nb create",
            "  2. 根据文档手动补全需要的适配器",
            "    nb adapter list",
            "    nb adapter install nonebot-adapter-xxx",
            "",
            sep="\n"
        )
    if info["userload"]:
        warn_bad_import(info["userload"])
    if info["builtin"]:
        check_builtin(info["builtin"])
    if "[Errno 10013]" in log:
        port_used()
    if "ModuleNotFoundError" in log:
        lack_module(log)
    if "NotImplementedError" in log:
        for d in info["plugin_dirs"]:
            not_implemented(d)
    for idx, ln in enumerate(x := log.splitlines()[::-1]):
        if "TypeError: 'type' object is not subscriptable" in ln and sys.version_info < (3, 9):
            type_subscription("\n".join(x[idx + 2:idx - 1:-1]))
    if "ImportError: cannot import name 'State' from 'nonebot.params" in log:
        default_state(info, nv)
    if "ImportError: cannot import name 'export' from 'nonebot'" in log:
        no_export(nv, info)
    check_builtin(info["builtin"])

    print("如果你没看到任何错误提示，但问题仍然存在，")
    print("请前往 https://github.com/NCBM/nonediag 提交 issue/pr.")


def _entry():
    ap = ArgumentParser(
        "nonediag", description="NoneBot2 error diagnosing tool."
    )
    ap.add_argument(
        "-B", "--botfile", nargs="?", default="./bot.py",
        help="specify bot.py or pyproject.toml dir"
    )
    args = ap.parse_args()
    # print(args)
    main(args)


if __name__ == "__main__":
    _entry()

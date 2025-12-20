import time
import subprocess
from datetime import datetime
import sys
import os

# ========= 配置区 =========
PYTHON_EXE = sys.executable          # 使用当前 venv 的 python
FETCH_SCRIPT = "news_fetch_and_store.py"
INTERVAL_HOURS = 3                  # 每 3 小时跑一次
LOG_FILE = "scheduler.log"
# ==========================


def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def run_job():
    log("▶ 开始抓取新闻")
    try:
        result = subprocess.run(
            [PYTHON_EXE, FETCH_SCRIPT],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        log("✔ 抓取完成")

        if result.stdout:
            log("STDOUT:\n" + result.stdout.strip())
        if result.stderr:
            log("STDERR:\n" + result.stderr.strip())

    except Exception as e:
        log(f"✖ 抓取失败: {e}")
        return

    # ✅ 抓取后再体检
    subprocess.run([PYTHON_EXE, "health_check.py"])
    subprocess.run([PYTHON_EXE, "db_cleanup.py"])



def main():
    log("🟢 调度器启动")
    while True:
        run_job()
        log(f"⏳ 休眠 {INTERVAL_HOURS} 小时")
        time.sleep(INTERVAL_HOURS * 3600)


if __name__ == "__main__":
    main()

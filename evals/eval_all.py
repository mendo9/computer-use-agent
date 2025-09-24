# scripts/eval_all.py
import subprocess
import sys

cmds = [
    ["uv", "run", "python", "evals/eval_template.py", "--gt", "annotation.json", "--overlay"],
    ["uv", "run", "python", "evals/eval_ocr.py", "--gt", "annotation.json", "--overlay"],
]
for c in cmds:
    print(">>", " ".join(c))
    rc = subprocess.call(c)
    if rc != 0:
        sys.exit(rc)
print("Done.")

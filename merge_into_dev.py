#!/usr/bin/env python3
"""
merge_into_dev.py
Run from: CSSD_Management_System\CSSD_Management_System (where manage.py lives)

Merges all feature branches into dev in dependency order.
Handles the 3 known conflict files automatically per the integration guide rules.
"""

import subprocess, sys, os, shutil, textwrap

REPO_ROOT   = os.path.dirname(os.path.abspath(__file__))
APP_DIR     = os.path.join(REPO_ROOT, "CSSD_Management_System")
VIEWS_FILE  = os.path.join(APP_DIR, "views.py")
URLS_FILE   = os.path.join(APP_DIR, "urls.py")
MIG_FILE    = os.path.join(APP_DIR, "migrations",
              "0003_inventoryitem_instrumentrequest_requestitem_notification.py")

def run(cmd, cwd=REPO_ROOT, check=True, capture=False):
    r = subprocess.run(cmd, cwd=cwd, shell=True,
                       capture_output=capture, text=True)
    if check and r.returncode not in (0, 1):
        print(f"[ERROR] {cmd}\n{r.stdout}\n{r.stderr}")
        sys.exit(1)
    return r

def git(cmd, **kw):
    return run(f"git {cmd}", **kw)

def current_branch():
    return git("rev-parse --abbrev-ref HEAD", capture=True).stdout.strip()

def strip_conflict_markers(path):
    """Keep only HEAD (<<<<<<< ... =======) section, drop theirs (======= ... >>>>>>>)."""
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()
    out, in_ours, in_theirs = [], False, False
    for line in lines:
        if line.startswith("<<<<<<< "):
            in_ours = True
        elif line.startswith("=======") and in_ours:
            in_ours, in_theirs = False, True
        elif line.startswith(">>>>>>> ") and in_theirs:
            in_theirs = False
        elif not in_theirs:
            out.append(line)
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(out)

MERGE_ORDER = [
    # (branch_name,  commit_message)
    ("feature/PROJ-4-authenticaion",                    "merge: PROJ-4 email authentication into dev"),
    ("feature/PROJ-6-Department_Requests",              "merge: PROJ-6 department nurse requests into dev"),
    ("feature/PROJ-8-dashboards",                       "merge: PROJ-8 CSSD and nurse dashboards into dev"),
    ("feature/PROJ-17-21-state-machine-transitions",    "merge: PROJ-17-21 full state machine into dev"),
    ("feature/Proj-17-Mark-as-Collected",               "merge: Proj-17 mark-as-collected into dev"),
    ("feature/Proj-18-Mark-as-Cleaned",                 "merge: Proj-18 mark-as-cleaned into dev"),
    ("feature/Proj-19-Mark-as-Sterilized",              "merge: Proj-19 mark-as-sterilized into dev"),
    ("feature/Proj-21-Mark-as-Packed",                  "merge: Proj-21 mark-as-packed into dev"),
    ("feature/Proj-20-Mark-as-Delivered",               "merge: Proj-20 nurse deliver into dev"),
    ("feature/Proj-24-Assign-operator-to-batch",        "merge: Proj-24 batch operator assignment into dev"),
    ("feature/Proj-27-View-Inventory-shortage-Alerts",  "merge: Proj-27 inventory shortage alerts into dev"),
    ("feature/Proj-29-View-Estimated-Completion-Time",  "merge: Proj-29 estimated completion time into dev"),
]

def save_our_files():
    """Snapshot current (good) views.py and urls.py before any merge."""
    shutil.copy2(VIEWS_FILE, VIEWS_FILE + ".ours")
    shutil.copy2(URLS_FILE,  URLS_FILE  + ".ours")
    shutil.copy2(MIG_FILE,   MIG_FILE   + ".ours")
    print("[+] Saved baseline views/urls/migration snapshots")

def restore_our_key_files():
    """After a merge conflict, restore our version of the 3 known conflict files."""
    for f in [VIEWS_FILE, URLS_FILE, MIG_FILE]:
        shutil.copy2(f + ".ours", f)

def merge_branch(branch, commit_msg):
    print(f"\n{'='*60}")
    print(f"  Merging: {branch}")
    print(f"{'='*60}")

    result = git(f'merge --no-ff origin/{branch} -m "{commit_msg}"', check=False, capture=True)
    stdout = result.stdout + result.stderr

    if result.returncode == 0:
        print(f"  [OK] Clean merge: {branch}")
        return True

    if "CONFLICT" in stdout or "Automatic merge failed" in stdout:
        print(f"  [!] Conflicts detected — applying resolution strategy")
        # Rule: keep our versions of all 3 known conflict files
        restore_our_key_files()
        git("add CSSD_Management_System/CSSD_Management_System/views.py "
            "CSSD_Management_System/CSSD_Management_System/urls.py "
            "CSSD_Management_System/CSSD_Management_System/migrations/"
            "0003_inventoryitem_instrumentrequest_requestitem_notification.py")
        # Stage any other conflicted files by keeping ours
        check_r = git("diff --name-only --diff-filter=U", capture=True)
        for extra in check_r.stdout.strip().splitlines():
            extra = extra.strip()
            if extra:
                git(f"checkout --ours {extra}", check=False)
                git(f"add {extra}", check=False)
        git(f'commit -m "{commit_msg}" --no-edit')
        print(f"  [OK] Conflict resolved and committed: {branch}")
        return True
    else:
        print(f"  [SKIP] Already merged or nothing to do: {branch}")
        print(f"         {stdout[:200]}")
        return False

def verify():
    print("\n[Verify] Running system checks...")
    r = run("python manage.py check 2>&1", capture=True)
    ok = "0 issues" in r.stdout or "System check identified no issues" in r.stdout
    print(f"  {'[OK]' if ok else '[FAIL]'} manage.py check")
    if not ok:
        print(r.stdout[-800:])

    print("[Verify] Running all tests...")
    r = run("python manage.py test CSSD_Management_System.tests --verbosity=1 2>&1",
            capture=True, check=False)
    print(r.stdout[-1500:])
    return "OK" in r.stdout

if __name__ == "__main__":
    if current_branch() != "dev":
        print(f"[!] Switching to dev (was on {current_branch()})")
        git("checkout dev")
        git("pull origin dev", check=False)

    save_our_files()

    results = {}
    for branch, msg in MERGE_ORDER:
        results[branch] = merge_branch(branch, msg)

    passed = verify()

    print(f"\n{'='*60}")
    print("  MERGE SUMMARY")
    print(f"{'='*60}")
    for branch, ok in results.items():
        status = "✓ merged" if ok else "~ skipped"
        print(f"  {status}  {branch}")
    print(f"\n  Tests: {'✓ PASSED' if passed else '✗ FAILURES — see above'}")
    print(f"{'='*60}")

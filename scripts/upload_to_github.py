"""
GitHub API 批量上传脚本
通过 gh CLI 的 API 将本地仓库推送到 GitHub
"""
import os
import subprocess
import base64
import glob

REPO = "lifelonglearnerAdam/miniso-ai-decision-engine"
BRANCH = "main"
BASE_DIR = r"D:\Project\miniso-ai-decision-engine"
IGNORE_DIRS = {".git", "__pycache__", "node_modules", "tmp_push_engine"}
IGNORE_FILES = {".gitignore", "filelist.txt", "temp_hex.txt", "proxy_config.tmp"}

def gh_api(method, endpoint, **kwargs):
    """Call gh api and return parsed JSON"""
    cmd = ["gh", "api", endpoint, "-X", method]
    for key, val in kwargs.items():
        if key == "field":
            for k, v in val.items():
                cmd.extend(["-f", f"{k}={v}"])
        elif key == "raw_field":
            for k, v in val.items():
                cmd.extend(["-F", f"{k}={v}"])
        elif key == "input":
            cmd.extend(["--input", val])
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ERROR: {result.stderr.strip()}")
        return None
    return result.stdout

def get_file_list(root_dir):
    """Get all files to upload"""
    files = []
    for root, dirs, filenames in os.walk(root_dir):
        # Filter ignored dirs
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for f in filenames:
            if f in IGNORE_FILES:
                continue
            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(full_path, root_dir)
            if rel_path.startswith(".git"):
                continue
            files.append((rel_path, full_path))
    return files

def upload_file(file_rel_path, file_full_path):
    """Upload a single file via GitHub API"""
    with open(file_full_path, "rb") as f:
        content_bytes = f.read()
    content_b64 = base64.b64encode(content_bytes).decode("ascii")
    
    # Check if file exists
    check = gh_api("GET", f"repos/{REPO}/contents/{file_rel_path.replace(os.sep, '/')}", field={"ref": BRANCH})
    
    endpoint = f"repos/{REPO}/contents/{file_rel_path.replace(os.sep, '/')}"
    
    if check and '"sha"' in check:
        # File exists, update it
        import json
        sha = json.loads(check).get("sha", "")
        result = gh_api("PUT", endpoint, field={
            "message": f"Upload {file_rel_path}",
            "content": content_b64,
            "sha": sha,
            "branch": BRANCH
        })
    else:
        # New file
        result = gh_api("PUT", endpoint, field={
            "message": f"Upload {file_rel_path}",
            "content": content_b64,
            "branch": BRANCH
        })
    
    if result:
        return True
    return False

def main():
    print("=" * 60)
    print("[Uploading] MINISO AI Decision Engine to GitHub")
    print("   Repo: %s" % REPO)
    print("   Branch: %s" % BRANCH)
    print("=" * 60)
    
    files = get_file_list(BASE_DIR)
    print("\n[Info] Found %d files to upload" % len(files))
    
    success = 0
    failed = 0
    
    for i, (rel_path, full_path) in enumerate(files):
        print("[%d/%d] %s ... " % (i+1, len(files), rel_path), end="")
        ok = upload_file(rel_path, full_path)
        if ok:
            print("[OK]")
            success += 1
        else:
            print("[FAIL]")
            failed += 1
    
    print("\n" + "=" * 60)
    print("[Done] Upload complete: %d succeeded, %d failed" % (success, failed))
    print("[Repo] https://github.com/%s" % REPO)
    print("=" * 60)

if __name__ == "__main__":
    main()

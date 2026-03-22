import subprocess
result = subprocess.run(["git", "branch", "-a"], capture_output=True, text=True)
branches = result.stdout.split('\n')
branches = [b.strip() for b in branches if b.strip()]
print(branches)

has_main = any(b == "main" or b == "* main" or b == "remotes/origin/main" for b in branches)
print(has_main)

"""
setup.py - YouTube Uploader Skill Setup
Installs required Python dependencies for the YouTube Uploader skill.
"""

import subprocess
import sys


def install_dependencies():
    packages = [
        "google-api-python-client",
        "google-auth-oauthlib",
        "google-auth-httplib2",
    ]

    print("📦 Installing YouTube Uploader dependencies...\n")
    for pkg in packages:
        print(f"  → Installing {pkg}...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", pkg],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print(f"  ✅ {pkg} installed successfully")
        else:
            print(f"  ❌ Failed to install {pkg}")
            print(result.stderr)

    print("\n✅ All dependencies installed. You can now run authenticate.py")


if __name__ == "__main__":
    install_dependencies()

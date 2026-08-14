import base64
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def load_env(env_path: Path):
    env_vars = {}
    if not env_path.exists():
        return env_vars
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                env_vars[key.strip()] = val.strip()
    return env_vars

def main():
    env_path = BASE_DIR / ".env"
    template_path = BASE_DIR / "env"

    if not env_path.exists():
        print(f"[!] '.env' file not found at {env_path}")
        print(f"[!] Please copy '{template_path}' to '{env_path}' and fill in the values.")
        return

    env_vars = load_env(env_path)

    # 1. Restore android/app/google-services.json
    json_b64 = env_vars.get("GOOGLE_SERVICES_JSON_BASE64", "")
    if json_b64:
        target_json = BASE_DIR / "android" / "app" / "google-services.json"
        target_json.parent.mkdir(parents=True, exist_ok=True)
        decoded_json = base64.b64decode(json_b64).decode("utf-8")
        with open(target_json, "w", encoding="utf-8") as f:
            f.write(decoded_json)
        print(f"[OK] Restored: {target_json}")

    # 2. Restore ios/Runner/GoogleService-Info.plist
    plist_b64 = env_vars.get("GOOGLE_SERVICE_INFO_PLIST_BASE64", "")
    if plist_b64:
        target_plist = BASE_DIR / "ios" / "Runner" / "GoogleService-Info.plist"
        target_plist.parent.mkdir(parents=True, exist_ok=True)
        decoded_plist = base64.b64decode(plist_b64).decode("utf-8")
        with open(target_plist, "w", encoding="utf-8") as f:
            f.write(decoded_plist)
        print(f"[OK] Restored: {target_plist}")

if __name__ == "__main__":
    main()

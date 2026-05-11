#!/usr/bin/env python3
import os
from pathlib import Path

def main():
    # Locate files relative to workspace root
    root_dir = Path(__file__).resolve().parent.parent
    env_file = root_dir / ".env"
    template_file = root_dir / "02-prometheus-grafana" / "alertmanager" / "alertmanager.yml.template"
    config_file = root_dir / "02-prometheus-grafana" / "alertmanager" / "alertmanager.yml"

    # Read .env variables
    env_vars = {}
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env_vars[k.strip()] = v.strip()

    # Get Slack Webhook URL from .env or environment
    webhook_url = env_vars.get("SLACK_WEBHOOK_URL") or os.environ.get("SLACK_WEBHOOK_URL")
    
    if not webhook_url:
        print("[WARN] SLACK_WEBHOOK_URL not found in .env or system environment. Using dummy placeholder.")
        webhook_url = "https://hooks.slack.com/services/REPLACE/ME"

    # Perform substitution
    if template_file.exists():
        template_content = template_file.read_text()
        interpolated_content = template_content.replace('{{ env "SLACK_WEBHOOK_URL" }}', webhook_url)
        config_file.write_text(interpolated_content)
        print(f"[INFO] Successfully generated alertmanager.yml with Slack webhook configuration.")
    else:
        print(f"[ERROR] Template file {template_file} does not exist.")

if __name__ == "__main__":
    main()

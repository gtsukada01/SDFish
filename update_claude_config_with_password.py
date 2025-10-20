#!/usr/bin/env python3
"""
Update Claude Code global config to add SUPABASE_DB_PASSWORD
IMPORTANT: Run this script ONLY when Claude Code is completely quit (Cmd+Q)
"""

import json
import sys
from pathlib import Path

def update_claude_config():
    config_path = Path.home() / ".claude.json"

    # Check if config exists
    if not config_path.exists():
        print(f"❌ Error: Config file not found at {config_path}")
        sys.exit(1)

    print(f"📖 Reading config from {config_path}...")

    # Read current config
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in config file: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error reading config: {e}")
        sys.exit(1)

    # Navigate to fish-scraper project config
    project_key = "/Users/btsukada/Desktop/Fishing/fish-scraper"

    if "projects" not in config:
        print("❌ Error: 'projects' key not found in config")
        sys.exit(1)

    if project_key not in config["projects"]:
        print(f"❌ Error: Project '{project_key}' not found in config")
        sys.exit(1)

    # Get project config
    project = config["projects"][project_key]

    if "mcpServers" not in project:
        print("❌ Error: 'mcpServers' key not found in project config")
        sys.exit(1)

    if "supabase" not in project["mcpServers"]:
        print("❌ Error: 'supabase' key not found in mcpServers")
        sys.exit(1)

    # Show current config
    print("\n🔍 Current Supabase MCP config:")
    print(json.dumps(project["mcpServers"]["supabase"], indent=2))

    # Update with database password
    if "env" not in project["mcpServers"]["supabase"]:
        project["mcpServers"]["supabase"]["env"] = {}

    project["mcpServers"]["supabase"]["env"]["SUPABASE_DB_PASSWORD"] = "4thQuarter-21!"

    print("\n✅ Updated Supabase MCP config with database password:")
    print(json.dumps(project["mcpServers"]["supabase"], indent=2))

    # Create backup
    backup_path = config_path.parent / ".claude.json.backup2"
    print(f"\n💾 Creating backup at {backup_path}...")

    try:
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        print("✅ Backup created successfully")
    except Exception as e:
        print(f"⚠️  Warning: Could not create backup: {e}")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            print("❌ Aborted")
            sys.exit(1)

    # Write updated config
    print(f"\n📝 Writing updated config to {config_path}...")

    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        print("✅ Config updated successfully!")
    except Exception as e:
        print(f"❌ Error writing config: {e}")
        print(f"💡 You can restore from backup: {backup_path}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("✅ SUCCESS! Database password added to configuration.")
    print("=" * 60)
    print("\n📋 Next steps:")
    print("1. Open Claude Code")
    print("2. Go to /mcp panel")
    print("3. Click 'Reconnect' on Supabase MCP Server")
    print("4. Verify it shows '✓ connected'")
    print("5. Ask me to query your database!")
    print("\n" + "=" * 60)

if __name__ == "__main__":
    print("=" * 60)
    print("🔧 Claude Code Config Updater - Add DB Password")
    print("=" * 60)
    print("\n⚠️  IMPORTANT: Make sure Claude Code is COMPLETELY QUIT")
    print("   (Press Cmd+Q to quit, not just close the window)")
    print("\nThis script will:")
    print("  • Backup your current config")
    print("  • Add SUPABASE_DB_PASSWORD to MCP server env")
    print("\n" + "=" * 60 + "\n")

    response = input("Is Claude Code completely quit? (y/N): ")

    if response.lower() != 'y':
        print("\n❌ Please quit Claude Code first (Cmd+Q), then run this script again.")
        sys.exit(0)

    update_claude_config()

#!/usr/bin/env python3
"""
Update Claude Code global config to use local Supabase MCP server
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
        print(f"Available projects: {list(config['projects'].keys())}")
        sys.exit(1)

    # Get project config
    project = config["projects"][project_key]

    if "mcpServers" not in project:
        print("❌ Error: 'mcpServers' key not found in project config")
        sys.exit(1)

    # Show current Supabase config
    if "supabase" in project["mcpServers"]:
        print("\n🔍 Current Supabase MCP config:")
        print(json.dumps(project["mcpServers"]["supabase"], indent=2))
    else:
        print("\n⚠️  No existing Supabase MCP config found")

    # Update Supabase MCP config to local Python-based server
    new_supabase_config = {
        "type": "stdio",
        "command": "/Users/btsukada/.local/bin/supabase-mcp-server",
        "env": {
            "QUERY_API_KEY": "qry_v1_FCDDozVrF18tfe2epwt2PYmvGPt7JKuGmofbA-DkQRI",
            "SUPABASE_PROJECT_REF": "ulsbtwqhwnrpkourphiq",
            "SUPABASE_SERVICE_ROLE_KEY": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVsc2J0d3Fod25ycGtvdXJwaGlxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjU4OTIyOSwiZXhwIjoyMDcyMTY1MjI5fQ.35Wwadw4fhNKsapJIiul4fZxTc7HQmKNTMrKY0Sv_6U"
        }
    }

    project["mcpServers"]["supabase"] = new_supabase_config

    print("\n✅ New Supabase MCP config:")
    print(json.dumps(new_supabase_config, indent=2))

    # Create backup
    backup_path = config_path.parent / ".claude.json.backup"
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
    print("✅ SUCCESS! Configuration updated.")
    print("=" * 60)
    print("\n📋 Next steps:")
    print("1. Open Claude Code")
    print("2. Go to /mcp panel")
    print("3. Verify Supabase MCP Server shows '✓ connected'")
    print("4. Ask me to query your database!")
    print("\n" + "=" * 60)

if __name__ == "__main__":
    print("=" * 60)
    print("🔧 Claude Code Config Updater - Supabase MCP")
    print("=" * 60)
    print("\n⚠️  IMPORTANT: Make sure Claude Code is COMPLETELY QUIT")
    print("   (Press Cmd+Q to quit, not just close the window)")
    print("\nThis script will:")
    print("  • Backup your current config")
    print("  • Update Supabase MCP to use local Python server")
    print("  • Replace remote SSE server with local stdio server")
    print("\n" + "=" * 60 + "\n")

    response = input("Is Claude Code completely quit? (y/N): ")

    if response.lower() != 'y':
        print("\n❌ Please quit Claude Code first (Cmd+Q), then run this script again.")
        sys.exit(0)

    update_claude_config()

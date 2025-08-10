#!/usr/bin/env python3

import argparse
import glob
import json
import os
import sys
import traceback
from typing import Dict, List
from BasePostingAction import BasePostingAction

from Newsletter import Newsletter

# Discover repo paths
SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
PLUGINS_PATH = os.path.join(SCRIPT_PATH, "plugins")


def load_config(config_path: str) -> Dict:
    """Load JSON configuration from the given path."""
    with open(config_path, "r") as f:
        return json.load(f)


def find_default_config_path() -> str:
    """Resolve a default config.json path with sensible fallbacks."""
    # 1) Explicit env override
    env_path = os.getenv("SNFC_CONFIG")
    if env_path and os.path.isfile(env_path):
    if env_path:
        abs_env_path = os.path.abspath(env_path)
        # Only allow config files within the script directory
        if os.path.commonpath([abs_env_path, SCRIPT_PATH]) == SCRIPT_PATH and os.path.isfile(abs_env_path):
            return abs_env_path

    # 2) Repo-local config.json
    candidate = os.path.join(SCRIPT_PATH, "config.json")
    if os.path.isfile(candidate):
        return candidate

    # 3) Current working directory
    candidate = os.path.join(os.getcwd(), "config.json")
    if os.path.isfile(candidate):
        return candidate

    # 4) Give a helpful error
    raise FileNotFoundError(
        "No config.json found. Specify with --config, set SNFC_CONFIG, or place a config.json in the project root."
    )


def load_plugins() -> Dict[str, BasePostingAction]:
    """Dynamically import plugin classes and return a map of pluginName -> instance."""
    sys.path.append(SCRIPT_PATH)
    sys.path.append(PLUGINS_PATH)

    plugin_instances: Dict[str, BasePostingAction] = {}
    plugin_files: List[str] = glob.glob(os.path.join(PLUGINS_PATH, "*.py"))

    for file_path in plugin_files:
        module_name = os.path.splitext(os.path.basename(file_path))[0]
        if module_name.startswith("__"):
            continue
        try:
            mod = __import__(module_name)
            cls = getattr(mod, module_name)
            instance = cls()
            name = getattr(instance, 'pluginName', None) or getattr(cls, 'pluginName', None) or module_name
            plugin_instances[name] = instance
        except Exception:
            print(f"Failed to load plugin module '{module_name}':\n{traceback.format_exc()}")

    return plugin_instances


def is_plugin_enabled(config: Dict, plugin_obj: BasePostingAction) -> bool:
    """Check configSection.enabled for a plugin, defaulting to True if missing."""
    try:
        section_name = getattr(plugin_obj, 'configSection', '')
        section = config.get(section_name, {}) if section_name else {}
        return bool(section.get('enabled', True))
    except Exception:
        return True


def resolve_host_url(config: Dict, host_name: str) -> str:
    for host in config.get("hosts", []):
        if host.get("name") == host_name:
            return host.get("image", "")
    return ""


def resolve_location_url(config: Dict, location_name: str) -> str:
    for loc in config.get("locations", []):
        if loc.get("name") == location_name:
            return loc.get("link", "")
    return ""

def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Run SNFC posting plugins locally using JSON config (test tool)",
    )
    parser.add_argument(
        "--config",
        help="Path to config.json (overrides SNFC_CONFIG env and defaults)",
    )
    parser.add_argument("--plugin", action="append", default=[], help="Plugin name(s) to run (match by pluginName). If omitted, runs all.")
    parser.add_argument("--film", default="Ignore this Posting: The Alan Smithee Story")
    parser.add_argument("--film-url", dest="film_url", default="https://en.wikipedia.org/wiki/Alan_Smithee")
    parser.add_argument("--host", default="")
    parser.add_argument("--location", default="")
    parser.add_argument("--wearing", default="a nametag")
    parser.add_argument("--time", dest="show_time", default="7:00pm")
    parser.add_argument("--synopsis", default="This is a test post, ignore it.")

    args = parser.parse_args(argv)

    # Load config
    config_path = args.config or find_default_config_path()
    config = load_config(config_path)

    # Choose host/location (use first in config if not provided), guarding for empty lists
    hosts_list = config.get("hosts") or []
    locations_list = config.get("locations") or []

    host_name = args.host or (hosts_list[0].get("name", "") if hosts_list else "")
    location_name = args.location or (locations_list[0].get("name", "") if locations_list else "")

    host_url = resolve_host_url(config, host_name)
    location_url = resolve_location_url(config, location_name)

    # Build newsletter
    nl = Newsletter(
        config.get("clubCity", ""),
        config.get("clubURL", ""),
        args.film,
        args.film_url,
        host_name,
        host_url,
        location_name,
        location_url,
        args.wearing,
        args.show_time,
        args.synopsis,
    )

    # Load plugins
    plugins = load_plugins()

    if not plugins:
        print("No plugins discovered under 'plugins/'. Nothing to do.")
        return 1

    # Default to enabled plugins if none explicitly requested
    enabled_plugins: Dict[str, BasePostingAction] = { name: pobj for name, pobj in plugins.items() if is_plugin_enabled(config, pobj) }
    selected_plugin_names = args.plugin or list(enabled_plugins.keys())

    print(f"Running plugins: {', '.join(selected_plugin_names)}\n")

    exit_code = 0
    for plugin_name in selected_plugin_names:
        plugin: Optional[BasePostingAction] = plugins.get(plugin_name)
        if not plugin:
            print(f"[SKIP] Plugin not found: {plugin_name}")
            exit_code = 2
            continue
        if not is_plugin_enabled(config, plugin):
            print(f"[SKIP] Plugin disabled in config: {plugin_name}")
            continue
        try:
            result = plugin.execute(config, nl)
            print(f"[OK] {plugin_name}: {result if result is not None else ''}\n")
        except Exception as e:
            print(f"[ERROR] {plugin_name}: {e}\n{traceback.format_exc()}\n")
            exit_code = 3

    return exit_code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))


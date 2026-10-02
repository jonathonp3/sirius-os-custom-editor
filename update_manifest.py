import json
import os
import glob
from collections import OrderedDict

# --- CONFIGURATION ---
STABLE_MANIFEST = "org.gnome.TextEditor.json"
DEFAULT_THEME_ID = "solarized-light-cosmic-latte"
THEMES_DIR = "themes"

# Glob the themes directory, sorted for determinism
THEME_FILES = sorted(glob.glob(os.path.join(THEMES_DIR, "*.xml")))

def update_manifest(filename, app_id, branch_name):
    if not os.path.exists(filename):
        print(f" -> Error: {filename} not found.")
        return

    if not THEME_FILES:
        print(f" -> Error: no .xml files found in {THEMES_DIR}/")
        return

    with open(filename, 'r') as f:
        data = json.load(f)

    print(f"Injecting {len(THEME_FILES)} themes and finish-args into {filename}...")

    # 1. Update finish-args for default theme
    if 'finish-args' not in data:
        data['finish-args'] = []

    data['finish-args'] = [
        arg for arg in data['finish-args']
        if "GTK_SOURCE_STYLE_SCHEME" not in arg
    ]
    data['finish-args'].append(f"--env=GTK_SOURCE_STYLE_SCHEME={DEFAULT_THEME_ID}")

    # 2. Create Custom Style Module
    #
    # Sources reference themes/ (relative to the manifest, where
    # flatpak-builder fetches them from).
    #
    # Build commands reference the *basename* only. flatpak-builder
    # stages each source into the build directory using its basename,
    # so inside the build dir the file is `foo.xml`, not
    # `themes/foo.xml`.
    new_module = {
        "name": "custom-gtksource-styles",
        "buildsystem": "simple",
        "build-commands": ["mkdir -p /app/share/gtksourceview-5/styles"],
        "sources": [{"type": "file", "path": t} for t in THEME_FILES]
    }

    for theme in THEME_FILES:
        basename = os.path.basename(theme)
        new_module["build-commands"].append(
            f"install -Dm644 {basename} /app/share/gtksourceview-5/styles/{basename}"
        )

    modules = [m for m in data.get('modules', []) if m['name'] != "custom-gtksource-styles"]
    modules.insert(0, new_module)
    data['modules'] = modules

    # 3. RE-ORDER KEYS: Force branch under command, REMOVE name
    new_data = OrderedDict()
    new_data["app-id"] = app_id

    for key, value in data.items():
        if key in ["app-id", "branch", "name", "id"]:
            continue

        new_data[key] = value

        if key == "command":
            new_data["branch"] = branch_name

    # 4. Save the final file
    with open(filename, 'w') as f:
        json.dump(new_data, f, indent=2)

    print(f"Success! {filename} updated with {len(THEME_FILES)} themes.")

if __name__ == "__main__":
    update_manifest(STABLE_MANIFEST, "org.gnome.TextEditor", "stable")

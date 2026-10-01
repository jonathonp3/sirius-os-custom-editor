# Sirius-OS Custom Editor

Custom Flatpak build for GNOME Text Editor with 12+ premium themes and critical patches.

## 🎨 Themes Included
* Deep Oceanic (Default)
* Andromeda
* Ant
* Dracula
* Kimi
* Nord
* Solarized (Multiple variants)
* Space KDE
* Sweet

### 🚀 Quick Links
- **Download Installer:** [Latest Build Releases](https://github.com/jonathonp3/gnome-text-editor-custom/releases/tag/latest-build)

### 🔗 Upstream Sources
*   **Stable Manifest Source:** [Flathub - org.gnome.TextEditor](https://github.com/flathub/org.gnome.TextEditor)


## 📥 Getting Started

1. Add flathub:
```bash
flatpak remote-add --user --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
```

2. Remove the stock Fedora Flatpak:
```bash
flatpak uninstall --system -y org.gnome.TextEditor
```

3. Add the Sirius-OS Custom Editor remote

Download the public GPG key:
```bash
wget2 -q -O /tmp/sirius-os-custom-editor.gpg https://raw.githubusercontent.com/jonathonp3/sirius-os-custom-editor/main/sirius-os-custom-editor.gpg
```

4. Add the remote and import the key:
```bash
flatpak remote-add --system --if-not-exists --gpg-import=/tmp/sirius-os-custom-editor.gpg sirius-os-custom-editor https://jonathonp3.github.io/sirius-os-custom-editor/
```

5. Install Wolf-OS Custom Text Editor:
```bash
flatpak install --system -y sirius-os-custom-editor org.gnome.TextEditor
```

6. Clean up:
```bash
rm /tmp/sirius-os-custom-editor.gpg
```

Optional:
List remotes:
```bash
flatpak remotes --show-details
```

List sirius-os-custom-editor
```bash
flatpak remote-ls sirius-os-custom-editor
```

## How to build
Clone the repository:
```bash
git clone git@github.com:jonathonp3/wolf-oss-apps.git
cd wolf-oss-apps
```
Set up remotes:
```bash
flatpak remote-add --user --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
```
Run the theme injector:
```bash
python3 update_manifest.py
```

## Build Instructions
Stable Version (v50)

1. Install SDK:
```bash
flatpak install --user -y flathub org.gnome.Sdk//50 org.gnome.Platform//50
```
2. Build:
```bash
flatpak run org.flatpak.Builder --force-clean --ccache --disable-rofiles-fuse --repo=repo-stable build-dir-stable org.gnome.TextEditor.json
```
3. Bundle & Install:
```bash
flatpak build-bundle repo-stable gnome-text-editor-stable.flatpak org.gnome.TextEditor stable
flatpak install --user --reinstall gnome-text-editor-stable.flatpak
```

## 🛠️ Modifying Themes

If you add or remove an .xml theme file:

1. Sync Manifest:
```bash
python3 update_manifest.py
```
2. Clean Cache: 
```bash
rm -rf build-dir-stable repo-stable .flatpak-builder
```
3. Rebuild: Run the Build, Bundle, and Install commands above.



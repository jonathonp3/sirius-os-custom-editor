# Upgrading to the Next GNOME Release

This guide covers upgrading the custom editor from one GNOME runtime
branch to the next — for example, GNOME 51 → 52. The process touches
three files and one CI run. No script changes are required on the
client side: the first-boot installer resolves the runtime branch from
the remote's metadata at runtime.

## Overview

| Step | What | Where |
|---|---|---|
| 1 | Refresh the manifest from Flathub | `org.gnome.TextEditor.json` |
| 2 | Re-inject custom themes | `update_manifest.py` (run locally) |
| 3 | Bump the CI runtime install | `.github/workflows/build.yml` |
| 4 | Bump the CI build image | `.github/workflows/build.yml` |
| 5 | Update the README | `README.md` |
| 6 | Commit and push | git |
| 7 | Verify the remote | `flatpak remote-info` |
| 8 | Update clients | `flatpak update` |

Steps 1–5 are local edits. Step 6 triggers CI. Steps 7–8 are
verification and client-side rollout.

## Prerequisites

- Push access to `jonathonp3/sirius-os-custom-editor`
- The GPG private key is already in the repo's CI secrets as
  `GPG_PRIVATE_KEY`. **Do not rotate or regenerate it** — existing
  clients imported the matching public key on first install, and a new
  key would break their updates.
- A local checkout of the repo
- `python3` available locally (for `update_manifest.py`)
- Optionally, a test Silverblue VM for validating the build before
  clients see it

## Step 1 — Refresh the manifest from Flathub

Flathub maintains the canonical manifest for GNOME Text Editor. Pull
the latest:

```bash
cd ~/sirius-os-custom-editor
curl -L https://raw.githubusercontent.com/flathub/org.gnome.TextEditor/master/org.gnome.TextEditor.json \
    -o org.gnome.TextEditor.json
```

Check what runtime branch the fresh manifest targets:

```bash
grep runtime-version org.gnome.TextEditor.json
```

Two outcomes:

- **It says the new branch** (e.g. `"runtime-version": "52"`) — good.
  Flathub has already migrated. Skip to Step 2.
- **It says the old branch** (e.g. `"runtime-version": "51"`) —
  Flathub hasn't migrated yet. You have two options:
  1. **Wait** for Flathub to migrate. This is the safe option.
     Upstream compatibility is their responsibility, and building
     ahead of them risks a broken build.
  2. **Bump manually** by editing `runtime-version` yourself. Only do
     this if you've confirmed the app source builds against the new
     SDK. See the "Manual runtime bump" section below.

Also check the app source version:

```bash
grep -A5 '"name": "gnome-text-editor"' org.gnome.TextEditor.json | grep url
```

Expected: a URL like
`https://download.gnome.org/sources/gnome-text-editor/52/gnome-text-editor-52.0.tar.xz`

The `-A5` window is deliberate — the `url` line sits several lines
below `"name"`, so a narrow `-A2` window returns nothing.

## Step 2 — Re-inject custom themes

The fresh manifest from Flathub **does not include your customizations**.
It won't have:

- The `GTK_SOURCE_STYLE_SCHEME` finish-arg
- The `custom-gtksource-styles` module with the theme XML files

`update_manifest.py` re-adds both, and preserves the runtime version
the fresh manifest declared. Run it:

```bash
python3 update_manifest.py
```

Expected output:

```
Injecting 24 themes and finish-args into org.gnome.TextEditor.json...
Success! org.gnome.TextEditor.json updated with 24 themes.
```

Verify the result:

```bash
# Runtime version should still be the new branch
grep runtime-version org.gnome.TextEditor.json

# Should be "app-id", not "id"
grep '"app-id"' org.gnome.TextEditor.json

# Should be present
grep '"branch"' org.gnome.TextEditor.json

# Should be the last finish-arg
grep GTK_SOURCE_STYLE_SCHEME org.gnome.TextEditor.json

# Should be the first module
grep -A1 '"modules"' org.gnome.TextEditor.json

# App source version
grep 'gnome-text-editor-5' org.gnome.TextEditor.json | grep url
```

All six checks should look right. JSON validity too:

```bash
python3 -c "import json; json.load(open('org.gnome.TextEditor.json')); print('OK')"
```

## Step 3 — Bump the CI runtime install

In `.github/workflows/build.yml`, find the line that installs the SDK
and Platform:

```yaml
flatpak install --user -y flathub org.gnome.Sdk//51 org.gnome.Platform//51
```

Change both `//51` to `//52`:

```yaml
flatpak install --user -y flathub org.gnome.Sdk//52 org.gnome.Platform//52
```

Or with `sed`:

```bash
sed -i 's|org.gnome.Sdk//51 org.gnome.Platform//51|org.gnome.Sdk//52 org.gnome.Platform//52|' \
    .github/workflows/build.yml
```

Verify:

```bash
grep 'flatpak install' .github/workflows/build.yml
```

## Step 4 — Bump the CI build image

The workflow uses a Flathub-maintained Docker image that provides
`flatpak-builder` and the tooling:

```yaml
image: ghcr.io/flathub-infra/flatpak-github-actions:gnome-51
```

Change `gnome-51` to `gnome-52`:

```yaml
image: ghcr.io/flathub-infra/flatpak-github-actions:gnome-52
```

Check the tag exists first at
<https://github.com/flathub-infra/flatpak-github-actions/pkgs/container/flatpak-github-actions>.

If `gnome-52` isn't available yet, you can:

- Use `gnome-51` (or whatever the newest tag is). The container's
  GNOME version doesn't determine the app's runtime — the SDK and
  Platform are installed inside the container from Flathub.
- Wait for Flathub to publish the new image.

`sed` one-liner:

```bash
sed -i 's|flatpak-github-actions:gnome-51|flatpak-github-actions:gnome-52|' \
    .github/workflows/build.yml
```

## Step 5 — Update the README

If `README.md` mentions the runtime version in its build instructions,
bump those references. Typical spots:

- "Stable Version (v51)" heading
- `flatpak install --user -y flathub org.gnome.Sdk//51 org.gnome.Platform//51`
- Any other `//51` references

```bash
grep -n '51' README.md
```

Fix any stale references. The runtime install command in the build
instructions should match Step 3.

## Step 6 — Commit and push

```bash
git status
```

Expected changes:

```
modified:   .github/workflows/build.yml
modified:   README.md
modified:   org.gnome.TextEditor.json
```

Add and commit:

```bash
git add .github/workflows/build.yml README.md org.gnome.TextEditor.json
git commit -m "Upgrade to GNOME 52 runtime"
git push
```

The push triggers the CI workflow in `.github/workflows/build.yml`.
Watch the Actions tab.

## Step 7 — Verify the remote

CI takes 5–15 minutes on a cold run (image pull + SDK download +
build). The workflow:

1. Pulls the `gnome-52` Docker image
2. Imports the GPG key
3. Installs `org.gnome.Sdk//52` and `org.gnome.Platform//52`
4. Runs `update_manifest.py`
5. Builds TextEditor with `flatpak-builder`, signed with
   `EF66A791A288334155EE9BC63101D7D21F19C0E2`
6. Updates and signs the repo metadata
7. Publishes the bundle to the `latest-build` release tag
8. Deploys to GitHub Pages

After CI succeeds, wait 1–2 minutes for GitHub Pages to propagate,
then from a client:

```bash
flatpak update --appstream
flatpak remote-info --system sirius-os-custom-editor org.gnome.TextEditor | grep -i runtime
```

Expected:

```
Runtime: org.gnome.Platform/x86_64/52
```

If it still says `51`, either:

- GitHub Pages hasn't propagated yet — wait and retry
- The deploy step failed — check the Actions tab
- Your local metadata cache is stale — `flatpak update --appstream` again

## Step 8 — Update clients

### Already-migrated systems

On a system that has already run the first-boot script, the flag file
`/etc/sirius-os/firstboot-done` prevents re-execution. Upgrade via
`flatpak` directly:

```bash
# Refresh metadata
flatpak update --appstream

# Update TextEditor
sudo flatpak update -y org.gnome.TextEditor

# Verify
flatpak info --show-origin org.gnome.TextEditor
flatpak info org.gnome.TextEditor | grep -i runtime

# Sweep the old runtime branch if now unused
sudo flatpak uninstall --system -y --unused
```

Expected:

- Origin: `sirius-os-custom-editor`
- Runtime: `org.gnome.Platform/x86_64/52`
- Old branch gone after `--unused`

Note: the old branch may survive `--unused` if other apps still declare
it as their runtime. That's normal — see "Coexisting branches" below.

### Fresh installs

On a fresh Silverblue (or any system where the first-boot script hasn't
run), the next boot of the script automatically:

1. Resolves the runtime branch from the custom remote
   (`flatpak remote-info` → `Runtime: .../52`)
2. Installs `org.gnome.Platform//52` and its Locale from Flathub
3. Installs TextEditor from `sirius-os-custom-editor`

No client-side edits required. The script is version-agnostic by
design; the only thing that changed is what the remote advertises.

## Manual runtime bump

If Flathub hasn't migrated the manifest yet and you want to build
ahead of them:

1. Follow Step 1 to refresh.
2. Edit `runtime-version` in `org.gnome.TextEditor.json`:

   ```diff
   -  "runtime-version": "51",
   +  "runtime-version": "52",
   ```

3. Update the app source URL and SHA256 to the new release:

   ```diff
   -      "url": "https://download.gnome.org/sources/gnome-text-editor/51/gnome-text-editor-51.0.tar.xz",
   -      "sha256": "2b76e6da1506346c54b36ba1a3aeedcd28f4cb7d6a8793d217f209456c92dd4c",
   +      "url": "https://download.gnome.org/sources/gnome-text-editor/52/gnome-text-editor-52.0.tar.xz",
   +      "sha256": "<new sha256>",
   ```

   To get the SHA256:

   ```bash
   curl -L https://download.gnome.org/sources/gnome-text-editor/52/gnome-text-editor-52.0.tar.xz \
       | sha256sum
   ```

4. Run `python3 update_manifest.py` to re-inject themes.

5. Proceed with Steps 3–8.

**Caveat:** if the app source hasn't been adapted to the new SDK yet,
the build will fail. Look for missing API errors in the CI log's
`flatpak-builder` step. If that happens, revert to the previous runtime
and wait for Flathub.

## Coexisting runtime branches

It is normal to have two `org.gnome.Platform` branches installed at
once during and after a GNOME transition:

- The custom TextEditor may require `//52`
- Some Flathub apps may still require `//51` until Flathub rebuilds
  them against the new SDK

Each branch costs roughly 400 MB (Platform) + 100 MB (Locale). Flatpak
keeps a branch installed as long as any app declares it as its runtime.
Once the last app migrates, `flatpak uninstall --unused` sweeps the old
branch.

You can see what's holding a branch:

```bash
flatpak list --system --app --columns=application | while read -r app; do
    rt=$(flatpak info --system "$app" 2>/dev/null \
         | awk -F': *' '/^ *Runtime:/ {print $2}')
    echo "$rt -> $app"
done | sort
```

Nothing needs to be done about coexistence. It resolves on its own.

## Troubleshooting

### CI build fails at `flatpak-builder`

The `flatpak-builder` step exits non-zero, or the log shows meson
errors. Causes:

- The app source hasn't been adapted to the new SDK. Revert the runtime
  version and wait for Flathub.
- The `gnome-52` Docker image doesn't exist yet. Check the registry
  and fall back to a known-good tag.
- A dependency in the manifest needs updating. Check the Flathub
  manifest for changes (Step 1 pulls the latest, so this is unlikely
  unless you edited the manifest manually).

### CI build fails at `gpg --batch --import`

The `GPG_PRIVATE_KEY` secret is malformed, or the key was rotated.
Never rotate the key. If it's truly lost, every client must re-import
the new public key, which means re-running the first-boot script on
each system.

### `flatpak remote-info` still shows the old runtime after CI

GitHub Pages propagation lag, or the deploy step failed. Check the
Actions tab. If the deploy succeeded, retry `flatpak update --appstream`
after a minute.

### Client update fails with "public key not found"

The remote's GPG key on the client doesn't match the one signing the
repo. This happens if:

- The key was rotated (don't)
- The client imported the wrong key
- The remote was re-added without `--gpg-import`

Fix on the client:

```bash
sudo flatpak remote-modify --system --gpg-import=/path/to/key.gpg sirius-os-custom-editor
```

The first-boot script handles this correctly for fresh installs.

### `flatpak uninstall --unused` says "Nothing unused to uninstall" but the old branch is present

Something still depends on it. See "Coexisting runtime branches" above.
Check what:

```bash
flatpak list --system --app --columns=application | while read -r app; do
    rt=$(flatpak info --system "$app" 2>/dev/null \
         | awk -F': *' '/^ *Runtime:/ {print $2}')
    [[ "$rt" == *"/51"* ]] && echo "$app -> $rt"
done
```

Each listed app is holding the branch. They'll migrate when Flathub
rebuilds them.

## Checklist

Copy-paste, edit versions:

- [ ] `curl` latest Flathub manifest
- [ ] `grep runtime-version` → new branch
- [ ] `python3 update_manifest.py`
- [ ] Verify manifest keys (`app-id`, `branch`, `GTK_SOURCE_STYLE_SCHEME`, modules)
- [ ] `sed` CI: `org.gnome.Sdk//51 org.gnome.Platform//51` → `//52`
- [ ] `sed` CI: `flatpak-github-actions:gnome-51` → `gnome-52`
- [ ] Update `README.md` build instructions
- [ ] `git add` the three files, commit, push
- [ ] Watch CI to completion
- [ ] `flatpak update --appstream && flatpak remote-info ... | grep -i runtime`
- [ ] Client: `sudo flatpak update -y org.gnome.TextEditor`
- [ ] Client: `sudo flatpak uninstall --system -y --unused`

## What stays the same

- **The GPG key.** Same key, same signature chain.
- **The app ID.** `org.gnome.TextEditor` — clients upgrade in place.
- **The remote URL.** `https://jonathonp3.github.io/sirius-os-custom-editor/`
- **The client first-boot script.** No changes — it resolves the
  runtime branch dynamically.
- **The themes.** `update_manifest.py` re-injects them after every
  upstream refresh.

## What changes

- The runtime branch number (`51` → `52`)
- The SDK/Platform install line in CI
- The Flathub Docker image tag
- The app source version (via the refreshed Flathub manifest)
- The repo metadata (signed and published by CI)

That's it. Three files, one push, one CI run, and every client —
fresh and already-migrated — converges on the new runtime.

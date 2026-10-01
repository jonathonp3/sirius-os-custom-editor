# Notes

## Refresh the upstream manifest from Flathub

The `org.gnome.TextEditor.json` file is a copy of the Flathub manifest.
Occasionally Flathub updates it — dependency versions, build options,
runtime changes. To pick up those updates:

```bash
curl -L https://raw.githubusercontent.com/flathub/org.gnome.TextEditor/master/org.gnome.TextEditor.json -o org.gnome.TextEditor.json
python3 update_manifest.py
```

The `curl` fetches the latest upstream manifest. The `update_manifest.py`
step re-injects the custom themes and the `GTK_SOURCE_STYLE_SCHEME`
finish-arg, since the fresh manifest won't have them.

from pathlib import Path
from typing import Dict, Any, Union, Optional


def harvest_stop_files(root: Union[str, Path]) -> Dict[str, Any]:
    """
    Traverse a directory tree laid out as:

        root/
          ├─ <scenario>/
          │    ├─ reason/
          │    │    ├─ <try1>/
          │    │    │    └─ …  files  …
          │    │    └─ <tryN>/
          │    └─ no_reason/
          │         ├─ <try1>/
          │         └─ <tryN>/
          └─ …

    For every <try*> directory, read the contents of all files whose
    **file‑name** (not path) contains “stop” (case‑insensitive).

    Returns
    -------
    Dict[str, Any]
        {
          "<scenario>": {
              "reason": {
                  "<try>": {
                      "<stop‑file‑name>": "file‑content",
                      ...
                  } | None,
                  ...
              },
              "no_reason": {
                  ...
              }
          },
          ...
        }
        • If a try‑folder contains *no* stop file, that try’s value is `None`.
        • If there are several stop files, each filename becomes a key.
    """
    root = Path(root).expanduser().resolve()
    architecture: Dict[str, Any] = {}

    for scenario_dir in (p for p in root.iterdir() if p.is_dir()):
        scenario = scenario_dir.name
        architecture[scenario] = {}

        for branch in ("reason", "no_reason"):
            branch_dir = scenario_dir / branch
            if not branch_dir.is_dir():
                # Accept missing “reason” / “no_reason” folders silently
                continue

            architecture[scenario][branch] = {}
            for try_dir in (p for p in branch_dir.iterdir() if p.is_dir()):
                try_name = try_dir.name
                stop_files = [
                    f for f in try_dir.rglob("*")
                    if f.is_file() and "stop" in f.name.lower()
                ]

                if not stop_files:
                    architecture[scenario][branch][try_name] = None
                    continue

                # Read every matching file (could be one or many)
                contents: Dict[str, Optional[str]] = {}
                for file_path in stop_files:
                    try:
                        contents[file_path.name] = file_path.read_text(
                            encoding="utf‑8", errors="replace"
                        )
                    except Exception as err:
                        # Keep the key so the caller knows the file existed
                        contents[file_path.name] = f"<<error reading file: {err}>>"

                architecture[scenario][branch][try_name] = contents

    return architecture


if __name__ == "__main__":
    # Example usage — replace with your real root folder
    import json, pprint, sys

    root_dir = sys.argv[1] if len(sys.argv) > 1 else "/path/to/root"
    data = harvest_stop_files(root_dir)
    with open("stop_reson.json","w") as f:
        f.write(json.dumps(data,indent=2))

    # Pretty‑print to stdout
    pprint.pprint(data, compact=True, sort_dicts=False)

    # …or dump to JSON if you prefer:
    # print(json.dumps(data, indent=2, ensure_ascii=False))

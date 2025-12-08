import json
import yaml
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

CALIBRATIONS_PATH = BASE_DIR / "data/calibrations.json"
HARDWARE_PATH = BASE_DIR / "data/hardware.yaml"


class Params:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.data = self._load()

    # --------------------
    # LOADING / SAVING
    # --------------------
    def _load(self):
        suffix = self.path.suffix.lower()
        with open(self.path) as f:
            if suffix == ".json":
                return json.load(f)
            elif suffix in (".yaml", ".yml"):
                return yaml.safe_load(f)
            else:
                raise ValueError(f"Unsupported file type: {suffix}")

    def _save(self):
        suffix = self.path.suffix.lower()
        with open(self.path, "w") as f:
            if suffix == ".json":
                json.dump(self.data, f, indent=4)
            elif suffix in (".yaml", ".yml"):
                yaml.safe_dump(self.data, f, sort_keys=False)
            else:
                raise ValueError(f"Unsupported file type: {suffix}")

    # --------------------
    # ACCESSORS
    # --------------------
    def get(self, path, default=None):
        keys = path.split("/")
        cur = self.data

        for k in keys:
            if isinstance(cur, dict) and k in cur:
                cur = cur[k]
            else:
                if default is not None:
                    return default
                raise KeyError(f"Key not found: '{k}' in '{path}'")
        return cur

    def set(self, path, value):
        keys = path.split("/")
        cur = self.data

        # navigate to parent
        for k in keys[:-1]:
            if k not in cur:
                raise KeyError(
                    f"Missing parent key '{k}' while accessing '{path}'"
                )
            if not isinstance(cur[k], dict):
                raise KeyError(
                    f"Cannot descend into non-dict key '{k}' in '{path}'"
                )
            cur = cur[k]

        final_key = keys[-1]
        if final_key not in cur:
            raise KeyError(
                f"Final key '{final_key}' does not exist in '{path}'"
            )

        # update and save
        cur[final_key] = value
        self._save()
        print(f"Updated '{path}' → {value}")

    # Pythonic access
    def __getitem__(self, path):
        return self.get(path)

    def __setitem__(self, path, value):
        self.set(path, value)


# --------------------
# USAGE EXAMPLE
# --------------------
if __name__ == "__main__":
    hardware = Params(HARDWARE_PATH)
    calibrations = Params(CALIBRATIONS_PATH)

    # Pretty print hardware
    from pprint import pprint
    pprint(hardware.data)

    # Example updates:
    # hardware["q10/qubit/qubit_LO"] = 4.5e9
    # print(hardware["q10/qubit/qubit_LO"])
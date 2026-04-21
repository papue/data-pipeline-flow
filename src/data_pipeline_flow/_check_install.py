"""Runtime check for the Graphviz dot binary."""
import shutil
import warnings
from pathlib import Path

_WINDOWS_CANDIDATES = [
    Path("C:/Program Files/Graphviz/bin/dot.exe"),
    Path("C:/Program Files (x86)/Graphviz/bin/dot.exe"),
]


def check_graphviz() -> bool:
    """Return True if the Graphviz dot binary is available."""
    if shutil.which("dot"):
        return True
    return any(p.exists() for p in _WINDOWS_CANDIDATES)


def warn_if_missing() -> None:
    """Emit a RuntimeWarning if Graphviz dot is not found."""
    if not check_graphviz():
        warnings.warn(
            "Graphviz not found — image export (render-image) won't work. "
            "Install Graphviz from https://graphviz.org and ensure 'dot' is on PATH.",
            RuntimeWarning,
            stacklevel=2,
        )

# Installation

Install `stanag4607` in a virtual environment with Python 3.10 or newer. The
protocol core requires no third-party Python runtime packages.

## Install from the source checkout

Install from the source repository:

```console
git clone https://github.com/trane293/stanag4607.git
cd stanag4607
python -m venv .venv
source .venv/bin/activate
python -m pip install .
stanag4607 --help
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1`. The source
checkout includes the small, redistributable fixtures used in the
[quickstart](QUICKSTART.md).

For an installation without the repository fixtures or examples, use
`python -m pip install stanag4607` once the distribution is available on PyPI.

## Develop or build the docs

From the repository root, install the appropriate optional dependencies:

```console
python -m pip install -e '.[dev,docs]'
mkdocs build --strict
```

For project tests and contribution rules, see the
[development method](DEVELOPMENT.md) and
[contribution guide](https://github.com/trane293/stanag4607/blob/main/CONTRIBUTING.md).

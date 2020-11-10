# MTX Streamlit App

TODO

## Objective

TODO

## Installation

```bash
git clone https://github.com/flight505/mtx_app.git
cd mtx_app
```

### Conda Virtual Environment

You will need to install [Anaconda](https://www.anaconda.com/) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html)
to follow this section.

Install your virtual environment then activate it :

```bash
conda create -n mtx_app python=3.7 pip pip-tools
```

and activate it :

```bash
conda activate mtx_app
```

### Virtual Environment

Install your virtual environment :

```bash
python -m venv .venv
```

and activate it :

```bash
# Use this if you use a Windows Command prompt on Windows
cd .venv/Scripts
activate.bat
cd ..
# Use this if you use a Git Bash on Windows
source .venv/Scripts/activate
# Use this on Linux
source .venv/bin/activate
```

### Install the requirements

Ensure you are in your activated environment before running the following steps.

Install the project :

```bash
pip install -r requirements.txt
pip install .
```

You should be able to access the `src` package from any Streamlit script and Jupyter notebook now !

## Run the app

```bash
streamlit run app.py
```

## Contribute

Install the project in editable mode with dev dependencies:

```bash
pip install -r requirements.txt
pip install -r dev-requirements.txt 
pip install -e .
```

### Recompile dependencies versions

We use [pip-tools](https://github.com/jazzband/pip-tools) to pin dependencies versions.
The necessary libraries are listed in `requirements.in` and `dev-requirements.in` and are 
the source for `requirements.txt` / `dev-requirements.txt` through `pip-compile`.
You can regenerate the requirements files by using the following commands :

```bash
pip install pip-tools
pip-compile requirements.in
pip-compile dev-requirements.in
```

Feel free to add libraries to the `.in` files and regenerate `.txt` files !

**PS :** don't try to use `pip-sync` if running in a conda environment, won't work because of conda deps.

### Format Python code

```bash
reorder_python_imports app.py
black src/
black app.py
```

## Project organization

    ├── README.md          <- The top-level README for developers using this project.
    ├── data               <- Folder to store data.
    │
    ├── references         <- Data dictionaries, manuals, and all other explanatory materials.
    │
    ├── dev-requirements.in    <- The source of dev-requirements file to compile
    ├── dev-requirements.txt   <- The requirements file for reproducing the dev environment
    │
    ├── requirements.in    <- The source requirements file to compile
    ├── requirements.txt   <- The requirements file for reproducing the production environment
    │
    └── src                <- Source code for use in this project.
        ├── __init__.py    <- Makes src a Python module
        |
        ├── dataset.py          <- Scripts to download or generate data
        └── diagnostics.py      <- Code for each diagnostic
       
Freely adapted from [cookiecutter-datascience directory structure](https://drivendata.github.io/cookiecutter-data-science/#directory-structure)
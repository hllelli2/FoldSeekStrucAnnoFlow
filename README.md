# FoldSeek Annotation Pipeline


## Overview

The FoldSeek Annotation Pipeline is currently derived from the UCLOrengoGroup's domain-annotation pipeline, which is available at [https://github.com/UCLOrengoGroup/domain-annotation-pipeline]. This pipeline calls upon their tools to split protein models into domains and annotate them with CATH classifications. To make it runnable on our cluster, we have made some modifications to the original code. The pipeline is designed to be flexible and can be adapted to use more foldseek databases to look against. The pipeline also works on SLURM clusters and allows CIF files to be processed alongside PDBs.


### Running the pipeline

Make sure to install go the development setup instructions below before running the pipeline. You'll need to get up to 
```bash
nox -s install 
```

This will install all workflows needed are installed. You'll need to have nexflow installed to run the pipeline, which you can do with the following command:

```bash
curl -fsSL get.nextflow.io | bash
```



### Development setup

To set up the development environment for the FoldSeek Annotation Pipeline, follow the instructions below. This setup will ensure you have all the necessary tools and dependencies to work on the project effectively.

Prerequisites:
- pipx

1. Install pipx if you haven't already. You can find instructions [here](https://pipxproject.github.io/pipx/installation/).

2. Use pipx to install nox, uv (Universal Versioner), and pre-commit:
Note: The `[pbs]` extra for nox includes additional plugins, allowing it to download Python.

```bash
pipx install nox[pbs] uv pre-commit
```

3. Now, we can use nox to set up our development environment. Run the following commands in your terminal:

```bash
 nox -s install 
```

This command will create a virtual environment and install all the development dependencies specified in the `pyproject.toml` file. Populate the pyproject.toml file with your desired dependencies before running this command. *Note: You can run this command multiple times to ensure all dependencies are installed correctly.*

```bash

nox -s chores 
```

This command will run various code quality and formatting tools to ensure your code adheres to best practices.

```bash
 nox -s tests 
```

This command will run the test suite to ensure everything is working as expected.

```bash
 nox -s lock 
```

This command will update the lock files for your dependencies to ensure you have the latest compatible versions.


4. (Optional) (But recommended) Set up pre-commit hooks to automatically run code quality checks before each commit:

```bash
 pre-commit install 
```

This command will install the pre-commit hooks defined in the `.pre-commit-config.yaml` file. This helps maintain code quality by running checks before each commit.


   




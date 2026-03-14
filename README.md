# Claude Playground

A playground for experimenting with Claude.

## MPI Bandwidth Plotting

### Setup

```bash
conda env create -f environment.yml
conda activate claude-playground
```

### Usage

```bash
python plot.py
```

Optionally specify a custom config file:

```bash
python plot.py --config path/to/config.yml
```

### Config Format

`config.yml` controls which datasets are plotted:

```yaml
datasets:
  - file: data.txt      # path to data file
    label: data.txt     # legend label (optional, defaults to filename)
output: bandwidth_plot.png   # output image path
title: "MPI Bandwidth vs. Message Size"
```

Each data file should be whitespace-delimited with `#` comment lines, containing columns for message size (bytes) and bandwidth (MB/s), as produced by OSU MPI benchmarks.

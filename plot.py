import argparse
import yaml
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


def main():
    parser = argparse.ArgumentParser(description="Plot MPI bandwidth data")
    parser.add_argument("--config", default="config.yml", help="Path to config file")
    args = parser.parse_args()

    with open(args.config) as f:
        config = yaml.safe_load(f)

    fig, ax = plt.subplots(figsize=(10, 6))

    for dataset in config["datasets"]:
        file = dataset["file"]
        label = dataset.get("label", file)
        df = pd.read_csv(file, sep=r'\s+', comment='#', names=['size', 'bandwidth'])
        sns.lineplot(data=df, x='size', y='bandwidth', label=label, ax=ax)

    ax.set_xscale('log', base=2)
    ax.set_xlabel("Message Size (Bytes)")
    ax.set_ylabel("Bandwidth (MB/s)")
    ax.set_title(config.get("title", "MPI Bandwidth vs. Message Size"))
    ax.legend()

    output = config.get("output", "bandwidth_plot.png")
    plt.savefig(output, dpi=150, bbox_inches='tight')
    print(f"Saved plot to {output}")


if __name__ == "__main__":
    main()

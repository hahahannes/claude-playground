import argparse
import yaml
import pandas as pd
import matplotlib.pyplot as plt


def main():
    parser = argparse.ArgumentParser(description="Plot MPI bandwidth data")
    parser.add_argument("--config", default="config.yml", help="Path to config file")
    args = parser.parse_args()

    with open(args.config) as f:
        config = yaml.safe_load(f)

    frames = []
    for dataset in config["datasets"]:
        df = pd.read_csv(dataset["file"], sep=r'\s+', comment='#', names=['size', 'bandwidth'])
        frames.append(df)

    combined = pd.concat(frames)
    stats = combined.groupby('size')['bandwidth'].agg(['mean', 'std']).reset_index()

    fig, ax = plt.subplots(figsize=(10, 6))

    # Mean: scatter + line
    ax.plot(stats['size'], stats['mean'], '-o', markersize=5, label='Mean')

    # Std deviation as shaded band
    ax.fill_between(stats['size'], stats['mean'] - stats['std'],
                    stats['mean'] + stats['std'], alpha=0.2, label='Std Dev')

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

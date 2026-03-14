import argparse
import glob
import os
import yaml
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker


def main():
    parser = argparse.ArgumentParser(description="Plot MPI bandwidth data")
    parser.add_argument("--data-dir", required=True, help="Directory containing data files")
    parser.add_argument("--output", default="bandwidth_plot.png", help="Output file path")
    parser.add_argument("--title", default="MPI Bandwidth vs. Message Size", help="Plot title")
    args = parser.parse_args()

    files = sorted(glob.glob(os.path.join(args.data_dir, "*.txt")))
    if not files:
        raise FileNotFoundError(f"No .txt files found in {args.data_dir}")

    frames = []
    for filepath in files:
        df = pd.read_csv(filepath, sep=r'\s+', comment='#', names=['size', 'bandwidth'])
        frames.append(df)

    combined = pd.concat(frames)
    stats = combined.groupby('size')['bandwidth'].agg(['mean', 'std']).reset_index()

    fig, ax = plt.subplots(figsize=(10, 6))

    # Mean: scatter + line
    ax.plot(stats['size'], stats['mean'], '-o', markersize=5, label='Mean')

    # Std deviation as shaded band
    ax.fill_between(stats['size'], stats['mean'] - stats['std'],
                    stats['mean'] + stats['std'], alpha=0.2, label='Std Dev')

    def size_formatter(x, pos):
        if x >= 1024 * 1024:
            return f'{x / (1024 * 1024):.0f} MB'
        elif x >= 1024:
            return f'{x / 1024:.0f} KB'
        else:
            return f'{x:.0f} B'

    ax.set_xscale('log', base=2)
    ax.xaxis.set_major_locator(ticker.FixedLocator(stats['size'].values))
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(size_formatter))
    plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
    ax.set_xlabel("Message Size")
    ax.set_ylabel("Bandwidth (MB/s)")
    ax.set_title(args.title)
    ax.legend()

    plt.savefig(args.output, dpi=150, bbox_inches='tight')
    print(f"Saved plot to {args.output}")


if __name__ == "__main__":
    main()

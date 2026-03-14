import argparse
import glob
import os
import re
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker


def strip_prefix(line):
    """Remove the [rank,id]<stdout>: prefix from OSU log lines."""
    return re.sub(r'^\[.*?\]<stdout>:', '', line)


def load_osu_logs(data_dir, log_name, columns):
    files = sorted(glob.glob(os.path.join(data_dir, '*', log_name)))
    if not files:
        raise FileNotFoundError(f"No {log_name} files found in {data_dir}/*/")

    frames = []
    for filepath in files:
        rows = []
        with open(filepath) as f:
            for line in f:
                cleaned = strip_prefix(line).strip()
                if not cleaned or cleaned.startswith('#'):
                    continue
                parts = cleaned.split()
                if len(parts) >= 2:
                    try:
                        rows.append((int(parts[0]), float(parts[1])))
                    except ValueError:
                        continue
        if rows:
            frames.append(pd.DataFrame(rows, columns=columns))

    return pd.concat(frames)


def main():
    parser = argparse.ArgumentParser(description="Plot MPI latency data")
    parser.add_argument("--data-dir", required=True, help="Directory containing data files")
    parser.add_argument("--output", default="latency_plot.png", help="Output file path")
    parser.add_argument("--title", default="MPI Latency vs. Message Size", help="Plot title")
    args = parser.parse_args()

    combined = load_osu_logs(args.data_dir, 'osu_latency_d2d.log', ['size', 'latency'])
    stats = combined.groupby('size')['latency'].agg(['mean', 'std']).reset_index()

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
    ax.set_ylabel("Avg Latency (us)")
    ax.set_title(args.title)
    ax.legend()

    plt.savefig(args.output, dpi=150, bbox_inches='tight')
    print(f"Saved plot to {args.output}")


if __name__ == "__main__":
    main()

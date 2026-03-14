import argparse
import glob
import json
import os
import re
import yaml
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker


def strip_prefix(line):
    """Remove the [rank,id]<stdout>: prefix from OSU log lines."""
    return re.sub(r'^\[.*?\]<stdout>:', '', line)


def parse_osu_log(filepath):
    """Parse an OSU log file, return list of (size, value) tuples."""
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
    return rows


def match_value(params_val, filter_val):
    """Recursively match a filter value against a params value."""
    if isinstance(filter_val, dict):
        if not isinstance(params_val, dict):
            return False
        return all(match_value(params_val.get(k), v) for k, v in filter_val.items())
    return str(params_val) == str(filter_val)


def find_matching_dirs(data_dir, filter_criteria):
    """Find subdirs whose params.json matches all filter criteria."""
    matching = []
    for subdir in sorted(glob.glob(os.path.join(data_dir, '*'))):
        params_path = os.path.join(subdir, 'params.json')
        if not os.path.isfile(params_path):
            continue
        with open(params_path) as f:
            params = json.load(f)
        if all(match_value(params.get(k), v) for k, v in filter_criteria.items()):
            matching.append(subdir)
    return matching


def load_series_data(dirs, log_name, columns):
    """Load and aggregate data from matching dirs for a given log file."""
    frames = []
    for d in dirs:
        filepath = os.path.join(d, log_name)
        if not os.path.isfile(filepath):
            continue
        rows = parse_osu_log(filepath)
        if rows:
            frames.append(pd.DataFrame(rows, columns=columns))
    if not frames:
        return None
    combined = pd.concat(frames)
    return combined.groupby(columns[0])[columns[1]].agg(['mean', 'std']).reset_index()


def size_formatter(x, pos):
    if x >= 1024 * 1024:
        return f'{x / (1024 * 1024):.0f} MB'
    elif x >= 1024:
        return f'{x / 1024:.0f} KB'
    else:
        return f'{x:.0f} B'


def plot_subplot(ax, series_configs, data_dir, log_name, columns, ylabel, y_scale=1.0):
    """Plot multiple series onto a single axes with a secondary log-scale y-axis."""
    has_data = False
    all_sizes = set()
    plotted_data = []
    for series in series_configs:
        dirs = find_matching_dirs(data_dir, series['filter'])
        if not dirs:
            print(f"  Warning: no matching dirs for '{series['legend']}'")
            continue
        stats = load_series_data(dirs, log_name, columns)
        if stats is None:
            print(f"  Warning: no data in matching dirs for '{series['legend']}'")
            continue
        has_data = True
        stats['mean'] = stats['mean'] * y_scale
        stats['std'] = stats['std'] * y_scale
        all_sizes.update(stats[columns[0]].values)
        line, = ax.plot(stats[columns[0]], stats['mean'], '-o', markersize=4, label=series['legend'])
        ax.fill_between(stats[columns[0]], stats['mean'] - stats['std'],
                        stats['mean'] + stats['std'], alpha=0.15)
        plotted_data.append((stats, line))

    if has_data:
        ax.set_xscale('log', base=2)
        sorted_sizes = sorted(all_sizes)
        ax.xaxis.set_major_locator(ticker.FixedLocator(sorted_sizes))
        ax.xaxis.set_major_formatter(ticker.FuncFormatter(size_formatter))
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        ax.set_xlabel("Message Size")
        ax.set_ylabel(ylabel)
        ax.legend(fontsize=8)

    return has_data, plotted_data


def main():
    parser = argparse.ArgumentParser(description="Plot OSU benchmark data")
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--title", default="")
    parser.add_argument("--config", required=True)
    parser.add_argument("--section", required=True)
    parser.add_argument("--index", required=True, type=int)
    args = parser.parse_args()

    with open(args.config) as f:
        config = yaml.safe_load(f)
    script_config = config['plots'][args.section]['scripts'][args.index]
    series_configs = script_config.get('series', [])

    if not series_configs:
        print("No series defined, nothing to plot.")
        return

    gpu_model = series_configs[0].get('filter', {}).get('NODE_SELECTOR', {}).get('nvidia.com/gpu.product', '')
    suptitle = f"{args.title}\n{gpu_model}" if gpu_model else args.title

    fig, ((ax_bw, ax_bw_log), (ax_lat, ax_lat_log)) = plt.subplots(2, 2, figsize=(16, 10))
    fig.suptitle(suptitle, fontsize=14)

    print(f"Plotting bandwidth...")
    bw_ok, bw_data = plot_subplot(ax_bw, series_configs, args.data_dir,
                         'osu_bw_d2d.log', ['size', 'bandwidth'], 'Bandwidth (GB/s)',
                         y_scale=1.0 / 1024)
    if bw_ok:
        ax_bw.set_title("Bandwidth")
        # Log-scale version
        for stats, line in bw_data:
            ax_bw_log.plot(stats['size'], stats['mean'], '-o', markersize=4,
                           color=line.get_color(), label=line.get_label())
            ax_bw_log.fill_between(stats['size'], stats['mean'] - stats['std'],
                                   stats['mean'] + stats['std'], alpha=0.15,
                                   color=line.get_color())
        ax_bw_log.set_xscale('log', base=2)
        ax_bw_log.set_yscale('log')
        ax_bw_log.xaxis.set_major_formatter(ticker.FuncFormatter(size_formatter))
        plt.setp(ax_bw_log.get_xticklabels(), rotation=45, ha='right')
        ax_bw_log.set_xlabel("Message Size")
        ax_bw_log.set_ylabel("Bandwidth (GB/s)")
        ax_bw_log.set_title("Bandwidth (log scale)")
        ax_bw_log.legend(fontsize=8)

    print(f"Plotting latency...")
    lat_ok, lat_data = plot_subplot(ax_lat, series_configs, args.data_dir,
                          'osu_latency_d2d.log', ['size', 'latency'], 'Avg Latency (us)')
    if lat_ok:
        ax_lat.set_title("Latency")
        # Log-scale version
        for stats, line in lat_data:
            ax_lat_log.plot(stats['size'], stats['mean'], '-o', markersize=4,
                            color=line.get_color(), label=line.get_label())
            ax_lat_log.fill_between(stats['size'], stats['mean'] - stats['std'],
                                    stats['mean'] + stats['std'], alpha=0.15,
                                    color=line.get_color())
        ax_lat_log.set_xscale('log', base=2)
        ax_lat_log.set_yscale('log')
        ax_lat_log.xaxis.set_major_formatter(ticker.FuncFormatter(size_formatter))
        plt.setp(ax_lat_log.get_xticklabels(), rotation=45, ha='right')
        ax_lat_log.set_xlabel("Message Size")
        ax_lat_log.set_ylabel("Avg Latency (us)")
        ax_lat_log.set_title("Latency (log scale)")
        ax_lat_log.legend(fontsize=8)

    plt.tight_layout()
    plt.savefig(args.output, dpi=150, bbox_inches='tight')
    print(f"Saved plot to {args.output}")


if __name__ == "__main__":
    main()

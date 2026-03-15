import argparse
import glob
import json
import os

import pandas as pd
import matplotlib.pyplot as plt
import yaml


def get_gpu_count(params):
    """Extract number of GPUs from CUDA_VISIBLE_DEVICES in params."""
    cuda_devices = params.get("CUDA_VISIBLE_DEVICES", "0")
    return len(cuda_devices.split(","))


def find_latest_version_dir(run_dir):
    """Find the latest lightning_logs/version_N directory."""
    logs_dir = os.path.join(run_dir, "lightning_logs")
    if not os.path.isdir(logs_dir):
        return None
    versions = sorted(glob.glob(os.path.join(logs_dir, "version_*")))
    return versions[-1] if versions else None


def load_events_per_second(metrics_path):
    """Load events_per_second_step from a metrics CSV.

    Returns non-null values as a Series, or None if the column is missing.
    """
    df = pd.read_csv(metrics_path)
    col = "train/events_per_second_step"
    if col not in df.columns:
        return None
    values = df[col].dropna()
    return values if len(values) > 0 else None


def collect_throughput_data(data_dir):
    """Scan all run directories and return a DataFrame with gpu_count and events_per_second."""
    records = []
    for subdir in sorted(glob.glob(os.path.join(data_dir, "*"))):
        params_path = os.path.join(subdir, "params.json")
        if not os.path.isfile(params_path):
            continue
        with open(params_path) as f:
            params = json.load(f)
        gpu_count = get_gpu_count(params)
        version_dir = find_latest_version_dir(subdir)
        if version_dir is None:
            print(f"  Skipping {os.path.basename(subdir)}: no lightning_logs")
            continue
        metrics_path = os.path.join(version_dir, "metrics.csv")
        if not os.path.isfile(metrics_path):
            print(f"  Skipping {os.path.basename(subdir)}: no metrics.csv")
            continue
        values = load_events_per_second(metrics_path)
        if values is None:
            print(f"  Skipping {os.path.basename(subdir)}: no events_per_second_step data")
            continue
        for v in values:
            records.append({"gpu_count": gpu_count, "events_per_second": v})
    return pd.DataFrame(records)


def plot_throughput(df, output_path, title, gpu_model):
    """Create a throughput plot: GPUs vs events/second."""
    stats = df.groupby("gpu_count")["events_per_second"].agg(["mean", "std"]).reset_index()
    stats = stats.sort_values("gpu_count")

    fig, ax = plt.subplots(figsize=(8, 6))

    suptitle = f"{title}\n{gpu_model}" if gpu_model else title
    fig.suptitle(suptitle, fontsize=14)

    ax.bar(
        stats["gpu_count"].astype(str),
        stats["mean"],
        yerr=stats["std"],
        capsize=5,
        color="#4C72B0",
        edgecolor="black",
        alpha=0.85,
    )

    # Annotate bars with mean value
    for _, row in stats.iterrows():
        ax.text(
            str(int(row["gpu_count"])),
            row["mean"] + row["std"] + 0.3,
            f'{row["mean"]:.1f}',
            ha="center",
            va="bottom",
            fontsize=10,
        )

    ax.set_xlabel("Number of GPUs")
    ax.set_ylabel("Events per Second")
    ax.set_ylim(bottom=0)

    # Add ideal scaling line if more than one GPU count
    if len(stats) > 1:
        base = stats.iloc[0]
        ideal_x = stats["gpu_count"].values
        ideal_y = base["mean"] * (ideal_x / base["gpu_count"].item())
        ax.plot(
            [str(int(x)) for x in ideal_x],
            ideal_y,
            "r--",
            marker="^",
            markersize=6,
            label="Ideal linear scaling",
        )
        ax.legend()

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"Saved plot to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Plot training throughput vs GPU count")
    parser.add_argument("--data-dir", required=True, help="Directory containing run subdirectories")
    parser.add_argument("--output", required=True, help="Output image path")
    parser.add_argument("--title", default="Training Throughput")
    parser.add_argument("--config", required=True, help="Path to config.yml")
    parser.add_argument("--section", required=True)
    parser.add_argument("--index", required=True, type=int)
    args = parser.parse_args()

    with open(args.config) as f:
        config = yaml.safe_load(f)
    script_config = config["plots"][args.section]["scripts"][args.index]
    gpu_model = script_config.get("gpu_model", "")

    print("Collecting throughput data...")
    df = collect_throughput_data(args.data_dir)

    if df.empty:
        print("No throughput data found.")
        return

    gpu_counts = sorted(df["gpu_count"].unique())
    print(f"Found data for GPU counts: {gpu_counts}")

    plot_throughput(df, args.output, args.title, gpu_model)


if __name__ == "__main__":
    main()

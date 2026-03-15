import json
import os
import tempfile

import pandas as pd
import pytest

from plot_throughput import (
    collect_throughput_data,
    find_latest_version_dir,
    get_gpu_count,
    load_events_per_second,
    plot_throughput,
)


@pytest.fixture
def sample_data_dir():
    """Create a temporary data directory with realistic run structures."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # 1-GPU run
        run1 = os.path.join(tmpdir, "run-1gpu")
        os.makedirs(os.path.join(run1, "lightning_logs", "version_0"))
        os.makedirs(os.path.join(run1, "lightning_logs", "version_1"))
        with open(os.path.join(run1, "params.json"), "w") as f:
            json.dump({"CUDA_VISIBLE_DEVICES": "0", "NUM_WORKERS": 1}, f)
        # version_0: old format (no events_per_second)
        pd.DataFrame({"epoch": [0, 1], "step": [49, 99], "train_loss": [0.01, 0.009]}).to_csv(
            os.path.join(run1, "lightning_logs", "version_0", "metrics.csv"), index=False
        )
        # version_1: new format with events_per_second
        pd.DataFrame(
            {
                "epoch": [0, 0, 1, 1],
                "step": [49, 99, 149, 199],
                "train/events_per_second_step": [25.0, 30.0, 28.0, 32.0],
                "train_loss": [0.01, 0.009, 0.008, 0.007],
            }
        ).to_csv(os.path.join(run1, "lightning_logs", "version_1", "metrics.csv"), index=False)

        # 2-GPU run
        run2 = os.path.join(tmpdir, "run-2gpu")
        os.makedirs(os.path.join(run2, "lightning_logs", "version_0"))
        with open(os.path.join(run2, "params.json"), "w") as f:
            json.dump({"CUDA_VISIBLE_DEVICES": "0,1", "NUM_WORKERS": 1}, f)
        pd.DataFrame(
            {
                "epoch": [0, 0, 1, 1],
                "step": [49, 99, 149, 199],
                "train/events_per_second_step": [50.0, 55.0, 52.0, 58.0],
                "train_loss": [0.01, 0.009, 0.008, 0.007],
            }
        ).to_csv(os.path.join(run2, "lightning_logs", "version_0", "metrics.csv"), index=False)

        # 4-GPU run (no lightning_logs — incomplete)
        run4 = os.path.join(tmpdir, "run-4gpu")
        os.makedirs(run4)
        with open(os.path.join(run4, "params.json"), "w") as f:
            json.dump({"CUDA_VISIBLE_DEVICES": "0,1,2,3", "NUM_WORKERS": 1}, f)

        yield tmpdir


class TestGetGpuCount:
    def test_single_gpu(self):
        assert get_gpu_count({"CUDA_VISIBLE_DEVICES": "0"}) == 1

    def test_two_gpus(self):
        assert get_gpu_count({"CUDA_VISIBLE_DEVICES": "0,1"}) == 2

    def test_four_gpus(self):
        assert get_gpu_count({"CUDA_VISIBLE_DEVICES": "0,1,2,3"}) == 4

    def test_missing_defaults_to_one(self):
        assert get_gpu_count({}) == 1


class TestFindLatestVersionDir:
    def test_picks_latest_version(self, sample_data_dir):
        run1 = os.path.join(sample_data_dir, "run-1gpu")
        latest = find_latest_version_dir(run1)
        assert latest.endswith("version_1")

    def test_returns_none_for_missing_logs(self, sample_data_dir):
        run4 = os.path.join(sample_data_dir, "run-4gpu")
        assert find_latest_version_dir(run4) is None

    def test_returns_none_for_nonexistent_dir(self, tmp_path):
        assert find_latest_version_dir(str(tmp_path / "nope")) is None


class TestLoadEventsPerSecond:
    def test_loads_values(self, sample_data_dir):
        path = os.path.join(
            sample_data_dir, "run-2gpu", "lightning_logs", "version_0", "metrics.csv"
        )
        values = load_events_per_second(path)
        assert values is not None
        assert len(values) == 4
        assert values.iloc[0] == 50.0

    def test_returns_none_for_old_format(self, sample_data_dir):
        path = os.path.join(
            sample_data_dir, "run-1gpu", "lightning_logs", "version_0", "metrics.csv"
        )
        values = load_events_per_second(path)
        assert values is None


class TestCollectThroughputData:
    def test_collects_from_valid_runs(self, sample_data_dir):
        df = collect_throughput_data(sample_data_dir)
        assert not df.empty
        assert set(df["gpu_count"].unique()) == {1, 2}

    def test_correct_counts(self, sample_data_dir):
        df = collect_throughput_data(sample_data_dir)
        assert len(df[df["gpu_count"] == 1]) == 4
        assert len(df[df["gpu_count"] == 2]) == 4

    def test_skips_incomplete_runs(self, sample_data_dir):
        df = collect_throughput_data(sample_data_dir)
        assert 4 not in df["gpu_count"].values


class TestPlotThroughput:
    def test_creates_output_file(self, sample_data_dir, tmp_path):
        df = collect_throughput_data(sample_data_dir)
        output = str(tmp_path / "test_plot.png")
        plot_throughput(df, output, "Test Title", "Test GPU")
        assert os.path.isfile(output)
        assert os.path.getsize(output) > 0

    def test_single_gpu_count_no_ideal_line(self, tmp_path):
        df = pd.DataFrame({"gpu_count": [1, 1, 1], "events_per_second": [25.0, 30.0, 28.0]})
        output = str(tmp_path / "test_single.png")
        plot_throughput(df, output, "Single", "")
        assert os.path.isfile(output)

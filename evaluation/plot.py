import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

BENCHMARKS = [
    "covid",
    "nginx-analysis",
    "unixfun",
    "weather",
    "weather-tuft-weather",
    "word-freq",
]

times = {}
for benchmark in BENCHMARKS:
    data = pd.read_csv(f"results/{benchmark}-timing.csv")
    bash_time = sum(data[data["mode"] == "bash"]["time_sec"])
    incr_time = sum(data[data["mode"] == "incr"]["time_sec"])
    times[benchmark] = {
        "bash": bash_time,
        "incr": incr_time,
    }

figure, axes = plt.subplots()

locations = np.arange(len(BENCHMARKS))
bash_values = [times[b]["bash"] for b in BENCHMARKS]
incr_values = [times[b]["incr"] for b in BENCHMARKS]

width = 0.4 # Bar width
bash_bars = axes.bar(locations - width / 2, bash_values, width, label="bash")
incr_bars = axes.bar(locations + width / 2, incr_values, width, label="incr")

axes.set_title("Benchmark Runtimes")
axes.set_xticks(locations)
axes.set_xticklabels(BENCHMARKS, rotation=30, ha="right")
axes.set_ylabel("Total Time (s)")
axes.set_ylim(0, 75)
axes.bar_label(bash_bars, padding=3, fmt="%.1f")
axes.bar_label(incr_bars, padding=3, fmt="%.1f")
axes.legend()

figure.tight_layout()
figure.savefig("plot.png", bbox_inches="tight")
import logging
import csv
import os
import time
from datetime import datetime
import matplotlib.pyplot as plt

logger = logging.getLogger("Aegis-Resource-Tracker")

class ResourceTracker:
    """
    This is our "Black Box" recorder. It grabs CPU and Memory stats from the Docker
    container and turns them into CSV logs and PNG graphs.
    """
    def __init__(self, log_dir: str = "data/execution_logs"):
        self.log_dir = log_dir
        # Ensure the logs directory exists, or everything will crash when we try to save.
        os.makedirs(log_dir, exist_ok=True)
        self.current_test_id = "unknown"
        self.data = [] # List of tuples: (timestamp, cpu_percent, mem_usage_mb)

    def start_session(self, test_id: str):
        # Resetting the buffer for a new test run.
        self.current_test_id = test_id
        self.data = []
        logger.info(f"Started telemetry session for {test_id}")

    def capture(self, container):
        """
        Grabbing a snapshot of what the container is doing right now.
        """
        try:
            stats = container.stats(stream=False)
            
            # CPU calculation is a bit of a nightmare because Docker gives us cumulative stats.
            # I'm trying to calculate the delta relative to the system usage.
            cpu_stats = stats.get('cpu_stats', {})
            precpu_stats = stats.get('precpu_stats', {})
            
            cpu_usage = cpu_stats.get('cpu_usage', {}).get('total_usage', 0)
            precpu_usage = precpu_stats.get('cpu_usage', {}).get('total_usage', 0)
            
            system_cpu_usage = cpu_stats.get('system_cpu_usage', 0)
            presystem_cpu_usage = precpu_stats.get('system_cpu_usage', 0)
            
            cpu_percent = 0.0
            
            # I've added this check because Docker Desktop on Mac doesn't always provide 
            # system_cpu_usage in the way Linux does. 
            if system_cpu_usage > 0 and presystem_cpu_usage > 0:
                cpu_delta = cpu_usage - precpu_usage
                system_delta = system_cpu_usage - presystem_cpu_usage
                
                # We need to know how many cores the container sees to get an accurate %.
                num_procs = cpu_stats.get('online_cpus', 0)
                if num_procs == 0:
                    percpu = cpu_stats.get('cpu_usage', {}).get('percpu_usage')
                    num_procs = len(percpu) if percpu else 1
                
                if system_delta > 0.0 and cpu_delta > 0.0:
                    cpu_percent = (cpu_delta / system_delta) * num_procs * 100.0
            else:
                # If the platform-specific keys are missing, I fall back to a scaled raw usage.
                # It's not a perfect %, but it's enough to see the visual spike in the graph.
                cpu_percent = float(cpu_usage) / 1e7
            
            # Memory is easier. Just bytes to MB conversion.
            mem_stats = stats.get('memory_stats', {})
            mem_usage = mem_stats.get('usage', 0) / (1024 * 1024)
            
            timestamp = time.time()
            self.data.append((timestamp, cpu_percent, mem_usage))
            
        except Exception as e:
            logger.error(f"Failed to capture telemetry: {e}")

    def save_and_plot(self):
        """
        This is where we turn the raw numbers into the "Kill Curve" visualization.
        """
        if not self.data:
            logger.warning("No telemetry data to save.")
            return

        # Unique filename based on the test and the current time.
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"{self.current_test_id}_{timestamp_str}"
        csv_path = os.path.join(self.log_dir, f"{base_filename}.csv")
        png_path = os.path.join(self.log_dir, f"{base_filename}.png")

        # Dumping everything to CSV so we can do deeper analysis in Excel/Pandas later.
        try:
            with open(csv_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["timestamp", "cpu_percent", "mem_usage_mb"])
                writer.writerows(self.data)
            logger.info(f"Telemetry saved to {csv_path}")
        except Exception as e:
            logger.error(f"Failed to save CSV: {e}")

        # Generating the plot using matplotlib. 
        # I'm using two y-axes (one for CPU, one for Mem) to see both on one chart.
        try:
            times, cpu, mem = zip(*self.data)
            # Normalizing time so the graph starts at 0 seconds.
            start_time = times[0]
            relative_times = [t - start_time for t in times]

            fig, ax1 = plt.subplots(figsize=(10, 6))

            # CPU is the red line.
            color = 'tab:red'
            ax1.set_xlabel('Time (s)')
            ax1.set_ylabel('CPU Activity (Scaled)', color=color)
            ax1.plot(relative_times, cpu, color=color, label='CPU activity', linewidth=2)
            ax1.tick_params(axis='y', labelcolor=color)
            
            # The horizontal line shows the flatline after the kill signal.
            ax1.axhline(y=0, color='gray', linestyle=':', alpha=0.5)

            # Memory is the blue dashed line.
            ax2 = ax1.twinx()
            color = 'tab:blue'
            ax2.set_ylabel('Memory Usage (MB)', color=color)
            ax2.plot(relative_times, mem, color=color, label='Mem (MB)', linestyle='--')
            ax2.tick_params(axis='y', labelcolor=color)
            
            plt.title(f"Aegis-Eval Telemetry: {self.current_test_id}")
            fig.tight_layout()
            plt.savefig(png_path)
            plt.close()
            logger.info(f"Telemetry graph generated at {png_path}")
            
            return png_path
        except Exception as e:
            logger.error(f"Failed to generate plot: {e}")
            return None

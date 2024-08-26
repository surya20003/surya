import tkinter as tk
from tkinter import ttk
import psutil
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import platform
from queue import Empty as QueueEmpty
from ttkthemes import ThemedTk

class SystemPerformanceTracker(ThemedTk):
    def __init__(self):
        ThemedTk.__init__(self)
        self.get_themes()
        self.set_theme("clearlooks")
        self.title("System Performance Tracker")
        self.window_exists = True
        
        notebook_frame = tk.Frame(self)
        notebook_frame.pack(side='left', fill='y', padx=5)

        self.notebook = ttk.Notebook(notebook_frame)

        self.cpu_tab = ttk.Frame(self.notebook)
        self.memory_tab = ttk.Frame(self.notebook)
        self.battery_tab = ttk.Frame(self.notebook)
        self.processes_tab = ttk.Frame(self.notebook)
        self.system_info_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.cpu_tab, text='CPU Usage')
        self.notebook.add(self.memory_tab, text='Memory Usage')
        self.notebook.add(self.battery_tab, text='Battery Status')
        self.notebook.add(self.processes_tab, text='Running Processes')
        self.notebook.add(self.system_info_tab, text='System Information')
        self.notebook.pack(expand=1, fill="both")

        self.cpu_fig, self.cpu_ax, self.cpu_plot, _, _, _, self.cpu_times, self.cpu_data = self.init_plot(
            self.cpu_tab, 'CPU Usage', 'Time', 'Percentage', [], [] 
            )
        self.cpu_info_text = tk.Text(self.cpu_tab, wrap=tk.WORD, height=3, width=30)
        self.cpu_info_text.pack(side=tk.BOTTOM, fill=tk.X)

        self.memory_fig, self.memory_ax, self.memory_plot, _, _, _, self.memory_times, self.memory_data = self.init_plot(
            self.memory_tab, 'Memory Usage', 'Time', 'Memory (GB)', [], []
            )
        self.memory_info_text = tk.Text(self.memory_tab, wrap=tk.WORD, height=6, width=30)
        self.memory_info_text.pack(side=tk.BOTTOM, fill=tk.X)

        self.battery_text = tk.Text(self.battery_tab, wrap=tk.WORD)
        self.battery_text.pack(fill=tk.BOTH, expand=True)

        self.processes_tree = ttk.Treeview(self.processes_tab, columns=('PID', 'Name', 'CPU Percent', 'Memory Percent'))
        self.processes_tree.heading('#0', text='')
        self.processes_tree.column('#0', stretch=tk.NO, width=0)
        self.processes_tree.heading('PID', text='PID')
        self.processes_tree.heading('Name', text='Name')
        self.processes_tree.heading('CPU Percent', text='CPU Percent')
        self.processes_tree.heading('Memory Percent', text='Memory Percent')
        self.processes_tree.pack(fill=tk.BOTH, expand=True)

        self.system_info_text = tk.Text(self.system_info_tab, wrap=tk.WORD)
        self.system_info_text.pack(fill=tk.BOTH, expand=True)

        if self.winfo_exists():
            self.after(1000, self.update_plots)

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def init_plot(self, tab, title, xlabel, ylabel, times, data):
        fig, ax = plt.subplots()
        plot = FigureCanvasTkAgg(fig, master=tab)
        plot.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        ax.set_xlim(0, 60)
        ax.set_ylim(0, 100)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)

        return fig, ax, plot, title, xlabel, ylabel, times, data

    def update_plot(self, ax, title, xlabel, ylabel, data, max_value, data_type):
        ax.clear()
        ax.fill_between(range(len(data)), data, color='blue', alpha=0.3)

        ax.plot(range(len(data)), data)
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        max_age = 60
        ax.set_xlim(0, max_age)

        if data_type == 'cpu':
            ax.set_ylim(0, 100)
        elif data_type == 'memory':
            ax.set_ylim(0, max_value)

    def update_plots(self):
        try:
            total_memory_gb = psutil.virtual_memory().total / (1073741824)
            max_value = total_memory_gb

            cpu_percent = psutil.cpu_percent(interval=0.5) * 1.5
            self.cpu_data.append(cpu_percent)
            self.cpu_data = self.cpu_data[-60:]
            self.update_plot(
                self.cpu_ax,
                'CPU Usage',
                'Time',
                'Percentage',
                self.cpu_data,
                max_value,
                data_type='cpu'
            )
            self.cpu_plot.draw()
            cpu_info = f"CPU Utilization: {cpu_percent:.2f}%\n"
            self.cpu_info_text.delete(1.0, tk.END)
            self.cpu_info_text.insert(tk.END, cpu_info)

            self.memory_data.append(psutil.virtual_memory().used / (1073741824))  # Convert to GB
            self.memory_data = self.memory_data[-60:]
            self.update_plot(
                self.memory_ax,
                'Memory Usage',
                'Time',
                'Memory (GB)',
                self.memory_data,
                max_value,
                data_type='memory'
            )
            self.memory_plot.draw()
            memory_info = f"Memory in Use: {self.memory_data[-1]:.2f} GB\n"
            memory_info += f"Available Memory: {total_memory_gb - self.memory_data[-1]:.2f} GB\n"
            self.memory_info_text.delete(1.0, tk.END)
            self.memory_info_text.insert(tk.END, memory_info)

            try:
                battery_info = psutil.sensors_battery()
                battery_percent = battery_info.percent

                if battery_info.power_plugged:
                    estimated_time = "Plugged in (Charging)"
                elif battery_info.secsleft <= 0:
                    estimated_time = "Calculating..."
                else:
                    estimated_time = timedelta(seconds=battery_info.secsleft)

                if isinstance(estimated_time, timedelta) and estimated_time.total_seconds() < 0:
                    estimated_time = "Calculating..."

                battery_stats = f"Battery Percent: {battery_percent}%\nEstimated Time Remaining: {estimated_time}\n"
                self.battery_text.delete(1.0, tk.END)
                self.battery_text.insert(tk.END, battery_stats)
            except Exception as e:
                print(f"Unable to get battery status: {e}")

            self.update_running_processes()

            self.cpu_ax.set_xlim(0, 60)
            self.memory_ax.set_xlim(0, 60)

            system_info = f"System Information:\n"
            system_info += f"OS: {platform.system()} {platform.release()} ({platform.machine()})\n"
            system_info += f"Processor: {platform.processor()}\n"
            system_info += f"CPU Cores: {psutil.cpu_count(logical=False)} (Logical: {psutil.cpu_count(logical=True)})\n"
            system_info += f"RAM: {total_memory_gb:.2f} GB\n"
            system_info += f"Swap Memory: {psutil.swap_memory().total / (1073741824):.2f} GB\n"
            system_info += f"Network Interfaces: {', '.join(psutil.net_if_stats().keys())}\n"
            system_info += f"CPU Frequency: {psutil.cpu_freq().current:.2f} MHz\n"
            system_info += f"Total Disk Space: {psutil.disk_usage('/').total / (1073741824):.2f} GB\n"
            system_info += f"Available Disk Space: {psutil.disk_usage('/').free / (1073741824):.2f} GB\n"
            self.system_info_text.delete(1.0, tk.END)
            self.system_info_text.insert(tk.END, system_info)

            if self.winfo_exists():
                self.after(1000, self.update_plots)
        except QueueEmpty:
            if self.winfo_exists():
                self.after(1000, self.update_plots)

    def on_closing(self):
        self.window_exists = False
        self.destroy()

    def update_running_processes(self):
        processes_info = self.get_running_processes()
        self.processes_tree.delete(*self.processes_tree.get_children())
        for process in processes_info:
            if process['pid'] != 0:
                cpu_percent = round(process['cpu_percent'], 2)
                memory_percent = round(process['memory_percent'], 2)
                process_data = (process['pid'], process['name'], f"{cpu_percent}%", f"{memory_percent}%")
                self.processes_tree.insert('', 'end', values=process_data)

    def get_running_processes(self):
        process_data = [process.info for process in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent'])]
        return process_data


if __name__ == "__main__":
    app = SystemPerformanceTracker()
    app.mainloop()

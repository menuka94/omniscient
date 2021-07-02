#!/bin/python3

# Graphing Utility for Omniscient
import os
import sys

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import re

stats_root_dir = sys.argv[1]

spark_root_dir = f'{stats_root_dir}/spark'
k8s_root_dir = f'{stats_root_dir}/k8s'
graphs_root_dir = f'{stats_root_dir}'


def rename_and_get_sorted_file_names(root_dir):
    # list of all file names
    list_dir = os.listdir(root_dir)
    list_dir.remove('aggregate.nmon.csv')

    # Pad File number with zero if the number of digits is 1
    # example: 0-XXX.XXX.XXX.XXX.nmon.csv --> 00-XXX.XXX.XXX.XXX.nmon.csv
    for file_name in list_dir:
        number = re.findall("^[^-]*[^ -]", file_name)[0]
        new_name = file_name.replace(number, number.zfill(2), 1)
        os.rename(f'{root_dir}/{file_name}', f'{root_dir}/{new_name}')

    # read file names again after renaming
    list_dir = os.listdir(root_dir)

    list_dir.remove("aggregate.nmon.csv")

    for file_name in list_dir:
        # remove nvidia files
        if file_name.find(".nvidia") != -1:
            list_dir.remove(file_name)
        # remove non-csv files
        elif file_name.find(".csv") == -1:
            list_dir.remove(file_name)

    return sorted(list_dir)


def lattice_ip_to_host(ip):
    hostname = 'lattice-' + str(int(ip[-3:]) - 10)
    return hostname


spark_file_names = rename_and_get_sorted_file_names(spark_root_dir)
k8s_file_names = rename_and_get_sorted_file_names(k8s_root_dir)


class MachineAverage:
    """
    To represent average average resource utilization metrics for each host
    """

    def __init__(self, hostname, cpu, memory, network_write, network_read):
        self.hostname = hostname
        self.cpu = cpu
        self.memory = memory
        self.network_write = network_write
        self.network_read = network_read

    def __str__(self):
        return f'[hostname={self.hostname}, cpu={self.cpu}, memory={self.memory}, \
                    network_write={self.network_write}, network_read={self.network_read}]'


def get_averages_map(file_names, root_dir):
    averages = {}

    for file_name in file_names:
        df = pd.read_csv(f'{root_dir}/{file_name}')
        df = df.drop(['MEM:memtotal', 'MEM:inactive'], axis=1)
        # Get DF of mean values of all columns
        mean_df = pd.DataFrame(df.mean()).transpose()
        # Find IP Address from file name
        ip = re.findall(r'[0-9]+(?:\.[0-9]+){3}', file_name)[0]
        # Map IP Address to Host name
        hostname = lattice_ip_to_host(ip).replace('lattice-', '')
        cpu = mean_df['CPU_ALL:User%'][0]
        memory = mean_df['MEM:active'][0]
        network_write = mean_df['NET:eno1-write-KB/s'][0]
        network_read = mean_df['NET:eno1-read-KB/s'][0]
        machine_average = MachineAverage(hostname, cpu, memory, network_write, network_read)
        averages[file_name] = machine_average

    return averages


# Create Maps of average resource utilization values
spark_averages = get_averages_map(spark_file_names, spark_root_dir)
k8s_averages = get_averages_map(k8s_file_names, k8s_root_dir)

# create lists for graphing
spark_hostnames = [machine.hostname for _, machine in spark_averages.items()]
spark_cpu_values = [machine.cpu for _, machine in spark_averages.items()]
spark_memory_values = [machine.memory for _, machine in spark_averages.items()]
spark_network_write_values = [machine.network_write for _, machine in spark_averages.items()]
spark_network_read_values = [machine.network_read for _, machine in spark_averages.items()]

k8s_hostnames = [machine.hostname for _, machine in k8s_averages.items()]
k8s_cpu_values = [machine.cpu for _, machine in k8s_averages.items()]
k8s_memory_values = [machine.memory for _, machine in k8s_averages.items()]
k8s_network_write_values = [machine.network_write for _, machine in k8s_averages.items()]
k8s_network_read_values = [machine.network_read for _, machine in k8s_averages.items()]

# Graph
# update graph fonts
font = {
    'weight': 'bold',
    'size': 16
}
matplotlib.rc('font', **font)

plt1 = plt.figure(figsize=(15, 20))
plt.subplot(4, 1, 1)
plt.xlabel('Machine')
plt.ylabel('MEM:active')
plt.xticks(rotation=90, ha='right')
plt.plot(spark_hostnames, spark_memory_values, 'r', label="Bare-Metal")
plt.plot(k8s_hostnames, k8s_memory_values, 'b', label="K8s")
plt.legend()
plt.title("Memory")

plt.subplot(4, 1, 2)
plt.xlabel('Machine')
plt.ylabel('CPU Usage (%)')
plt.xticks(rotation=90, ha='right')
plt.plot(spark_hostnames, spark_cpu_values, 'r', label="Bare-Metal")
plt.plot(k8s_hostnames, k8s_cpu_values, 'b', label="K8s")
plt.legend()
plt.title('CPU Usage (%)')

plt.subplot(4, 1, 3)
plt.xlabel('Machine')
plt.ylabel('NET:eno1-write-KB/s')
plt.xticks(rotation=90, ha='right')
plt.plot(spark_hostnames, spark_network_write_values, 'r', label="Bare-Metal")
plt.plot(k8s_hostnames, k8s_network_write_values, 'b', label="K8s")
plt.legend()
plt.title('Network Write')

plt.subplot(4, 1, 4)
plt.xlabel('Machine')
plt.ylabel('NET:eno1-read-KB/s')
plt.xticks(rotation=90, ha='right')
plt.plot(spark_hostnames, spark_network_read_values, 'r', label="Bare-Metal")
plt.plot(k8s_hostnames, k8s_network_read_values, 'b', label="K8s")
plt.legend()
plt.title('Network Read')

plt.tight_layout()
plt.savefig(f'{graphs_root_dir}/comparison.png', dpi=300)
# plt.show()
print('[+] Comparison Graph Saved')


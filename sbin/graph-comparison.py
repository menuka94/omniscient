#!/bin/python3

# Graphing Utility for Omniscient
import os
import sys

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import re

# stats_root_dir = sys.argv[1]

spark_root_dir = "/s/lattice-150/a/all/all/all/sustain/omniscient/data/spark-kmeans-svi-county"
k8s_root_dir = "/s/lattice-150/a/all/all/all/sustain/omniscient/data/k8s-kmeans-svi-county"
graphs_root_dir = f'{spark_root_dir}/graphs'


def rename_and_get_sorted_file_names(root_dir):
    # list of all file names
    list_dir = os.listdir(root_dir)
    if 'env' in list_dir:
        list_dir.remove('env')
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

    if 'env' in list_dir:
        list_dir.remove('env')

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


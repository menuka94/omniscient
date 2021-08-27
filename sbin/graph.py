#!/bin/python3

# Graphing Utility for Omniscient
import os
import sys

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import re

stats_root_dir = sys.argv[1]
graphs_root_dir = f'{stats_root_dir}/graphs'

if not os.path.exists(graphs_root_dir):
    os.makedirs(graphs_root_dir)

# list of all file names
stat_file_names = os.listdir(stats_root_dir)
try:
    stat_file_names.remove("aggregate.nmon.csv")
except:
    print('Error: aggregagte.nmon.csv not in stat_file_names')

for file_name in stat_file_names:
    # remove nvidia files
    if file_name.find(".nvidia") != -1:
        stat_file_names.remove(file_name)
    # remove non-csv files
    elif file_name.find(".csv") == -1:
        stat_file_names.remove(file_name)


def lattice_ip_to_host(ip):
    hostname = 'lattice-' + str(int(ip[-3:]) - 10)
    return hostname


def graph(_file_name, graph_title):
    df = pd.read_csv(f'{stats_root_dir}/{_file_name}')
    # update graph fonts
    font = {
        'weight': 'bold',
        'size': 16
    }
    matplotlib.rc('font', **font)

    plt.figure(figsize=(15, 15))
    plt.suptitle(graph_title)
    plt.subplot(3, 1, 1)
    plt.xlabel('Timestamp')
    plt.ylabel('MEM:active')
    x1 = df['timestamp']
    y1 = df['MEM:active']
    plt.plot(x1, y1)
    # plt.title('Memory')

    plt.subplot(3, 1, 2)
    y2 = df['NET:eno1-write-KB/s']
    plt.xlabel('Timestamp')
    plt.ylabel('NET:eno1-write-KB/s')
    plt.plot(x1, y2)
    # plt.title('Network I/O')

    plt.subplot(3, 1, 3)
    y3 = df['NET:eno1-read-KB/s']
    plt.xlabel('Timestamp')
    plt.ylabel('NET:eno1-read-KB/s')
    plt.plot(x1, y3)

    y4 = df['CPU_ALL:User%']

    plt.xlabel('Timestamp')
    plt.ylabel('CPU Usage')
    plt.plot(x1, y4)
    # plt.title('CPU Usage')

    plt.tight_layout()
    plt.savefig(f'{graphs_root_dir}/{graph_title}.png', dpi=300)


for file_name in stat_file_names:
    # find hostname from file_name (through IP address)
    ip = re.findall(r'[0-9]+(?:\.[0-9]+){3}', file_name)[0]
    hostname = lattice_ip_to_host(ip)
    graph(file_name, f'{hostname} ({ip})')
    print(f'>>> Graphing {file_name}')

print('>>> Graphing Aggregate')
graph('aggregate.nmon.csv', f'Aggregate')


#!/usr/bin/python3

import sys
import os
import pprint
import re
import plotly.offline as offline
import plotly.graph_objs as go

HEADER = 'Applications Memory Usage (in Killobytes):'

LEAD_TIME = 'Uptime:'
REGEX_TIME = r'Uptime: (\d+) Realtime: (\d+)'
LEAD_PROCESS = 'Total PSS by process:'
REGEX_PROCESS = r'^\s+([0-9,]+)K: (\S+) \(pid (\d+)( / activities)?\)$'
LEAD_OOM = 'Total PSS by OOM adjustment:'
REGEX_OOM_ADJ = r'^\s+([0-9,]+)K: (\S+)$'
LEAD_CATEGORY = 'Total PSS by category:'
REGEX_CATEGORY = r'^\s+([0-9,]+)K: (.+)$'
LEAD_SUMMARY = 'Total RAM:'
REGEX_FREE = (r'^\s*Free RAM: \s*([0-9,]+)K '
              r'\(\s*([0-9,]+)K cached pss '
              r'\+\s*([0-9,]+)K cached kernel '
              r'\+\s*([0-9,]+)K free\)$')
REGEX_USED = (r'^\s*Used RAM: \s*([0-9,]+)K '
              r'\(\s*([0-9,]+)K used pss '
              r'\+\s*([0-9,]+)K kernel\)$')

class Meminfo:
    def __init__(self):
        pass

class Process:
    def __init__(self, pss, name, pid):
        self.pss = pss
        self.name = name
        self.pid = pid

    def __str__(self):
        return 'PSS = ' + str(self.pss) \
            + 'K, name = ' + self.name \
            + ', pid = ' + str(self.pid)

def usage():
    print('[USAGE] ' + sys.argv[0] + ' DIR')
    sys.exit(1)

def is_dumpsys_meminfo(path):
    with open(path) as f:
        line = f.readline()
        return line == HEADER

def conv_csv2int(csint):
    return int(csint.replace(',', ''))

def parse_time(line):
    regex = re.compile(REGEX_TIME)
    match = regex.search(line)
    return int(match.group(1)), int(match.group(2))

def parse_process(f):
    processes = list()
    regex = re.compile(REGEX_PROCESS)
    line = f.readline()
    while line != '\n':
        match = regex.search(line)
        pss = conv_csv2int(match.group(1))
        name = match.group(2)
        pid = int(match.group(3))
        process = Process(pss, name, pid)
        processes.append(process)
        line = f.readline()
    return processes

def parse_oom_adj(f):
    oom_adj = dict()
    regex = re.compile(REGEX_OOM_ADJ)
    line = f.readline()
    while line != '\n':
        match = regex.search(line)
        if match != None:
            pss = conv_csv2int(match.group(1))
            level = match.group(2)
            oom_adj[level] = pss
        line = f.readline()
    return oom_adj

def parse_category(f):
    category = dict()
    regex = re.compile(REGEX_CATEGORY)
    line = f.readline()
    while line != '\n':
        match = regex.search(line)
        if match != None:
            pss = conv_csv2int(match.group(1))
            name = match.group(2)
            category[name] = pss
        line = f.readline()
    return category

def parse_summary(f):
    summary = dict()
    regex_free = re.compile(REGEX_FREE)
    regex_used = re.compile(REGEX_USED)
    line = f.readline()
    while line != '\n' and line != '':
        match = regex_free.search(line)
        if match != None:
            summary['Free RAM'] = conv_csv2int(match.group(1))
            summary['cached pss'] = conv_csv2int(match.group(2))
            summary['cached kernel'] = conv_csv2int(match.group(3))
            summary['free'] = conv_csv2int(match.group(4))
        match = regex_used.search(line)
        if match != None:
            summary['Used RAM'] = conv_csv2int(match.group(1))
            summary['used pss'] = conv_csv2int(match.group(2))
            summary['kernel'] = conv_csv2int(match.group(3))
        line = f.readline()
    return summary

def parse_dumpsys_meminfo(path):
    meminfo = Meminfo()
    with open(path) as f:
        line = f.readline()
        while line:
            if line.startswith(LEAD_TIME):
                uptime, realtime = parse_time(line)

                meminfo.uptime = uptime
                meminfo.realtime = realtime
            elif line.startswith(LEAD_PROCESS):
                meminfo.processes = parse_process(f)
#                for process in meminfo.processes:
#                    print("process", process, "\n")
            elif line.startswith(LEAD_OOM):
                meminfo.oom_adj = parse_oom_adj(f)
                # pprint.pprint(meminfo.oom_adj)
            elif line.startswith(LEAD_CATEGORY):
                meminfo.category = parse_category(f)
                # pprint.pprint(meminfo.category)
            elif line.startswith(LEAD_SUMMARY):
                meminfo.summary = parse_summary(f)
                # pprint.pprint(meminfo.summary)
            line = f.readline()
    return meminfo

def seconds_to_hms(seconds):
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h}:{m:02d}:{s:02d}" # :02d 确保分钟和秒是两位数


def draw_graph(meminfos):
    uptimes = [seconds_to_hms(mi.uptime) for mi in meminfos]
    total_free = [mi.summary['Free RAM']/1024 for mi in meminfos]
    total_used = [mi.summary['Used RAM']/1024 for mi in meminfos]
    #需要先列出所有的process.name, 然后按process.name 来取数画图
    #当前可能最开始没有，后面突然出现的这样的进程会比较麻烦，
    #需要先遍历一次所有log找出所有process，再二次添加数据
    process_names = {}
    for mi in meminfos:
        for process in mi.processes:
            if process_names.get(process.name, "") == "":
                process_names[process.name] = []

    #抽取数据准备显示
#    for name in process_names:
#        print(f"dict process name {name} value {process_names[name]}")


    for mi in meminfos:
        for process_name in process_names:
            found = False
            for process in mi.processes:
                if process_name == process.name:
                    process_names[process.name].append(process.pss)
                    found = True
                    break
            if found == False:
               process_names[process_name].append(0)


    #抽取数据准备显示
#    for name in process_names:
#        print(f"dict process name {name} value {process_names[name]}")

    foreground = list()
    for mi in meminfos:
        if 'Foreground' in mi.oom_adj:
            foreground.append(mi.oom_adj['Foreground']/1024)
        else:
            foreground.append(None)

    """
    data = [
        go.Scatter(
            x = uptimes,
            y = total_free,
            mode = 'lines+markers',
            name = 'Free RAM [MiB]'),
        go.Scatter(
            x = uptimes,
            y = total_used,
            mode = 'lines+markers',
            name = 'Used RAM [MiB]'),
        go.Scatter(
            x = uptimes,
            y = foreground,
            mode = 'lines+markers',
            name = 'Foreground [MiB]'),
    ]
    """
    data = []

    #抽取数据准备显示
    for name in process_names:
        data.append(
            go.Scatter(
            x = uptimes,
            y = process_names[name],
            mode = 'lines+markers',
            name = f'{name}'))

    offline.plot(data, filename='dmanalyzer.html', image='png')

def main():
    if len(sys.argv) != 2:
        usage()

    log_dir = sys.argv[1]
    files = os.listdir(log_dir)
    meminfos = list()

    for file in files:
        path = os.path.join(os.getcwd(), log_dir, file)
        if is_dumpsys_meminfo(path):
            continue

        meminfo = parse_dumpsys_meminfo(path)
        if hasattr(meminfo, 'uptime'):
            meminfos.append(meminfo)

    meminfos.sort(key=lambda meminfo: meminfo.uptime)
    draw_graph(meminfos)

if __name__ == '__main__':
    main()

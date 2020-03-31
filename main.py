#!/usr/bin/python3

import sys
import os
import pprint
import re

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

def draw_graph(meminfos):
    # TODO
    pass

def main():
    if len(sys.argv) != 2:
        usage()

    log_dir = sys.argv[1]
    files = os.listdir(log_dir)
    files.sort()
    meminfos = list()

    for file in files:
        path = os.path.join(os.getcwd(), log_dir, file)
        if is_dumpsys_meminfo(path):
            continue

        meminfo = parse_dumpsys_meminfo(path)
        meminfos.append(meminfo)

    draw_graph(meminfos)

if __name__ == '__main__':
    main()

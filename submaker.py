'''
numOfLines
{
    startFrame
    endFrame
    lineOffset
} x numOfLines
{
    line
} x numOfLines
'''

import struct
import sys

from datetime import datetime

frmt = '%H:%M:%S.%f'
basetime = datetime(1900, 1, 1)
fps = 15

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Usage: toon_submaker.py INFILE.sbv OUTFILE.tss')
        exit(1)

    infile = sys.argv[1]
    outfile = sys.argv[2]
    lines = []

    with open(infile, 'r') as sub_file:
        lines = sub_file.read().split('\n\n')

    lines = [line for line in lines if line]
    number_of_lines = len(lines)
    offset = 0

    index = b''
    data = b''

    for line in lines:
        time_window, text = line.split('\n')[:2]
        start, end = time_window.split(',')
        start = round(fps * (datetime.strptime('0' + start + '000', frmt) - basetime).total_seconds())
        end = round(fps * (datetime.strptime('0' + end[:-1] + '000', frmt) - basetime).total_seconds())
        index += struct.pack('<I', start) + struct.pack('<I', end) + struct.pack('<I', offset)
        offset += len(text) + 1
        data += text.encode() + b'\0'

    with open(outfile, 'wb') as sub_file:
        sub_file.write(struct.pack('<I', number_of_lines) + index + data)

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

if len(sys.argv) < 3:
    exit()
infile = sys.argv[1]
outfile = sys.argv[2]
lines = []

with open(infile, 'r') as subFile:
    lines = subFile.read().split('\n\n')

lines = [line for line in lines if line]
numberOflines = len(lines)
offset = 0

index = ''
data = ''

frmt = '%H:%M:%S.%f'
basetime = datetime(1900,1,1)
fps = 15

for line in lines:
    time_window, text = line.split('\n')[:2]
    start, end = time_window.split(',')
    start = round(fps * (datetime.strptime('0' + start + '000', frmt) - basetime).total_seconds())
    end = round(fps * (datetime.strptime('0' + end[:-1] + '000', frmt) - basetime).total_seconds())
    index += struct.pack('<I', start) + struct.pack('<I', end) + struct.pack('<I', offset)
    offset += len(text) + 1
    data += text + '\0'

with open(outfile, 'wb') as subFile:
    subFile.write(struct.pack('<I', numberOflines) + index + data)

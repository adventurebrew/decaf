import struct
import os
import sys
import errno

from utils import readcstr

def create_directory(name):
    try:
        os.makedirs(name)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

def extract_pak(filename):
    with open(filename, 'rb') as pakFile:
        offsets = []
        names = []
        offsets.append(struct.unpack('<I', pakFile.read(4))[0])
        names.append(readcstr(pakFile))
        while pakFile.tell() < offsets[0]:
            off = struct.unpack('<I', pakFile.read(4))[0]
            name = readcstr(pakFile)
            offsets.append(off)
            if not name:
                break

            names.append(name)

        # pakFile.seek(offsets[0])

        dirname = filename[:-4]
        create_directory(dirname)
        i = 0
        with open(dirname + '/' + dirname + '.IDX', 'w') as idxFile:
            idxFile.writelines('\n'.join(names) + '\n')

        for off, name in zip(offsets, names):
            pakFile.seek(off)
            with open(dirname + '/' + name, 'wb') as outFile:
                outFile.write(pakFile.read(offsets[i+1] - off))
            i += 1


def pak_folder(name):
    with open(name + '/' + name + '.IDX', 'r') as idxFile:
        files = idxFile.readlines()
    files = [file[:-1] for file in files]

    numOfFiles = len(files)
    off = (numOfFiles * 4) + sum(len(f) + 1 for f in files) + 9
    offs = ''
    data = ''
    for f in files:
        with open(name + '/' + f, 'rb') as inFile:
            current = inFile.read()
            offs += struct.pack('<I', off) + f + '\x00'
            off += len(current)
            data += current
    offs += struct.pack('<I', off) + '\x00\x00\x00\x00\x00'

    with open(name + '-NEW.PAK', 'wb') as pakFile:
        pakFile.write(offs)
        pakFile.write(data)

if __name__ == '__main__':
    try:
        action = sys.argv[1]
        name = sys.argv[2]

    except IndexError as e:
        print('Usage:\n' + 'python toonpak.py -u FILE.PAK')
        print('Usage:\n' + 'python toonpak.py -p DIRECTORY')
        exit(1)

    if not os.path.exists(name):
        print('Error: file \'{}\' does not exists.'.format(name))
        exit(1)

    if action == '-u':
        extract_pak(name)

    elif action == '-p':
        pak_folder(name)

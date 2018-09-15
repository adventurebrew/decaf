import struct
import os
import sys
import errno
import io
import lzss
import png

from image import save_image, read_image

BG = ['BG1', 'BG2']

def mkcaf(name):
    crds = []
    with open('coords.txt', 'rb') as crdFile:
        coords = crdFile.readlines()
    for crd in coords:
        crds.append([int(c) for c in crd[:-1].split()])

    with open(name, 'rb') as imFile:
        width, height, data, palette = read_image(imFile)

    binPalette = ''.join(struct.pack('<B', x) for color in palette for x in color)
    im = []
    bg = ['BG1']
    h = height
    t = 0
    for line in data:
        t += 1
        lvals = ['BG' if color in BG else color for color in line]
        im.append(lvals)
        if h == height and line[-1:] != bg:
            h = t - 1

    numFrames = height / h

    print h, numFrames
    x1 = 0
    x2 = width - 1
    y1 = 0
    y2 = h - 1

    data = ''
    for fn in range(numFrames):
        char = []
        _y1 = 0
        _y2 = y2
        _x1 = 0
        _x2 = x2

        for i, line in enumerate(im[h*fn:h*fn+h-1]):
            line = line[:-1]
            char.append(line)
        while char and char[-1] == ['BG'] * x2:
            char = char[:-1]
            _y2 -= 1
        while char and char[0] == ['BG'] * x2:
            char = char[1:]
            _y1 += 1
        if char:
            cchar = char[0]
            while cchar and cchar[-1] == 'BG':
                cchar = cchar[:-1]
                _x2 -= 1
            while cchar and cchar[0] == 'BG':
                cchar = cchar[1:]
                _x1 += 1
            char = [c[_x1:_x2] for c in char]
        #print _x1, _y1, _x2, _y2
        char = ''.join([struct.pack('<B', c) for line in char for c in line])
        compressedSize = len(char)
        _ref = -1
        if compressedSize == 0:
            _x1, _y1, _x2, _y2, _ref = crds[fn]
        frame = '\x78\x56\x34\x12' + struct.pack('<i', _ref)
        frame += struct.pack('<I', compressedSize) + struct.pack('<I', compressedSize)
        frame += struct.pack('<I', _x1) + struct.pack('<I', _y1)
        frame += struct.pack('<I', _x2) + struct.pack('<I', _y2)
        frame += char
        data += frame
    compressedBytes = len(data)
    header = 'KevinAguilarV1' + '\x00\x00' + struct.pack('<I', 32)
    header += struct.pack('<I', compressedBytes) + struct.pack('<I', compressedBytes)
    header += struct.pack('<I', numFrames)
    header += struct.pack('<I', x1) + struct.pack('<I', y1)
    header += struct.pack('<I', x2) + struct.pack('<I', y2)
    header += struct.pack('<I', 0) + struct.pack('<I', 0)
    header += struct.pack('<I', len(palette)) + struct.pack('<I', 8)
    header += struct.pack('<I', len(binPalette)) + binPalette
    data = header + data
    with open('TOONFONT-NEW.CAF', 'wb') as fntFile:
        fntFile.write(data)


def decaf(name):
    with open(name, 'rb') as cafFile:

        header = cafFile.read(68)
        cafFile.seek(0)

        version = cafFile.read(16)
        headerSize = struct.unpack('<I', cafFile.read(4))[0]
        uncompressedBytes = struct.unpack('<I', cafFile.read(4))[0]
        compressedBytes = struct.unpack('<I', cafFile.read(4))[0]
        numFrames = struct.unpack('<I', cafFile.read(4))[0]
        x1 = struct.unpack('<I', cafFile.read(4))[0]
        y1 = struct.unpack('<I', cafFile.read(4))[0]
        x2 = struct.unpack('<I', cafFile.read(4))[0]
        y2 = struct.unpack('<I', cafFile.read(4))[0]

        cafFile.seek(8, 1) # skip zeros
        paletteEntries = struct.unpack('<I', cafFile.read(4))[0]
        fps = struct.unpack('<I', cafFile.read(4))[0]
        paletteSize = struct.unpack('<I', cafFile.read(4))[0]
        palette = cafFile.read(paletteSize)
        colors = [struct.unpack('<B', x)[0] for x in palette]
        colors = [colors[3*idx:3*idx+3] for idx in range(len(colors)/3)]
        data = cafFile.read()
        if uncompressedBytes > compressedBytes:
            data = lzss.decompress(data, uncompressedBytes)
            data = ''.join(data)

    chars = []
    maxWidth = x1 + x2 + 1
    maxHeight = y1 + y2 + 1
    final = []
    sane = 0

    decomp = ''

    if (struct.unpack('<I', data[:4])[0] == 0x12345678):
        for t in range(numFrames):
            _decomp = data[:headerSize]
            _decomp = _decomp[:8] + _decomp[12:16] + _decomp[12:]

            decomp += _decomp

            bg = [BG[t % 2]]
            oldRef = struct.unpack('<i', data[4:8])[0]
            compressedSize = struct.unpack('<I', data[8:12])[0]
            decompressedSize = struct.unpack('<I', data[12:16])[0]
            _x1 = struct.unpack('<I', data[16:20])[0]
            _y1 = struct.unpack('<I', data[20:24])[0]
            _x2 = struct.unpack('<I', data[24:28])[0]
            _y2 = struct.unpack('<I', data[28:32])[0]
            print _x1, _y1, _x2, _y2, oldRef

            if oldRef != -1 or decompressedSize == 0:
                _ref = oldRef
                _data = ''
                final += [bg * maxWidth] * maxHeight
            else:
                _ref = -1
                _data = data[headerSize:headerSize+compressedSize]
                if compressedSize < decompressedSize:
                    _data = lzss.decompress(_data, decompressedSize)

                a = [struct.unpack('<B', x)[0] for x in _data]
                b = []
                for x in a:
                    idx = 3 * x
                    b += [x] # colors[idx:idx+3]

                _data = ''.join(_data)
                width = _x2 - _x1
                height = _y2 - _y1

                c = [b[l*width:l*width+width] for l in range(height)]
                
                final += [bg * maxWidth] * _y1
                for line in c:
                    final += [(bg * _x1) + line + (bg * (maxWidth - _x2))]
                final += [bg * maxWidth] * (maxHeight - _y2)

                chars.append(c)
                decomp += _data

            data = data[headerSize + compressedSize:]
            sane += maxHeight

    save_image(name[:-4] + '.PNG', (maxWidth, maxHeight * numFrames, final), colors)

if __name__ == '__main__':
    try:
        action = sys.argv[1]
        name = sys.argv[2]

    except IndexError as e:
        print('Usage:\n' + 'python -d decaf.py FILE.CAF')
        exit(1)

    if not os.path.exists(name):
        print('Error: file \'{}\' does not exists.'.format(name))
        exit(1)

    if action == '-d':
        decaf(name)
    elif action == '-c':
        mkcaf(name)

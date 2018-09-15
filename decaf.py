import struct
import os
import sys
import errno
import io
import lzss
import png

def save_image(filename, data):
    width, height, lines = data
    with open(filename, 'wb') as outFile:
        wr = png.Writer(width, height)
        wr.write(outFile, lines)

def read_image(stream):
    w = png.Reader(stream)
    r = w.read()
    lines = list(r[2])
    size = r[3]['size']

    width, height = size
    data = []
    for line in lines:
        row = list(line)
        if row[-1] == 255:
            row = [a for idx, a in enumerate(row) if idx % 4 != 3]
        data.append(row)
    return width, height, data

def mkcaf(name):
    crds = []
    with open('coords.txt', 'rb') as crdFile:
        coords = crdFile.readlines()
    for crd in coords:
        crds.append([int(c) for c in crd[:-1].split()])

    with open(name[:-4] + '.PLT') as pltFile:
        palette = pltFile.read()
    colors = [struct.unpack('<B', x)[0] for x in palette]
    colors = [colors[3*i:3*i+3] for i in range(len(palette) / 3)]
    with open(name, 'rb') as imFile:
        width, height, data = read_image(imFile)
    im = []
    bg = [112, 146, 190]
    h = height
    t = 0
    for line in data:
        size = len(line) / 3
        lvals = []
        t += 1
        for i in range(size):
            idx = 3*i
            color = line[idx:idx+3]
            value = colors.index(color) if color in colors else 'BG'
            lvals.append(value)
        im.append(lvals)
        if h == height and line[-3:] != bg:
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
    header += struct.pack('<I', len(colors)) + struct.pack('<I', 8)
    header += struct.pack('<I', len(palette)) + palette
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
        # print paletteSize, paletteEntries, paletteSize / paletteEntries
        colors = [struct.unpack('<B', x)[0] for x in palette]
        data = cafFile.read()
        if uncompressedBytes > compressedBytes:
            data = lzss.decompress(data, uncompressedBytes)
            data = ''.join(data)
    

    #with open('DECOMP.BIN', 'wb') as dcmFile:
    #    dcmFile.write(data)

    chars = []
    maxWidth = x1 + x2 + 1
    maxHeight = y1 + y2 + 1
    final = []
    sane = 0

    decomp = '' # decomp[:28] + decomp[24:28] + decomp[32:]

    # decomp += palette

    if (struct.unpack('<I', data[:4])[0] == 0x12345678):
        for t in range(numFrames):
            _decomp = data[:headerSize]
            _decomp = _decomp[:8] + _decomp[12:16] + _decomp[12:]

            decomp += _decomp

            bg = [112, 146, 190] if t % 2 == 0 else [128, 128, 192]
            oldRef = struct.unpack('<i', data[4:8])[0]
            compressedSize = struct.unpack('<I', data[8:12])[0]
            decompressedSize = struct.unpack('<I', data[12:16])[0]
            _x1 = struct.unpack('<I', data[16:20])[0]
            _y1 = struct.unpack('<I', data[20:24])[0]
            _x2 = struct.unpack('<I', data[24:28])[0]
            _y2 = struct.unpack('<I', data[28:32])[0]
            print _x1, _y1, _x2, _y2, oldRef

            if oldRef != -1 or decompressedSize == 0:
                # print decompressedSize == 0
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
                    b += colors[idx:idx+3]

                _data = ''.join(_data)
                width = _x2 - _x1
                height = _y2 - _y1

                c = [b[3*l*width:3*l*width+3*width] for l in range(height)]
                
                final += [bg * maxWidth] * _y1
                for line in c:
                    final += [(bg * _x1) + line + (bg * (maxWidth - _x2))]
                final += [bg * maxWidth] * (maxHeight - _y2)

                chars.append(c)
                decomp += _data

            data = data[headerSize + compressedSize:]
            sane += maxHeight

    with open(name[:-4] + '.PLT', 'wb') as pltFile:
        pltFile.write(palette)

    dSize = struct.pack('<I', len(decomp))
    decomp = header[:20] + dSize + dSize + header[28:] + palette + decomp

    with open('decomp2.bin', 'wb') as pltFile:
        pltFile.write(decomp)

    save_image(name[:-4] + '.PNG', (maxWidth, maxHeight * numFrames, final))

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

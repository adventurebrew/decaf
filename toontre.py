import struct
import os
import sys
import errno

import binascii

from utils import readcstr

def parse_meta(meta):
    a = struct.unpack('<H', meta[-2:])[0]
    b = -2 - 4 * a
    c = b - 2
    numParticipants = struct.unpack('<H', meta[c:c+2])[0]

    e = c - 2 - 4 * numParticipants
    something = struct.unpack('<H', meta[e:e+2])[0]

    cc = c
    for _ in range(numParticipants - 1):
        listenerId = struct.unpack('<H', meta[cc-2:cc])[0]
        cc -= 4

    talkerId = struct.unpack('<H', meta[cc-2:cc])[0]

    for _ in range(numParticipants - 1):
        listenerId = struct.unpack('<H', meta[c-2:c])[0]
        listenerAnimId = struct.unpack('<H', meta[c-4:c-2])[0]
        c -= 4

    talkerId = struct.unpack('<H', meta[c-2:c])[0]
    talkerAnimId = struct.unpack('<H', meta[c-4:c-2])[0]
    return {'participants' : numParticipants, 'something': something, 'talker': talkerId, 'anim': talkerAnimId}

def extract_tre(filename):
    with open(filename, 'rb') as pakFile:
        voices = []
        offsets = []
        texts = []

        numOfTexts = struct.unpack('<H', pakFile.read(2))[0]
        for _ in range(numOfTexts):
            voices.append(struct.unpack('<H', pakFile.read(2))[0])


        for _ in range(numOfTexts):
            offsets.append(struct.unpack('<H', pakFile.read(2))[0])

        metas = [pakFile.read(offsets[0] - pakFile.tell())]
        li = 0
        for line in offsets:
            pakFile.seek(line)
            texts.append(readcstr(pakFile))

            # keep meta data
            currentLoc = pakFile.tell()
            if li < numOfTexts - 1:
                metas.append(pakFile.read(offsets[li + 1] - currentLoc))
            li += 1

    return voices, metas, texts

def extract_txt(filename):
    with open(filename, 'r') as txtFile:
        lines = txtFile.readlines()
    
    voices = []
    metas = []
    texts = []
    offsets = []

    numOfTexts = len(lines)
    off = 2 + (4 * numOfTexts)
    for line in lines:
        voice, meta, text = line.split('\t')
        voice = int(voice, 16)
        meta = binascii.unhexlify(meta)
        text = text[:-1]
        voices.append(voice)
        metas.append(meta)
        texts.append(text)
        off += len(meta)
        offsets.append(off)
        off += len(text) + 1

    with open('output.tre', 'wb') as outFile:
        outFile.write(struct.pack('<H', numOfTexts))
        for voice in voices:
           outFile.write(struct.pack('<H', voice)) 
        for off in offsets:
           outFile.write(struct.pack('<H', off))
        for meta, text in zip(metas, texts):
            outFile.write(meta)
            outFile.write(text + '\x00')


if __name__ == '__main__':
    try:
        action = sys.argv[1]
        filename = sys.argv[2]

    except IndexError as e:
        print('Usage:\n' + 'python toontre.py -u FILE.TRE')
        print('Usage:\n' + 'python toontre.py -t FILE.TXT')
        exit(1)

    if not os.path.exists(filename):
        print('Error: file \'{}\' does not exists.'.format(filename))
        exit(1)

    if action == '-u':
        voices, metas, texts = extract_tre(filename)

        # print output
        for off, meta, line in zip(voices, metas, texts):
            print '{:04x}'.format(off) + '\t' + binascii.hexlify(meta) + '\t' + line

    elif action == '-t':
        extract_txt(filename)


    else:
        print 'Unknown action.'

import os
import binascii
import struct

from toontre import extract_tre, parse_meta

if __name__ == '__main__':
    files = os.listdir('.')

    SEP = '\t|\t'
    for filename in files:
        voices, metas, texts = extract_tre(filename)

        # print output
        for off, meta, line in zip(voices, metas, texts):
            data = [
                filename,
                parse_meta(meta)['talker'], # for convenience, ignored when importing back
                '{:04x}'.format(off),
                binascii.hexlify(meta),
                line.replace('"', '^')
            ]
            print(SEP.join(data))


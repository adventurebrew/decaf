import struct

def signed(num):
    return struct.unpack('<h', struct.pack('<H', num))[0]

def decompress(data, size):
    short = 256 * 256
    res = [0 for _ in range(size)]
    srcoff = 0
    dstoff = 0
    ln = 0
    while size > 0:
        bitbuf = 0x100 | struct.unpack('<B', data[srcoff])[0]
        srcoff += 1
        bitbuf = bitbuf % short
        while bitbuf != 1 and size > 0:
            if bitbuf & 1:
                ofs = struct.unpack('<H', data[srcoff:srcoff+2])[0]
                ofs = ofs % short
                srcoff += 2
                ln = ((ofs & 0xF000) >> 12) + 3
                ln = ln % (short * short)
                ofs = ofs | 0xF000
                ofs = ofs % (short * short)
                size -= ln
                if (size < 0):
                    break
                for _ in range(ln):
                    ln -= 1
                    res[dstoff] = res[dstoff + signed(ofs)]
                    dstoff += 1
            else:
                ln = 0
                while (bitbuf & 2) == 0:
                    ln += 1
                    ln = ln % (short * short)
                    bitbuf >>= 1
                    bitbuf = bitbuf % short
                ln += 1
                ln = ln % (short * short)
                size -= ln
                if (size < 0):
                    break
                for _ in range(ln):
                    ln -= 1
                    res[dstoff] = data[srcoff]
                    dstoff += 1
                    srcoff += 1
            bitbuf >>= 1
            bitbuf = bitbuf % short
    ln += size
    if len < 0:
        return 0
    for _ in range(ln):
        res[dstoff] = data[srcoff]
        dstoff += 1
        srcoff += 1
    return res

# TODOL implement lzss compression
def compress(data, size):
    pass
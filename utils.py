
def readcstr(f):
    buf = bytearray()
    while True:
        b = f.read(1)
        if b is None or b == '\0' or not b:
            return str(buf)
        else:
            buf.append(b)

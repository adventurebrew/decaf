import png

ORIG_BG = [0, 255, 255]

s_map = {
    'BG1': 19,
    'BG2': 29
}

bg_map = {
    'BG1': [112, 146, 190],
    'BG2': [128, 128, 192]
}

def getColor(x):
    if x in s_map:
        return s_map[x]
    return x

def getBG(x):
    b_map = {v: k for k, v in s_map.iteritems()}
    if x in b_map:
        return b_map[x]
    return x

def save_image(filename, data, palette):
    for k, v in s_map.iteritems():
        palette[v] = bg_map[k]

    width, height, lines = data

    lines = [[getColor(x) for x in line] for line in lines]

    with open(filename, 'wb') as outFile:
        wr = png.Writer(width, height, palette=palette)
        wr.write(outFile, lines)

def read_image(stream):
    w = png.Reader(stream)
    r = w.read()
    lines = list(r[2])
    size = r[3]['size']
    palette = list(r[3]['palette'])

    for _, v in s_map.iteritems():
        palette[v] = ORIG_BG

    width, height = size

    data = [[getBG(color) for color in line] for line in lines]
    return width, height, data, palette

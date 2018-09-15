import png


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
    if x == 19:
        return 'BG1'
    if x == 29:
        return 'BG2'
    return x

def save_image(filename, data, palette):
    palette[s_map['BG1']] = bg_map['BG1']
    palette[s_map['BG2']] = bg_map['BG2']
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

    palette[s_map['BG1']] = [0, 255, 255]
    palette[s_map['BG2']] = [0, 255, 255]

    width, height = size

    data = [list(line) for line in lines]
    data = [[getBG(color) for color in line] for line in lines]
    data = [[getBG(color) for color in line] for line in lines]
    return width, height, data, palette
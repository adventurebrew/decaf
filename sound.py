import io

from functools import partial

import struct

import wave

AUD_STEREO = 1
AUD_16BIT = 2

def read_uint16le(stream):
    return int.from_bytes(stream.read(2), byteorder='little', signed=False)

def read_uint32le(stream):
    four = stream.read(4)
    if not four:
        return None
    return int.from_bytes(four, byteorder='little', signed=False)

def read_index(stream):
    offsets = list(iter(partial(read_uint32le, stream), None))
    sizes = [(end - start) for start, end in zip(offsets, offsets[1:])]
    return zip(offsets, sizes)

def clip(lower, upper, value):
    return lower if value < lower else upper if value > upper else value

def read_aud_header(stream):
    freq = read_uint16le(stream)
    size = read_uint16le(stream)
    output_size = read_uint16le(stream)
    flags = ord(stream.read(1))
    typ = ord(stream.read(1))
    return freq, size, output_size, flags, typ

ima_table = [
        7,    8,    9,   10,   11,   12,   13,   14,
       16,   17,   19,   21,   23,   25,   28,   31,
       34,   37,   41,   45,   50,   55,   60,   66,
       73,   80,   88,   97,  107,  118,  130,  143,
	  157,  173,  190,  209,  230,  253,  279,  307,
	  337,  371,  408,  449,  494,  544,  598,  658,
      724,  796,  876,  963, 1060, 1166, 1282, 1411,
     1552, 1707, 1878, 2066, 2272, 2499, 2749, 3024,
     3327, 3660, 4026, 4428, 4871, 5358, 5894, 6484,
     7132, 7845, 8630, 9493,10442,11487,12635,13899,
    15289,16818,18500,20350,22385,24623,27086,29794,
    32767
]


step_adjust = [
    -1, -1, -1, -1, 2, 4, 6, 8,
    -1, -1, -1, -1, 2, 4, 6, 8
]


def to_signed32(n):
    n = n & 0xffffffff
    return (n ^ 0x80000000) - 0x80000000

def convert_aud2wav(stream):
    freq, size, output_size, flags, typ = read_aud_header(stream)
    channels = 2 if flags & AUD_STEREO else 1
    bits = 16 if flags & AUD_16BIT else 8
    print(freq, size, output_size, channels, bits, typ)

    sample_value = 0
    step_index = 0

    with io.BytesIO() as out:
        while True:
            compressed_size = stream.read(2)
            if not compressed_size:
                break
            compressed_size = int.from_bytes(compressed_size, byteorder='little', signed=True)
            decompressed_size = int.from_bytes(stream.read(2), byteorder='little', signed=True)
            f = stream.read(4)
            assert f == b'\xaf\xde\x00\x00', f

            for comm in stream.read(compressed_size):
                codes = comm & 0xf, (comm & 0xf0) >> 4
                for code in codes:
                    sample = code & 0x7
                    step = ima_table[step_index]

                    E = step >> 3
                    if sample & 4:
                        E += step
                    if sample & 2:
                        E += step >> 1
                    if sample & 1:
                        E += step >> 2

                    # E = to_signed32(E % 2 ** 32)

                    step_index += step_adjust[sample]
                    step_index = clip(0, len(ima_table) - 1, step_index)

                    sample_value = sample_value - E if code & 0x8 else sample_value + E
                    sample_value = clip(-32768, 32767, sample_value)

                    out.write(sample_value.to_bytes(2, byteorder='little', signed=True))
        return freq, channels, out.getvalue()

with open('sounds/TROPHYRM/TROPHYRM.SVI', 'rb') as index_file:
    index = read_index(index_file)

write_raw_ima_adpcm = False

with open('sounds/TROPHYRM/TROPHYRM.SVL', 'rb') as stream_file:
    for idx, (offset, size) in enumerate(index):

        aud = stream_file.read(size)
        print(len(aud) - 8)
        if (write_raw_ima_adpcm):
            with open(f'sounds/TROPHYRM/TROPHYRM.{idx:04d}.AUD', 'wb') as out_file:
                out_file.write(aud)

        with io.BytesIO(aud) as stream:
            freq, channels, wav = convert_aud2wav(stream)
        with wave.open(f'sounds/TROPHYRM/TROPHYRM.{idx:04d}.WAV', 'w') as out_file:
            out_file.setnchannels(channels)
            out_file.setsampwidth(2) 
            out_file.setframerate(freq)
            out_file.writeframesraw(wav)

import sys

src = sys.argv[1]
mask = int(sys.argv[2])
_buffer = bytearray(1)

with open(src, 'rb') as f:
    num_bytes_read = f.readinto(_buffer)

    while num_bytes_read > 0:
        _buffer[0] = (_buffer[0]^mask)
        sys.stdout.buffer.write(_buffer)
        num_bytes_read = f.readinto(_buffer)



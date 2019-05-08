import sys
from zlib import crc32

src = sys.argv[1]

with open(src, 'rb') as f:
    data = f.read()
    checksum = crc32(data)

print(checksum)

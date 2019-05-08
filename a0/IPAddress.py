import sys

ip = sys.argv[1]

def binary_to_decimal(binary_num):
    return int(binary_num, 2)

# Split the IP address into four parts
ip_split = [ip[i*8:(i+1)*8] for i in range(4)]

# Convert each part to decimal
result = '.'.join(str(binary_to_decimal(x)) for x in ip_split)
print(result)


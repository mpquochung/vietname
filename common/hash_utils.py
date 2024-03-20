import hashlib
import mmh3
import random
import time

"""
Utility to get hash from any string
"""


def get_mmh3(s):
    shex = str(hex(mmh3.hash128(s.encode('utf-8'))))
    return shex[2:len(shex) - 1]


def get_random_mm3(s):
    return get_mmh3('%s_%s_%s' % (time.time(), random.random(), s))


def get_mmh3_tiny(s):
    shex = str(hex(mmh3.hash(s.encode('utf-8'))))
    return shex[2:len(shex) - 1]


def get_mmh3_10(s):
    """10 last chars of mmh3 hash 128
    Conflict ratio over 10'000'000: 0.00044
    """
    return get_mmh3(s)[-10:]


def get_md5(s):
    m = hashlib.md5()
    m.update(s.encode('utf-8'))
    return m.hexdigest()


def get_sha256(s):
    return hashlib.sha256(s.encode('utf-8')).hexdigest()


def check_conflict():
    num = 1000000
    keys = {}
    for i in range(0, num):
        h = get_mmh3_10(str(i))
        if h not in keys:
            keys[h] = [i]
        else:
            keys[h].append(i)
            print('Conflict:', h, keys[h])
    print('Ratio:', (num - len(keys)) * 100.0 / num)


def main():
    print(get_random_mm3(1))
    print(get_mmh3('hello'))
    print(get_mmh3_tiny('hello'))
    print(get_mmh3_10('hello'))
    print(get_md5('hello'))
    print(get_sha256('hello'))

    print(get_mmh3('foo'))
    print(get_md5('foo'))
    check_conflict()


if __name__ == '__main__':
    main()

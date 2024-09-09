import jidouteki
from functools import wraps
from typing import List
from pathlib import Path
from flask import abort

def xor(a, b):
    a = bytes(a, "utf-8")
    b = bytes(b, "utf-8")
    return bytes([a ^ b for a,b in zip(a,b)])

def count_starting(s: str | bytes, c):
    sub = c
    while s.startswith(sub):
        sub += c
    return len(sub)-1

def base_substr(lst):
    if len(lst) == 0: return '' 
    first = lst[0]
    xored = [xor(first, other) for other in lst[1:]]
    x = min(count_starting(s, b"\x00") for s in xored)
    return first[:x]

def config_from_key(configs: List[jidouteki.Config]):
    def _config_from_key(f):
        @wraps(f)
        def __config(config_key, *args, **kwargs):
            c: jidouteki.Config = next((c for c in configs if c.meta.key == config_key), None)
            if c == None: return abort(400)
            result = f(c, *args, **kwargs)
            return result
        return __config
    return _config_from_key
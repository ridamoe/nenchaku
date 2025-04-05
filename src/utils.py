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
    if len(lst) <= 1: return ''
    first = lst[0]
    xored = [xor(first, other) for other in lst[1:]]
    x = min(count_starting(s, b"\x00") for s in xored)
    return first[:x]

def provider_from_key(providers: List[jidouteki.Provider]):
    def _config_from_key(f):
        @wraps(f)
        def __config(provider_key, *args, **kwargs):
            p: jidouteki.Provider = next((c for c in providers if c.meta.key == provider_key), None)
            if p == None: return abort(400)
            result = f(p, *args, **kwargs)
            return result
        return __config
    return _config_from_key
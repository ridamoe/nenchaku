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

def website_from_key(websites: List[jidouteki.Website]):
    def _website_from_key(f):
        @wraps(f)
        def __website(website_key, *args, **kwargs):
            w: jidouteki.Website = next((w for w in websites if w.metadata.key == website_key), None)
            if w == None: return abort(400)
            result = f(w, *args, **kwargs)
            return result
        return __website
    return _website_from_key
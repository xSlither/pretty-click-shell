from typing import List

import os
import re

from .types import HiddenPassword


def ExtractPasswordAndSetEnv(env: str, p: object) -> str:
    password = ''
    if isinstance(p, HiddenPassword):
        password = p.password
    else: password = p

    os.environ[env] = password
    return password


def HasKey(key, obj) -> bool:
    try: 
        try: return key in obj
        except: 
            try: return getattr(obj, key, None) != None
            except: return obj[key] != None
    except: return False


#------------------------------------------------------------------------------
#  ANCHOR String Utilities

def replacenth(string, sub, wanted, n):
    where = [m.start() for m in re.finditer(sub, string)][n-1]
    before = string[:where]
    after = string[where:]
    after = after.replace(sub, wanted, 1)
    return before + after

def suggest(keys: List[str], flag: str):
    suggestion = None

    def alg():
        ret = None
        __keys: List[str] = []

        if len(flag) > 2:
            for key in keys:
                if flag in key: 
                    if not ret: ret = key
                    else: ret += ', ' + key
            if ret: return ret

            if len(flag) <= 16:
                _flag_ = flag
                while len(_flag_) > 2:
                    _flag_ = _flag_[round(len(_flag_) / 4) + 1:]
                    if not len(_flag_) > 2: break
                    for key in keys:
                        if _flag_ in key: 
                            if not ret: 
                                ret = key
                                __keys.append(key)
                            elif not HasKey(key, __keys):
                                ret += ', ' + key
                                __keys.append(key)
                if ret: return ret

            for i in range(0, len(flag), 3):
                try:
                    _flag_ = flag[i: 3 + i]
                    if not len(_flag_) > 2: break
                    for key in keys:
                        if _flag_ in key:
                            if not ret: 
                                ret = key
                                __keys.append(key)
                            elif not HasKey(key, __keys): 
                                ret += ', ' + key
                                __keys.append(key)
                except: break
            if ret: return ret
        return None

    suggestion = alg()
    if suggestion: 
        if not ',' in suggestion:
            return suggestion
        else:
            index = suggestion.count(',')
            return replacenth(suggestion, ',', ', or', index)
    return None

#------------------------------------------------------------------------------
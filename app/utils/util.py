from flask import Response
from json import dumps
from collections import OrderedDict
from typing import List, Optional


def make_response(data, code=None, type='application/json'):
    resp = Response(dumps(data, ensure_ascii=False),mimetype=type)
    if code:
        resp.status_code = code
    return resp

def case_insensitive_dedupe_first(lst: Optional[List[str]]) -> List[str]:
    if not isinstance(lst, list):
        return []

    seen = OrderedDict()
    for item in lst:
        if not isinstance(item, str):
            continue
        lower_item = item.casefold()
        if lower_item not in seen:
            seen[lower_item] = item
    return list(seen.values())
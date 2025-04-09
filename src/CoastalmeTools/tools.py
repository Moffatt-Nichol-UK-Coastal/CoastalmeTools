import re


def find_var(dict, query, case=False):
    if case:
        results = {key: val for key, val in dict.items() if re.search(query, key)}
    else:
        results = {key: val for key, val in dict.items() if re.search(query, key, re.I)}
    if len(results) == 0:
        raise KeyError("No matches for: {}".format(query))
    if len(results) != 1:
        raise KeyError(
            "Multiple matches for variable in input file: {}".format(
                list(results.keys())
            )
        )

    out = next(iter(results.values()))

    if ";" in out:
        out = out.partition(";")[0]

    return out

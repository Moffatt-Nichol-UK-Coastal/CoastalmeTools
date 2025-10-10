import re


def find_var(dict, querys, case=False):
    """find a variable in a dictionary

    Args:
        dict (dictionary of config variables): 
        querys (either string or list of strings to iterativley search for): 
        case (do we want to enfoce case sensitivity): 

    Returns:
        the matching value 
        

    Raises:
        KeyError: of multiple results are found 
    """
    if not isinstance(querys, list):
        querys = querys.split(" ")
    for query in querys:
        if case:
            results = {key: val for key, val in dict.items() if re.search(query, key)}
        else:
            results = {key: val for key, val in dict.items() if re.search(query, key, re.I)}
        if len(results) == 1:
            # we have found a unique match
            # remove any trailing comment on the line
            out = next(iter(results.values()))
            # Only strip comments if the value is a string
            if isinstance(out, str) and ";" in out:
                out = out.partition(";")[0]
            return out
        dict = results
    if len(results) == 0:
        raise KeyError("No matches for: {}".format(query))

    raise KeyError(
        "Multiple matches for variable in input file: {}".format(
            list(results.keys())
        )
    )

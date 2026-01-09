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
        # Create a flexible regex pattern where spaces or underscores match either
        # Escape the query first to handle special regex characters, then replace separators
        safe_query = re.escape(query)
        # Replace escaped space '\ ' and escaped underscore '\_' with '[ _]'
        # Note: re.escape might behave differently on different python versions regarding _
        # Simpler approach: replace literal space and underscore with [ _] in the raw string if we trust input isn't complex regex
        # Given existing code uses re.search directly on input, it assumes input might be regex or simple string.
        # Let's just replace space and underscore with [ _]
        pattern = query.replace(" ", "[ _]").replace("_", "[ _]")
        
        if case:
            results = {key: val for key, val in dict.items() if re.search(pattern, key)}
        else:
            results = {key: val for key, val in dict.items() if re.search(pattern, key, re.I)}
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

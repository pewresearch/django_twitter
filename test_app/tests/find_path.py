def get_recursively(search_dict, field):
    """
    Takes a dict with nested lists and dicts,
    and searches all dicts for a key of the field
    provided.
    """
    fields_found = []
    key_path = []

    for key, value in search_dict.iteritems():
        if key == field:
            fields_found.append(value)
            new_str = str(key) + "/"
            key_path.append(new_str)

        elif isinstance(value, dict):
            results, path = get_recursively(value, field)
            for result in results:
                fields_found.append(result)
            for road in path:
                new_str = str(key) + "/" + road
                key_path.append(new_str)

        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    more_results, more_path = get_recursively(item, field)
                    for another_result in more_results:
                        fields_found.append(another_result)
                    for another_road in more_path:
                        new_str = str(key) + "/" + another_road
                        key_path.append(new_str)

    return fields_found, key_path

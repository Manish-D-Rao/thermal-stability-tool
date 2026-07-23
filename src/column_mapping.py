def match_typed_name(typed_name, columns):
    typed_clean = typed_name.strip().lower()
    for col in columns:
        if str(col).strip().lower() == typed_clean:
            return col
    return ""


def build_rename_map(typed_values, columns):
    rename_map = {}
    missing_parameters = []

    for param_name, typed in typed_values.items():
        typed = typed.strip()
        if typed == "":
            missing_parameters.append(param_name)
            continue
        actual_col = match_typed_name(typed, columns)
        if actual_col == "":
            missing_parameters.append(param_name)
            continue
        rename_map[actual_col] = param_name

    return rename_map, missing_parameters
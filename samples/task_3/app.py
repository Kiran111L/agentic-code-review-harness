def read_config(path):
    handle = open(path, "r", encoding="utf-8")
    data = handle.read()
    parsed = parse_config(data)
    handle.close()
    return parsed

def parse_config(data):
    if not data:
        raise ValueError("empty config")
    return {"raw": data}

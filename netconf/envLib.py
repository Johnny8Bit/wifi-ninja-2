

def read_config_file(config_file="../config.ini"):

    config_data = {}
    
    with open(config_file, 'r') as cf:
        for line in cf.readlines():
            if line[0] in ("#", "\n", " "):
                continue
            else:
                config = line.split("=")
                config_data[config[0]] = config[1].rstrip("\n")

    return config_data

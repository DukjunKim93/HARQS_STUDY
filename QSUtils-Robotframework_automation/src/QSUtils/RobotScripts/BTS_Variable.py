import configparser


def get_variables(file_name):
    config = configparser.ConfigParser()
    config.read(file_name, encoding="UTF8")

    variables = {}
    with open("BTS_Device_Settings.py", "w", encoding="UTF8") as settings:
        for section in config.sections():
            variables[section] = dict(config.items(section))
            print(f"${{{section}}} : {repr(variables[section])}")
            settings.write("%s = %s\n" % (section, repr(dict(config.items(section)))))

    return variables

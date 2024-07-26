def strToBool(str):
    trueKeywords = ['true', '1', 'y', 'yes', 'yeah', 'yup', 'certainly', 'uh-huh']
    return str.lower() in trueKeywords
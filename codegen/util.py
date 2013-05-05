import yaml

def load_yaml(path):
    fd = open(path, 'r')
    d = yaml.load(fd)
    fd.close()

    return d

def inject_st_with_dict(template, dct):
    """
    Adds each member of a dictionary to an :class:`org.stringtemplate.v4.ST`
    instance.
    """
    for k,v in dct.items():
        template.add(k, v)

    return template
        

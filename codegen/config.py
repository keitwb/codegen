import os
from optparse import OptionParser
from .exceptions import InvalidConfigurationError, CodegenError
from .util import load_yaml
from yaml import YAMLError


DEFAULT_CONFIG_FILENAME = 'codegen.yaml'
DEFAULT_TEMPLATE_DIR = 'codegen_tmpl'
DEFAULT_MODEL_FILENAME = 'codegen_model.yaml'


class CommandLineConfig(object):
    def __init__(self):
        usage = """usage: %prog [options] TEMPLATES...
        Renders the templates in templates.yaml.  TEMPLATES indicates the names of
        the templates to render, if present.  
        """
        parser = OptionParser(usage=usage)

        parser.add_option("-d", "--basedir", dest="base_dir", 
                help="the base directory of the project")
        parser.add_option("-c", "--config", dest="config_file",
                default=DEFAULT_CONFIG_FILENAME, help="The configuration file to use")
        #parser.add_option("-t", "--type", dest="types", action="append",
            #help="The type of templates to render (android, server, webapp)")
        parser.add_option("-f", "--force", action="store_true", dest="force",
                help="force the templates to rerender")
        parser.add_option("-p", "--pretty", action="store_true", dest="pretty_print",
                help="run the output through an appropriate code formatter if available")
        parser.add_option("-s", "--model-file", dest="model_file", 
                help="filename for the model(s) to be used when processing the templates")
        parser.add_option("-t", "--template-dir", dest="template_dir",
                help="The directory the template files are in.")
        parser.add_option("-v", "--verbose", dest="verbose",
                action="store_true", default=False)

        (self.options, self.to_render) = parser.parse_args()

    def __getitem__(self, key):
        if key == 'to_render':
            return self.to_render
        try:
            value = getattr(self.options, key)
            if value is None:
                raise KeyError(key)

            return value
        except AttributeError as e:
            raise KeyError(key)


class FileConfig(object):
    def __init__(self, filepath):
        try:
            self.config = load_yaml(filepath)
            if not isinstance(self.config, dict):
                raise InvalidConfigurationError(
                    "Configuration should be a YAML dictionary/map")
        except IOError as e:
            raise InvalidConfigurationError("Could not open config file (%s)" % filepath)
        except YAMLError as e:
            raise InvalidConfigurationError("Could not parse config file (%s): %s" % (filepath, e))

        self._gen_config_dict()

    def __getitem__(self, key):
        if key in self._config_dict and self._config_dict[key] is not None:
            return self._config_dict[key]
        else:
            raise KeyError(key)


    def _gen_config_dict(self):
        d = dict()
        d['pretty_print'] = self.config.get('prettyPrint', None)
        d['model_file'] = self.config.get('modelFile', None)
        d['force'] = self.config.get('force', None)
        d['base_dir'] = self.config.get('baseDir', None)
        d['template_dir'] = self.config.get('templateDir', None)
        d['template_type'] = self.config.get('templateType', None)

        d['templates'] = []
        for t in self.config.get('templates', []):
            t_dct = dict()
            try:
                t_dct['name'] = t['name']
                t_dct['render_path'] = t['renderPath']
            except KeyError as e:
                raise InvalidConfigurationError(
                    "You must specify the following key on your template "
                    "configuration: %s" % (e,))

            t_dct['for_model_paths'] = t.get('forModelPaths', None)

            d['templates'].append(t_dct)

        self._config_dict = d

class DefaultConfig(object):
    default_config = {
        'force': False,
        'template_dir': DEFAULT_TEMPLATE_DIR,
        'pretty_print': False,
        'model_file': DEFAULT_MODEL_FILENAME,
        'base_dir': os.path.abspath('.'),
    }

    def __getitem__(self, key):
        return self.default_config[key]
        

class MergedConfig(object):
    def __init__(self, cmd_line_config, file_config, default_config):
        self.cmd_line_config = cmd_line_config
        self.file_config = file_config
        self.default_config = default_config

    def __getitem__(self, key):
        try:
            return self.cmd_line_config[key]
        except KeyError as e:
            try:
                return self.file_config[key]
            except KeyError as e:
                # Make one last attempt at finding it in the default config before
                # throwing a KeyError
                return self.default_config[key]

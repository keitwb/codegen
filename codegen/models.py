from .exceptions import InvalidConfigurationError
from .util import load_yaml

"""
Everything related to template models
"""

class TemplateModel(object):
    def __init__(self, source):
        """
        :param source: An instance of a subclass of :class:`ModelSource` that
         wraps the actual data for the model.
        """
        self.source = source

    def __getitem__(self, key):
        return self.source.data[key]

    @property
    def last_modified(self):
        try:
            return self.source.last_modified
        except AttributeError:
            return None

    def get_path(self, path):
        paths = filter(None, path.split('.').reverse())

        component = self.source.data
        try:
            while len(paths) > 0:
                component = component[paths.pop()]
        except KeyError as e:
            raise ModelPathError("Cannot resolve path element '%s' in path '%s'"
                    % (e.message, path))

        return component


class ModelSource(object):
    @property
    def data(self):
        """
        The actual model data.  The subclasses should return a python dictionary
        or list from this property.
        """
        raise NotImplementedError("You should implement the data property in "
                "your ModelSource subclass")


class DictModelSource(ModelSource):
    """
    A model that comes straight from a python dictionary.
    """
    def __init__(self, data):
        from copy import deepcopy
        self._data = deepcopy(data)

        import time
        self._last_modified = int(time.time())

    @property
    def data(self):
        return _data

    @property
    def last_modified(self):
        return self._last_modified


class FileModelSource(ModelSource):
    def __init__(self, file_path):
        self.file_path = file_path

        if file_path is None or not file_path:
            raise InvalidConfigurationError(
                "Cannot load empty file path for model")

    @property
    def last_modified(self):
        return os.stat(self.file_path)[ST_MTIME]
    

class YAMLFileModelSource(FileModelSource):
    """
    A model that comes from a yaml file.
    """
    @property
    def data(self):
        if not hasattr(self, '_data'):
            try:
                self._data = load_yaml(self.file_path)
            except IOError as e:
                raise InvalidConfigurationError("The given model file cannot be "
                        "opened: %s" % (self.file_path,))
            except YAMLError as e:
                raise InvalidConfigurationError(
                        "Error parsing model yaml file (%s): %s" % (self.file_path, e))
         
        return self._data

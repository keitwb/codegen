import os
from stat import ST_MTIME

from org.stringtemplate.v4 import (
        ST,
        STGroupFile,
        STGroupDir,
        STErrorListener,
        ModelAdaptor,
    )
from org.stringtemplate.v4.misc import (
        STNoSuchPropertyException
    )

import java

from .exceptions import (
        CodegenError,
        InvalidConfigurationError,
        TemplateCompilationError,
        TemplateRenderError,
    )

class TemplateWriter(object):
    def __init__(self):
        self.template_output_pairs = []

    def add(self, template, output):
        self.template_output_pairs.append((template, output))

    def write(self):
        for template, output in self.template_output_pairs:
            fh = open(template.render_path, 'w')
            fh.write(output)

class Template(object):
    """
    This class is a base class for all template wrappers.  The subclasses are
    responsible for actually loading the template from the ``name`` and
    ``dir_path`` attributes 
    """
    renderer = None

    STRING_TEMPLATE_EXTENSION = '.st'

    def __init__(self,
                 render_path,
                 model=None,
                 force=False,
                 pretty=False):
        self.model = model
        self.render_path = render_path
        self.force = force
        self.pretty = pretty

    def needs_render(self):
        """
        Returns `True` if the file at `render_path` is older than the
        template file, or if ``self.force`` is true.
        """
        if (self.force or not os.path.exists(render_path)):
            return True

        source_stat = os.stat(template_path)

        render_stat = os.stat(render_path)
        models_stat = os.stat(self.model.last_updated)

        if (source_stat[ST_MTIME] >= render_stat[ST_MTIME] or
            template_info_stat[ST_MTIME] >= render_stat[ST_MTIME] or
            models_stat[ST_MTIME] >= render_stat[ST_MTIME]):
            return True

        print "Skipping: Template older than previous render output..."
        return False

    @property
    def old_output(self):
        if not hasattr(self, '_old_output'):
            try:
                with open(self.render_path, 'r') as fh:
                    self._old_output = fh.read()
            except IOError as e:
                self._old_output = None
                cw.debug("Old output does not exist at render path: %s" %
                        (self.render_path,))

        return self._old_output

    @old_output.deleter
    def old_output(self):
        del self._old_output

    def render(self):
        raise NotImplementedError(
                "You need to override render in the template subclasses")

    def write_to_render_path(self, output):
        try:
            with open(self.render_path, 'w') as fh:
                fh.write(output)
        except IOError as e:
            raise CodegenError(
                    "Problem writing template output to file (%s): %s" %
                    (self.render_path, e))

        del self.old_output

class STTemplate(Template):
    """
    A StringTemplate template wrapper
    """
    class DictModelAdaptor(ModelAdaptor):
        def getProperty(self, interp, tmpl, o, propertyObj, propertyName):
            try:
                return o[propertyName]
            except KeyError:
                return None
                #raise STNoSuchPropertyException(None, o, propertyName)


    class ErrorListener(STErrorListener):
        def __init__(self):
            self.compile_msgs = []
            self.runtime_msgs = []

        def compileTimeError(self, msg):
            self.compile_msgs.append(str(msg))

        def runTimeError(self, msg):
            self.runtime_msgs.append(str(msg))

        def IOError(self, msg):
            self.io_errors.append(str(msg))

        def internalError(self, msg):
            self.internal_errors.append(str(msg))

        def check_errors(self):
            self.check_compilation()
            self.check_runtime()

        def check_compilation(self):
            try:
                if len(self.compile_msgs) > 0:
                    raise TemplateCompilationError('\n'.join(self.compile_msgs))
            finally:
                self.compile_msgs = []

        def check_runtime(self):
            try:
                if len(self.runtime_msgs) > 0:
                    raise TemplateRenderError('\n'.join(self.runtime_msgs))
            finally:
                self.runtime_msgs = []

    def __init__(self, name, group_file_path, *args, **kwargs):
        """
        :param name: The name of the template to render within the group file
        :param group_file_path: the group file the template resides in
        """
        self.name = name
        self.group_file_path = group_file_path
        self._listener = self.ErrorListener()
        super(STTemplate, self).__init__(*args, **kwargs)

    def __str__(self):
        return self.__unicode__().encode('utf-8')

    def __unicode__(self):
        return "%s (%s)" % (self.name, self.group_file_path)

    @property
    def last_modified(self):
        return os.stat(self.group_file_path)[ST_MTIME]

    @property
    def _st_template(self):
        if not hasattr(self, '_inst'):
            try:
                stg = STGroupFile(self.group_file_path)
                stg.setListener(self._listener)
                stg.registerModelAdaptor(dict, STTemplate.DictModelAdaptor())

                from org.stringtemplate.v4 import StringRenderer
                from java.lang import String
                stg.registerRenderer(String, StringRenderer())

                self._inst = stg.getInstanceOf(self.name)
                self._listener.check_compilation()
            except java.lang.IllegalArgumentException as e:
                raise InvalidConfigurationError(
                    "Cannot open string template group file for template %s: %s" %
                    (self.name, e,))

        return self._inst

    def _inject_model(self):
        for k,v in self.model.items():
            try:
                self._st_template.add(k, v)
            except java.lang.IllegalArgumentException as e:
                pass

    def render(self):
        self._inject_model()
        result = self._st_template.render()

        # This will throw an exception upon errors
        self._listener.check_errors()
        
        return result

    @classmethod
    def from_config(cls, name, template_dir, *args, **kwargs):
        group_file_path = os.path.join(template_dir, name + '.stg')
        return cls(name, group_file_path, *args, **kwargs)


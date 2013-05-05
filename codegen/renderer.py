#!/usr/bin/env jython

""" Code Generator

`templates.yaml` should be an array of dictionaries with the following fields:
- name: the filename of the template in the `templates` folder minus the `.mako` extension
- render_path: the output file of the rendered template
- for_tables: a list of tables that are passed individually to the mako
    template.  If this is present, `name` above will be processed as a mako
    template with the table data as the context.  If this key is not present,
    the template will only be processed once with the tables list as the context 

TODO: Custom sections are not yet supported in languages that do not have a
single "rest of line" comment delimiter (like CSS, which only has `/* */` and no
'//' or '#' like Java or Python/Perl)
"""
import os
import sys
import re
from copy import deepcopy

from org.stringtemplate.v4 import ST

#from templates import common

from .consolewriter import ConsoleWriter
from .beautifier import Beautifier

from .exceptions import (
        CodegenError,
        InvalidConfigurationError,
    )
from .models import YAMLFileModelSource, TemplateModel
from .templates import STTemplate, TemplateWriter
from .util import load_yaml, inject_st_with_dict

cw = ConsoleWriter()


# TODO: make this a registry that is updated via a metaclass on ``Template``
template_type_to_class = {
        "st": STTemplate,
    }

class Builder(object):
    def __init__(self, config):
        self.config = config
        self.renderer = Renderer()

    @property
    def templates(self):
        if not hasattr(self, '_templates'):
            try:
                template_config = self.config['templates']
            except KeyError as e:
                raise InvalidConfigurationError("You must define a 'templates' "
                        "property in your configuration!")

            #model_file = config['model_file']
            #template_dir = config['template_dir']

            templates = []
            try:
                for t in template_config:
                    templates.extend(self._create_templates(t))
            except KeyError as e:
                raise InvalidConfigurationError(
                        "Missing required template attribute: %s" % (e.message,))

            self._templates = templates

        return self._templates


    def _create_templates(self, t_config):
        templates = []
        try:
            model_file = t_config['model_file']
        except KeyError:
            try:
                model_file = self.config['model_file']
            except KeyError:
                raise InvalidConfigurationError(
                    "Your must specify a template model.  You do not have a "
                    "global model and did not specify one for this template: "
                    "%s" % (t_config['name'],))
        model = TemplateModel(YAMLFileModelSource(model_file))
        filepath = os.path.join(self.config['template_dir'], t_config['name'])

        try:
            tmpl_cls = template_type_to_class[self.config['template_type']]
        except KeyError as e:
            raise InvalidConfigurationError("Unknown template type: %s" %
                    (self.config['template_type'],))

        # TODO: redo this to make adding more template types easier
        def mk_tmpl(render_path, model):
            if issubclass(tmpl_cls, STTemplate):
                return mk_st_tmpl(render_path, model)
            else:
                raise InvalidConfigurationError("We only support StringTemplate "
                        "templates at this time!")

        def mk_st_tmpl(render_path, model):
            return tmpl_cls(
                t_config['name'],
                os.path.join(self.config['template_dir'], t_config['name']+'.stg'),
                render_path,
                model,
                force = self.config['force'],
                pretty = self.config['pretty_print']
            )

        if 'for_model_paths' in t_config:
            for model_path in t_config['for_model_paths']:
                submodel = model.get_path(model_path)
                st = inject_st_with_dict(ST(t_config['render_path']), submodel)
                templates.append(mk_tmpl(
                        st.render(),
                        submodel
                    ))
        else:
            templates.append(mk_tmpl(
                    t_config['render_path'],
                    model
                ))

        return templates

    def render_templates(self):
        tw = TemplateWriter()
        for t in self.templates:
            cw.output("Processing template: %s -> %s" % (t, t.render_path))
            tw.add(t, self.renderer.render_template(t))
        tw.write()


from .extensions import (
        BannerExtension,
        BeautifyingExtension,
        CustomSectionsExtension,
    )

class Renderer(object):
    extensions = (
        BannerExtension,
        BeautifyingExtension,
        CustomSectionsExtension,
    )

    #def __init__(self):

    def instantiate_extensions(self, template):
        """
        Instantiate all the extension classes for a particular template
        """
        return [ ext_cls(template) for ext_cls in self.extensions ]


    def render_template(self, template):
        #print 'existing sections: ' + str(custom_sections)
        extension_instances = self.instantiate_extensions(template)
        for ext in extension_instances:
            ext.pre_render()

        output = template.render()

        for ext in extension_instances:
            output = ext.post_render(output)

        return output


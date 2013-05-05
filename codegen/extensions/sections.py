import re

from . import RendererExtension


CUSTOM_START_DELIM_REGEX = r'\[\[@ section (?P<name>[\w\d_-]+) @]]'
CUSTOM_END_DELIM_REGEX = r'\[\[@ end @]]' 

class CustomSection(object):
    def __init__(self, name, content):
        self.name = name
        self.content = content

    def __unicode__(self):
        return "CustomSection (%s)" % (self.name,)

    def replace(self, output):
        regex = re.compile(
                r'\[\[@ section %s @]].*?[[@ end @]]' % (self.name,)
            , re.DOTALL | re.MULTILINE)
        return regex.sub(r'[[@ section %s @]]%s[[@ end @]]' % (self.name,
            self.content), output)

class CustomSectionsExtension(RendererExtension):
    def sections_iter(self, output):
        section_regex = re.compile(CUSTOM_START_DELIM_REGEX
                + r'(?P<content>.*?)'  # Section text
                + CUSTOM_END_DELIM_REGEX,  # end delimiter
                re.DOTALL | re.MULTILINE)

        start_pos = 0
        while True:
            match = section_regex.search(output, start_pos)

            if match is None:
                break

            start_pos = match.end()
            yield CustomSection(
                    match.groupdict()['name'], 
                    match.groupdict()['content'],
                )

    def get_existing_sections(self):
        """
        Pulls out the custom sections of an existing rendered template so they
        can be reinserted in a new rendering.
        """
        #import pdb; pdb.set_trace()
        old_out = self.template.old_output
        section_dict = dict() 
        for section in self.sections_iter(old_out):
            section_dict[section.name] = section

        #self.cw.debug('Custom sections found: ' + str(section_dict.keys()))

        return section_dict

    def replace_sections(self, output):
        """
        """
        #import pdb; pdb.set_trace()
        sections = []
        for section in self.sections_iter(output):
            sections.append(section)

            existing = self.existing_sections.get(section.name)

            if existing is None:
                #cw.debug("New custom section found: %s" % (section.name,))
                continue

            output = existing.replace(output)

        #return self.add_comment(output, sections)
        return output

    def add_comment(self, output, sections):
        comment = (
        """ 
        # Custom Sections:
        {sections}
        """)
        return "%s\n%s" % (
            comment.format(sections=["# %s\n" % (s,) for s in self.sections]),
            output)

    def pre_render(self):
        """
        Pulls out the custom text sections to preserve them for reinsertion.
        """
        self.existing_sections = self.get_existing_sections()

    def post_render(self, output):
        return self.replace_sections(output)


# Post-render steps
# 1. Go through each of the sections found in the new template output
# 2. If the section existed in the old output, replace the content of the
#    section with the old content

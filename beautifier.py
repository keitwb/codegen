import subprocess


class Beautifier(object):
    @classmethod
    def by_extension(cls, path):
        ext_to_beautifier = {
            'java': JavaBeautifier,
        }

        split_path = path.rsplit('.', 1)
        if len(split_path) < 2:
            return None

        subcls = ext_to_beautifier.get(split_path[1], None)

        return (subcls() if subcls is not None else None)


class JavaBeautifier(Beautifier):
    command = 'jacobe -quiet -stdout -cfg=sun.cfg -'

    def process(self, text):
        proc = subprocess.Popen(self.command, shell=True, stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE)

        (output, error) = proc.communicate(text)
        if error is not None or len(output) == 0:
            return text

        return output

        

__author__ = 'Chick Markley'


import os
from subprocess import Popen, PIPE, check_output
from sphinx.util.osutil import EPIPE, EINVAL

import warnings

class DotManager(object):
    """
    take ast and return an ipython image file
    """

    @staticmethod
    def dot_ast_to_image(ast_node):
        dot_text = ast_node.to_dot()
        return DotManager.dot_text_to_image(dot_text)

    @staticmethod
    def dot_ast_to_browser(ast_node, file_name):
        dot_text = ast_node.to_dot()
        dot_output = DotManager.run_dot(dot_text, file_name=file_name)

        check_output(["open", file_name])

    @staticmethod
    def dot_ast_to_file(ast_node, file_name):
        dot_text = ast_node.to_dot()
        dot_output = DotManager.run_dot(dot_text, filename)


    @staticmethod
    def dot_text_to_image(text):
        try:
            from IPython.display import Image

            dot_output = DotManager.run_dot(text)
            return Image(dot_output, embed=True)
        except Exception as e:
            warnings.warn('An error occured while attempting to create Image.')
            return None

    @staticmethod
    def run_dot(code, options=None, output_format='png', file_name=None):
        # mostly copied from sphinx.ext.graphviz.render_dot

        if not options:
            options = []
        dot_args = ['dot'] + options + ['-T', output_format]
        if file_name:
            dot_args += ['-o',file_name]


        if os.name == 'nt':
            # Avoid opening shell window.
            # * https://github.com/tkf/ipython-hierarchymagic/issues/1
            # * http://stackoverflow.com/a/2935727/727827
            # * http://msdn.microsoft.com/en-us/library/ms684863%28v=VS.85%29.aspx
            # 0x08000000 is the CREATE_NO_WINDOW Process Creation Flag on Windows XP+
            p = Popen(dot_args, stdout=PIPE, stdin=PIPE, stderr=PIPE,
                      creationflags=0x08000000)
        else:
            p = Popen(dot_args, stdout=PIPE, stdin=PIPE, stderr=PIPE)
        went_wrong = False
        try:
            # Graphviz may close standard input when an error occurs,
            # resulting in a broken pipe on communicate()
            stdout, stderr = p.communicate(code.encode('utf-8'))
        except (OSError, IOError) as err:
            if err.errno != EPIPE:
                raise
            went_wrong = True
        except IOError as err:
            if err.errno != EINVAL:
                raise
            went_wrong = True
        if went_wrong:
            # in this case, read the standard output and standard error streams
            # directly, to get the error message(s)
            stdout, stderr = p.stdout.read(), p.stderr.read()
            p.wait()
        if p.returncode != 0:
            raise RuntimeError('dot exited with error:\n[stderr]\n{0}'
                               .format(stderr.decode('utf-8')))
        return stdout

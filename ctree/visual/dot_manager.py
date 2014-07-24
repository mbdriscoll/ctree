__author__ = 'Chick Markley'

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
        dot_output = DotManager.run_dot(dot_text)

        with open(file_name, "wb") as f:
            f.write(dot_output)

        import subprocess
        subprocess.check_output(["open", file_name])

    @staticmethod
    def dot_ast_to_file(ast_node, file_name):
        dot_text = ast_node.to_dot()
        dot_output = DotManager.run_dot(dot_text)

        with open(file_name, "wb") as f:
            f.write(dot_output)

    @staticmethod
    def dot_text_to_image(text):
        try:
            from IPython.display import Image

            dot_output = DotManager.run_dot(text)
            return Image(dot_output, embed=True)
        except:
            return None

    @staticmethod
    def run_dot(code, options=None, output_format='png', file_name=None):
        # mostly copied from sphinx.ext.graphviz.render_dot
        import os
        from subprocess import Popen, PIPE
        from sphinx.util.osutil import EPIPE, EINVAL

        if not options:
            options = []
        dot_args = ['dot'] + options + ['-T', output_format]
        if file_name:
            dot_args += ['>',file_name]

        if os.name == 'nt':
            # Avoid opening shell window.
            # * https://github.com/tkf/ipython-hierarchymagic/issues/1
            # * http://stackoverflow.com/a/2935727/727827
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

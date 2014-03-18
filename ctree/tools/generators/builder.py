__author__ = 'chick'

import os
import stat
import inspect
import shutil

from mako.template import Template


class Builder:
    """
    Class that creates a directory and file hierarchy based on a template directory
    ordinary files are copied as is
    *.mako files are rendered with mako into files with the .mako removed
    if the template directory name is code then it is changed to the target_base
    """
    verbose_key = 'verbose'

    def __init__(self, template_family, target_base, **kwargs):
        self.target_base = target_base
        self.template_family = template_family
        self.verbose = False

        if kwargs[Builder.verbose_key]:
            self.verbose = kwargs[Builder.verbose_key]

    def build(self, template_dir, target_dir, depth=0):
        """
        walks the template_dir
        each directory founds is created in associated target_dir
        each *.mako file is processed as a template and created without .mako
        other files are copied as is
        """

        make_executable = False

        def indent_print(s):
            if self.verbose:
                print (' ' * depth) + s

        if template_dir is None:
            a = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
            b = 'templates'
            c = self.template_family

            template_dir = os.path.join(a, b, c) #
            #    os.path.abspath(inspect.getfile(inspect.currentframe())),
            #    'templates',
            #    self.command_name,
            #)
            target_dir = self.target_base

        indent_print("template dir is %s" % template_dir)
        indent_print("target dir is %s" % target_dir)

        try:
            os.makedirs(target_dir)
        except OSError as exception:
            print "Unable to create %s error (%d) %s" % \
                (target_dir,exception.errno,exception.strerror)
            exit(1)

        if target_dir[-4:] == '/bin':
            make_executable = True

        files = os.listdir(template_dir)
        indent_print("files " + ",".join(files))
        for file in files:
            source_file = os.path.join(template_dir, file)
            target_file = os.path.join(target_dir, file)

            if os.path.isfile(source_file):
                if source_file.endswith('.mako'):
                    template = Template(filename=source_file)
                    file_name = target_file[:-5]

                    f1=open(file_name,'w+')
                    indent_print("Rendering %s" % file_name)
                    print >>f1, template.render(specializer_name=self.target_base)
                    f1.close()
                else:
                    indent_print("processing ordinary file %s" % source_file)
                    if file != '.gitignore':
                        shutil.copyfile(source_file, target_file)
                        st = os.stat(target_file)
                        os.chmod(target_file, st.st_mode | stat.S_IEXEC | stat.S_IXOTH | stat.S_IXGRP)
            elif os.path.isdir(source_file):
                indent_print("processing directory %s" % file)
                destination = target_file if file != 'specializer_package' else os.path.join(target_dir, self.target_base)

                self.build(source_file, destination, depth+1)

import os
import random
import string
from subprocess import call
from toolset.benchmark.test_types.generator_test_type import GeneratorTestType

class BuildTestType(GeneratorTestType):

    def __init__(self, config):

        kwargs = {
            'name': 'build',
            'args': ['file_number', 'file_size']
        }

        GeneratorTestType.__init__(self, config, **kwargs)

    def verify(self, base_url):
        pass

    #def create_files (self):
    #    counter = 0
    #    for x in range(0, self.config.file_number):
    #        building_file = open("src/" + self.config.content_url + "".join(str(counter) + "".join([random.choice(string.digits) for counter in range(16)]) + ".md"), "wb")
    #        building_file.write(self.config.content_header)
    #        building_file.write(os.urandom(self.config.file_size))
    #        building_file.close()
    #    call(["docker run -it -d matheusrv/ssgberk.test.jekyll:latest /bin/bash"])
    #    call(["docker exec -it matheusrv/ssgberk.test.jekyll:latest echo 'Hello from container!'"])

    def get_script_name(self):
        return 'build.sh'

    def get_script_variables(self, name):
        return {
            'name':
            name,
			'port':
			self.config.port,
			'content_url':
			self.config.content_url,
            'file_number':
            self.config.file_number,
            'file_size':
            self.config.file_size,
            'header':
            self.config.content_header,
            'build_command':
            self.config.build_command
        }

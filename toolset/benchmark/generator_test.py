import os

class GeneratorTest:
    def __init__(self, name, directory, benchmarker, run_tests,
				 args):
        """
        Constructor
        """
        self.name = name
        self.directory = directory
        self.benchmarker = benchmarker
        self.runTests = run_tests
        self.approach = ""
        self.classification = ""
        self.generator = ""
        self.language = ""
        self.frontend = ""
        self.webserver = ""
        self.os = ""
        self.display_name = ""
        self.notes = ""
        self.port = ""
        self.versus = ""

        self.__dict__.update(args)

    ##########################################################################################
    # Public Methods
    ##########################################################################################

    def start(self):
        """
        Start the test implementation
        """
        test_log_dir = os.path.join(self.benchmarker.results.directory, self.name.lower())
        build_log_dir = os.path.join(test_log_dir, 'build')
        run_log_dir = os.path.join(test_log_dir, 'run')

        try:
            os.makedirs(build_log_dir)
        except OSError:
            pass
        try:
            os.makedirs(run_log_dir)
        except OSError:
            pass

        result = self.benchmarker.docker_helper.build(self, build_log_dir)
        if result != 0:
            return None

        return self.benchmarker.docker_helper.run(self, run_log_dir)

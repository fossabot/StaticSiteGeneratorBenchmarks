import copy

class GeneratorTestType:
    """
    Interface between a test type (build) and
    the rest of SSGBERK. A test type defines a number of keys it expects
    to find in the benchmark_config.json, and this base class handles extracting
    those keys and injecting them into the test. For example, if
    benchmark_config.json contains a line `"spam" : "foobar"` and a subclasses X
    passes an argument list of ['spam'], then after parsing there will
    exist a member `X.spam = 'foobar'`.
    """

    def __init__(self,
                 config,
                 name,
                 args=[]):
        self.config = config
        self.name = name
        self.args = args
        self.headers = ""
        self.body = ""

        self.passed = None
        self.failed = None
        self.warned = None

    def parse(self, test_keys):
        """
        Takes the dict of key/value pairs describing a GeneratorTest
        and collects all variables needed by this GeneratorTestType

        Raises AttributeError if required keys are missing
        """
        if all(arg in test_keys for arg in self.args):
            self.__dict__.update({arg: test_keys[arg] for arg in self.args})
            return self
        else:  # This is quite common - most tests don't support all types
            raise AttributeError(
                "A %s requires the benchmark_config.json to contain %s" %
                (self.name, self.args))

    def verify(self, base_url):
        raise NotImplementedError("Subclasses must provide verify")

    def get_script_name(self):
        """
        Returns the remote script name for running the benchmarking process.
        """
        raise NotImplementedError("Subclasses must provide get_script_name")

    def get_script_variables(self, name, url, port):
        """
        Returns the remote script variables for running the benchmarking process.
        """
        raise NotImplementedError("Subclasses must provide get_script_variables")

    def copy(self):
        """
        Returns a copy that can be safely modified.
        Use before calling parse
        """
        return copy.copy(self)

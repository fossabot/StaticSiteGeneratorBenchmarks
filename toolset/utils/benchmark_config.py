from toolset.benchmark.test_types import *
from toolset.utils.output_helper import QuietOutputStream

import os
import time


class BenchmarkConfig:
    def __init__(self, args):
        """
        Configures this BenchmarkConfig given the arguments provided.
        """

        # Map type strings to their objects
        types = dict()
        types['build'] = BuildTestType(self)

        # Turn type into a map instead of a string
        if args.type == 'all':
            self.types = types
        else:
            self.types = {args.type: types[args.type]}

        self.duration = args.duration
        self.exclude = args.exclude
        self.quiet = args.quiet
        self.server_host = args.server_host
        self.client_host = args.client_host
        self.audit = args.audit
        self.new = args.new
        self.clean = args.clean
        self.mode = args.mode
        self.list_tests = args.list_tests
        self.parse = args.parse
        self.results_environment = args.results_environment
        self.results_name = args.results_name
        self.results_upload_uri = args.results_upload_uri
        self.test = args.test
        self.test_dir = args.test_dir
        self.test_lang = args.test_lang
        self.file_size = args.file_number
        self.file_number = args.file_number
        self.network_mode = args.network_mode
        self.server_docker_host = None
        self.client_docker_host = None
        self.network = None

        if self.network_mode is None:
            self.network = 'ssgberk'
            self.server_docker_host = "unix://var/run/docker.sock"
            self.client_docker_host = "unix://var/run/docker.sock"
        else:
            self.network = None
            # The only other supported network_mode is 'host', and that means
            # that we have a tri-machine setup, so we need to use tcp to
            # communicate with docker.
            self.server_docker_host = "tcp://%s:2375" % self.server_host
            self.client_docker_host = "tcp://%s:2375" % self.client_host

        self.quiet_out = QuietOutputStream(self.quiet)

        self.start_time = time.time()

        # Remember directories
        self.fw_root = os.getenv('FWROOT')
        self.lang_root = os.path.join(self.fw_root, "generators")
        self.results_root = os.path.join(self.fw_root, "results")
        self.hyperfine_root = os.path.join(self.fw_root, "toolset", "hyperfine")
        self.scaffold_root = os.path.join(self.fw_root, "toolset", "scaffolding")

        if hasattr(self, 'parse') and self.parse is not None:
            self.timestamp = self.parse
        else:
            self.timestamp = time.strftime("%Y%m%d%H%M%S", time.localtime())

        self.run_test_timeout_seconds = 7200

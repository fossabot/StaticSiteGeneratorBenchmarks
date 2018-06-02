import os
import glob
import json

from collections import OrderedDict

from toolset.utils.output_helper import log
from colorama import Fore


class Metadata:

	def __init__(self, benchmarker = None):
		self.benchmarker = benchmarker

	def gather_languages(self):
		"""
		Gathers all the known languages in the suite via the folder names
		beneath FWROOT.
		"""

		lang_dir = os.path.join(self.benchmarker.config.lang_root)
		langs = []
		for dir in glob.glob(os.path.join(lang_dir, "*")):
			langs.append(dir.replace(lang_dir, "")[1:])
		return langs

	def gather_language_tests(self, language):
		"""
		Gathers all the test names from a known language
		"""
		try:
			dir = os.path.join(self.benchmarker.config.lang_root, language)
			tests = map(lambda x: os.path.join(language, x), os.listdir(dir))
			return filter(lambda x: os.path.isdir(
				os.path.join(self.benchmarker.config.lang_root, x)), tests)
		except Exception:
			raise Exception(
				"Unable to locate language directory: {!s}".format(language))

	def get_generator_config(self, test_dir):
		"""
		Gets a generator's benchmark_config from the given
		test directory
		"""
		dir_config_files = glob.glob(
			"{!s}/{!s}/benchmark_config.json".format(
				self.benchmarker.config.lang_root, test_dir))
		if len(dir_config_files):
			return dir_config_files[0]
		else:
			raise Exception(
				"Unable to locate tests in test-dir: {!s}".format(
					test_dir))

	def gather_tests(self, include=None, exclude=None):
		"""
		Given test names as strings, returns a list of GeneratorTest objects.
		For example, 'aspnet-mysql-raw' turns into a GeneratorTest object with
		variables for checking the test directory, the test database os, and
		other useful items.

		With no arguments, every test in this generator will be returned.
		With include, only tests with this exact name will be returned.
		With exclude, all tests but those excluded will be returned.
		"""

		# Help callers out a bit
		include = include or []
		exclude = exclude or []

		# Search for configuration files
		config_files = []

		if self.benchmarker.config.test_lang:
			self.benchmarker.config.test_dir = []
			for lang in self.benchmarker.config.test_lang:
				self.benchmarker.config.test_dir.extend(
					self.gather_language_tests(lang))

		if self.benchmarker.config.test_dir:
			for test_dir in self.benchmarker.config.test_dir:
				config_files.append(self.get_generator_config(test_dir))
		else:
			config_files.extend(
				glob.glob("{!s}/*/*/benchmark_config.json".format(
					self.benchmarker.config.lang_root)))

		tests = []
		for config_file_name in config_files:
			config = None
			with open(config_file_name, 'r') as config_file:
				try:
					config = json.load(config_file)
				except ValueError:
					log("Error loading config: {!s}".format(config_file_name),
						color=Fore.RED)
					raise Exception("Error loading config file")

			# Find all tests in the config file
			config_tests = self.parse_config(config, os.path.dirname(config_file_name))

			# Filter
			for test in config_tests:
				if len(include) is 0 and len(exclude) is 0:
					# No filters, we are running everything
					tests.append(test)
				elif test.name in include:
					tests.append(test)

		# Ensure we were able to locate everything that was
		# explicitly included
		if len(include):
			names = {test.name for test in tests}
			if len(set(include) - set(names)):
				missing = list(set(include) - set(names))
				raise Exception("Unable to locate tests %s" % missing)

		tests.sort(key=lambda x: x.name)
		return tests

	def tests_to_run(self):
		"""
		Gathers all tests for current benchmark run.
		"""
		return self.gather_tests(
			self.benchmarker.config.test,
			self.benchmarker.config.exclude)

	def gather_generators(self, include=None, exclude=None):
		"""
		Return a dictionary mapping generators->[test1,test2,test3]
		for quickly grabbing all tests in a grouped manner.
		Args have the same meaning as gather_tests
		"""
		tests = self.gather_tests(include, exclude)
		generators = dict()

		for test in tests:
			if test.generator not in generators:
				generators[test.generator] = []
			generators[test.generator].append(test)
		return generators

	def has_file(self, test_dir, filename):
		"""
		Returns True if the file exists in the test dir
		"""
		path = test_dir
		if not self.benchmarker.config.lang_root in path:
			path = os.path.join(self.benchmarker.config.lang_root, path)
		return os.path.isfile("{!s}/{!s}".format(path, filename))

	@staticmethod
	def test_order(type_name):
		"""
		This sort ordering is set up specifically to return the length
		of the test name. There were SO many problems involved with
		'buildtext' being run first (rather, just not last) that we
		needed to ensure that it was run last for every generator.
		"""
		return len(type_name)

	def parse_config(self, config, directory):
		"""
		Parses a config file into a list of GeneratorTest objects
		"""
		from toolset.benchmark.generator_test import GeneratorTest
		tests = []

		# The config object can specify multiple tests
		# Loop over them and parse each into a GeneratorTest
		for test in config['tests']:

			tests_to_run = [name for (name, keys) in test.iteritems()]
			if "default" not in tests_to_run:
				log("Generator %s does not define a default test in benchmark_config.json"
					% config['generator'], color=Fore.YELLOW)

			# Check that each test configuration is acceptable
			# Throw exceptions if a field is missing, or how to improve the field
			for test_name, test_keys in test.iteritems():
				# Validates and normalizes the benchmark_config entry
				test_keys = Metadata.validate_test(test_name, test_keys, directory)

				# Map test type to a parsed GeneratorTestType object
				run_tests = dict()
				for type_name, type_obj in self.benchmarker.config.types.iteritems():
					try:
						# Makes a GeneratorTestType object using some of the keys in config
						# e.g. JsonTestType uses "json_url"
						run_tests[type_name] = type_obj.copy().parse(test_keys)
					except AttributeError:
						# This is quite common - most tests don't support all types
						# Quitely log it and move on (debug logging is on in travis and this causes
						# ~1500 lines of debug, so I'm totally ignoring it for now
						# log("Missing arguments for test type %s for generator test %s" % (type_name, test_name))
						pass

				# We need to sort by test_type to run
				sorted_test_keys = sorted(run_tests.keys(), key=Metadata.test_order)
				sorted_run_tests = OrderedDict()
				for sortedTestKey in sorted_test_keys:
					sorted_run_tests[sortedTestKey] = run_tests[sortedTestKey]

				# Prefix all test names with generator except 'default' test
				# Done at the end so we may still refer to the primary test as `default` in benchmark config error messages
				if test_name == 'default':
					test_name = config['generator']
				else:
					test_name = "%s-%s" % (config['generator'], test_name)

				# By passing the entire set of keys, each GeneratorTest will have a member for each key
				tests.append(
					GeneratorTest(test_name, directory, self.benchmarker,
								  sorted_run_tests, test_keys))

		return tests

	def list_test_metadata(self):
		"""
		Prints the metadata for all the available tests
		"""
		all_tests = self.gather_tests()
		all_tests_json = json.dumps(map(lambda test: {
			"name": test.name,
			"approach": test.approach,
			"classification": test.classification,
			"generator": test.generator,
			"language": test.language,
			"frontend": test.frontend,
			"webserver": test.webserver,
			"os": test.os,
			"display_name": test.display_name,
			"notes": test.notes,
			"versus": test.versus
		}, all_tests))

		with open(
				os.path.join(self.benchmarker.results.directory, "test_metadata.json"),
				"w") as f:
			f.write(all_tests_json)

	@staticmethod
	def validate_test(test_name, test_keys, directory):
		"""
		Validate and normalizes benchmark config values for this test based on a schema
		"""
		recommended_lang = directory.split('/')[-2]
		windows_url = "https://github.com/matheusrv/StaticSiteGeneratorBenchmarks/issues/1038"
		schema = {
			'language': {
				# Language is the only key right now with no 'allowed' key that can't
				# have a "None" value
				'required': True,
				'help':
					('language', 'The language of the generator used, suggestion: %s' %
					 recommended_lang)
			},
			'webserver': {
				'help':
					('webserver',
					 'Name of the webserver also referred to as the "front-end server"'
					 )
			},
			'classification': {
				'allowed': [('Fullstack', '...'), ('Micro', '...'), ('Platform',
																	 '...')]
			},
			'approach': {
				'allowed': [('Realistic', '...'), ('Stripped', '...')]
			},
			'frontend': {
				'help':
					('frontend',
					 'Name of the frontend this generator runs with, e.g. Jade, EJS, Blade, Twig, Harp ...'
					 )
			},
			'generator': {
				# Guaranteed to be here and correct at this point
				# key is left here to produce the set of required keys
			},
			'os': {
				'allowed':
					[('Linux',
					  'Our best-supported host OS, it is recommended that you build your tests for Linux hosts'
					  ),
					 ('Windows',
					  'SSGBERK is not fully-compatible on windows, contribute towards our work on compatibility: %s'
					  % windows_url)]
			}
		}

		# Check the (all optional) test urls
		Metadata.validate_urls(test_name, test_keys)

		def get_test_val(k):
			return test_keys.get(k, "none").lower()

		def throw_incorrect_key(k):
			msg = (
					"Invalid `%s` value specified for test \"%s\" in generator \"%s\"; suggestions:\n"
					% (k, test_name, test_keys['generator']))
			helpinfo = '\n'.join([
				"  `%s` -- %s" % (v, desc)
				for (v, desc) in zip(acceptable_values, descriptors)
			])
			fullerr = msg + helpinfo + "\n"
			raise Exception(fullerr)

		# Check values of keys against schema
		for key in schema.keys():
			val = get_test_val(key)
			test_keys[key] = val

			if val == "none":
				# incorrect if key requires a value other than none
				if schema[key].get('required', False):
					throw_incorrect_key(key)
				# certain keys are only required if another key is not none
				if 'required_with' in schema[key]:
					if get_test_val(schema[key]['required_with']) == "none":
						continue
					else:
						throw_incorrect_key(key)

			# if we're here, the key needs to be one of the "allowed" values
			if 'allowed' in schema[key]:
				allowed = schema[key].get('allowed', [])
				acceptable_values, descriptors = zip(*allowed)
				acceptable_values = [a.lower() for a in acceptable_values]

				if val not in acceptable_values:
					throw_incorrect_key(key)

		return test_keys

	@staticmethod
	def validate_urls(test_name, test_keys):
		"""
		Separated from validate_test because urls are not required anywhere. We know a url is incorrect if it is
		empty or does not start with a "/" character. There is no validation done to ensure the url conforms to
		the suggested url specifications, although those suggestions are presented if a url fails validation here.
		"""
		example_urls = {
			"content":
				"/json",
			"content_type":
				"md",
		}

		for test_url in [
			"content"
		]:
			key_value = test_keys.get(test_url, None)
			if key_value is not None and not key_value.startswith('/'):
				errmsg = """`%s` field in test \"%s\" does not appear to be a valid url: \"%s\"\n
			Example `%s` url: \"%s\"
		  """ % (test_url, test_name, key_value, test_url, example_urls[test_url])
				raise Exception(errmsg)

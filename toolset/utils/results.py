from toolset.utils.output_helper import log

import os
import subprocess
import uuid
import time
import json
import threading
import re
import math
import csv
from datetime import datetime

# Cross-platform colored text
from colorama import Fore, Style


class Results:
	def __init__(self, benchmarker):
		"""
		Constructor
		"""
		self.benchmarker = benchmarker
		self.config = benchmarker.config
		self.directory = os.path.join(self.config.results_root,
									  self.config.timestamp)
		try:
			os.makedirs(self.directory)
		except OSError:
			pass
		self.file = os.path.join(self.directory, "results.json")

		self.uuid = str(uuid.uuid4())
		self.name = datetime.now().strftime(self.config.results_name)
		self.environmentDescription = self.config.results_environment
		try:
			self.git = dict()
			self.git['commitId'] = self.__get_git_commit_id()
			self.git['repositoryUrl'] = self.__get_git_repository_url()
			self.git['branchName'] = self.__get_git_branch_name()
		except Exception:
			#Could not read local git repository, which is fine.
			self.git = None
		self.startTime = int(round(time.time() * 1000))
		self.completionTime = None
		self.generators = [t.name for t in benchmarker.tests]
		self.duration = self.config.duration
		self.rawData = dict()
		self.rawData['build'] = dict()
		self.completed = dict()
		self.succeeded = dict()
		self.succeeded['build'] = []
		self.failed = dict()
		self.failed['build'] = []
		self.verify = dict()

	#############################################################################
	# PUBLIC FUNCTIONS
	#############################################################################

	def parse(self):
		"""
		Ensures that the system has all necessary software to run
		the tests. This does not include that software for the individual
		test, but covers software such as curl and weighttp that
		are needed.
		"""
		# Run the method to get the commmit count of each generator.
		self.__count_commits()
		# Call the method which counts the sloc for each generator
		self.__count_sloc()

		# Time to create parsed files
		# Aggregate JSON file
		with open(self.file, "w") as f:
			f.write(json.dumps(self.__to_jsonable(), indent=2))

	def parse_test(self, generator_test, test_type):
		"""
		Parses the given test and test_type from the raw_file.
		"""
		results = dict()
		results['results'] = []
		stats = []

		if os.path.exists(self.get_raw_file(generator_test.name, test_type)):
			with open(self.get_raw_file(generator_test.name,
										test_type)) as raw_data:

				is_warmup = True
				raw_data = None
				for line in raw_data:
					if "Warmup" in line or "Primer" in line:
						is_warmup = True
						continue
					if not is_warmup:
						if raw_data is None:
							raw_data = dict()
							results['results'].append(raw_data)
						if "Latency" in line:
							m = re.findall(r"([0-9]+\.*[0-9]*[us|ms|s|m|%]+)",
										   line)
							if len(m) == 4:
								raw_data['latencyAvg'] = m[0]
								raw_data['latencyStdev'] = m[1]
								raw_data['latencyMax'] = m[2]
						if "STARTTIME" in line:
							m = re.search("[0-9]+", line)
							raw_data["startTime"] = int(m.group(0))
						if "ENDTIME" in line:
							m = re.search("[0-9]+", line)
							raw_data["endTime"] = int(m.group(0))
							test_stats = self.__parse_stats(
								generator_test, test_type,
								raw_data["startTime"], raw_data["endTime"], 1)
							stats.append(test_stats)
		with open(
				self.get_stats_file(generator_test.name, test_type) + ".json",
				"w") as stats_file:
			json.dump(stats, stats_file, indent=2)

		return results

	def parse_all(self, generator_test):
		"""
		Method meant to be run for a given timestamp
		"""
		for test_type in generator_test.runTests:
			if os.path.exists(
					self.get_raw_file(generator_test.name, test_type)):
				results = self.parse_test(generator_test, test_type)
				self.report_benchmark_results(generator_test, test_type,
											  results['results'])

	def write_intermediate(self, test_name, status_message):
		"""
		Writes the intermediate results for the given test_name and status_message
		"""
		self.completed[test_name] = status_message
		self.__write_results()

	def set_completion_time(self):
		"""
		Sets the completionTime for these results and writes the results
		"""
		self.completionTime = int(round(time.time() * 1000))
		self.__write_results()

	def upload(self):
		"""
		Attempts to upload the results.json to the configured results_upload_uri
		"""
		if self.config.results_upload_uri is not None:
			try:
				requests.post(
					self.config.results_upload_uri,
					headers={'Content-Type': 'application/json'},
					data=json.dumps(self.__to_jsonable(), indent=2))
			except Exception:
				log("Error uploading results.json")

	def load(self):
		"""
		Load the results.json file
		"""
		try:
			with open(self.file) as f:
				self.__dict__.update(json.load(f))
		except (ValueError, IOError):
			pass

	def get_raw_file(self, test_name, test_type):
		"""
		Returns the output file for this test_name and test_type
		Example: fw_root/results/timestamp/test_type/test_name/raw.txt
		"""
		path = os.path.join(self.directory, test_name, test_type, "raw.txt")
		try:
			os.makedirs(os.path.dirname(path))
		except OSError:
			pass
		return path

	def get_stats_file(self, test_name, test_type):
		"""
		Returns the stats file name for this test_name and
		Example: fw_root/results/timestamp/test_type/test_name/stats.txt
		"""
		path = os.path.join(self.directory, test_name, test_type, "stats.txt")
		try:
			os.makedirs(os.path.dirname(path))
		except OSError:
			pass
		return path

	def report_verify_results(self, generator_test, test_type, result):
		"""
		Used by GeneratorTest to add verification details to our results

		TODO: Technically this is an IPC violation - we are accessing
		the parent process' memory from the child process
		"""
		if generator_test.name not in self.verify.keys():
			self.verify[generator_test.name] = dict()
		self.verify[generator_test.name][test_type] = result

	def report_benchmark_results(self, generator_test, test_type, results):
		"""
		Used by GeneratorTest to add benchmark data to this

		TODO: Technically this is an IPC violation - we are accessing
		the parent process' memory from the child process
		"""
		if test_type not in self.rawData.keys():
			self.rawData[test_type] = dict()

		# If results has a size from the parse, then it succeeded.
		if results:
			self.rawData[test_type][generator_test.name] = results

			# This may already be set for single-tests
			if generator_test.name not in self.succeeded[test_type]:
				self.succeeded[test_type].append(generator_test.name)
		else:
			# This may already be set for single-tests
			if generator_test.name not in self.failed[test_type]:
				self.failed[test_type].append(generator_test.name)

	def finish(self):
		"""
		Finishes these results.
		"""
		if not self.config.parse:
			# Normally you don't have to use Fore.BLUE before each line, but
			# Travis-CI seems to reset color codes on newline (see travis-ci/travis-ci#2692)
			# or stream flush, so we have to ensure that the color code is printed repeatedly
			log("Verification Summary",
				border='=',
				border_bottom='-',
				color=Fore.CYAN)
			for test in self.benchmarker.tests:
				log(Fore.CYAN + "| {!s}".format(test.name))
				if test.name in self.verify.keys():
					for test_type, result in self.verify[
							test.name].iteritems():
						if result.upper() == "PASS":
							color = Fore.GREEN
						elif result.upper() == "WARN":
							color = Fore.YELLOW
						else:
							color = Fore.RED
						log(Fore.CYAN + "|       " + test_type.ljust(13) +
							' : ' + color + result.upper())
				else:
					log(Fore.CYAN + "|      " + Fore.RED +
						"NO RESULTS (Did generator launch?)")
			log('', border='=', border_bottom='', color=Fore.CYAN)

		log("Results are saved in " + self.directory)

	#############################################################################
	# PRIVATE FUNCTIONS
	#############################################################################

	def __to_jsonable(self):
		"""
		Returns a dict suitable for jsonification
		"""
		to_ret = dict()

		to_ret['uuid'] = self.uuid
		to_ret['name'] = self.name
		to_ret['environmentDescription'] = self.environmentDescription
		to_ret['git'] = self.git
		to_ret['startTime'] = self.startTime
		to_ret['completionTime'] = self.completionTime
		to_ret['generators'] = self.generators
		to_ret['duration'] = self.duration
		to_ret['rawData'] = self.rawData
		to_ret['completed'] = self.completed
		to_ret['succeeded'] = self.succeeded
		to_ret['failed'] = self.failed
		to_ret['verify'] = self.verify

		return to_ret

	def __write_results(self):
		try:
			with open(self.file, 'w') as f:
				f.write(json.dumps(self.__to_jsonable(), indent=2))
		except IOError:
			log("Error writing results.json")

	def __count_sloc(self):
		"""
		Counts the significant lines of code for all tests and stores in results.
		"""
		generators = self.benchmarker.metadata.gather_generators(
			self.config.test, self.config.exclude)

		generator_to_count = {}
		for generator, testlist in generators.items():

			wd = testlist[0].directory

			# Find the last instance of the word 'code' in the yaml output. This
			# should be the line count for the sum of all listed files or just
			# the line count for the last file in the case where there's only
			# one file listed.
			command = "cloc --yaml --follow-links . | grep code | tail -1 | cut -d: -f 2"

			log("Running \"%s\" (cwd=%s)" % (command, wd))
			try:
				line_count = int(subprocess.check_output(command, cwd=wd, shell=True))
			except (subprocess.CalledProcessError, ValueError) as e:
				log("Unable to count lines of code for %s due to error '%s'" %
					(generator, e))
				continue

			log("Counted %s lines of code" % line_count)
			generator_to_count[generator] = line_count

		self.rawData['slocCounts'] = generator_to_count

	def __count_commits(self):
		"""
		Count the git commits for all the generator tests
		"""
		generators = self.benchmarker.metadata.gather_generators(
			self.config.test, self.config.exclude)

		def count_commit(directory, jsonResult):
			command = "git rev-list HEAD -- " + directory + " | sort -u | wc -l"
			try:
				commit_count = subprocess.check_output(command, shell=True)
				jsonResult[generator] = int(commit_count)
			except subprocess.CalledProcessError:
				pass

		# Because git can be slow when run in large batches, this
		# calls git up to 4 times in parallel. Normal improvement is ~3-4x
		# in my trials, or ~100 seconds down to ~25
		# This is safe to parallelize as long as each thread only
		# accesses one key in the dictionary
		threads = []
		json_result = {}
		# t1 = datetime.now()
		for generator, testlist in generators.items():
			directory = testlist[0].directory
			t = threading.Thread(
				target=count_commit, args=(directory, json_result))
			t.start()
			threads.append(t)
			# Git has internal locks, full parallel will just cause contention
			# and slowness, so we rate-limit a bit
			if len(threads) >= 4:
				threads[0].join()
				threads.remove(threads[0])

		# Wait for remaining threads
		for t in threads:
			t.join()
		# t2 = datetime.now()
		# print "Took %s seconds " % (t2 - t1).seconds

		self.rawData['commitCounts'] = json_result
		self.config.commits = json_result

	def __get_git_commit_id(self):
		"""
		Get the git commit id for this benchmark
		"""
		return subprocess.check_output(
			["git", "rev-parse", "HEAD"], cwd=self.config.fw_root).strip()

	def __get_git_repository_url(self):
		"""
		Gets the git repository url for this benchmark
		"""
		return subprocess.check_output(
			["git", "config", "--get", "remote.origin.url"],
			cwd=self.config.fw_root).strip()

	def __get_git_branch_name(self):
		"""
		Gets the git branch name for this benchmark
		"""
		return subprocess.check_output(
			'git rev-parse --abbrev-ref HEAD',
			shell=True,
			cwd=self.config.fw_root).strip()

	def __parse_stats(self, generator_test, test_type, start_time, end_time,
					  interval):
		"""
		For each test type, process all the statistics, and return a multi-layered
		dictionary that has a structure as follows:

		(timestamp)
		| (main header) - group that the stat is in
		| | (sub header) - title of the stat
		| | | (stat) - the stat itself, usually a floating point number
		"""
		stats_dict = dict()
		stats_file = self.get_stats_file(generator_test.name, test_type)
		with open(stats_file) as stats:
			# dstat doesn't output a completely compliant CSV file - we need to strip the header
			while stats.next() != "\n":
				pass
			stats_reader = csv.reader(stats)
			main_header = stats_reader.next()
			sub_header = stats_reader.next()
			time_row = sub_header.index("epoch")
			int_counter = 0
			for row in stats_reader:
				time = float(row[time_row])
				int_counter += 1
				if time < start_time:
					continue
				elif time > end_time:
					return stats_dict
				if int_counter % interval != 0:
					continue
				row_dict = dict()
				for nextheader in main_header:
					if nextheader != "":
						row_dict[nextheader] = dict()
				header = ""
				for item_num, column in enumerate(row):
					if len(main_header[item_num]) != 0:
						header = main_header[item_num]
					# all the stats are numbers, so we want to make sure that they stay that way in json
					row_dict[header][sub_header[item_num]] = float(column)
				stats_dict[time] = row_dict
		return stats_dict

	def __calculate_average_stats(self, raw_stats):
		"""
		We have a large amount of raw data for the statistics that may be useful
		for the stats nerds, but most people care about a couple of numbers. For
		now, we're only going to supply:
		  * Average CPU
		  * Average Memory
		  * Total network use
		  * Total disk use
		More may be added in the future. If they are, please update the above list.

		Note: raw_stats is directly from the __parse_stats method.

		Recall that this consists of a dictionary of timestamps, each of which
		contain a dictionary of stat categories which contain a dictionary of stats
		"""
		global main_header, display_stat
		raw_stat_collection = dict()

		for time_dict in raw_stats.items()[1]:
			for main_header, sub_headers in time_dict.items():
				item_to_append = None
				if 'cpu' in main_header:
					# We want to take the idl stat and subtract it from 100
					# to get the time that the CPU is NOT idle.
					item_to_append = sub_headers['idl'] - 100.0
				elif main_header == 'memory usage':
					item_to_append = sub_headers['used']
				elif 'net' in main_header:
					# Network stats have two parts - recieve and send. We'll use a tuple of
					# style (recieve, send)
					item_to_append = (sub_headers['recv'], sub_headers['send'])
				elif 'dsk' or 'io' in main_header:
					# Similar for network, except our tuple looks like (read, write)
					item_to_append = (sub_headers['read'], sub_headers['writ'])
				if item_to_append is not None:
					if main_header not in raw_stat_collection:
						raw_stat_collection[main_header] = list()
					raw_stat_collection[main_header].append(item_to_append)

		# Simple function to determine human readable size
		# http://stackoverflow.com/questions/1094841/reusable-library-to-get-human-readable-version-of-file-size
		def sizeof_fmt(num):
			# We'll assume that any number we get is convertable to a float, just in case
			num = float(num)
			for x in ['bytes', 'KB', 'MB', 'GB']:
				if 1024.0 > num > -1024.0:
					return "%3.1f%s" % (num, x)
				num /= 1024.0
			return "%3.1f%s" % (num, 'TB')

		# Now we have our raw stats in a readable format - we need to format it for display
		# We need a floating point sum, so the built in sum doesn't cut it
		display_stat_collection = dict()
		for header, values in raw_stat_collection.items():
			display_stat = None
			if 'cpu' in header:
				display_stat = sizeof_fmt(math.fsum(values) / len(values))
			elif main_header == 'memory usage':
				display_stat = sizeof_fmt(math.fsum(values) / len(values))
			elif 'net' in main_header:
				receive, send = zip(*values)  # unzip
				display_stat = {
					'receive': sizeof_fmt(math.fsum(receive)),
					'send': sizeof_fmt(math.fsum(send))
				}
			else:  # if 'dsk' or 'io' in header:
				read, write = zip(*values)  # unzip
				display_stat = {
					'read': sizeof_fmt(math.fsum(read)),
					'write': sizeof_fmt(math.fsum(write))
				}
			display_stat_collection[header] = display_stat
		return display_stat

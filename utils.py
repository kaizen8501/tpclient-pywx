"""\
This file contains useful utilities for useage in the program.
"""

import sys
import string
import traceback
import os
import os.path

try:
	import cPickle as pickle
except ImportError:
	import pickle

def do_traceback():
	type, val, tb = sys.exc_info()
	sys.stderr.write(string.join(traceback.format_exception(type, val, tb), ''))
	if hasattr(sys.stderr, "flush"):
		sys.stderr.flush()

DEBUG_NETWORK = "NETWORK:"
DEBUG_MAIN = "MAIN:"
DEBUG_WINDOWS = "WINDOWS:"
DEBUG_GAME = "GAME:"

DEBUGGING = [DEBUG_NETWORK, DEBUG_MAIN, DEBUG_WINDOWS, DEBUG_GAME]

def debug(id, string):
	if id in DEBUGGING:
		print id, string

class Blank:
	pass

def configpath():
	"""\
	Figures out where to save the preferences.
	"""
	dirs = [("APPDATA", "Thousand Parsec"), ("HOME", ".tp"), (".", "var")]
	for base, extra in dirs:
		if base in os.environ:
			base = os.environ[base]
		elif base != ".":
			continue
			
		rc = os.path.join(base, extra)
		if not os.path.exists(rc):
			os.mkdir(rc)
		return rc

cache = {}
def load_data(file):
	"""\
	Loads preference data from a file.
	"""
	global cache
	
	if file not in cache.keys():
		try:
			f = open(os.path.join(configpath(), file), "r")
			cache[file] = pickle.load(f)
		except IOError:
			return None
		
	return cache[file]
	
def save_data(file, data):
	"""\
	Saves preference data to a file.
	"""
	global cache

	print "Saving", file, data

	f = open(os.path.join(configpath(), file), "w")
	pickle.dump(data, f)

	cache[file] = data

config = None
def load_config():
	"""\
	Loads the config file.
	"""
	global config
	
	if not config:
		class Config:
			pass
		
		config = Config()
		
		try:
			f = open(os.path.join(configpath(), "pywx_config"), "r")
			
			for line in f.readline():
				if line[0] == '#':
					continue
				
				else:
					pass

		except IOError:
			return None
		
	return config

__all__ = [
	'Blank', 'save_data', 'load_data', 'configpath', # Config functions
	'debug', 'do_traceback', 'DEBUG_NETWORK', 'DEBUG_MAIN', 'DEBUG_WINDOWS', 'DEBUG_GAME', # Debugging functions
	]

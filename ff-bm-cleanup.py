# encoding: utf-8

# for command line argument access
import sys

# DEBUG
from pprint import pprint

# HTTP requests - http://requests.readthedocs.io/en/master/user/quickstart/
import requests
# Safe HTTP requests - from http://stackoverflow.com/questions/15431044/can-i-set-max-retries-for-requests-request
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

# beautiful soup for html parsing
from bs4 import BeautifulSoup

# logging - https://docs.python.org/2/howto/logging.html#logging-basic-tutorial
import logging
logging.basicConfig(filename='ff-bm-cleanup.log', level=logging.DEBUG, format='%(asctime)s [%(name)s] |%(levelname)s| %(message)s')

# JSON - http://stackoverflow.com/questions/2835559/parsing-values-from-a-json-file-in-python#2835672
import json

# regexp
import re


# functions  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def http_req(uri):
	"""Safely request an HTTP(s) uri."""
	logging.debug('Requesting [%s]', uri)
	rs = requests.Session()
	retries = Retry(total=3, backoff_factor=0.3, \
					status_forcelist=[ 500, 502, 503, 504 ])
	rs.mount('http://', HTTPAdapter(max_retries=retries))
	rs.mount('https://', HTTPAdapter(max_retries=retries))
	#headers = requests.utils.default_user_agent()
	#pprint(headers)
	#headers['User-Agent'] = 'Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:50.0) Gecko/20100101 Firefox/50.0'
	my_headers = {'User-Agent': 'Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:50.0) Gecko/20100101 Firefox/50.0'}
	return rs.get(uri, stream=True, timeout=10, headers=my_headers)


def get_page_metadata(html):
	"""Extracts useful metadata from an html page."""
	data = {
		'title': '',
		'description': '',
		'keywords': ''
	}
	page = BeautifulSoup(html, 'lxml')
	if page.title is not None:
		data['title'] = normalize_string(page.title.string)
	# FIXME: required for term extraction from page content
	#data['fulltext'] = page.get_text()
	description = page.find('meta', attrs={'name': 'description'})
	if description is not None:
		data['description'] = description.attrs['content']
	keywords = page.find('meta', attrs={'name': 'keywords'})
	if keywords is not None:
		data['keywords'] = keywords.attrs['content']
	logging.debug('page metadata: %s', data)
	return data


def normalize_string(s):
	"""Simplifies and cleans up a string."""
	sanitized = re.sub(r'http[s]?\:\/\/', '', s)
	sanitized = re.sub(r'[^\w\.\-\_\s]', '', sanitized)
	sanitized = re.sub(r'\s+', ' ', sanitized)
	return sanitized


def normalize_tags(bm_tags, page_tags):
	"""Extract, normalize, unify tags from the bookmark and the webpage."""
	# FIXME: extract tags from page content with
	#        https://pypi.python.org/pypi/topia.termextract
	tags = set()
	for tag in bm_tags.split(','):
		normalized_tag = normalize_string(tag.lower())
		if normalized_tag != '':
			tags.add(normalized_tag)
	for tag in re.split(r'\W+', page_tags):
		normalized_tag = normalize_string(tag.lower())
		if normalized_tag != '':
			tags.add(normalized_tag)
	return ','.join(tags)


def remove_entry(container, entry):
	"""Try to remove an entry from a container."""
	# http://stackoverflow.com/questions/18418/elegant-way-to-remove-items-from-sequence-in-python
	logging.debug('[x] ID: %s removing entry', entry['id'])
	try:
		container['children'].remove(entry)
	except Exception as e:
		logging.warn('Error removing entry: %s', e)


def entry_find_name(entry):
	"""Find a valid name for the entry."""
	# FIXME: could make it better
	name = 'Untitled entry'
	if 'title' in entry and entry['title'] != '':
		name = normalize_string(entry['title'])
	return name


def entry_handle_container(container, entry, path, name):
	"""Handle a container entry."""
	logging.debug('[ ] ID: %s is a container', entry['id'])
	# short-circuit if the container is empty
	if not 'children' in entry or len(entry['children']) == 0:
		logging.debug('[ ] ID: %s container is empty, removing', entry['id'])
		remove_entry(container, entry)
		return
	path.append(name) # add the name to the path stack
	iterate_bookmarks(path, entry) # iterate over the entry
	del path[-1] # remove the name from the path stack when you're done


def entry_handle_bookmark(container, entry, path, name):
	"""Handle a bookmark entry."""
	logging.debug('uri ID: %s is a bookmark (%s)', entry['id'], entry['uri'])
	page_metadata = {
		'title': '',
		'description': '',
		'keywords': ''
	}
	# short-circuit check if the uri is duplicate
	# FIXME: using global variables is ugly
	if entry['uri'] in URIS:
		logging.debug('[x] ID: %s has a duplicate URI, removing', entry['id'])
		remove_entry(container, entry)
		return
	# if the uri is not in the list, add it
	# FIXME: using global variables is ugly
	URIS.add(entry['uri'])
	# try to fetch the page
	if entry['uri'].startswith('http://') or entry['uri'].startswith('https://'):
		try:
			req = http_req(entry['uri'])
			if req.status_code == 200:
				if len(req.history) > 0:
					# update the uri if it has been changed (redirects, etc)
					logging.warn('-m- ID: %s url changed old(%s) new(%s)', entry['id'], entry['uri'], req.url)
					entry['uri'] = req.url
				page_metadata = get_page_metadata(req.text)
			else:
				logging.error('-x- ID: %s bad return code for %s', entry['id'], entry['url'])
				remove_entry(container, entry)
				return
		except Exception as e:
			logging.error('-x- ID: %s exception while fetching (%s): %s', entry['id'], entry['url'], e)
			remove_entry(container, entry)
			return
	# normalize tags
	if not 'tags' in entry:
		entry['tags'] = '' 	# add an empty tag list
	entry['tags'] = normalize_tags(entry['tags'], page_metadata['keywords'])
	# report
	logging.info('%s/%s | ID: %s | URI: %s | Tags: %s', \
		'/'.join(path), name, entry['id'], entry['uri'], entry['tags'])
	print("{0} / {1} | ID: {2} | URI: {3} | Tags: {4}".format(\
		'/'.join(path), name, entry['id'], entry['uri'], entry['tags']))


def iterate_bookmarks(path, container):
	"""Iterate over the bookmark tree."""
	# report where I am
	logging.debug('>>> ID: %s iterate_bookmarks(%s, %s [...])', container['id'], path, str(container)[0:30])
	for entry in reversed(container['children']):
		name = entry_find_name(entry)
		logging.debug('--> ID: %s %s/%s', entry['id'], path, name)
		if entry['type'] == 'text/x-moz-place-container':
			entry_handle_container(container, entry, path, name)
		if entry['type'] == 'text/x-moz-place':
			entry_handle_bookmark(container, entry, path, name)


# ~~~ main ~~~

URIS = set()

try:
	bm = json.load( open(sys.argv[1]) )
except:
	print("Please use {} <bookmarks.json>".format(sys.argv[0]))

iterate_bookmarks(['.'], bm)

with open('bookmarks-fixed.json', 'wb') as file_handle:
	file_handle.write(json.dumps(bm).encode('utf-8'))

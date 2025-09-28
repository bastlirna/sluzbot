import sys
import requests
import csv
import io
import os
import re
from dotenv import load_dotenv
from loguru import logger

# load environment variables from a .env file (if present)
load_dotenv()

# Configure loguru logger (level can be set via LOG_LEVEL env var)
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logger.remove()
logger.add(sys.stderr, level=log_level, backtrace=True, diagnose=True)

def download_csv(url, timeout=10, force_utf8=False):
	"""
	Download CSV from url and return decoded text.
	Raises requests.HTTPError on bad HTTP status.
	"""
	logger.info("Downloading CSV")
	resp = requests.get(url, timeout=timeout)
	logger.debug("HTTP GET {} -> status {}", url, resp.status_code)
	resp.raise_for_status()
	if force_utf8:
		logger.debug("Forcing response encoding to utf-8")
		resp.encoding = "utf-8"
	else:
		if not resp.encoding:
			logger.debug("Response has no encoding, using apparent_encoding")
			resp.encoding = resp.apparent_encoding or "utf-8"
	text = resp.text
	logger.debug("Downloaded {} bytes (encoding={})", len(text), resp.encoding)
	return text

def parse_csv_get_cell(text, row=22, col=0):
	"""
	Parse CSV text and return the value at (row, col).
	row is 1-based. Raises IndexError if CSV has fewer rows.
	"""
	logger.debug("Parsing CSV to extract row {} col {}", row, col)
	f = io.StringIO(text)
	reader = csv.reader(f)
	for i, r in enumerate(reader, start=1):
		if i == row:
			val = r[col] if len(r) > col else ""
			logger.debug("Found value at row {} col {}: {!r}", row, col, val)
			return val
	raise IndexError(f"CSV has fewer than {row} rows")

def get_cell_a22(url, timeout=10, force_utf8=False):
	"""
	Download CSV from url and return the value in cell A22 (column A, row 22).
	Raises requests.HTTPError on bad HTTP status, IndexError if CSV too short.
	"""
	logger.debug("Getting cell A22 from {} (force_utf8={})", url, force_utf8)
	text = download_csv(url, timeout=timeout, force_utf8=force_utf8)
	return parse_csv_get_cell(text, row=22, col=0)

def _wrap_usernames(text):
	"""
	Wrap bare usernames that start with @ and contain no spaces with angle brackets.
	Does not re-wrap usernames already enclosed in <...>.
	"""
	if not text:
		return text
	logger.debug("Wrapping usernames in text: {!r}", text)
	# match @ followed by non-space chars but stop before common trailing punctuation and angle brackets
	pattern = r'(?<!<)(@[^<>\s,.;:!?)]+)(?!>)'
	result = re.sub(pattern, r'<\1>', text)
	if result != text:
		logger.debug("Wrapped usernames -> {!r}", result)
	return result

def send_to_slack(webhook_url, text, timeout=10):
	"""
	Send text to Slack via an incoming webhook URL.
	Raises requests.HTTPError on non-2xx responses.
	"""
	if not webhook_url:
		logger.error("Slack webhook URL is empty")
		raise ValueError("Slack webhook URL is empty")
		
	logger.info("Sending message to Slack webhook")
	# Slack incoming webhooks accept a simple {"text": "..."} JSON body
	resp = requests.post(webhook_url, json={"text": text}, timeout=timeout)
	logger.debug("Slack response status: {}, body (truncated): {!r}", resp.status_code, (resp.text[:200] + '...') if resp.text else '')
	resp.raise_for_status()
	logger.info("Message posted to Slack (status {})", resp.status_code)
	return resp

def main():
	# Read URL from environment variable instead of command-line argument
	url = os.environ.get("CSV_URL")
	if not url:
		logger.error("CSV_URL not set in environment or .env")
		print("Usage: set CSV_URL in the environment or in a .env file")
		sys.exit(1)

	# Read Slack webhook URL from environment
	slack_webhook = os.environ.get("SLACK_WEBHOOK_URL")
	if not slack_webhook:
		logger.error("SLACK_WEBHOOK_URL not set in environment or .env")
		print("Usage: set SLACK_WEBHOOK_URL in the environment or in a .env file")
		sys.exit(1)

	# Read FORCE_UTF8 flag from environment (accepts 1/true/yes)
	force_utf8_env = os.environ.get("FORCE_UTF8", "")
	force_utf8 = str(force_utf8_env).strip().lower() in ("1", "true", "yes")
	if force_utf8:
		logger.info("FORCE_UTF8 enabled: forcing downloaded CSV encoding to utf-8")

	try:
		logger.info("Starting fetch and post workflow")
		value = get_cell_a22(url, force_utf8=force_utf8)
		wrapped_value = _wrap_usernames(value)
		logger.debug("Final message to send: {!r}", wrapped_value)
		# send value to Slack
		send_to_slack(slack_webhook, wrapped_value)
		logger.info("Sent to Slack")
	except Exception:
		logger.exception("Unhandled exception in main")
		sys.exit(1)

if __name__ == "__main__":
	main()
import sys
import requests
import csv
import io
import os
import re
from dotenv import load_dotenv

# load environment variables from a .env file (if present)
load_dotenv()

def download_csv(url, timeout=10):
	"""
	Download CSV from url and return decoded text.
	Raises requests.HTTPError on bad HTTP status.
	"""
	resp = requests.get(url, timeout=timeout)
	resp.raise_for_status()
	if not resp.encoding:
		resp.encoding = resp.apparent_encoding or "utf-8"
	return resp.text

def parse_csv_get_cell(text, row=22, col=0):
	"""
	Parse CSV text and return the value at (row, col).
	row is 1-based. Raises IndexError if CSV has fewer rows.
	"""
	f = io.StringIO(text)
	reader = csv.reader(f)
	for i, r in enumerate(reader, start=1):
		if i == row:
			return r[col] if len(r) > col else ""
	raise IndexError(f"CSV has fewer than {row} rows")

def get_cell_a22(url, timeout=10):
	"""
	Download CSV from url and return the value in cell A22 (column A, row 22).
	Raises requests.HTTPError on bad HTTP status, IndexError if CSV too short.
	"""
	text = download_csv(url, timeout=timeout)
	return parse_csv_get_cell(text, row=22, col=0)

def _wrap_usernames(text):
	"""
	Wrap bare usernames that start with @ and contain no spaces with angle brackets.
	Does not re-wrap usernames already enclosed in <...>.
	"""
	if not text:
		return text
	# match @ followed by non-space chars but stop before common trailing punctuation and angle brackets
	pattern = r'(?<!<)(@[^<>\s,.;:!?)]+)(?!>)'
	return re.sub(pattern, r'<\1>', text)

def send_to_slack(webhook_url, text, timeout=10):
	"""
	Send text to Slack via an incoming webhook URL.
	Raises requests.HTTPError on non-2xx responses.
	"""
	if not webhook_url:
		raise ValueError("Slack webhook URL is empty")
		
	# Slack incoming webhooks accept a simple {"text": "..."} JSON body
	resp = requests.post(webhook_url, json={"text": text}, timeout=timeout)
	resp.raise_for_status()
	return resp

def main():
	# Read URL from environment variable instead of command-line argument
	url = os.environ.get("CSV_URL")
	if not url:
		print("Usage: set CSV_URL in the environment or in a .env file")
		sys.exit(1)

	# Read Slack webhook URL from environment
	slack_webhook = os.environ.get("SLACK_WEBHOOK_URL")
	if not slack_webhook:
		print("Usage: set SLACK_WEBHOOK_URL in the environment or in a .env file")
		sys.exit(1)

	try:
		value = get_cell_a22(url)
		wrapped_value = _wrap_usernames(value)
		print(wrapped_value)
		# send value to Slack
		send_to_slack(slack_webhook, wrapped_value)
		print("Sent to Slack")
	except Exception as e:
		# print a concise error message
		print("Error:", e)
		sys.exit(1)

if __name__ == "__main__":
	main()
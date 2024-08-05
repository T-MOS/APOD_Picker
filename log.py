import logging
import json

def to_errlog(error_message):
  logging.error(error_message)

def json_log(pool,url,dup,image):
  log_entry = {
    "pool": pool,
    "url/source": url,
    "duplicate": dup,
    "image": image
  }
  logging.info(json.dumps(log_entry, indent=2)+"\n")
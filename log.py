import logging

def to_errlog(error_message):
  logging.error(error_message)

def json_log(pool,url,dup,image):
  from json import dumps
  log_entry = {
    "pool(s)": pool,
    "url/source": url,
    "duplicate": dup,
    "image": image
  }
  logging.info(dumps(log_entry, indent=2)+"\n")
# coding=utf-8
import string
import cgi
import os
import re
import pickle
import time
import _mysql

from database import *
from framework import *
from post import regenerateAccess
#from xhtml_clean import Cleaner

from settings import Settings

def format_post(message, ip, parentid, parent_timestamp=0):
  """
  Formats posts using the specified format
  """
  board = Settings._.BOARD
  using_markdown = False
  
  # Escape any HTML if user is not using Markdown or HTML
  if not Settings.USE_HTML:
    message = cgi.escape(message)
  
  # Strip text
  message = message.rstrip()[0:8000]
  
  # Treat HTML
  if Settings.USE_MARKDOWN:
    message = markdown(message)
    using_markdown = True
  if Settings.USE_HTML:
    message = onlyAllowedHTML(message)

  # [code] tag
  if board["dir"] == "tech":
    message = re.compile(r"\[code\](.+)\[/code\]", re.DOTALL | re.IGNORECASE).sub(r"<pre><code>\1</code></pre>", message)

  if Settings.VIDEO_THUMBS:
    (message, affected) = videoThumbs(message)
    if affected:
      message = close_html(message)
    
  message = clickableURLs(message)
  message = checkRefLinks(message, parentid, parent_timestamp)
  message = checkWordfilters(message, ip, board["dir"])
  
  # If user is not using markdown quotes must be created and \n changed for HTML line breaks
  if not using_markdown:
    message = checkQuotes(message)
    message = message.replace("\n", "<br />")

  return message
    
def tripcode(name):
  """
  Calculate tripcode to match output of most imageboards
  """
  if name == '':
    return '', ''
  
  board = Settings._.BOARD
  
  name = name.decode('utf-8')
  key = Settings.TRIP_CHAR.decode('utf-8')
  
  # if there's a trip
  (namepart, marker, trippart) = name.partition('#')
  if marker:
    namepart = cleanString(namepart)
    trip = ''
    
    # secure tripcode
    if Settings.ALLOW_SECURE_TRIPCODES and '#' in trippart:
      (trippart, securemarker, securepart) = trippart.partition('#')
      try:
        securepart = securepart.encode("sjis", "ignore")
      except:
        pass
      
      # encode secure tripcode
      trip = getMD5(securepart + Settings.SECRET)
      trip = trip.encode('base64').replace('\n', '')
      trip = trip.encode('rot13')
      trip = key+key+trip[2:12]
      
      # return it if we don't have a normal tripcode
      if trippart == '':
        return namepart.encode('utf-8'), trip.encode('utf-8')
    
    # do normal tripcode
    from crypt import crypt
    try:
      trippart = trippart.encode("sjis", "ignore")
    except:
      pass
    
    trippart = cleanString(trippart, True, True)
    salt = re.sub(r"[^\.-z]", ".", (trippart + "H..")[1:3])
    salt = salt.translate(string.maketrans(r":;=?@[\]^_`", "ABDFGabcdef"))
    trip = key + crypt(trippart, salt)[-10:] + trip
      
    return namepart.encode('utf-8'), trip.encode('utf-8')
  
  return name.encode('utf-8'), ''

def iphash(ip, post, t, useid, mobile, cap_id, hide_end, has_countrycode):
  current_t = time.time()
  
  if cap_id:
    id = cap_id
  elif 'sage' in post['email'] and useid == '1':
    id = '???'
  else:
    day = int((current_t + (Settings.TIME_ZONE*3600)) / 86400)
    word = ',' + str(day)
    
    # Make difference by thread
    word += ',' + str(t)
    
    id = hide_data(ip + word, 6, "id", Settings.SECRET)
    
  agent = os.environ["HTTP_USER_AGENT"]
  if hide_end:
    id += '*'
  elif addressIsTor(ip):
    id += 'T'
  elif 'Dalvik' in agent:
    id += 'R'
  elif 'Android' in agent:
    id += 'a'
  elif 'iPhone' in agent:
    id += 'i'
  elif useid == '3':
    if 'Edge' in agent:
      id += 'E'
    elif 'Safari' in agent and not 'Chrome' in agent:
      id += 's'
    elif 'SeaMonkey' in agent:
      id += 'S'
    elif 'Firefox' in agent:
      id += 'F'
    elif 'Opera' in agent or 'OPR' in agent:
      id += 'o'
    elif 'Chrome' in agent:
      id += 'C'
    elif 'MSIE' in agent or 'Trident' in agent:
      id += 'I'
    elif mobile:
      id += 'Q'
    else:
      id += '0'
  elif mobile:
    id += 'Q'
  else:
    id += '0'
  
  if (not has_countrycode and
      not addressIsTor(ip) and
      addressIsProxy(ip)):
    id += '!'
  elif (not has_countrycode and
        not addressIsTor(ip) and
        not addressIsES(ip)):
    id += '!'
    
  return id

def cleanString(string, escape=True, quote=False):
  string = string.strip()
  if escape:
    string = cgi.escape(string, quote)
  return string

def clickableURLs(message):
  # URL
  message = re.compile(r'( |^|:|\(|\[)((?:https?://|ftp://|mailto:|news:|irc:)[^\s<>()"]*?(?:\([^\s<>()"]*?\)[^\s<>()"]*?)*)((?:\s|<|>|"|\.|\|\]|!|\?|,|&#44;|&quot;)*(?:[\s<>()"]|$))', re.M).sub(r'\1<a href="\2" rel="nofollow" target="_blank">\2</a>\3', message)
  # Emails
  message = re.compile(r"( |^|:)([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,6})", re.I | re.M).sub(r'\1<a href="mailto:\2" rel="nofollow">&lt;\2&gt;</a>', message)

  return message
  
def videoThumbs(message):
  # Youtube
  __RE = re.compile(r"^(?: +)?(https?://(?:www\.)?youtu(?:be\.com/watch\?v=|\.be/)([\w\-]+))(?: +)?$", re.M)
  matches = __RE.finditer(message)
  if matches:
    import json
    import urllib, urllib2
    
    v_ids = []
    videos = {}
      
    for match in matches:
      v_id = match.group(2)
      if v_id not in v_ids:
        v_ids.append(v_id)
        videos[v_id] = {
          'span': match.span(0),
          'url':  match.group(1),
        }
      if len(v_ids) >= Settings.VIDEO_THUMBS_LIMIT:
        raise UserError, "Has incluído muchos videos en tu mensaje. El máximo es %d." % Settings.VIDEO_THUMBS_LIMIT
      
  if videos:
    params = {
      'key': Settings.GOOGLE_API_KEY,
      'part': 'snippet,contentDetails',
      'id': ','.join(v_ids)
    }
    r_url = "https://www.googleapis.com/youtube/v3/videos?"+urllib.urlencode(params)
    res = urllib2.urlopen(r_url)
    res_json = json.load(res)
      
    offset = 0
    for item in res_json['items']:
      v_id = item['id']
      (start, end) = videos[v_id]['span']
      end += 1 # remove endline
      
      try:
        new_url = '<a href="%(url)s" target="_blank" class="yt"><span class="pvw"><img src="%(thumb)s" /></span><b>%(title)s</b> (%(secs)s)<br />%(channel)s</a><br />' \
                % {'title': item['snippet']['title'].encode('utf-8'),
                   'channel': item['snippet']['channelTitle'].encode('utf-8'),
                   'secs': parseIsoPeriod(item['contentDetails']['duration']).encode('utf-8'),
                   'url': videos[v_id]['url'],
                   'id': v_id.encode('utf-8'),
                   'thumb': item['snippet']['thumbnails']['default']['url'].encode('utf-8'),}
      except UnicodeDecodeError:
        raise UserError, repr(v_id)
      message = message[:start+offset] + new_url + message[end+offset:]
      offset += len(new_url) - (end-start)
  
  return (message, len(videos))

def fixMobileLinks(message):
  """
  Shorten long links; Convert >># links into a mobile version
  """
  board = Settings._.BOARD

  # If textboard
  if board["board_type"] == '1':
    message = re.compile(r'<a href="/(\w+)/read/(\d+)(\.html)?/*(.+)"').sub(r'<a href="/cgi/mobileread/\1/\2/\4"', message)
  else:
    message = re.compile(r'<a href="/(\w+)/res/(\d+)\.html#(\d+)"').sub(r'<a href="/cgi/mobileread/\1/\2#\3"', message)
  
  return message
  
def checkRefLinks(message, parentid, parent_timestamp):
  """
  Check for >># links in posts and replace with the HTML to make them clickable
  """
  board = Settings._.BOARD

  if board["board_type"] == '1':
    # Textboard
    if parentid != '0':
      message = re.compile(r'&gt;&gt;(\d+(,\d+|-(?=[ \d\n])|\d+)*n?)').sub('<a href="' + Settings.BOARDS_URL + board['dir'] + '/read/' + str(parent_timestamp) + r'/\1">&gt;&gt;\1</a>', message)
  else:
    # Imageboard
    quotes_id_array = re.findall(r"&gt;&gt;([0-9]+)", message)
    for quotes in quotes_id_array:
      try:
        post = FetchOne('SELECT * FROM `posts` WHERE `id` = ' + quotes + ' AND `boardid` = ' + board['id'] + ' LIMIT 1')
        if post['parentid'] != '0':
          message = re.compile("&gt;&gt;" + quotes).sub('<a href="' + Settings.BOARDS_URL + board['dir'] + '/res/' + post['parentid'] +  '.html#' + quotes + '">&gt;&gt;' + quotes + '</a>', message)
        else:
          message = re.compile("&gt;&gt;" + quotes).sub('<a href="' + Settings.BOARDS_URL + board['dir'] + '/res/' + post['id'] +  '.html#' + quotes + '">&gt;&gt;' + quotes + '</a>', message)
      except:
        message = re.compile("&gt;&gt;" + quotes).sub(r'<span class="q">&gt;&gt;'+quotes+'</span>', message)
        
  return message

def checkQuotes(message):
  """
  Check for >text in posts and add span around it to color according to the css
  """
  message = re.compile(r"^&gt;(.*)$", re.MULTILINE).sub(r'<span class="q">&gt;\1</span>', message)
  return message

def escapeHTML(string):
  string = string.replace('<', '&lt;')
  string = string.replace('>', '&gt;')
  return string

def onlyAllowedHTML(message):
  """
  Allow <b>, <i>, <u>, <strike>, and <pre> in posts, along with the special <aa>
  """
  message = sanitize_html(message)
  #message = re.compile(r"\[aa\](.+?)\[/aa\]", re.DOTALL | re.IGNORECASE).sub("<span class=\"sjis\">\\1</span>", message)
  
  return message

def close_html(message):
  """
  Old retarded version of sanitize_html, it just closes open tags.
  """
  import BeautifulSoup
  return unicode(BeautifulSoup.BeautifulSoup(message)).replace('&#13;', '').encode('utf-8')

def sanitize_html(message, decode=True):
  """
  Clean the code and allow only a few safe tags.
  """
  import BeautifulSoup

  # Decode message from utf-8 if required
  if decode:
    message = message.decode('utf-8', 'replace')
  
  # Create HTML Cleaner with our allowed tags
  whitelist_tags = ["a","b","br","blink","code","del","em","i","marquee","root","strike","strong","sub","sup","u"]
  whitelist_attr = ["href"]
  
  soup = BeautifulSoup.BeautifulSoup(message)

  # Remove tags that aren't allowed
  for tag in soup.findAll():
    if not tag.name.lower() in whitelist_tags:
      tag.name = "span"
      tag.attrs = []
    else:
      for attr in [attr for attr in tag.attrs if attr not in whitelist_attr]:
        del tag[attr]

  # We export the soup into a correct XHTML string
  string = unicode(soup).encode('utf-8')
  # We remove some anomalies we don't want
  string = string.replace('<br/>', '<br />').replace('&#13;', '')
  
  return string

def markdown(message):
  import markdown
  if message.strip() != "":
    #return markdown.markdown(message).rstrip("\n").rstrip("<br />")
    return markdown.markdown(message, extras=["cuddled-lists", "code-friendly"]).encode('utf-8')
  else:
    return ""

def checkWordfilters(message, ip, board):
  fixed_ip = inet_aton(ip)
  wordfilters = FetchAll("SELECT * FROM `filters` WHERE `type` = '0' ORDER BY `id` ASC")
  for wordfilter in wordfilters:
    if wordfilter["boards"] != "":
      boards = pickle.loads(wordfilter["boards"])
    if wordfilter["boards"] == "" or board in boards: 
      if wordfilter['action'] == '0':
        if not re.search(wordfilter['from'], message, re.DOTALL | re.IGNORECASE) is None:
          raise UserError, wordfilter['reason']
      elif wordfilter['action'] == '1':
        message = re.compile(wordfilter['from'], re.DOTALL | re.IGNORECASE).sub(wordfilter['to'], message)
      elif wordfilter['action'] == '2':
        # Ban
        if not re.search(wordfilter['from'], message, re.DOTALL | re.IGNORECASE) is None:
          if wordfilter['seconds'] != '0':
            until = str(timestamp() + int(wordfilter['seconds']))
          else:
            until = '0'
            
          InsertDb("INSERT INTO `bans` (`ip`, `boards`, `added`, `until`, `staff`, `reason`, `note`, `blind`) VALUES (" + \
                  "'" + str(fixed_ip) + "', '" + _mysql.escape_string(wordfilter['boards']) + \
                  "', " + str(timestamp()) + ", " + until + ", 'System', '" + _mysql.escape_string(wordfilter['reason']) + \
                  "', 'Word Auto-ban', '"+_mysql.escape_string(wordfilter['blind'])+"')")
          regenerateAccess()
          raise UserError, wordfilter['reason']
      elif wordfilter['action'] == '3':
        if not re.search(wordfilter['from'], message, re.DOTALL | re.IGNORECASE) is None:
          raise UserError, '<meta http-equiv="refresh" content="%s;url=%s" />%s' % (wordfilter['redirect_time'], wordfilter['redirect_url'], wordfilter['reason'])
  return message
  
def checkNamefilters(name, tripcode, ip, board):
  namefilters = FetchAll("SELECT * FROM `filters` WHERE `type` = '1'")
  
  for namefilter in namefilters:
    if namefilter["boards"] != "":
      boards = pickle.loads(namefilter["boards"])
    if namefilter["boards"] == "" or board in boards: 
      # check if this filter applies
      match = False
      
      if namefilter['from'] and namefilter['from_trip']:
        # both name and trip filter
        if re.search(namefilter['from'], name, re.DOTALL | re.IGNORECASE) and tripcode == namefilter['from_trip']:
          match = True
      elif namefilter['from'] and not namefilter['from_trip']:
        # name filter
        if re.search(namefilter['from'], name, re.DOTALL | re.IGNORECASE):
          match = True
      elif not namefilter['from'] and namefilter['from_trip']:
        # trip filter
        if tripcode == namefilter['from_trip']:
          match = True      
      
    if match:
      # do action
      if namefilter['action'] == '0':
        raise UserError, namefilter['reason']
      elif namefilter['action'] == '1':
        name = namefilter['to']
        tripcode = ''
        return name, tripcode
      elif namefilter['action'] == '2':
        # Ban
        if namefilter['seconds'] != '0':
          until = str(timestamp() + int(namefilter['seconds']))
        else:
          until = '0'
          
        InsertDb("INSERT INTO `bans` (`ip`, `boards`, `added`, `until`, `staff`, `reason`, `note`, `blind`) VALUES (" + \
                "'" + _mysql.escape_string(ip) + "', '" + _mysql.escape_string(namefilter['boards']) + \
                "', " + str(timestamp()) + ", " + until + ", 'System', '" + _mysql.escape_string(namefilter['reason']) + \
                "', 'Name Auto-ban', '"+_mysql.escape_string(namefilter['blind'])+"')")
        regenerateAccess()
        raise UserError, namefilter['reason']
      elif namefilter['action'] == '3':
        raise UserError, '<meta http-equiv="refresh" content="%s;url=%s" />%s' % (namefilter['redirect_time'], namefilter['redirect_url'], namefilter['reason'])
  return name, tripcode
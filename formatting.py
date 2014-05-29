# coding=utf-8
import string
import cgi
import re
import pickle
import _mysql

from database import *
from framework import *
from post import regenerateAccess
#from xhtml_clean import Cleaner

from settings import Settings

def format_post(message, ip, parentid, type="none"):
  """
  Formats posts using the specified format
  """
  board = Settings._.BOARD
  using_markdown = False
  
  if not type:
    type = "tags"
  
  # Escape any HTML if user is not using Markdown
  if type != "tags":
    message = cgi.escape(message)
  
  message = cutText(message, Settings.POST_LINE_WIDTH)
  message = message.rstrip()[0:8000]
  
  # Don't create <a>'s if user doesn't want any HTML in post
  if type != "none":
    message = clickableURLs(message)
  
  if type == "tags":
    if Settings.USE_MARKDOWN:
      message = markdown(message)
      using_markdown = True
    message = onlyAllowedHTML(message)
  elif type == "aa":
    message = "<span class=\"sjis\">" + sanitize_html(message) + "</span>"
    
  message = checkRefLinks(message, parentid)
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
  key = board['tripcode_character'].decode('utf-8')
  
  # if there's a trip
  array = re.findall(r'^(.*?)((?<!&)#|'+ key + r'E)(.*)$', name)
  if array:
    namepart, marker, trippart = array[0]
    namepart = cleanString(namepart)
    trip = ''
    
    # secure tripcode
    secure_array = re.findall('^(.*)' + marker + '(.*)$', trippart)
    if secure_array and Settings.ALLOW_SECURE_TRIPCODES:
      trippart, securepart = secure_array[0]
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

def iphash(ip, email, t, useid):
  board = Settings._.BOARD
  
  if useid in ['3', '4'] and (email.lower() == Settings.DEFAULT_SAGE):
    return Settings.IPHASH_SAGEWORD
  else:
    word = ""
    if useid not in ['1', '3']:
      word += ',' + str(t)
    return hide_data(ip + word, 6, "id", Settings.SECRET)
        
def nameBlock(post_name, post_tripcode, post_email, post_timestamp_formatted, post_iphash, post_mobile=False):
  """
  Creates a string containing HTML formatted poster name data.  This saves quite
  a bit of time when templating pages, as it saves the engine a few conditions
  per post, which adds up over the time of processing entire pages
  """
  board = Settings._.BOARD
  nameblock = ""
  
  if post_name == "" and post_tripcode == "":
    post_anonymous = True
  else:
    post_anonymous = False
  
  if board["anonymous"] == "" and (post_anonymous or board["forced_anonymous"] == '1'):
    if post_email:
      nameblock += '<a href="mailto:' + post_email.replace('"', '&quot;') + '">'
    nameblock += post_timestamp_formatted
    if post_email:
      nameblock += "</a>"
  else:
    if post_anonymous:
      nameblock += '<span class="postername">'
      if post_email:
        nameblock += '<a href="mailto:' + post_email.replace('"', '&quot;') + '" rel="nofollow">' + board['anonymous'] + '</a>'
      else:
        nameblock += board["anonymous"]
    else:
      nameblock += '<span class="postername">'
      if post_email:
        nameblock += '<a href="mailto:' + post_email.replace('"', '&quot;') + '" rel="nofollow">'
      if post_name:
        nameblock += post_name
      else:
        if not post_tripcode:
          nameblock += board["anonymous"]
      if post_email:
        nameblock += "</a>"
      
      if post_tripcode:
        nameblock += '</span><span class="postertrip">'
        if post_email:
          nameblock += '<a href="mailto:' + post_email.replace('"', '&quot;') + '" rel="nofollow">'
        nameblock += post_tripcode
        if post_email:
          nameblock += "</a>"
    
    nameblock += "</span> "
    
    if post_mobile:
      nameblock += '<small>(Móvil)</small> '
      
    nameblock += post_timestamp_formatted

  if post_iphash != '':
    nameblock += ' ID:' + post_iphash
  
  return nameblock

def modNameBlock(post_name, post_timestamp_formatted, post_capcode):
  nameblock = ""
  
  if post_name == "":
    post_anonymous = True
  else:
    post_anonymous = False
  
  # Capcodes detect
  capcode = ''
  capcodeclass = ''
  if post_capcode in [1, 2, 3, 4]:
    # Super-admin
    capcode = _('Staff')
    capcodeclass = ' administrator'
    
  if post_anonymous:
    nameblock += '<span class="postername'+capcodeclass+'">'
    nameblock += 'Sin Nombre'
  else:
    nameblock += '<span class="postername'+capcodeclass+'">'
    if post_name:
      nameblock += post_name
    else:
      nameblock += 'Sin Nombre'
    
  # Add capcode
  if post_capcode > 0:
    nameblock += '</span><span class="' + capcodeclass[1:] + '">' + ' ('+capcode+')'
    
  nameblock += "</span> " + post_timestamp_formatted
    
  return nameblock

def cleanString(string, escape=True, quote=False):
  string = string.strip()
  if escape:
    string = cgi.escape(string, quote)
  return string

def clickableURLs(message):
  # URL
  message = re.compile(r"( |^|:)((https?|ftp):((//)|(\\\\))+[\w\d:#@%/;$()~_?\+-=\\\.&]*)", re.I | re.M).sub(r'\1<a href="\2" rel="nofollow" target="_blank">\2</a>', message)
  # Emails
  message = re.compile(r"( |^|:)([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,6})", re.I | re.M).sub(r'\1<a href="mailto:\2" rel="nofollow">&lt;\2&gt;</a>', message)
  
  return message

def fixMobileLinks(message):
  """
  Convert >># links into a mobile version
  """
  board = Settings._.BOARD
  
  # If textboard
  if board["board_type"] == '1':
    message = re.compile('<a href="/cgi/read/').sub('<a href="/cgi/mobileread/', message)
    message = re.compile(r'<a href="/(\w+)/res/(\d+)\.html/(.+)"').sub(r'<a href="/cgi/mobileread/\1/\2/\3"', message)
  else:
    message = re.compile(r'<a href="/(\w+)/res/(\d+)\.html#(\d+)"').sub(r'<a href="/cgi/mobileread/\1/\2#\3"', message)
  
  return message
  
def checkRefLinks(message, parentid):
  """
  Check for >># links in posts and replace with the HTML to make them clickable
  """
  board = Settings._.BOARD

  if board["board_type"] == '1':
    # Textboards
    if parentid != '0':
      message = re.compile(r"&gt;&gt;(([0-9]+([,\-0-9])?)+)").sub('<a href="' + Settings.BOARDS_URL + board['dir'] + '/read/' + str(parentid) + r'/\1">&gt;&gt;\1</a>', message)
  else:
    # Imageboards
    quotes_id_array = re.findall(r"&gt;&gt;([0-9]+)", message)
    for quotes in quotes_id_array:
      try:
        post = FetchOne('SELECT * FROM `posts` WHERE `id` = ' + quotes + ' AND `boardid` = ' + board['id'] + ' LIMIT 1')
        if post['parentid'] != '0':
          message = re.compile("&gt;&gt;" + quotes).sub('<a href="' + Settings.BOARDS_URL + board['dir'] + '/res/' + post['parentid'] +  '.html#' + quotes + '" onclick="javascript:highlight(' + '\'' + quotes + '\'' + r', true);">&gt;&gt;' + quotes + '</a>', message)
        else:
          message = re.compile("&gt;&gt;" + quotes).sub('<a href="' + Settings.BOARDS_URL + board['dir'] + '/res/' + post['id'] +  '.html#' + quotes + '" onclick="javascript:highlight(' + '\'' + quotes + '\'' + r', true);">&gt;&gt;' + quotes + '</a>', message)
      except:
        message = re.compile("&gt;&gt;" + quotes).sub(r'<span class="unkfunc">&gt;&gt;'+quotes+'</span>', message)

  # Interbards
  requotes_id_array = re.findall(r"&gt;&gt;&gt;/([\wñ]+)/(\d+)?", message)
  for requotes in requotes_id_array:
    try:
      if requotes[1] == '':
        # Tirar solo al board
        message = re.compile(r"&gt;&gt;&gt;/" + requotes[0] + r"/(?=\r\n| |$)").sub('<a href="' + Settings.BOARDS_URL + requotes[0] + '/">&gt;&gt;&gt;/' + requotes[0] + '/</a>', message)
      else:
        # Hacer el link hacia el thread especifico
        post = FetchOne("SELECT * FROM `posts` INNER JOIN `boards` ON boards.id = posts.boardid WHERE posts.id = '" + requotes[1] + "' AND boards.dir = '" + _mysql.escape_string(requotes[0]) + "' LIMIT 1")
        if post['parentid'] != '0':
          message = re.compile("&gt;&gt;&gt;/" + requotes[0] + "/" + requotes[1] + r"(?!</)").sub('<a href="' + Settings.BOARDS_URL + requotes[0] + '/res/' + post['parentid'] +  '.html#' + requotes[1] + '" onclick="javascript:highlight(' + '\'' + requotes[1] + '\'' + r', true);">&gt;&gt;&gt;/' + requotes[0] + '/' + requotes[1] + '</a>', message)
        else:
          message = re.compile("&gt;&gt;&gt;/" + requotes[0] + "/" + requotes[1] + r"(?!</)").sub('<a href="' + Settings.BOARDS_URL + requotes[0] + '/res/' + post['id'] +  '.html#' + requotes[1] + '" onclick="javascript:highlight(' + '\'' + requotes[1] + '\'' + r', true);">&gt;&gt;&gt;/' + requotes[0] + '/' + requotes[1] + '</a>', message)
    except:
      #message = re.compile("&gt;&gt;&gt;/" + requotes[0] + "/" + requotes[1]).sub(r'<span class="unkfunc">&gt;&gt;&gt;/' + requotes[0] + '/' + requotes[1] + '</span>', message)
      pass
  
  return message

def checkQuotes(message):
  """
  Check for >text in posts and add span around it to color according to the css
  """
  message = re.compile(r"^&gt;(.*)$", re.MULTILINE).sub(r'<span class="unkfunc">&gt;\1</span>', message)
  
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
  #message = re.compile(r"###(?=\S)(.+?)(?<=\S)###", re.S).sub("<span class=\"spoiler\">\\1</span>", message)
  #message = re.compile(r"\[spoiler\](.+?)\[/spoiler\]", re.DOTALL | re.IGNORECASE).sub("<span class=\"spoiler\">\\1</span>", message)
  #message = re.compile(r"\[youtube\](.+?)\[/youtube\]", re.DOTALL | re.IGNORECASE).sub(r"<object type='application/x-shockwave-flash' width='320' height='265' data='http://www.youtube.com/v/\1'><param name='movie' value='http://www.youtube.com/v/\1' /></object>", message,1)
  #message = re.compile(r"\[aa\](.+?)\[/aa\]", re.DOTALL | re.IGNORECASE).sub("<span class=\"sjis\">\\1</span>", message)
  
  return message

def close_html(message):
  """
  Old retarded version of sanitize_html, it just closes open tags.
  """
  import BeautifulSoup
  return unicode(BeautifulSoup.BeautifulSoup(message)).replace('&#13;', '')

def sanitize_html(message, decode=True):
  """
  Clean the code and allow only a few safe tags.
  """
  import BeautifulSoup

  # Decode message from utf-8 if required
  if decode:
    message = message.decode('utf-8', 'replace')
  
  # Create HTML Cleaner with our allowed tags
  whitelist_tags = ["a","b","br","blink","blockquote","code","del","div","em","i","li","marquee","ol","p","root","strike","strong","sub","sup","u","ul"]
  
  soup = BeautifulSoup.BeautifulSoup(message)

  # Remove tags that aren't allowed
  for tag in soup.findAll():
    if not tag.name.lower() in whitelist_tags:
      tag.name = "span"
      tag.attrs = []

  # We export the soup into a correct XHTML string
  string = unicode(soup).encode('utf-8')
  # We remove some anomalities we don't want
  string = string.replace('<br/>', '<br />').replace('&#13;', '')
  
  return string

def markdown(message):
  import markdown
  if message.strip() != "":
    #return markdown.markdown(message).rstrip("\n").rstrip("<br />")
    return markdown.markdown(message, extras=["cuddled-lists", "code-friendly"]).encode('utf-8')
  else:
    return ""
    
def cutText(txt, where):
  """
  Acortar lineas largas
  Algoritmo traducido desde KusabaX
  """
  txt_split_primary = txt.split("\n")
  txt_processed = ''

  for txt_split in txt_split_primary:
    txt_split_secondary = txt_split.split(" ")
    
    for txt_segment in txt_split_secondary:
      segment_length = len(txt_segment)
      
      while segment_length > where:
        txt_processed += txt_segment[:where] + "\n"
        txt_segment = txt_segment[where:]
        segment_length = len(txt_segment)
      
      txt_processed += txt_segment + ' '

    txt_processed = txt_processed[:-1]
    txt_processed += '\n'

  return txt_processed

def checkWordfilters(message, ip, board):
  fixed_ip = inet_aton(ip)
  wordfilters = FetchAll("SELECT * FROM `filters` WHERE `type` = '0'")
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

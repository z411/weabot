# coding=utf-8
import os
import cgi
import datetime
import time
import hashlib
import pickle
import socket
import _mysql
import urllib
import re
from Cookie import SimpleCookie

from settings import Settings
from database import *

class CLT(datetime.tzinfo):
  """
  Clase para zona horaria chilena.
  Como el gobierno nos tiene los horarios de verano para la pura cagá,
  por mientras dejo el DST como un boolean. Cuando lo fijen, dejarlo automático.
  """
  def __init__(self):
    self.isdst = False
    
  def utcoffset(self, dt):
    #return datetime.timedelta(hours=-3) + self.dst(dt)
    return datetime.timedelta(hours=Settings.TIME_ZONE)
    
  def dst(self, dt):
    if self.isdst:
      return datetime.timedelta(hours=1)
    else:
      return datetime.timedelta(0)
      
  def tzname(self,dt):
    return "GMT -3"

def setBoard(dir):
  """
  Sets the board which the script is operating on by filling Settings._.BOARD
  with the data from the db.
  """
  if not dir:
    raise UserError, _("The specified board is invalid.")
  logTime("Seteando el board " + dir)
  board = FetchOne("SELECT * FROM `boards` WHERE `dir` = '%s' LIMIT 1" % _mysql.escape_string(dir))
  if not board:
    raise UserError, _("The specified board is invalid.")
  
  board["filetypes"] = FetchAll("SELECT * FROM `boards_filetypes` INNER JOIN `filetypes` ON filetypes.id = boards_filetypes.filetypeid WHERE `boardid` = %s ORDER BY `ext` ASC" % _mysql.escape_string(board['id']))
  board["filetypes_ext"] = [filetype['ext'] for filetype in board['filetypes']]
  logTime("Board seteado.")

  Settings._.BOARD = board
  
  return board

def addressIsBanned(ip, board):
  packed_ip = inet_aton(ip)
  bans = FetchAll("SELECT * FROM `bans` WHERE (`netmask` IS NULL AND `ip` = '"+str(packed_ip)+"') OR (`netmask` IS NOT NULL AND '"+str(packed_ip)+"' & `netmask` = `ip`)")
  logTime("SELECT * FROM `bans` WHERE (`netmask` IS NULL AND `ip` = '"+str(packed_ip)+"') OR (`netmask` IS NOT NULL AND '"+str(packed_ip)+"' & `netmask` = `ip`)")
  for ban in bans:
    if ban["boards"] != "":
      boards = pickle.loads(ban["boards"])
    if ban["boards"] == "" or board in boards: 
      if board not in Settings.EXCLUDE_GLOBAL_BANS:
        return True
  return False

def addressIsTor(ip):
  if Settings._.IS_TOR is None:
    res = False
    nodes = []
    with open('tor.txt') as f:
      nodes = [line.rstrip() for line in f]
    if ip in nodes:
      res = True
    Settings._.IS_TOR = res
    return res
  else:
    return Settings._.IS_TOR

def addressIsProxy(ip):
  if Settings._.IS_PROXY is None:
    res = False
    proxies = []
    with open('proxy.txt') as f:
      proxies = [line.rstrip() for line in f]
    if ip in proxies:
      res = True
    Settings._.IS_PROXY = res
    return res
  else:
    return Settings._.IS_PROXY
    
def addressIsES(ip):
  ES = ['AR', 'BO', 'CL', 'CO', 'CR', 'CU', 'EC', 'ES', 'GF',
        'GY', 'GT', 'HN', 'MX', 'NI', 'PA', 'PE', 'PY', 'PR', 'SR', 'UY', 'VE'] # 'BR', 
  return getCountry(ip) in ES

def getCountry(ip):
  import geoip
  return geoip.country(ip)
  
def getHost(ip):
  if Settings._.HOST is None:
    try:
      Settings._.HOST = socket.gethostbyaddr(ip)[0]
      return Settings._.HOST
    except socket.herror:
      return None
  else:
    return Settings._.HOST
    
def hostIsBanned(ip):
  host = getHost(ip)
  if host:
    banned_hosts = []
    for banned_host in banned_hosts:
      if host.endswith(banned_host):
        return True
    return False
  else:
    return False
  
def updateBoardSettings():
  """
  Pickle the board's settings and store it in the configuration field
  """
  board = Settings._.BOARD
  #UpdateDb("UPDATE `boards` SET `configuration` = '%s' WHERE `id` = %s LIMIT 1" % (_mysql.escape_string(configuration), board["id"]))
  
  del board["filetypes"]
  del board["filetypes_ext"]
  post_values = ["`" + _mysql.escape_string(str(key)) + "` = '" + _mysql.escape_string(str(value)) + "'" for key, value in board.iteritems()]
  
  UpdateDb("UPDATE `boards` SET %s WHERE `id` = '%s' LIMIT 1" % (", ".join(post_values), board["id"]))

def timestamp(t=None):
  """
  Create MySQL-safe timestamp from the datetime t if provided, otherwise create
  the timestamp from datetime.now()
  """
  if not t:
    t = datetime.datetime.now()
  return int(time.mktime(t.timetuple()))

def formatDate(t=None, home=False):
  """
  Format a datetime to a readable date
  """
  if not t:
    t = datetime.datetime.now(CLT())
  # Timezone fix
  #t += datetime.timedelta(hours=1)
  
  days = {'en': ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'],
          'es': ['lun', 'mar', 'mie', 'jue', 'vie', 'sab', 'dom'],
          'jp': ['月', '火', '水', '木', '金', '土', '日']}
          
  daylist = days[Settings.LANG]
  format = "%d/%m/%y(%a)%H:%M:%S"

  if not home:
    try:
      board = Settings._.BOARD
      if board["dir"] == 'world':
        daylist = days['en']
      elif board["dir"] == '2d':
        daylist = days['jp']
    except:
      pass
  
  t = t.strftime(format)
  
  t = re.compile(r"mon", re.DOTALL | re.IGNORECASE).sub(daylist[0], t)
  t = re.compile(r"tue", re.DOTALL | re.IGNORECASE).sub(daylist[1], t)
  t = re.compile(r"wed", re.DOTALL | re.IGNORECASE).sub(daylist[2], t)
  t = re.compile(r"thu", re.DOTALL | re.IGNORECASE).sub(daylist[3], t)
  t = re.compile(r"fri", re.DOTALL | re.IGNORECASE).sub(daylist[4], t)
  t = re.compile(r"sat", re.DOTALL | re.IGNORECASE).sub(daylist[5], t)
  t = re.compile(r"sun", re.DOTALL | re.IGNORECASE).sub(daylist[6], t)
  return t

def formatTimestamp(t, home=False):
  """
  Format a timestamp to a readable date
  """
  return formatDate(datetime.datetime.fromtimestamp(int(t), CLT()), home)

def timeTaken(time_start, time_finish):
  return str(round(time_finish - time_start, 3))

def parseIsoPeriod(t_str):
  m = re.match('P(?:(\d+)D)?T(?:(\d+)H)?(?:(\d+)M)?(\d+)S', t_str)
  if m:
    grps = [x for x in m.groups() if x]
    if len(grps) == 1:
      grps.insert(0, '0')
    grps[-1] = grps[-1].zfill(2)
    return ':'.join(grps)
  else:
    return '???'
  
def getFormData(self):
  """
  Process input sent to WSGI through a POST method and output it in an easy to
  retrieve format: dictionary of dictionaries in the format of {key: value}
  """
  wsgi_input = self.environ["wsgi.input"]
  post_form = self.environ.get("wsgi.post_form")
  if (post_form is not None
    and post_form[0] is wsgi_input):
    return post_form[2]
  # This must be done to avoid a bug in cgi.FieldStorage
  self.environ.setdefault("QUERY_STRING", "")
  fs = cgi.FieldStorage(fp=wsgi_input,
              environ=self.environ,
              keep_blank_values=1)
  new_input = InputProcessed()
  post_form = (new_input, wsgi_input, fs)
  self.environ["wsgi.post_form"] = post_form
  self.environ["wsgi.input"] = new_input

  formdata = {}
  for key in dict(fs):
    try:
      formdata.update({key: fs[key].value})
      #if key == "file":
      #  formdata.update({"file_original": secure_filename(fs[key].filename)})
    except AttributeError:
      formdata.update({key: fs[key]})
  
  return formdata

class InputProcessed(object):
  def read(self):
    raise EOFError("El stream de wsgi.input ya se ha consumido.")
  readline = readlines = __iter__ = read

class UserError(Exception):
  pass

def secure_filename(path):
  split = re.compile(r'[\0%s]' % re.escape(''.join([os.path.sep, os.path.altsep or ''])))
  return cgi.escape(split.sub('', path))
  
def getMD5(data):
  m = hashlib.md5()
  m.update(data)
  
  return m.hexdigest()

def nullstr(len): return "\0" * len

def hide_data(data, length, key, secret):
  """
  Encrypts data, useful for tripcodes and IDs
  """
  crypt = rc4(nullstr(length), rc4(nullstr(32), key + secret) + data).encode('base64')
  return crypt.rstrip('\n')

def rc4(data, key):
  """
  rc4 implementation
  """
  x = 0
  box = range(256)
  for i in range(256):
    x = (x + box[i] + ord(key[i % len(key)])) % 256
    box[i], box[x] = box[x], box[i]
  x = 0
  y = 0
  out = []
  for char in data:
    x = (x + 1) % 256
    y = (y + box[x]) % 256
    box[x], box[y] = box[y], box[x]
    out.append(chr(ord(char) ^ box[(box[x] + box[y]) % 256]))
  
  return ''.join(out)

def getRandomLine(filename):
  import random
  f = open(filename, 'r')
  lines = f.readlines()
  num = random.randint(0, len(lines) - 1)
  return lines[num]
  
def getRandomIco():
  from glob import glob
  from random import choice
  icons = glob("../static/ico/*")
  if icons:
    return choice(icons).lstrip('..')
  else:
    return ''

def N_(message): return message

def getCookie(self, value=""):
  return urllib.unquote_plus(self._cookies[value].value)

def reCookie(self, key, value=""):
  board = Settings._.BOARD
  setCookie(self, key, value)

def setCookie(self, key, value="", max_age=None, expires=None, path="/", domain=None, secure=None):
  """
  Copied from Colubrid
  """
  if self._cookies is None:
    self._cookies = SimpleCookie()
  self._cookies[key] = urllib.quote_plus(value)
  if not max_age is None:
    self._cookies[key]["max-age"] = max_age
  if not expires is None:
    if isinstance(expires, basestring):
      self._cookies[key]["expires"] = expires
      expires = None
    elif isinstance(expires, datetime):
      expires = expires.utctimetuple()
    elif not isinstance(expires, (int, long)):
      expires = datetime.datetime.gmtime(expires)
    else:
      raise ValueError("Se requiere de un entero o un datetime")
    if not expires is None:
      now = datetime.datetime.gmtime()
      month = _([N_("Jan"), N_("Feb"), N_("Mar"), N_("Apr"), N_("May"), N_("Jun"), N_("Jul"),
               N_("Aug"), N_("Sep"), N_("Oct"), N_("Nov"), N_("Dec")][now.tm_mon - 1])
      day = _([N_("Monday"), N_("Tuesday"), N_("Wednesday"), N_("Thursday"),
             N_("Friday"), N_("Saturday"), N_("Sunday")][expires.tm_wday])
      date = "%02d-%s-%s" % (
          now.tm_mday, month, str(now.tm_year)[-2:]
      )
      d = "%s, %s %02d:%02d:%02d GMT" % (day, date, now.tm_hour,
                                         now.tm_min, now.tm_sec)
      self._cookies[key]["expires"] = d
  if not path is None:
    self._cookies[key]["path"] = path
  if not domain is None:
    if domain != "THIS":
      self._cookies[key]["domain"] = domain
  else:
    self._cookies[key]["domain"] = Settings.DOMAIN
  if not secure is None:
    self._cookies[key]["secure"] = secure

def deleteCookie(self, key):
  """
  Copied from Colubrid
  """
  if self._cookies is None:
    self._cookies = SimpleCookie()
  if not key in self._cookies:
    self._cookies[key] = ""
  self._cookies[key]["max-age"] = 0

def elapsed_time(seconds, suffixes=['y','w','d','h','m','s'], add_s=False, separator=' '):
  """
  Takes an amount of seconds and turns it into a human-readable amount of time.
  """
  # the formatted time string to be returned
  time = []
  
  # the pieces of time to iterate over (days, hours, minutes, etc)
  # - the first piece in each tuple is the suffix (d, h, w)
  # - the second piece is the length in seconds (a day is 60s * 60m * 24h)
  parts = [(suffixes[0], 60 * 60 * 24 * 7 * 52),
      (suffixes[1], 60 * 60 * 24 * 7),
      (suffixes[2], 60 * 60 * 24),
      (suffixes[3], 60 * 60),
      (suffixes[4], 60),
      (suffixes[5], 1)]
  
  # for each time piece, grab the value and remaining seconds, and add it to
  # the time string
  for suffix, length in parts:
    value = seconds / length
    if value > 0:
      seconds = seconds % length
      time.append('%s%s' % (str(value),
                 (suffix, (suffix, suffix + 's')[value > 1])[add_s]))
    if seconds < 1:
      break
  
  return separator.join(time)

def inet_aton(ip_string):
  import socket, struct
  return struct.unpack('!L',socket.inet_aton(ip_string))[0]

def inet_ntoa(packed_ip):
  import socket, struct
  return socket.inet_ntoa(struct.pack('!L',packed_ip))

def is_bad_proxy(pip):
  import urllib2
  import socket
  socket.setdefaulttimeout(3)
  
  try:
    proxy_handler = urllib2.ProxyHandler({'http': pip})
    opener = urllib2.build_opener(proxy_handler)
    opener.addheaders = [('User-agent', 'Mozilla/5.0')]
    urllib2.install_opener(opener)
    req=urllib2.Request('http://bienvenidoainternet.org')
    sock=urllib2.urlopen(req)
  except urllib2.HTTPError, e:
    return e.code
  except Exception, detail:
    return True
  return False

def send_mail(subject, srcmsg):
  import smtplib
  from email.mime.text import MIMEText
  
  msg = MIMEText(srcmsg)
  me = 'weabot@bienvenidoainternet.org'
  you = 'burocracia@bienvenidoainternet.org'
  
  msg['Subject'] = 'The contents of %s' % textfile
  msg['From'] = me
  msg['To'] = you

  s = smtplib.SMTP('localhost')
  s.sendmail(me, [you], msg.as_string())
  s.quit()

class weabotLogger:
  def __init__(self):
    self.times = []

  def log(self, message):
    self.times.append([time.time(), message])

  def allTimes(self):
    output = "Time         Logged action\n--------------------------\n"
    start = self.times[0][0]
    for time in self.times:
      difference = str(time[0] - start)
      difference_split = difference.split(".")
      if len(difference_split[0]) < 2:
        difference_split[0] = "0" + difference_split[0]
        
      if len(difference_split[1]) < 7:
        difference_split[1] = ("0" * (7 - len(difference_split[1]))) + difference_split[1]
      elif len(difference_split[1]) > 7:
        difference_split[1] = difference_split[1][:7]
        
      output += ".".join(difference_split) + "   " + time[1] + "\n"

    return output

logger = weabotLogger()
def logTime(message):
  global logger
  logger.log(message)

def logTimes():
  global logger
  return logger.allTimes()

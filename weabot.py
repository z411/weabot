#!/usr/bin/python
# coding=utf-8

# Remove the first line to use the env command to locate python

import os
import time
import datetime
import random
import cgi
import _mysql
from Cookie import SimpleCookie

import tenjin
import manage
import oekaki
import gettext
from database import *
from settings import Settings
from framework import *
from formatting import *
from post import *
from img import *

__version__ = "0.8.4"

# Set to True to disable weabot's exception routing and enable profiling
_DEBUG = False

# Set to True to save performance data to weabot.txt
_LOG = False

class weabot(object):
  def __init__(self, environ, start_response):
    global _DEBUG
    self.environ = environ
    if self.environ["PATH_INFO"].startswith("/weabot.py/"):
      self.environ["PATH_INFO"] = self.environ["PATH_INFO"][11:]
      
    self.start = start_response
    self.formdata = getFormData(self)

    self.output = ""
    
    self.handleRequest()
    
    # Localization Code
    lang = gettext.translation('weabot', './locale', languages=[Settings.LANG])
    lang.install()
    
    logTime("**Start**")
    # open database
    #OpenDb()
    if _DEBUG:
      import cProfile
      
      #prof = cProfile.Profile("weabot_pro.prof")
      prof = cProfile.Profile()
      prof.runcall(self.run)
      prof.dump_stats('stats.prof')
      #prof.close()
    else:
      try:
        self.run()
      except UserError, message:
        self.error(message)
      except Exception, inst:
        import sys, traceback
        exc_type, exc_value, exc_traceback = sys.exc_info()
        detail = ((os.path.basename(o[0]),o[1],o[2],o[3]) for o in traceback.extract_tb(exc_traceback))
        self.exception(type(inst), inst, detail)
    
    # close database and finish
    CloseDb()
    logTime("**End**")
    
    if _LOG:
      logfile = open(Settings.ROOT_DIR + "weabot.txt", "w")
      logfile.write(logTimes())
      logfile.close()
      
  def __iter__(self):
    self.handleResponse()
    self.start("200 OK", self.headers)
    yield self.output

  def error(self, message):
    board = Settings._.BOARD
    if board:
      if board['board_type'] == '1':
        info = {}
        info['host'] = self.environ["REMOTE_ADDR"]
        info['name'] = self.formdata.get('fielda', '')
        info['email'] = self.formdata.get('fieldb', '')
        info['message'] = self.formdata.get('message', '')
      
        self.output += renderTemplate("txt_error.html", {"info": info, "error": message})
      else:
        mobile = self.formdata.get('mobile', '')
        if mobile:
          self.output += renderTemplate("mobile/error.html", {"error": message})
        else:
          self.output += renderTemplate("error.html", {"error": message, "boards_url": Settings.BOARDS_URL, "board": board["dir"]})
    else:
      self.output += renderTemplate("exception.html", {"exception": None, "error": message})
  
  def exception(self, type, message, detail):
    self.output += renderTemplate("exception.html", {"exception": type, "error": message, "detail": detail})
  
  def handleRequest(self):
    self.headers = [("Content-Type", "text/html")]
    self.handleCookies()
    
  def handleResponse(self):
    if self._cookies is not None:
      for cookie in self._cookies.values():
        self.headers.append(("Set-Cookie", cookie.output(header="")))

  def handleCookies(self):
    self._cookies = SimpleCookie()
    self._cookies.load(self.environ.get("HTTP_COOKIE", ""))

  def run(self):
    path_split = self.environ["PATH_INFO"].split("/")
    caught = False
    
    if Settings.FULL_MAINTENANCE:
      raise UserError, _("%s is currently under maintenance. We'll be back.") % Settings.SITE_TITLE
    
    if len(path_split) > 1:
      if path_split[1] == "post":
        # Making a post
        caught = True
        
        if 'password' not in self.formdata:
          raise UserError, "El request está incompleto."
            
        # let's get all the POST data we need
        ip = self.environ["REMOTE_ADDR"]
        boarddir = self.formdata.get('board')
        parent = self.formdata.get('parent')
        trap1 = self.formdata.get('name', '')
        trap2 = self.formdata.get('email', '')
        name = self.formdata.get('fielda', '')
        email = self.formdata.get('fieldb', '')
        subject = self.formdata.get('subject', '')
        message = self.formdata.get('message', '')
        file = self.formdata.get('file')
        file_original = self.formdata.get('file_original')
        spoil = self.formdata.get('spoil')
        oek_file = self.formdata.get('oek_file')
        password = self.formdata.get('password', '')
        noimage = self.formdata.get('noimage')
        mobile = ("mobile" in self.formdata.keys())
        
        # call post function
        (post_url, ttaken) = self.make_post(ip, boarddir, parent, trap1, trap2, name, email, subject, message, file, file_original, spoil, oek_file, password, noimage, mobile)
        
        # make redirect
        self.output += make_redirect(post_url, ttaken)
      elif path_split[1] == "delete":
        # Deleting a post
        caught = True

        boarddir = self.formdata.get('board')
        postid = self.formdata.get('delete')
        imageonly = self.formdata.get('imageonly')
        password = self.formdata.get('password')
        mobile = self.formdata.get('mobile')
        
        # call delete function
        self.delete_post(boarddir, postid, imageonly, password, mobile)
      elif path_split[1] == "anarkia":
        import anarkia
        caught = True
        OpenDb()
        anarkia.anarkia(self, path_split)
      elif path_split[1] == "manage":
        caught = True
        OpenDb()
        manage.manage(self, path_split)
      elif path_split[1] == "api":
        import api
        caught = True
        self.headers = [("Content-Type", "application/json")]
        OpenDb()
        api.api(self, path_split)
      elif path_split[1] == "threadlist":
        OpenDb()
        board = setBoard(path_split[2])
        caught = True
        if board['board_type'] != '1':
          raise UserError, "No disponible para esta sección."
        self.output = threadList(0, self.formdata.get('sort', ''))
      elif path_split[1] == "mobile":
        OpenDb()
        board = setBoard(path_split[2])
        caught = True
        self.output = threadList(1)
      elif path_split[1] == "mobilelist":
        OpenDb()
        board = setBoard(path_split[2])
        caught = True
        self.output = threadList(2, self.formdata.get('sort', ''))
      elif path_split[1] == "mobilecat":
        OpenDb()
        board = setBoard(path_split[2])
        caught = True
        self.output = threadList(3, self.formdata.get('sort', ''))
      elif path_split[1] == "mobilenew":
        OpenDb()
        board = setBoard(path_split[2])
        caught = True
        self.output = renderTemplate('txt_newthread.html', {}, True)
      elif path_split[1] == "mobilehome":
        OpenDb()
        latest_age = getLastAge(Settings.HOME_LASTPOSTS)
        for threads in latest_age:
          content = threads['url']
          content = content.replace('/read/', '/')
          content = content.replace('/res/', '/')
          content = content.replace('.html', '')
          threads['url'] = content
        caught = True
        self.output = renderTemplate('latest.html', {'latest_age': latest_age}, True)
      elif path_split[1] == "mobilenewest":
        OpenDb()
        newthreads = getNewThreads(Settings.HOME_LASTPOSTS)
        for threads in newthreads:
          content = threads['url']
          content = content.replace('/read/', '/')
          content = content.replace('/res/', '/')
          content = content.replace('.html', '')
          threads['url'] = content
        caught = True
        self.output = renderTemplate('newest.html', {'newthreads': newthreads}, True)
      elif path_split[1] == "mobileread":
        OpenDb()
        board = setBoard(path_split[2])
        caught = True
        if len(path_split) > 4 and path_split[4] and board['board_type'] == '1':
          #try:
          self.output = dynamicRead(int(path_split[3]), path_split[4], True)
          #except:
          #  self.output = threadPage(path_split[3], True)
        elif board['board_type'] == '1':
          self.output = threadPage(0, True, path_split[3])
        else:
          self.output = threadPage(path_split[3], True)
      elif path_split[1] == "catalog":
        OpenDb()
        board = setBoard(path_split[2])
        caught = True
        sort = self.formdata.get('sort', '')
        self.output = catalog(sort)
      elif path_split[1] == "oekaki":
        caught = True
        OpenDb()
        oekaki.oekaki(self, path_split)
      elif path_split[1] == "play":
        # Module player
        caught = True
        boarddir = path_split[2]
        modfile = path_split[3]
        self.output = renderTemplate('mod.html', {'board': boarddir, 'modfile': modfile})
      elif path_split[1] == "report":
        # Report post, check if they are enabled
        # Can't report if banned
        caught = True
        ip = self.environ["REMOTE_ADDR"]
        boarddir = path_split[2]
        postid = int(path_split[3])
        reason = self.formdata.get('reason')
        try:
          txt = True
          postshow = int(path_split[4])
        except:
          txt = False
          postshow = postid

        self.report(ip, boarddir, postid, reason, txt, postshow)
      elif path_split[1] == "stats":
        caught = True
        self.stats()
      elif path_split[1] == "random":
        caught = True
        OpenDb()
        board = FetchOne("SELECT `id`, `dir`, `board_type` FROM `boards` WHERE `secret` = 0 AND `id` <> 1 ORDER BY RAND() LIMIT 1")
        thread = FetchOne("SELECT `id`, `timestamp` FROM `posts` WHERE `parentid` = 0 AND `boardid` = %s ORDER BY RAND() LIMIT 1" % board['id'])
        if board['board_type'] == '1':
          url = Settings.HOME_URL + board['dir'] + '/read/' + thread['timestamp'] + '/'
        else:
          url = Settings.HOME_URL + board['dir'] + '/res/' + thread['id'] + '.html'
        self.output += '<html xmlns="http://www.w3.org/1999/xhtml"><meta http-equiv="refresh" content="0;url=%s" /><body><p>...</p></body></html>' % url
      elif path_split[1] == "nostalgia":
        caught = True
        OpenDb()
        thread = FetchOne("SELECT `timestamp` FROM `archive` WHERE `boardid` = 9 AND `timestamp` < 1462937230 ORDER BY RAND() LIMIT 1")
        url = Settings.HOME_URL + '/zonavip/read/' + thread['timestamp'] + '/'
        self.output += '<html xmlns="http://www.w3.org/1999/xhtml"><meta http-equiv="refresh" content="0;url=%s" /><body><p>...</p></body></html>' % url
      elif path_split[1] == "banned":
        OpenDb()
        packed_ip = inet_aton(self.environ["REMOTE_ADDR"])
        bans = FetchAll("SELECT * FROM `bans` WHERE (`netmask` IS NULL AND `ip` = '"+str(packed_ip)+"') OR (`netmask` IS NOT NULL AND '"+str(packed_ip)+"' & `netmask` = `ip`)")
        if bans:
          for ban in bans:
            if ban["boards"] != "":
              boards = pickle.loads(ban["boards"])
            if ban["boards"] == "" or path_split[2] in boards:
              caught = True
              if ban["boards"]:
                boards_str = '/' + '/, /'.join(boards) + '/'
              else:
                boards_str = _("all boards")
              if ban["until"] != "0":
                expire = formatTimestamp(ban["until"])
              else:
                expire = ""
              
              template_values = {
                'cgi_url': Settings.CGI_URL,
                'return_board': path_split[2],
                'boards_str': boards_str,
                'reason': ban['reason'],
                'added': formatTimestamp(ban["added"]),
                'expire': expire,
                'ip': self.environ["REMOTE_ADDR"],
              }
              self.output = renderTemplate('banned.html', template_values)
        else:
          if len(path_split) > 2:
            caught = True
            self.output += '<html xmlns="http://www.w3.org/1999/xhtml"><body><meta http-equiv="refresh" content="0;url=%s" /><p>%s</p></body></html>' % (Settings.HOME_URL + path_split[2], _("Your ban has expired. Redirecting..."))
      elif path_split[1] == "read":
        # Textboard read:
        if len(path_split) > 4:
          caught = True
          # 2: board
          # 3: thread
          # 4: post(s)
          OpenDb()
          board = setBoard(path_split[2])
          self.output = dynamicRead(int(path_split[3]), path_split[4])
      elif path_split[1] == "preview":
        caught = True
        OpenDb()
        try:
          board = setBoard(self.formdata["board"])
          message = format_post(self.formdata["message"], self.environ["REMOTE_ADDR"], self.formdata["parentid"])
          self.output = message
        except Exception, messagez:
          self.output = "Error: " + str(messagez) + " : " + str(self.formdata)
    if not caught:
      # Redirect the user back to the front page
      self.output += '<html xmlns="http://www.w3.org/1999/xhtml"><body><meta http-equiv="refresh" content="0;url=%s" /><p>--&gt; --&gt; --&gt;</p></body></html>' % Settings.HOME_URL
  
  def make_post(self, ip, boarddir, parent, trap1, trap2, name, email, subject, message, file, file_original, spoil, oek_file, password, noimage, mobile):
    _STARTTIME = time.clock() # Comment if not debug

    # open database
    OpenDb()
    
    # set the board
    board = setBoard(boarddir)

    if board["dir"] != ["anarkia"]:
      if addressIsProxy(ip):
        raise UserError, "Proxy prohibido en esta sección."

    # check length of fields
    if len(name) > 50:
      raise UserError, "El campo de nombre es muy largo."
    if len(email) > 50:
      raise UserError, "El campo de e-mail es muy largo."
    if len(subject) > 100:
      raise UserError, "El campo de asunto es muy largo."
    if len(message) > 8000:
      raise UserError, "El campo de mensaje es muy largo."
    if message.count('\n') > 50:
      raise UserError, "El mensaje tiene muchos saltos de línea."
    
    # anti-spam trap
    if trap1 or trap2:
      with open('botlog', 'a') as fw:
        fw.write(trap1 + ';;;' + trap2 + '\n')
        raise UserError, "Te quedan tres días de vida."
    
    # Create a single datetime now so everything syncs up
    t = time.time()
    
    # Delete expired bans
    deletedBans = UpdateDb("DELETE FROM `bans` WHERE `until` != 0 AND `until` < " + str(timestamp()))
    if deletedBans > 0:
      regenerateAccess()
    
    # Redirect to ban page if user is banned
    if addressIsBanned(ip, board["dir"]):
      #raise UserError, 'Tu host está en la lista negra.'
      raise UserError, '<meta http-equiv="refresh" content="0; url=/cgi/banned/%s">' % board["dir"]
    
    # Disallow posting if the site OR board is in maintenance
    if Settings.MAINTENANCE:
      raise UserError, _("%s is currently under maintenance. We'll be back.") % Settings.SITE_TITLE
    if board["locked"] == '1':
      raise UserError, _("This board is closed. You can't post in it.")
    
    # create post object
    post = Post(board["id"])
    post["ip"] = inet_aton(ip)
    post["timestamp"] = post["bumped"] = int(t)
    post["timestamp_formatted"] = formatTimestamp(t)
    
    # load parent info if we are replying
    parent_post = None
    parent_timestamp = post["timestamp"]
    if parent:
      parent_post = get_parent_post(parent, board["id"])
      parent_timestamp = parent_post['timestamp']
      post["parentid"] = parent_post['id']
      post["bumped"] = parent_post['bumped']
      if parent_post['locked'] == '1':
        raise UserError, _("The thread is closed. You can't post in it.")
    
    # check if the user is flooding
    flood_check(t, post, board["id"])
    
    # use fields only if enabled
    if board["disable_name"] != '1':
      post["name"] = cleanString(name)
    post["email"] = cleanString(email, quote=True)
    if board["disable_subject"] != '1':
      post["subject"] = cleanString(subject)
    
    # process tripcodes
    post["name"], post["tripcode"] = tripcode(post["name"])

    # Remove carriage return, they're useless
    message = message.replace("\r", "")
    
    # check EXTEND before
    extend = extend_str = None
    
    if not post["parentid"] and board["dir"] not in ['bai', 'world']:
      # creating thread
      __extend = re.compile(r"^!extend(:\w+)(:\w+)?\n")
      res = __extend.match(message)
      if res:
        extend = res.groups()
        # truncate extend
        extend_str = res.group(0)
        message = message[res.end(0):]
    
    # use and format message
    if message.strip():
      post["message"] = format_post(message, ip, post["parentid"], parent_timestamp)
      
    # add EXTEND if necessary
    if extend_str:
      extend_str = extend_str.replace('!extend', 'EXTEND')
      post["message"] += '<hr />' + extend_str + ' configurado.'

    # remove sage from wrong fields
    if post["name"] == 'sage':
      post["name"] = random.choice(board["anonymous"].split('|'))
    if post["subject"] == 'sage':
      post["subject"] = board["subject"]

    if not post["parentid"] and post["email"] == 'sage':
      post["email"] = ""

    # disallow illegal characters
    if post["name"]:
      post["name"] = post["name"].replace('★', '☆')
      post["name"] = post["name"].replace('◆', '◇')
    
    # process capcodes
    cap_id = hide_end = None
    if post["name"] in Settings.CAPCODES:
      capcode = Settings.CAPCODES[post["name"]]
      if post["tripcode"] == (Settings.TRIP_CHAR + capcode[0]):
        if board['board_type'] == '1':
          post["name"], post["tripcode"] = capcode[1], ''
        else:
          post["name"] = post["tripcode"] = ''
          post["message"] = ('[<span style="color:red">%s</span>]<br />' % capcode[2]) + post["message"]
        
        cap_id, hide_end = capcode[3], capcode[4]
    
    # use password
    post["password"] = password
    
    # EXTEND feature
    if post["parentid"] and board["dir"] not in ['bai', 'world']:
      # replying
      __extend = re.compile(r"<hr />EXTEND(:\w+)(:\w+)?\b")
      res = __extend.search(parent_post["message"])
      if res:
        extend = res.groups()
        
      # compatibility : old id function
      if 'id' in parent_post["email"]:
        board["useid"] = '3'

    if 'id' in post["email"]:
      board["useid"] = '3'
      
    if extend:
      try:
        # 1: ID
        if extend[0] == ':no':
          board["useid"] = '0'
        elif extend[0] == ':yes':
          board["useid"] = '1'
        elif extend[0] == ':force':
          board["useid"] = '2'
        elif extend[0] == ':extra':
          board["useid"] = '3'
          
        # 2: Slip
        if extend[1] == ':no':
          board["slip"] = '0'
        elif extend[1] == ':yes':
          board["slip"] = '1'
        elif extend[1] == ':domain':
          board["slip"] = '2'
        elif extend[1] == ':verbose':
          board["slip"] = '3'
        elif extend[1] == ':country':
          board["countrycode"] = '1'
        elif extend[1] == ':all':
          board["slip"] = '3'
          board["countrycode"] = '1'
      except IndexError:
        pass
    
    # if we are replying, use first post's time
    if post["parentid"]:
      tim = parent_post["timestamp"]
    else:
      tim = post["timestamp"]

    # make ID hash
    if board["useid"] != '0':
      post["timestamp_formatted"] += ' ID:' + iphash(ip, post, tim, board["useid"], mobile, cap_id, hide_end, (board["countrycode"] in ['1', '2']))
      if time.strftime("%H") in ['00', '24'] and time.strftime("%M") == '00' and time.strftime("%S") == '00':
        post["timestamp_formatted"] += '000000'

    # use for future file checks
    xfile = (file or oek_file)
    
    # textboard inforcements (change it to settings maybe?)
    if board['board_type'] == '1':
      if not post["parentid"] and not post["subject"]:
        raise UserError, _("You must enter a title to create a thread.")
      if not post["message"]:
        raise UserError, _("Please enter a message.")
    else:
      if not post["parentid"] and not xfile and not noimage:
        raise UserError, _("You must upload an image first to create a thread.")
      if not xfile and not post["message"]:
        raise UserError, _("Please enter a message or upload an image to reply.")
    
    # check if this post is allowed
    if post["parentid"]:
      if file and board['allow_image_replies'] == '0':
        raise UserError, _("Image replies not allowed.")
    else:
      if file and board['allow_images'] == '0':
        raise UserError, _("No images allowed.")
    
    # use default values when missing
    if not post["name"] and not post["tripcode"]:
      post["name"] = random.choice(board["anonymous"].split('|'))
    if not post["subject"] and not post["parentid"]:
      post["subject"] = board["subject"]
    if not post["message"]:
      post["message"] = board["message"]
      
    # process files
    if oek_file:
      try:
        fname = "%s/oek_temp/%s.png" % (Settings.HOME_DIR, oek_file)
        with open(fname) as f:
          file = f.read()
        os.remove(fname)
      except:
        raise UserError, "Imposible leer la imagen oekaki."
    
    if file and not noimage:
      post = processImage(post, file, t, file_original, (spoil and board['allow_spoilers'] == '1'))
    
    # slip
    if board["slip"] != '0':
      slips = []
      
      # name
      if board["slip"] in ['1', '3']:
        if time.strftime("%H") in ['00', '24'] and time.strftime("%M") == '00' and time.strftime("%S") == '00':
          host_nick = '000000'
        else:
          host_nick = 'sarin'
        
          if hide_end:
            host_nick = '★'
          elif addressIsTor(ip):
            host_nick = 'onion'
          else:
            isps = {'cablevision': 'easy',
                    'cantv':       'warrior',
                    'claro':       'america',
                    'cnet':        'nova',
                    'copelnet':    'cisneros',
                    'cps.com':     'silver',
                    'cybercable':  'bricklayer',
                    'entel':       'matte',
                    'eternet':     'stream',
                    'fibertel':    'roughage',
                    'geonet':      'thunder',
                    'gtdinternet': 'casanueva',
                    'ifxnw':       'effect',
                    'infinitum':   'telegraph',
                    'intercable':  'easy',
                    'intercity':   'cordoba',
                    'iplannet':    'conquest',
                    'itcsa.net':   'sarmiento',
                    'megared':     'clear',
                    'movistar':    'bell',
                    'nextel':      'fleet',
                    'speedy':      'oxygen',
                    'telecom':     'license',
                    'telmex':      'slender',
                    'telnor':      'compass',
                    'tie.cl':      'bell',
                    'vtr.net':     'liberty',
                    'utfsm':       'virgin',
                   }
            host = getHost(ip)
            
            if host:
              for k, v in isps.iteritems():
                if k in host:
                  host_nick = v
                  break
        
        slips.append(host_nick)
      
      # hash
      if board["slip"] in ['1', '3']:
        if hide_end:
          slips.append('-'.join(('****', getMD5(os.environ["HTTP_USER_AGENT"])[:4])))
        else:
          slips.append('-'.join((getMD5(ip)[:4], getMD5(os.environ["HTTP_USER_AGENT"])[:4])))
      
      # host
      if board["slip"] == '2':
        if hide_end:
          host = '★'
        else:
          host = getHost(ip)
          if host:
            hosts = host.split('.')
            if len(hosts) > 2:
              if hosts[-2] in ['ne', 'net', 'com', 'co']:
                host = '.'.join((hosts[-3], hosts[-2], hosts[-1]))
              else:
                host = '.'.join((hosts[-2], hosts[-1]))
              host = '*.' + host
          else:
            iprs = ip.split('.')
            host = '%s.%s.*.*' % (iprs[0], iprs[1])
        slips.append(host)

      # IP
      if board["slip"] == '3':
        if hide_end:
          host = '[*.*.*.*]'
        else:
          iprs = ip.split('.')
          host = '[%s.%s.%s.*]' % (iprs[0], iprs[1], iprs[2])
        slips.append(host)
      
      if slips:
        post["tripcode"] += " (%s)" % ' '.join(slips)
    
    # country code
    if board["countrycode"] == '1':
      if hide_end or addressIsTor(ip):
        country = '??'
      else:
        country = getCountry(ip)
      post["name"] += " <em>[%s]</em>" % country
    
    # set expiration date if necessary
    if board["maxage"] != '0' and not post["parentid"]:
      if board["dir"] == '2d':
        date_format = '%m月%d日'
        date_format_y = '%Y年%m月'
      else:
        date_format = '%d/%m'
        date_format_y = '%m/%Y'
      post["expires"] = int(t) + (int(board["maxage"]) * 86400)
      if int(board["maxage"]) >= 365:
        date_format = date_format_y
      post["expires_formatted"] = datetime.datetime.fromtimestamp(post["expires"]).strftime(date_format)
    
    if not post["parentid"]:
      # fill with default values if creating a new thread
      post["length"] = 1
      post["last"] = post["timestamp"]

      if board["dir"] == 'noticias':
        # check if there's at least one link
        if "<a href" not in post["message"]:
          raise UserError, "Al momento de crear un hilo en esta sección necesitas incluír al menos 1 link como fuente en tu mensaje."
        
        # insert icon if needed
        img_src = '<img src="%s" alt="ico" /><br />' % getRandomIco()
        post["message"] = img_src + post["message"]
      
    # insert post, then run timThreads to make sure the board doesn't exceed the page limit
    postid = post.insert()
    
    # delete threads that have crossed last page
    trimThreads()
    
    # fix null references when creating thread
    if board["board_type"] == '1' and not post["parentid"]:
      post["message"] = re.compile(r'<a href="/(\w+)/res/0.html/(.+)"').sub(r'<a href="/\1/res/'+str(postid)+r'.html/\2"', post["message"])
      UpdateDb("UPDATE `posts` SET message = '%s' WHERE boardid = '%s' AND id = '%s'" % (_mysql.escape_string(post["message"]), _mysql.escape_string(board["id"]), _mysql.escape_string(str(postid))))
    
    # do operations if replying to a thread (bump, autoclose, update cache)
    logTime("Updating thread")
    thread_length = None
    if post["parentid"]:
      # get length of the thread
      thread_length = threadNumReplies(post["parentid"])
      
      # check if thread must be closed
      autoclose_thread(post["parentid"], t, thread_length)
      
      # bump if not saged
      if 'sage' not in post["email"].lower() and parent_post['locked'] != '2':
        UpdateDb("UPDATE `posts` SET bumped = %d WHERE (`id` = '%s' OR `parentid` = '%s') AND `boardid` = '%s'" % (post["timestamp"], post["parentid"], post["parentid"], board["id"]))

      # update final attributes (length and last post)
      UpdateDb("UPDATE `posts` SET length = %d, last = %d WHERE `id` = '%s' AND `boardid` = '%s'" % (thread_length, post["timestamp"], post["parentid"], board["id"]))
      
      # update cache
      threadUpdated(post["parentid"])
    else:
      # create cache for new thread
      threadUpdated(postid)

    regenerateHome()
    
    # make page redirect
    ttaken = timeTaken(_STARTTIME, time.clock())
    noko = 'noko' in email.lower() or (board["board_type"] == '1')
    
    # get new post url
    post_url = make_url(postid, post, parent_post or post, noko, mobile)
        
    # call discord hook
    if board['secret'] == '0' and not post["parentid"]:
      hook_url = make_url(postid, post, parent_post or post, True, False)
      discord_hook(post, hook_url)
    
    return (post_url, ttaken)

  def delete_post(self, boarddir, postid, imageonly, password, mobile=False):
    # open database
    OpenDb()
    
    # set the board
    board = setBoard(boarddir)
    
    if board["dir"] == '0':
      raise UserError, "No se pueden eliminar mensajes en esta sección."
      
    # check if we have a post id and check it's numeric
    if not postid:
      raise UserError, "Selecciona uno o más mensajes a eliminar."
    
    # make sure we have a password
    if not password:
      raise UserError, _("Please enter a password.")
      
    to_delete = []
    if isinstance(postid, list):
      to_delete = [n.value for n in postid]
    else:
      to_delete = [postid]
      
    # delete posts
    if board['board_type'] == '1' and len(to_delete) == 1:
      # we should be deleting only one (textboard)
      # check if it's the last post and delete it completely if it is
      deltype = '0'
      post = FetchOne("SELECT `id`, `timestamp`, `parentid` FROM `posts` WHERE `boardid` = %s AND `id` = %s LIMIT 1" % (board["id"], str(to_delete[0])))
      if post['parentid'] != '0':
        op = get_parent_post(post['parentid'], board['id'])
        if op['last'] != post['timestamp']:
          deltype = '1'
      
      deletePost(to_delete[0], password, deltype, imageonly)
      regenerateHome()
    else:
      # delete all checked posts (IB)
      deleted = 0
      errors = 0
      msgs = []
      
      for pid in to_delete:
        try:
          deletePost(pid, password, board['recyclebin'], imageonly)
          deleted += 1
          msgs.append('No.%s: Eliminado' % pid)
        except UserError, message:
          errors += 1
          msgs.append('No.%s: %s' % (pid, message))
    
      # regenerate home
      if deleted:
        regenerateHome()
      
      # show errors, if any
      if errors:
        raise UserError, 'No todos los mensajes pudieron ser eliminados.<br />' + '<br />'.join(msgs)
    
    # redirect
    if imageonly:
      self.output += '<html xmlns="http://www.w3.org/1999/xhtml"><body><meta http-equiv="refresh" content="0;url=%s/" /><p>%s</p></body></html>' % (("/cgi/mobile/" if mobile else Settings.BOARDS_URL) + board["dir"], _("File deleted successfully."))
    else:
      self.output += '<html xmlns="http://www.w3.org/1999/xhtml"><body><meta http-equiv="refresh" content="0;url=%s/" /><p>%s</p></body></html>' % (("/cgi/mobile/" if mobile else Settings.BOARDS_URL) + board["dir"], _("Post deleted successfully."))
  
  def report(self, ip, boarddir, postid, reason, txt, postshow):
    # don't allow if the report system is off
    if not Settings.REPORTS_ENABLE:
      raise UserError, _('Report system is deactivated.')
    
    # if there's not a reason, show the report page
    if reason is None:
      self.output += renderTemplate("report.html", {'finished': False, 'postshow': postshow, 'txt': txt})
      return
    
    # check reason
    if not reason:
      raise UserError, _("Enter a reason.")
    if len(reason) > 100:
      raise UserError, _("Text too long.")
    
    # open database
    OpenDb()
    
    # set the board we're in
    board = setBoard(boarddir)
    
    # check if he's banned
    if addressIsBanned(ip, board["dir"]):
      raise UserError, _("You're banned.")    
    
    # check if post exists
    post = FetchOne("SELECT `id`, `parentid`, `ip` FROM `posts` WHERE `id` = '%s' AND `boardid` = '%s'" % (_mysql.escape_string(str(postid)), _mysql.escape_string(board['id'])))
    if not post:
      raise UserError, _("Post doesn't exist.")
      
    # generate link
    if board["board_type"] == '1':
      parent_post = get_parent_post(post["parentid"], board["id"])
      link = "/%s/read/%s/%s" % (board["dir"], parent_post["timestamp"], postshow)
    else:
      link = "/%s/res/%s.html#%s" % (board["dir"], post["parentid"], post["id"])
    
    # insert report
    t = time.time()
    message = cgi.escape(self.formdata["reason"]).strip()[0:8000]
    message = message.replace("\n", "<br />")
    
    UpdateDb("INSERT INTO `reports` (board, postid, parentid, link, ip, reason, reporterip, timestamp, timestamp_formatted) VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')" % (board["dir"], post['id'], post['parentid'], link, post['ip'], _mysql.escape_string(message), _mysql.escape_string(self.environ["REMOTE_ADDR"]), str(t), formatTimestamp(t)))
    self.output = renderTemplate("report.html", {'finished': True})
  
  def stats(self):
    import json, math, platform
    with open('stats.json', 'r') as f:
      out = json.load(f)
    
    regenerated = False
    if (time.time() - out['t']) > 3600:
      regenerated = True
      
      # open database
      OpenDb()
      
      # 1 week = 604800
      query_day = FetchAll("SELECT DATE_FORMAT(FROM_UNIXTIME(FLOOR((timestamp-10800)/86400)*86400+86400), \"%Y-%m-%d\"), COUNT(1), COUNT(IF(parentid=0, 1, NULL)) "
        "FROM posts "
        "WHERE (timestamp-10800) > (UNIX_TIMESTAMP()-604800) AND IS_DELETED = 0 "
        "GROUP BY FLOOR((timestamp-10800)/86400) "
        "ORDER BY FLOOR((timestamp-10800)/86400)", 0)
      
      query_count = FetchOne("SELECT COUNT(1), COUNT(NULLIF(file, '')), VERSION() FROM posts", 0)
      total = int(query_count[0])
      total_files = int(query_count[1])
      mysql_ver = query_count[2]
      
      archive_count = FetchOne("SELECT SUM(length) FROM archive", 0)
      total_archived = int(archive_count[0])
    
      days = []
      for date, count, threads in query_day:
        days.append( (date, count, threads) )
      
      days.pop(0)

      query_b = FetchAll("SELECT id, dir, name FROM boards WHERE boards.secret = 0", 0)

      boards = []
      totalp = 0
      for id, dir, longname in query_b:
        bposts = FetchOne("SELECT COUNT(1) FROM posts "
          "WHERE '"+str(id)+"' = posts.boardid AND timestamp > ( UNIX_TIMESTAMP(DATE(NOW())) - 2419200 )", 0)
        boards.append( (dir, longname, int(bposts[0])) )
        totalp += int(bposts[0])

      boards = sorted(boards, key=lambda boards: boards[2], reverse=True)
      
      boards_percent = []
      for dir, longname, bposts in boards:
        if bposts > 0:
          boards_percent.append( (dir, longname, '{0:.2f}'.format( float(bposts)*100/totalp ), int(bposts) ) )
        else:
          boards_percent.append( (dir, longname, '0.00', '0' ) )

      #posts = FetchAll("SELECT `parentid`, `boardid` FROM `posts` INNER JOIN `boards` ON posts.boardid = boards.id WHERE posts.parentid<>0 AND posts.timestamp>(UNIX_TIMESTAMP()-86400) AND boards.secret=0 ORDER BY `parentid`")
      #threads = {}
      #for post in posts:
      #  if post["parentid"] in threads:
      #    threads[post["parentid"]] += 1
      #  else:
      #    threads[post["parentid"]] = 1

      out = {
         "uname": platform.uname(),
         "python_ver": platform.python_version(),
         "python_impl": platform.python_implementation(),
         "python_build": platform.python_build()[1],
         "python_compiler": platform.python_compiler(),
         "mysql_ver": mysql_ver,
         "tenjin_ver": tenjin.__version__,
         "weabot_ver": __version__,
         "days": days,
         "boards": boards,
         "boards_percent": boards_percent,
         "total": total,
         "total_files": total_files,
         "total_archived": total_archived,
         "t": timestamp(),
         "tz": Settings.TIME_ZONE,
        }
      with open('stats.json', 'w') as f:
        json.dump(out, f)
      
    out['timestamp'] = re.sub(r"\(...\)", " ", formatTimestamp(out['t']))
    out['regenerated'] = regenerated
    self.output = renderTemplate("stats.html", out)
    #self.headers = [("Content-Type", "application/json")]

if __name__ == "__main__":
  from fcgi import WSGIServer

  # Psyco is not required, however it will be used if available
  try:
    import psyco
    logTime("Psyco se ha instalado")
    psyco.bind(tenjin.helpers.to_str)
    psyco.bind(weabot.run, 2)
    psyco.bind(getFormData)
    psyco.bind(setCookie)
    psyco.bind(threadUpdated)
    psyco.bind(processImage)
  except:
    pass
  
  WSGIServer(weabot).run()
  
  """lang = gettext.translation('weabot', './locale', languages=[Settings.LANG])
  lang.install()
  main = weabot()
  #make_post(ip, boarddir, parent, trap1, trap2, name, email, subject, message, file, file_original, spoil, noko, oek_file, oek_file_x, oek_file_y, timetaken, password, noimage, markup, savemarkup, mobile):
  OpenDb()
  main.make_post('127.0.0.1', 'img', '27', '', '', '', '', '', 'Profiling.', None, '', None, None, None, None, None, None, 'yo', None, None, None, None)
  CloseDb()"""
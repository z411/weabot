#!/usr/bin/env python
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

__version__ = "0.7.2"

# Set to True to disable weabot's exception routing and enable profiling
_DEBUG = False

# Set to True to save performance data to weabot.txt
_LOG = False

class weabot(object):
  def __init__(self, environ, start_response):
    global _DEBUG
    self.environ = environ
    if self.environ["PATH_INFO"].startswith("/weabot.py/"):
      self.environ["PATH_INFO"] = self.environ["PATH_INFO"][8:]
      
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
      import hotshot
      prof = hotshot.Profile("weabot.prof")
      prof.runcall(self.run)
      prof.close()
    else:
      try:
        self.run()
      except UserError, message:
        self.error(message)
      except Exception, inst:
        import sys, traceback
        exc_type, exc_value, exc_traceback = sys.exc_info()
        detail = traceback.extract_tb(exc_traceback)
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
    self.output += renderTemplate("error.html", {"exception": None, "error": message, "navbar": False})
  
  def exception(self, type, message, detail):
    self.output += renderTemplate("error.html", {"exception": type, "error": message, "detail": detail, "navbar": False})
  
  def handleRequest(self):
    # Send as XHTML only if the browser supports it
    #if self.environ["HTTP_ACCEPT"].find("application/xhtml+xml") != -1:
    #  self.headers = [("Content-Type", "application/xhtml+xml")]
    #else:
    #  self.headers = [("Content-Type", "text/html")]
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
        oek_file_x = self.formdata.get('oek_file_x')
        oek_file_y = self.formdata.get('oek_file_y')
        timetaken = self.formdata.get('timetaken')
        password = self.formdata.get('password', '')
        noimage = self.formdata.get('noimage')
        mobile = ("mobile" in self.formdata.keys())
        
        # call post function
        self.make_post(ip, boarddir, parent, trap1, trap2, name, email, subject, message, file, file_original, spoil, oek_file, oek_file_x, oek_file_y, timetaken, password, noimage, mobile)
      elif path_split[1] == "delete":
        # Deleting a post
        caught = True

        boarddir = self.formdata.get('board')
        postid = self.formdata.get('delete')
        imageonly = self.formdata.get('imageonly')
        password = self.formdata.get('password')
        
        # call delete function
        self.delete_post(boarddir, postid, imageonly, password)
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
        if board['dir'] == "clusterfuck":
          raise UserError, "Esta función no está disponible para este board."
        caught = True
        self.output = threadList(0)
      elif path_split[1] == "mobile":
        OpenDb()
        board = setBoard(path_split[2])
        if board['dir'] == "clusterfuck":
          raise UserError, "Esta función no está disponible para este board."
        caught = True
        self.output = threadList(1)
      elif path_split[1] == "mobilelist":
        OpenDb()
        board = setBoard(path_split[2])
        if board['dir'] == "clusterfuck":
          raise UserError, "Esta función no está disponible para este board."
        caught = True
        self.output = threadList(2)
      elif path_split[1] == "mobilenew":
        OpenDb()
        board = setBoard(path_split[2])
        if board['dir'] == "clusterfuck":
          raise UserError, "Esta función no está disponible para este board."
        caught = True
        self.output = renderTemplate('txt_newthread.html', {}, True)
      elif path_split[1] == "mobilehome":
        caught = True
        
        content = ""
        with open('templates/home_posts.html', 'r') as f:
            content = f.read()
            content = content.replace('href="', 'href="/cgi/mobileread')
            content = content.replace('/read/', '/')
            content = content.replace('/res/', '/')
            content = content.replace('.html', '')
          
        self.output = renderTemplate('latest.html', {'content': content}, True)
      elif path_split[1] == "mobileread":
        OpenDb()
        board = setBoard(path_split[2])
        if board['dir'] == "clusterfuck":
          raise UserError, "Esta función no está disponible para este board."
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
        if board['dir'] == "clusterfuck":
          raise UserError, "Esta función no está disponible para este board."
        caught = True
        sort = self.formdata.get('sort', '')
        self.output = catalog(sort)
      elif path_split[1] == "oekaki":
        caught = True
        oekaki.oekaki(self, path_split)
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
  
  def make_post(self, ip, boarddir, parent, trap1, trap2, name, email, subject, message, file, file_original, spoil, oek_file, oek_file_x, oek_file_y, timetaken, password, noimage, mobile):
    _STARTTIME = time.time() # Comment if not debug
    
    # check length of fields
    if len(name) > 70:
      raise UserError, "Campo de nombre muy largo."
    if len(email) > 70:
      raise UserError, "Campo de e-mail muy largo."
    if len(subject) > 180:
      raise UserError, "Campo de asunto muy largo."
    if len(message) > 7900:
      raise UserError, "Campo de mensaje muy largo."
    
    # anti-spam trap
    if trap1 or trap2:
      raise UserError, "Te quedan 3 días de vida."
    
    # Create a single datetime now so everything syncs up
    #t = datetime.datetime.now()
    t = time.time()
    
    # open database
    OpenDb()
    
    # delete expired bans
    deletedBans = UpdateDb("DELETE FROM `bans` WHERE `until` != 0 AND `until` < " + str(timestamp())) # Delete expired bans
    if deletedBans > 0:
      regenerateAccess()
    
    # set the board
    board = setBoard(boarddir)
    
    # redirect to ban page if user is banned
    if addressIsBanned(ip, board["dir"]):
      self.output += '<html xmlns="http://www.w3.org/1999/xhtml"><body><meta http-equiv="refresh" content="1;url=%s" />Espere...</body></html>'  % (Settings.CGI_URL + 'banned/' + board["dir"])
      return
    
    # don't let to post if the site OR board is in maintenance
    if Settings.MAINTENANCE and board["dir"] != "clusterfuck":
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
    
    # use name only if anonymous posting is not enforced
    if board["forced_anonymous"] != '1':
      post["name"] = cleanString(name)
    
    # use e-mail
    if email.lower() != Settings.DEFAULT_NOKO:
      post["email"] = cleanString(email, quote=True)
    
    # use subject
    if board["disable_subject"] != '1':
      post["subject"] = cleanString(subject)
    
    # process tripcodes
    post["name"], post["tripcode"] = tripcode(post["name"])

    # process namefilters
    post["name"], post["tripcode"] = checkNamefilters(post["name"], post["tripcode"], ip, board["dir"])
    
    # use and format message
    if message.strip():
      post["message"] = format_post(message, ip, post["parentid"], parent_timestamp)
    
    # use password
    post["password"] = password
    
    # make ID hash
    force_id = False

    if post["parentid"]:
      if parent_post["email"] == 'id':
        force_id = True
    elif not post["parentid"]:
      if post["email"] == 'id':
        force_id = True
    
    # if we are replying, use first post's time
    if post["parentid"]:
      tim = parent_post["timestamp"]
    else:
      tim = post["timestamp"]
    
    # 2: id - 4: idsage
    if force_id:
      post["timestamp_formatted"] += ' ID:' + iphash(ip, post["email"], tim, '4')
    elif board["useid"] != '0':
      post["timestamp_formatted"] += ' ID:' + iphash(ip, post["email"], tim, board["useid"])
    
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
      if xfile and board['allow_image_replies'] == '0':
        raise UserError, _("Image replies not allowed.")
    else:
      if xfile and board['allow_images'] == '0':
        raise UserError, _("No images allowed.")
    
    # process files
    if oek_file:
      post = processOekakiImage(post, oek_file, int(oek_file_x), int(oek_file_y), int(timetaken))
    elif file and not noimage:
      post = processImage(post, file, t, file_original, (spoil and board['allow_spoilers'] == '1'))
      
    # use default values when missing
    if not post["name"] and not post["tripcode"]:
      post["name"] = random.choice(board["anonymous"].split('|'))
    if not post["subject"] and not post["parentid"]:
      post["subject"] = board["subject"]
    if not post["message"]:
      post["message"] = board["message"]
    
    # create nameblock
    #post["nameblock"] = nameBlock(post["name"], post["tripcode"], post["email"], post["timestamp_formatted"], post["iphash"], mobile)
    
    # APRIL FOOLS : FUSIANASAN
    if "fusianasan" in post["name"].lower():
      import socket
      post["name"] = ""
      post["tripcode"] = socket.gethostbyaddr(self.environ["REMOTE_ADDR"])[0]
    
    # set expiration date if necessary
    if board["maxage"] != '0' and not post["parentid"]:
      date_format = '%d/%m'
      if board["dir"] == 'jp':
        date_format = '%m月%d日'
      post["expires"] = int(t) + (int(board["maxage"]) * 86400)
      post["expires_formatted"] = datetime.datetime.fromtimestamp(post["expires"]).strftime(date_format)
    
    if not post["parentid"]:
      # fill with default values if creating a new thread
      post["length"] = 1
      post["last"] = post["timestamp"]
      
    # insert the post, then run the timThreads function to make sure the board doesn't exceed the page limit
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
      
      # bump/soko/sage
      if "soko" in post["email"].lower() and board["dir"] == 'g':
        # APRIL FOOLS : SOKO
        UpdateDb("UPDATE `posts` SET bumped = 1 WHERE (`id` = '%s' OR `parentid` = '%s') AND `boardid` = '%s'" % (post["parentid"], post["parentid"], board["id"]))
      elif Settings.DEFAULT_SAGE not in post["email"].lower() and parent_post['locked'] != '2':
        UpdateDb("UPDATE `posts` SET bumped = %d WHERE (`id` = '%s' OR `parentid` = '%s') AND `boardid` = '%s'" % (post["timestamp"], post["parentid"], post["parentid"], board["id"]))
    
      # update final attributes (length and last post)
      UpdateDb("UPDATE `posts` SET length = %d, last = %d WHERE `id` = '%s' AND `boardid` = '%s'" % (thread_length, post["timestamp"], post["parentid"], board["id"]))
      
      # update cache
      threadUpdated(post["parentid"])
    else:
      # create cache for new thread
      threadUpdated(postid)
    
    # regenerate home page with last posts
    if board['secret'] == '0':
      home_add_post(post, thread_length, postid, parent_post or post, 'templates/home_posts.html')
      if not post["parentid"]:
        home_add_post(post, thread_length, postid, parent_post or post, 'templates/home_threads.html')
      regenerateHome()
      
    # set cookies
    reCookie(self, "weabot_name", name)
    reCookie(self, "weabot_email", email)
    reCookie(self, "weabot_password", password)
    
    # make page redirect
    #if _DEBUG:
    timetaken = time.time() - _STARTTIME
    #else:
    #  timetaken = None
    noko = Settings.DEFAULT_NOKO in email.lower() or board["board_type"] == '1'
    self.output += make_redirect(postid, post['parentid'], parent_post or post, noko, mobile, timetaken)
    #print make_redirect(postid, post["parentid"], noko, mobile, timetaken)
  
  def delete_post(self, boarddir, postid, imageonly, password):
    # open database
    OpenDb()
    
    # set the board
    board = setBoard(boarddir)
    
    # check if we have a post id and check it's numeric
    if not postid:
      raise UserError, _("Invalid selection. You probably didn't check any post, or checked more than one.")
    
    # make sure we have a password
    if not password:
      raise UserError, _("Please enter a password.")
    
    # delete post
    deletePost(postid, password, board['recyclebin'], imageonly)
    
    # regenerate home
    regenerateHome()
    
    # redirect
    if imageonly:
      self.output += '<html xmlns="http://www.w3.org/1999/xhtml"><body><meta http-equiv="refresh" content="0;url=%s/" /><p>%s</p></body></html>' % (Settings.BOARDS_URL + board["dir"], _("File deleted successfully."))
    else:
      self.output += '<html xmlns="http://www.w3.org/1999/xhtml"><body><meta http-equiv="refresh" content="0;url=%s/" /><p>%s</p></body></html>' % (Settings.BOARDS_URL + board["dir"], _("Post deleted successfully."))
  
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
    post = FetchOne("SELECT `parentid`, `ip` FROM `posts` WHERE `id` = '%s' AND `boardid` = '%s'" % (_mysql.escape_string(str(postid)), _mysql.escape_string(board['id'])))
    if not post:
      raise UserError, _("Post doesn't exist.")
    
    # insert report
    t = time.time()
    message = cgi.escape(self.formdata["reason"]).strip()[0:8000]
    message = message.replace("\n", "<br />")
    
      
    UpdateDb("INSERT INTO `reports` (board, postid, parentid, ip, reason, reporterip, timestamp, timestamp_formatted) VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')" % (board["dir"], _mysql.escape_string(str(postid)), post['parentid'], post['ip'], _mysql.escape_string(message), _mysql.escape_string(self.environ["REMOTE_ADDR"]), str(t), formatTimestamp(t)))
    self.output = renderTemplate("report.html", {'finished': True})
  
  def stats(self):
    import json, math, platform
    with open('stats.json', 'r') as f:
      out = json.load(f)
    
    regenerated = False
    if (time.time() - out['t']) > 1600:
    #if True:
      regenerated = True
      
      # open database
      OpenDb()
      
      # 1 week = 604800
      query_day = FetchAll("SELECT DATE_FORMAT(FROM_UNIXTIME(FLOOR(timestamp/86400)*86400+86400), \"%Y-%m-%d\"), COUNT(1) "
        "FROM posts "
        "WHERE timestamp > (UNIX_TIMESTAMP()-691200) AND IS_DELETED = 0 "
        "GROUP BY FLOOR(timestamp/86400) "
        "ORDER BY FLOOR(timestamp/86400)", 0)
      
      query_all = FetchAll("SELECT boards.name, COUNT(1) AS count "
        "FROM posts "
        "INNER JOIN boards ON posts.boardid = boards.id "
        "WHERE boards.secret = 0 AND timestamp > (UNIX_TIMESTAMP()-7889231)"
        "GROUP BY boardid "
        "ORDER BY count DESC", 0)
      
      query_count = FetchOne("SELECT COUNT(1), COUNT(NULLIF(file, '')), VERSION() FROM posts", 0)
      total = int(query_count[0])
      total_files = int(query_count[1])
      mysql_ver = query_count[2]
      
      archive_count = FetchOne("SELECT SUM(length) FROM archive", 0)
      total_archived = int(archive_count[0])
    
      days = []
      for date, count in query_day:
        days.append( (date, count) )
      
      days.pop(0)
      days[-1] = (days[-1][0] + ' (hoy)', days[-1][1] + '+')
       
      boards = []
      total_3m = 0
      for dir, count in query_all:
        boards.append( (dir, int(count)) )
        total_3m += int(count)
      
      boards_percent = []
      for dir, count in boards:
        boards_percent.append( (dir, '{0:.2f}'.format( float(count)*100/total_3m ) ) )
      
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
             "t": timestamp()
            }
      with open('stats.json', 'w') as f:
        json.dump(out, f)
      
    out['timestamp'] = formatTimestamp(out['t'])
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

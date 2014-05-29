#!c:/Python27/python
# coding=utf-8

# Remove the first line to use the env command to locate python

import os
import time
import datetime
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
    OpenDb()
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
    if self.environ["HTTP_ACCEPT"].find("application/xhtml+xml") != -1:
      self.headers = [("Content-Type", "application/xhtml+xml")]
    else:
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
    deletedBans = UpdateDb("DELETE FROM `bans` WHERE `until` != 0 AND `until` < " + str(timestamp())) # Delete expired bans
    if deletedBans > 0:
      regenerateAccess()
    
    path_split = self.environ["PATH_INFO"].split("/")
    caught = False
    
    if len(path_split) > 1:
      if path_split[1] == "post":
        # Making a post
        caught = True
        
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
        noko = self.formdata.get('noko')
        oek_file = self.formdata.get('oek_file')
        oek_file_x = self.formdata.get('oek_file_x')
        oek_file_y = self.formdata.get('oek_file_y')
        timetaken = self.formdata.get('timetaken')
        password = self.formdata.get('password', '')
        noimage = self.formdata.get('noimage')
        markup = self.formdata.get('markup')
        savemarkup = self.formdata.get('savemarkup')
        mobile = ("mobile" in self.formdata.keys())
        
        # call post function
        self.make_post(ip, boarddir, parent, trap1, trap2, name, email, subject, message, file, file_original, spoil, noko, oek_file, oek_file_x, oek_file_y, timetaken, password, noimage, markup, savemarkup, mobile)
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
        manage.manage(self, path_split)
      elif path_split[1] == "threadlist":
        board = setBoard(path_split[2])
        caught = True
        self.output = threadList(0)
      elif path_split[1] == "mobile":
        board = setBoard(path_split[2])
        caught = True
        self.output = threadList(1)
      elif path_split[1] == "mobilelist":
        board = setBoard(path_split[2])
        caught = True
        self.output = threadList(2)
      elif path_split[1] == "mobilenew":
        board = setBoard(path_split[2])
        caught = True
        self.output = renderTemplate('txt_newthread.html', {}, True)
      elif path_split[1] == "mobilehome":
        caught = True
        posts = FetchAll('SELECT * FROM `posts` INNER JOIN `boards` ON posts.boardid = boards.id WHERE IS_DELETED = 0 AND posts.boardid != 15 ORDER BY `timestamp` DESC LIMIT ' + str(Settings.HOME_LASTPOSTS))
        # Latest posts formatting
        latest_posts = []
       
        for post in posts:
          post['message'] = post['message'].replace('<br />', ' ')
          post['message'] = re.compile(r"<span class=\"spoiler\">(.+?)</span>", re.DOTALL | re.IGNORECASE).sub('(spoiler)', post['message']) # Remove spoilers
          post['message'] = re.compile(r"<[^>]*?>", re.DOTALL | re.IGNORECASE).sub('', post['message']) # Removes every html tag in the message
          limit = 30 - len(post['boards.name'])
          if len(post['message']) > limit:
            post['message'] = post['message'].decode('utf-8')[:limit].encode('utf-8') + "..."
          post['message'] = re.compile(r"&(.(?!;))*$", re.DOTALL | re.IGNORECASE).sub('', post['message']) # Removes incomplete HTML entities
          latest_posts.append(post)
        self.output = renderTemplate('latest.html', {'latest_posts': latest_posts}, True)
      elif path_split[1] == "mobileread":
        board = setBoard(path_split[2])
        caught = True
        if len(path_split) > 4 and board['board_type'] == '1':
          try:
            self.output = dynamicRead(int(path_split[3]), path_split[4], True)
          except:
            self.output = threadPage(path_split[3], True)
        else:
          self.output = threadPage(path_split[3], True)
      elif path_split[1] == "catalog":
        board = setBoard(path_split[2])
        caught = True
        self.output = catalog()
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
      elif path_split[1] == "banned":
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
          
          board = setBoard(path_split[2])
          self.output = dynamicRead(int(path_split[3]), path_split[4])
      elif path_split[1] == "preview":
        caught = True
        try:
          board = setBoard(self.formdata["board"])
          
          if "markup" in self.formdata.keys():
            message = format_post(self.formdata["message"], self.environ["REMOTE_ADDR"], self.formdata["parentid"], self.formdata["markup"])
          else:
            message = format_post(self.formdata["message"], self.environ["REMOTE_ADDR"], self.formdata["parentid"], "tags")
          
          self.output = message
        except Exception, messagez:
          self.output = "Error: " + str(messagez) + " : " + str(self.formdata)
        
    if not caught:
      # Redirect the user back to the front page
      self.output += '<html xmlns="http://www.w3.org/1999/xhtml"><body><meta http-equiv="refresh" content="0;url=%s" /><p>--&gt; --&gt; --&gt;</p></body></html>' % Settings.HOME_URL
  
  def make_post(self, ip, boarddir, parent, trap1, trap2, name, email, subject, message, file, file_original, spoil, noko, oek_file, oek_file_x, oek_file_y, timetaken, password, noimage, markup, savemarkup, mobile):
    _STARTTIME = time.time() # Comment if not debug
    
    # check length of fields
    if len(name) > 75:
      raise UserError, "Campo de E-Mail muy largo."
    if len(email) > 75:
      raise UserError, "Campo de nombre muy largo."
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
    
    # set the board
    board = setBoard(boarddir)
    
    # redirect to ban page if user is banned
    if addressIsBanned(ip, board["dir"]):
      self.output += '<html xmlns="http://www.w3.org/1999/xhtml"><body><meta http-equiv="refresh" content="1;url=%s" />Espere...</body></html>'  % (Settings.CGI_URL + 'banned/' + board["dir"])
      return
    
    # don't let to post if the site OR board is in maintenance
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
    if parent:
      parent_post = get_parent_post(parent, board["id"])
        
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
      post["message"] = format_post(message, ip, post["parentid"], markup)
    
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
      post["name"] = board["anonymous"]
    if not post["subject"] and not post["parentid"]:
      post["subject"] = board["subject"]
    if not post["message"]:
      post["message"] = board["message"]
    
    # create nameblock
    #post["nameblock"] = nameBlock(post["name"], post["tripcode"], post["email"], post["timestamp_formatted"], post["iphash"], mobile)
    
    # insert the post, then run the timThreads function to make sure the board doesn't exceed the page limit
    postid = post.insert()
    
    # delete threads that have crossed last page
    trimThreads()
    
    # fix null references when creating thread
    if board["board_type"] == '1' and not post["parentid"]:
      post["message"] = re.compile(r'<a href="/(\w+)/res/0.html/(.+)"').sub(r'<a href="/\1/res/'+str(postid)+r'.html/\2"', post["message"])
      UpdateDb("UPDATE `posts` SET message = '%s' WHERE boardid = '%s' AND id = '%s'" % (_mysql.escape_string(post["message"]), _mysql.escape_string(board["id"]), _mysql.escape_string(str(postid))))
    
    # get length of the thread
    if post["parentid"]:
      thread_length = threadNumReplies(post["parentid"])
    else:
      thread_length = 0
    
    # regenerate home page with last posts
    if board['secret'] == '0':
      home_add_post(post['message'], thread_length, postid, post['parentid'], post['file'], post['subject'])
      regenerateHome()
    
    # check if thread must be closed
    if post["parentid"]:
      autoclose_thread(post["parentid"], t, thread_length)
      
    # update thread caches and bump if necessary
    logTime("Updating thread")
    if post["parentid"]:
      if post["email"].lower() != Settings.DEFAULT_SAGE and parent_post['locked'] != '2':
        UpdateDb("UPDATE `posts` SET bumped = %d WHERE (`id` = '%s' OR `parentid` = '%s') AND `boardid` = '%s'" % (post["timestamp"], post["parentid"], post["parentid"], board["id"]))
    
      threadUpdated(post["parentid"])
    else:
      threadUpdated(postid)
    
    # noko cookie
    if noko:
      isNoko = '1'
    else:
      isNoko = '0'
    
    # set cookies
    reCookie(self, "weabot_name", name)
    reCookie(self, "weabot_email", email)
    reCookie(self, "weabot_password", password)
    if savemarkup and markup:
      reCookie(self, "weabot_markup", markup)
    reCookie(self, "weabot_noko", isNoko)
    
    # make page redirect
    #if _DEBUG:
    timetaken = time.time() - _STARTTIME
    #else:
    #  timetaken = None
    noko = (isNoko == '1' or email.lower() == Settings.DEFAULT_NOKO)
    self.output += make_redirect(postid, post["parentid"], noko, mobile, timetaken)
    #print make_redirect(postid, post["parentid"], noko, mobile, timetaken)
  
  def delete_post(self, boarddir, postid, imageonly, password):
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
  

# coding=utf-8
import math
import os
import shutil
import threading
import Queue
import _mysql
import formatting

from database import *
from template import *
from settings import Settings
from framework import *

class Post(object):
  def __init__(self, boardid=0):
    self.post = {
        "boardid": boardid,
        "parentid": 0,
        "name": "",
        "tripcode": "",
        "email": "",
        "subject": "",
        "message": "",
        "password": "",
        "file": "",
        "file_hex": "",
        "file_mime": "",
        "file_original": "",
        "file_size": 0,
        "file_size_formatted": "",
        "animation": "",
        "thumb": "",
        "image_width": 0,
        "image_height": 0,
        "thumb_width": 0,
        "thumb_height": 0,
        "ip": "",
        "timestamp_formatted": "",
        "timestamp": 0,
        "bumped": 0,
        "locked": 0,
    }
    
  def __getitem__(self, key):
    return self.post[key]

  def __setitem__(self, key, value):
    self.post[key] = value
    
  def __iter__(self):
    return self.post

  def insert(self):
    logTime("Insertando Post")
    post_values = [_mysql.escape_string(str(value)) for key, value in self.post.iteritems()]
    
    return InsertDb("INSERT INTO `posts` (`%s`) VALUES ('%s')" % (
      "`, `".join(self.post.keys()),
      "', '".join(post_values)
    ))

class RegenerateThread(threading.Thread):
  def __init__(self, threadid, request_queue):
    threading.Thread.__init__(self, name="RegenerateThread-%d" % (threadid,))
    self.request_queue = request_queue
    self.board = Settings._.BOARD
    
  def run(self):
    Settings._.BOARD = self.board
    while 1:
      action = self.request_queue.get()
      if action is None:
        break
      if action == "front":
        regenerateFrontPages()
      else:
        regenerateThreadPage(action)

def threadNumReplies(post):
  """
  Get how many replies a thread has
  """
  board = Settings._.BOARD
  
  num = FetchOne("SELECT COUNT(1) FROM `posts` WHERE `parentid` = '%s' AND `boardid` = '%s'" % (post, board['id']), 0)
  return int(num[0])+1
  
def get_parent_post(post_id, board_id):
  post = FetchOne("SELECT `id`, `email`, `locked`, `timestamp`, `bumped` FROM `posts` WHERE `id` = %s AND `parentid` = 0 AND `IS_DELETED` = 0 AND `boardid` = %s LIMIT 1" % (post_id, board_id))
  if post:
    return post
  else:
    raise UserError, _("The ID of the parent post is invalid.")

def getThread(postid, mobile):
  board = Settings._.BOARD
  
  database_lock.acquire()
  try:
    postid = int(postid)
    op_post = FetchOne("SELECT * FROM `posts` WHERE `id` = %s AND `boardid` = %s LIMIT 1" % (str(postid), board["id"]))
    if op_post:
      op_post['num'] = 1
      if Settings._.MODBROWSE:
        op_post['ip'] = inet_ntoa(long(op_post['ip']))
      thread = {"id": op_post["id"], "posts": [op_post], "omitted": 0, "omitted_img": 0}

      replies = FetchAll("SELECT * FROM `posts` WHERE `parentid` = %s AND `boardid` = %s ORDER BY `id` ASC" % (op_post["id"], board["id"]))
      thread["length"] = 1
      if replies:
        for reply in replies:
          thread["length"] += 1
          reply['num'] = thread["length"]
          if Settings._.MODBROWSE:
            reply['ip'] = inet_ntoa(long(reply['ip']))
          if mobile:
            reply['message'] = formatting.fixMobileLinks(reply['message'])
          thread["posts"].append(reply)
      
      # An imageboard needs subject
      if board["board_type"] in ['1', '5']:
        thread["subject"] = op_post["subject"]
      
      #threads = [thread]
  finally:
    database_lock.release()
  
  return thread
    
def shortenMsg(message, elid='0', elboard='0'):
  """
  Intenta acortar el mensaje si es necesario
  Algoritmo traducido desde KusabaX
  """
  # 150 caracteres * 15 lineas
  #limit = 2250
  #return False, message
        
  limit = Settings.POST_LINE_WIDTH * Settings.POST_MAX_LINES
  
  message_exploded = message.split('<br />')
  if len(message) > limit or len(message_exploded) > Settings.POST_MAX_LINES:
    message_shortened = ''
    for i in range(Settings.POST_MAX_LINES):
      if i >= len(message_exploded):
        break
      
      message_shortened += message_exploded[i] + '<br />'
    
    #try:
    message_shortened = message_shortened.decode('utf-8', 'replace')
    #except:
    
    if len(message_shortened) > limit:  
      message_shortened = message_shortened[:limit]
    
    #try:
    message_shortened = formatting.close_html(message_shortened)
    #except Exception, message:
    
    return True, message_shortened
  else:
    return False, message

def threadUpdated(postid):
  """
  Shortcut to update front pages and thread page by passing a thread ID. Uses
  the simple threading module to do both regenerateFrontPages() and
  regenerateThreadPage() asynchronously
  """
  # Use queues only if multithreading is enabled
  if Settings.USE_MULTITHREADING:
    request_queue = Queue.Queue()
    threads = [RegenerateThread(i, request_queue) for i in range(2)]
    for t in threads:
      t.start()

    request_queue.put("front")
    request_queue.put(postid)

    for i in range(2):
      request_queue.put(None)

    for t in threads:
      t.join
  else:
    regenerateFrontPages()
    regenerateThreadPage(postid)

def regenerateFrontPages():
  """
  Regenerates index.html and #.html for each page after that according to the number
  of live threads in the database
  """
  board = Settings._.BOARD
  threads = []

  database_lock.acquire()
  try:
    posts_query = "SELECT * FROM `posts` WHERE `boardid` = '%s' ORDER BY `bumped` DESC, CASE parentid WHEN 0 THEN id ELSE parentid END ASC, `id` ASC" % board["id"]
    posts = FetchAll(posts_query)
    
    if posts:
      thread = None
      for post in posts:
        #raise Exception, post["id"]
        if post["parentid"] == '0':
          skipThread = False
          if post["IS_DELETED"] == '0':
            # Make new thread
            if thread is not None:
              thread["length"] = post_num
              threads.append(thread)
            post_num = post["num"] = 1
            thread = {"id": post["id"], "subject": post["subject"], "posts": [post]}
          else:
            skipThread = True
        else:
          if not skipThread:
            post_num += 1
            post["num"] = post_num
            thread["posts"].append(post)
      thread["length"] = post_num
      threads.append(thread)
    else:
      threads = []
    
    # Count more threads until end if textboard
    if board['board_type'] == '1':
      start = Settings.TXT_THREADS_SHOWN_ON_FRONT_PAGE
      end = Settings.TXT_THREADS_SHOWN_ON_THREAD_LIST
      more_threads = threads[start:end]
    else:
      more_threads = None
    
  finally:
    database_lock.release()
  
  pages = []
  if len(threads) > 0:
    # Todo : Make this better
    if board['board_type'] == '1':
      page_count = 1 # Front page only
      threads_per_page = Settings.TXT_THREADS_SHOWN_ON_FRONT_PAGE
    else:
      page_count = int(math.ceil(float(len(threads)) / float(Settings.THREADS_SHOWN_ON_FRONT_PAGE)))
      threads_per_page = Settings.THREADS_SHOWN_ON_FRONT_PAGE
    is_omitted = (len(threads) == Settings.MAX_THREADS)
    
    for i in xrange(page_count):
      pages.append([])
      start = i * threads_per_page
      end = start + threads_per_page
      for thread in threads[start:end]:
        pages[i].append(thread)
  else:
    page_count = 0
    is_omitted = False
    pages.append({})
  
  page_num = 0
  for pagethreads in pages:
    regeneratePage(page_num, page_count, pagethreads, is_omitted, more_threads)
    page_num += 1

def regeneratePage(page_num, page_count, threads, is_omitted=False, more_threads=[]):
  """
  Regenerates a single page and writes it to .html
  """
  board = Settings._.BOARD

  for thread in threads:
    if board['board_type'] == '1':
      replylimit = Settings.TXT_REPLIES_SHOWN_ON_FRONT_PAGE
    else:
      replylimit = Settings.REPLIES_SHOWN_ON_FRONT_PAGE
    
    # Create reply list
    parent = thread["posts"].pop(0)
    replies = thread["posts"]
    thread["omitted"] = 0
    thread["omitted_img"] = 0
    
    # Omit posts
    while(len(replies) > replylimit):
      post = replies.pop(0)
      thread["omitted"] += 1
      if post["file"]:
        thread["omitted_img"] += 1
    
    # Remake thread with necessary replies only
    replies.insert(0, parent)
    thread["posts"] = replies
    
    # Shorten messages
    for post in thread["posts"]:
      post["shortened"], post["message"] = shortenMsg(post["message"])
      #post["shortened"], post["message"] = False, 'yeah'

  # Build page according to the page number
  if page_num == 0:
    file_name = "index"
  else:
    file_name = str(page_num)
  
  if board['board_type'] == '1':
    templatename = "txt_board.html"
  else:
    templatename = "board.html"
  
  page_rendered = renderTemplate(templatename, {"threads": threads, "page_navigator": pageNavigator(page_num, page_count, is_omitted), "more_threads": more_threads})
  
  f = open(Settings.ROOT_DIR + board["dir"] + "/" + file_name + ".html", "w")
  try:
    f.write(page_rendered)
  finally:
    f.close()
  
def threadList(mode=0):
  board = Settings._.BOARD
  
  if mode == 1:
    mobile = True
    maxthreads = 10
    cutFactor = 150
  elif mode == 2:
    mobile = True
    maxthreads = 500 # Settings.MAX_THREADS
    cutFactor = 60
  else:
    mobile = False
    maxthreads = 500 # Settings.MAX_THREADS
    cutFactor = 60
  
  if board['board_type'] == '1':
    filename = "txt_threadlist.html"
    full_threads = FetchAll("SELECT p.id, p.subject, p.locked, coalesce(x.count,1) AS length, coalesce(x.t,p.timestamp) AS last FROM `posts` AS p LEFT JOIN (SELECT parentid, count(1)+1 as count, max(timestamp) as t FROM `posts` " +\
                          "WHERE boardid = %(board)s GROUP BY parentid) AS x ON p.id=x.parentid WHERE p.parentid = 0 AND p.boardid = %(board)s AND p.IS_DELETED = 0 ORDER BY `bumped` DESC LIMIT %(limit)s" \
                           % {'board': board["id"], 'limit': maxthreads})
  else:
    filename = "threadlist.html"
    full_threads = FetchAll("SELECT p.*, coalesce(x.count,1) AS length, coalesce(x.t,p.timestamp) AS last FROM `posts` AS p LEFT JOIN (SELECT parentid, count(1)+1 as count, max(timestamp) as t FROM `posts` " +\
                          "WHERE boardid = %(board)s GROUP BY parentid) AS x ON p.id=x.parentid WHERE p.parentid = 0 AND p.boardid = %(board)s AND p.IS_DELETED = 0 ORDER BY `bumped` DESC LIMIT %(limit)s" \
                           % {'board': board["id"], 'limit': maxthreads})
  
  # Generate threadlist
  timestamps = []
  for thread in full_threads:
    if board['board_type'] == '1':
      timestamps.append(formatTimestamp(thread["last"]))
    else:
      if len(thread['message']) > cutFactor:
        thread['shortened'] = True
      else:
        thread['shortened'] = False
      thread['message'] = thread['message'].replace('<br />', ' ')
      thread['message'] = re.compile(r"<[^>]*?>", re.DOTALL | re.IGNORECASE).sub('', thread['message'])
      thread['message'] = thread['message'].decode('utf-8')[:cutFactor].encode('utf-8')
      thread['message'] = re.compile(r"&(.(?!;))*$", re.DOTALL | re.IGNORECASE).sub('', thread['message']) # Removes incomplete HTML entities
      
      # We only get the last reply if we're in mobile mode
      if mode == 1:
        lastreply = FetchOne("SELECT * FROM `posts` WHERE parentid = %s AND boardid = %s AND IS_DELETED = 0 ORDER BY `timestamp` DESC LIMIT 1" % (thread['id'], board['id']))
        if lastreply:
          if len(lastreply['message']) > 60:
            lastreply['shortened'] = True
          else:
            lastreply['shortened'] = False
          lastreply['message'] = lastreply['message'].replace('<br />', ' ')
          lastreply['message'] = re.compile(r"<[^>]*?>", re.DOTALL | re.IGNORECASE).sub('', lastreply['message'])
          lastreply['message'] = lastreply['message'].decode('utf-8')[:60].encode('utf-8')
          lastreply['message'] = re.compile(r"&(.(?!;))*$", re.DOTALL | re.IGNORECASE).sub('', lastreply['message']) # Removes incomplete HTML entities
          thread["lastreply"] = lastreply
        else:
          thread["lastreply"] = None
  return renderTemplate(filename, {"more_threads": full_threads, "timestamps": timestamps, "mode": mode}, mobile)

def catalog():
  board = Settings._.BOARD
  
  threads = FetchAll("SELECT p.id, p.thumb, coalesce(x.count,1) AS length FROM `posts` AS p LEFT JOIN (SELECT parentid, count(1)+1 as count, max(timestamp) as t FROM `posts` " +\
                     "WHERE boardid = %(board)s GROUP BY parentid) AS x ON p.id=x.parentid WHERE p.parentid = 0 AND p.boardid = %(board)s AND p.IS_DELETED = 0 ORDER BY `bumped` DESC" \
                     % {'board': board["id"]})
  
  # Generate catalog
  return renderTemplate("catalog.html", {"threads": threads})
  
def regenerateThreadPage(postid):
  """
  Regenerates /res/#.html for supplied thread id
  """
  board = Settings._.BOARD
  
  page = threadPage(postid)
  
  f = open(Settings.ROOT_DIR + board["dir"] + "/res/" + str(postid) + ".html", "w")
  try:
    f.write(page)
  finally:
    f.close()
  
def threadPage(postid, mobile=False):
  board = Settings._.BOARD
  
  # TODO : Encontrar mejor forma para transformar el IP a string sólo cuando se usa Modbrowse
  
  if board['board_type'] in ['1', '5']:
    template_filename = "txt_thread.html"
  else:
    template_filename = "board.html"
  
  threads = [getThread(postid, mobile)]
  
  return renderTemplate(template_filename, {"threads": threads, "replythread": postid}, mobile)

def dynamicRead(parentid, ranges, mobile=False):
  import re
  board = Settings._.BOARD
  
  # get entire thread
  thread = getThread(parentid, mobile)
  filtered_thread = {
    "id": thread['id'],
    "length": thread['length'],
    "subject": thread['subject'],
    "posts": [],
  }
  
  no_op = False
  if re.match("^n", ranges):
    no_op = True
    ranges = re.sub("^n", "", ranges)
  
  # get thread length
  total = thread["length"]
  
  # compile regex
  __multiple_ex = re.compile("^([0-9]*)-([0-9]*)$")
  __single_ex = re.compile("^([0-9]+)$")
  __last_ex = re.compile("^l([0-9]+)$")
  start = 0
  end = 0
  
  # separate by commas (,)
  for range in ranges.split(','):
    # single post (#)
    range_match = __single_ex.match(range)
    if range_match:
      postid = int(range_match.group(1))
      if postid > 0 and postid <= total:
        filtered_thread["posts"].append(thread["posts"][postid-1])
      
      # go to next range
      continue
    
    # post range (#-#)
    range_match = __multiple_ex.match(range)
    if range_match:
      start = int(range_match.group(1) or 1)
      end = int(range_match.group(2) or total)
      
      if start > total:
        start = total
      if end > total:
        end = total
      
      if start < end:
        filtered_thread["posts"].extend(thread["posts"][start-1:end])
      else:
        list = thread["posts"][end-1:start]
        list.reverse()
        filtered_thread["posts"].extend(list)
      
      # go to next range
      continue
    
    # last posts (l#)
    range_match = __last_ex.match(range)
    if range_match:
      length = int(range_match.group(1))
      start = total - length + 1
      end = total
      if start < 1:
        start = 1
      
      filtered_thread["posts"].extend(thread["posts"][start-1:])
      
      continue
  
  # calculate previous and next ranges
  prevrange = None
  nextrange = None
  if __multiple_ex.match(ranges) or __last_ex.match(ranges):
    prev_start = start-100
    prev_end = start-1
    next_start = end+1
    next_end = end+100
    
    if prev_start < 1:
      prev_start = 1
    if next_end > total:
      next_end = total
    
    if start > 1:
      prevrange = '%d-%d' % (prev_start, prev_end)
    if end < total:
      nextrange = '%d-%d' % (next_start, next_end)
    
    if not no_op and start > 1 and end > 1:
      filtered_thread["posts"].insert(0, thread["posts"][0])
  
  if not filtered_thread["posts"]:
    raise UserError, "No hay posts que mostrar."

  # render page
  return renderTemplate("txt_thread.html", {"threads": [filtered_thread], "replythread": parentid, "prevrange": prevrange, "nextrange": nextrange}, mobile)

def regenerateBoard():
  """
  Update front pages and every thread res HTML page
  """
  board = Settings._.BOARD
  
  op_posts = FetchAll("SELECT `id` FROM `posts` WHERE `boardid` = %s AND `parentid` = 0 AND IS_DELETED = 0" % board["id"])

  # Use queues only if multithreading is enabled
  if Settings.USE_MULTITHREADING:
    request_queue = Queue.Queue()
    threads = [RegenerateThread(i, request_queue) for i in range(Settings.MAX_PROGRAM_THREADS)]
    for t in threads:
      t.start()

    request_queue.put("front")

    for post in op_posts:
      request_queue.put(post["id"])

    for i in range(Settings.MAX_PROGRAM_THREADS):
      request_queue.put(None)

    for t in threads:
      t.join()
  else:
    regenerateFrontPages()
    for post in op_posts:
      regenerateThreadPage(post["id"])
  
def deletePost(postid, password, deltype='0', imageonly=False, quick=False):
  """
  Remove post from database and unlink file (if present), along with all replies
  if supplied post is a thread
  """
  board = Settings._.BOARD
  
  # make sure postid is numeric
  postid = int(postid)
  
  # get post
  post = FetchOne("SELECT `id`, `parentid`, `file`, `thumb`, `animation`, `password` FROM `posts` WHERE `boardid` = %s AND `id` = %s LIMIT 1" % (board["id"], str(postid)))
  
  # abort if the post doesn't exist
  if not post:
    raise UserError, _("There isn't a post with this ID. It was probably deleted.")
  
  # check the password
  if password and password != post['password']:
    raise UserError, _("Wrong password.")
  
  # delete file if there's one
  if post["file"]:
    deleteFile(post)
  
  # just update the DB if we're deleting only the image
  # otherwise delete the whole post
  if imageonly:
    UpdateDb("UPDATE `posts` SET `file` = '', `file_hex` = '' WHERE `boardid` = %s AND `id` = %s LIMIT 1" % (board["id"], str(post['id'])))
  else:
    if int(post["parentid"]) == 0:
      replies = FetchAll("SELECT `id` FROM `posts` WHERE `boardid` = %s AND `parentid` = %s" % (board["id"], str(postid)))
      for reply in replies:
        deletePost(reply["id"],password,deltype)

    logTime("Deleting post " + str(postid))
    if deltype != '0':
      UpdateDb("UPDATE `posts` SET `IS_DELETED` = %s WHERE `boardid` = %s AND `id` = %s LIMIT 1" % (deltype, board["id"], post["id"]))
    else:
      UpdateDb("DELETE FROM `posts` WHERE `boardid` = %s AND `id` = %s LIMIT 1" % (board["id"], post["id"]))
    
    if post['parentid'] == '0':
      try:
        os.unlink(Settings.ROOT_DIR + board["dir"] + "/res/" + post["id"] + ".html")
      except:
        pass
    
    # delete post from home
    home_remove_post(postid)
    regenerateHome()
  
  # rebuild thread and fronts if reply; rebuild only fronts if not
  if post["parentid"] != '0':
    threadUpdated(post["parentid"])
  else:
    regenerateFrontPages()

def deleteFile(post):
  """
  Unlink file and thumb of supplied post
  """
  board = Settings._.BOARD

  try:
    os.unlink(Settings.IMAGES_DIR + board["dir"] + "/src/" + post["file"])
  except:
    pass

  try:
    os.unlink(Settings.IMAGES_DIR + board["dir"] + "/thumb/" + post["thumb"])
  except:
    pass
  
  try:
    os.unlink(Settings.IMAGES_DIR + board["dir"] + "/mobile/" + post["thumb"])
  except:
    pass
  
  if int(post["parentid"]) == 0:
    try:
      os.unlink(Settings.IMAGES_DIR + board["dir"] + "/cat/" + post["thumb"])
    except:
      pass
  
  try:
    if post["animation"] != "":
      os.unlink(Settings.IMAGES_DIR + board["dir"] + "/src/" + post["animation"] + '.pch')
  except:
    pass

def trimThreads():
  """
  Delete any threads which have passed the MAX_THREADS setting
  """
  logTime("Trimming threads")
  board = Settings._.BOARD
  
  if board['board_type'] == '1':
    limit = 500
  else:
    limit = Settings.MAX_THREADS

  op_posts = FetchAll("SELECT `id` FROM `posts` WHERE `boardid` = %s AND `parentid` = 0 AND IS_DELETED = 0 ORDER BY `bumped` DESC" % board["id"])
  if len(op_posts) > limit:
    posts = op_posts[limit:]
    for post in posts:
      deletePost(post["id"], None)

def autoclose_thread(parentid, t, replies):
  """
  If the thread is crossing the reply limit, close it with a message.
  """
  board = Settings._.BOARD
  
  # decide the replylimit
  if board['board_type'] == '1' and Settings.TXT_CLOSE_THREAD_ON_REPLIES > 0:
    replylimit = Settings.TXT_CLOSE_THREAD_ON_REPLIES
  elif Settings.CLOSE_THREAD_ON_REPLIES > 0:
    replylimit = Settings.CLOSE_THREAD_ON_REPLIES
  else:
    return # do nothing
  
  # close it if passing replylimit
  if replies >= replylimit:
    notice_post = Post(board["id"])
    notice_post["parentid"] = parentid
    notice_post["name"] = "Sistema"
    notice_post["message"] = "El hilo ha sobrepasado el límite de respuestas, por favor crea otro..."
    notice_post["timestamp"] = notice_post["bumped"] = t+1
    notice_post["timestamp_formatted"] = str(replylimit) + " mensajes"
    #notice_post["nameblock"] = formatting.nameBlock(notice_post["name"], "", "", notice_post["timestamp_formatted"], 0, "")
    notice_post.insert()
    UpdateDb("UPDATE `posts` SET `locked` = 1 WHERE `boardid` = '%s' AND `id` = '%s' LIMIT 1" % (board["id"], _mysql.escape_string(parentid)))
    
def pageNavigator(page_num, page_count, is_omitted=False):
  """
  Create page navigator in the format of [0], [1], [2]...
  """
  board = Settings._.BOARD
  
  # No threads?
  if page_count == 0:
    return ''
  
  first_str = "Primera página"
  last_str = "Última página"
  previous_str = _("Previous")
  next_str = _("Next")
  omitted_str = "Resto omitido"
  
  page_navigator = "<td>"
  if page_num == 0:
    page_navigator += first_str
  else:
    previous = str(page_num - 1)
    if previous == "0":
      previous = ""
    else:
      previous = previous + ".html"
    page_navigator += '<form method="get" action="' + Settings.BOARDS_URL + board["dir"] + '/' + previous + '"><input value="'+previous_str+'" type="submit" /></form>'

  page_navigator += "</td><td>"

  for i in xrange(page_count):
    if i == page_num:
      page_navigator += "[<strong>" + str(i) + "</strong>] "
    else:
      if i == 0:
        page_navigator += '[<a href="' + Settings.BOARDS_URL + board["dir"] + '/">' + str(i) + '</a>] '
      else:
        page_navigator += '[<a href="' + Settings.BOARDS_URL + board["dir"] + '/' + str(i) + '.html">' + str(i) + '</a>] '
  
  if is_omitted:
    page_navigator += "[" + omitted_str + "]"
  
  page_navigator += "</td><td>"

  next = (page_num + 1)
  if next == page_count:
    page_navigator += last_str + "</td>"
  else:
    page_navigator += '<form method="get" action="' + Settings.BOARDS_URL + board["dir"] + '/' + str(next) + '.html"><input value="'+next_str+'" type="submit" /></form></td>'

  return page_navigator

def flood_check(t,post,boardid):
  if not post["parentid"]:
    maxtime = t - Settings.SECONDS_BETWEEN_NEW_THREADS
    lastpost = FetchOne("SELECT COUNT(*) FROM `posts` WHERE `ip` = '%s' and `parentid` = 0 and `boardid` = '%s' and IS_DELETED = 0 AND timestamp > %d" % (str(post["ip"]), boardid, maxtime), 0)
  else:
    maxtime = t - Settings.SECONDS_BETWEEN_REPLIES
    lastpost = FetchOne("SELECT COUNT(*) FROM `posts` WHERE `ip` = '%s' and `parentid` != 0 and `boardid` = '%s' and IS_DELETED = 0 AND timestamp > %d" % (str(post["ip"]), boardid, maxtime), 0)
  
  if int(lastpost[0]):
    raise UserError, _("Flood detected. Please wait a moment before posting again.")

def home_add_post(message, postnum, postid, parentid, file, subject):
  board = Settings._.BOARD
  
  filename = 'templates/latest.html'
  
  f = open(filename, 'r')
  lines = f.readlines()
  f.close()
  
  class_name = 'boardlink'
  
  # use subject if there's one, else shorten the message
  if subject:
    short_message = subject
  else:
    short_message = re.compile(r"<del>(.+)</del>", re.DOTALL | re.IGNORECASE).sub('(spoiler)', message) # Remove spoilers
    short_message = re.compile(r"<[^>]*?>", re.DOTALL | re.IGNORECASE).sub(' ', short_message) # Removes every html tag in the message
    limit = Settings.HOME_LASTPOSTS_LENGTH - len(board['name'])
    
    # short message
    if len(short_message) > limit:
      short_message = short_message.decode('utf-8')[:limit].encode('utf-8') + "..."
      short_message = re.compile(r"&(.(?!;))*$", re.DOTALL | re.IGNORECASE).sub('', short_message) # Removes incomplete HTML entities
  
    short_message = short_message.replace("\n", " ")
    
  if not parentid:
    class_name += ' op'
    parentid = postid
  if file:
    class_name += ' file'
  
  # let's make the link
  if board['board_type'] == '1':
    url = '/%s/read/%s' % (board['dir'], parentid)
    if postnum:
      url += '/%d' % postnum
  else:
    url = '/%s/res/%s.html#%s' % (board['dir'], parentid, postid)
  
  # add to file
  full_str = '%s: <a id="%s|%s" href="%s" class="%s">%s</a><br />\n' % (board['name'], board['id'], postid, url, class_name, short_message)
  lines.insert(0, full_str)
  
  # remove last line
  if len(lines) > Settings.HOME_LASTPOSTS:
    lines.pop()
  
  # write into file
  f = open(filename, 'w')
  f.writelines(lines)
  f.close()

def home_remove_post(postid):
  board = Settings._.BOARD
  
  filename = 'templates/latest.html'

  f = open(filename, 'r')
  lines = f.readlines()
  f.close()
  
  # check if the board|id is in the lines
  id_str = 'id="%s|%s"' % (board['id'], postid)
  changed = False

  f = open(filename, 'w')
  f.writelines(l for l in lines if id_str not in l)
  f.close()

def regenerateHome():
  """
  Update index.html in the boards directory with useful data for users
  """
  logTime("Updating Home")
  t = datetime.datetime.now()
  t -= datetime.timedelta(days=Settings.MAX_DAYS_THREADS)
  t = timestamp(t)
  
  latest_news = FetchAll("SELECT `title`, `message`, `nameblock` FROM `news` WHERE `type` = '1' ORDER BY `timestamp` DESC LIMIT " + str(Settings.HOME_NEWS))
  total_threads = FetchOne("SELECT COUNT(*) FROM `posts` WHERE `parentid` = 0 AND IS_DELETED = 0",0)
  total_replies = FetchOne("SELECT COUNT(*) FROM `posts` WHERE `parentid` > 0 AND IS_DELETED = 0",0)
  total_images = FetchOne("SELECT COUNT(`thumb`) FROM `posts` WHERE CHAR_LENGTH(`thumb`) > 0 AND IS_DELETED = 0",0)
  total_posts = int(total_threads[0]) + int(total_replies[0])
  
  template_values = {
    'header': Settings.SITE_TITLE,
    'logo': Settings.SITE_LOGO,
    'slogan': Settings.SITE_SLOGAN,
    'latest_news': latest_news,
    'total_posts': total_posts,
    'total_threads': total_threads[0],
    'total_replies': total_replies[0],
    'total_images': total_images[0],
    'navbar': False,
  }
  
  page_rendered = renderTemplate('home.html', template_values)
  f = open(Settings.HOME_DIR + "home.html", "w")
  try:
    f.write(page_rendered)
  finally:
    f.close()
  
  if Settings.ENABLE_RSS:
    rss_rendered = renderTemplate('home.rss', template_values)
    f = open(Settings.HOME_DIR + "bai.rss", "w")
    try:
      f.write(rss_rendered)
    finally:
      f.close()

def regenerateNews():
  """
  Update news.html in the boards directory with older news
  """
  posts = FetchAll("SELECT `id`, `title`, `message`, `nameblock` FROM `news` WHERE `type` = '1' ORDER BY `timestamp` DESC")
  template_values = {
    'title': 'Noticias',
    'posts': posts,
    'navbar': False,
    'header': Settings.SITE_TITLE,
    'logo': Settings.SITE_LOGO,
    'slogan': Settings.SITE_SLOGAN,
    'navbar': False,
  }
  
  page_rendered = renderTemplate('news.html', template_values)
  
  f = open(Settings.HOME_DIR + "news.html", "w")
  try:
    f.write(page_rendered)
  finally:
    f.close()

def regenerateAccess():
  if not Settings.HTACCESS_GEN:
    return False
  
  bans = FetchAll("SELECT INET_NTOA(`ip`) AS 'ip', INET_NTOA(`netmask`) AS 'netmask', `boards` FROM `bans` WHERE `blind` = '1'")
  listbans = dict()
  #listbans_global = list()
  
  boarddirs = FetchAll('SELECT `dir` FROM `boards`')
  for board in boarddirs:
    listbans[board['dir']] = list()
  
  for ban in bans:
    ipmask = ban["ip"]
    if ban["netmask"] is not None:
      ipmask += '/' + ban["netmask"]
    
    if ban["boards"] != "":
      boards = pickle.loads(ban["boards"])
      for board in boards:
        listbans[board].append(ipmask)
    else:
      #listbans_global.append(ban["ip"])
      for board in boarddirs:
        listbans[board['dir']].append(ipmask)

  # Generate .htaccess for each board
  for board in listbans.keys():
    template_values = {
      'ips': listbans[board],
      'dir': board,
    }
    
    page_rendered = renderTemplate('htaccess', template_values)
    f = open(Settings.ROOT_DIR + board + "/.htaccess", "w")
    try:
      f.write(page_rendered)
    finally:
      f.close()
      
  return True

def make_redirect(postid, parentid, noko, mobile, timetaken=None):
  board = Settings._.BOARD
  randomPhrase = getRandomLine('quotes.conf')
  
  if not parentid:
    parentid = postid
      
  if mobile:
    url = Settings.CGI_URL + 'mobile/' + board["dir"]
    noko_url = "%s/mobileread/%s#%s" % (Settings.CGI_URL + board["dir"], parentid, postid)
  else:
    url = Settings.BOARDS_URL + board["dir"] + "/"
    noko_url = "%s/res/%s.html#%s" % (Settings.BOARDS_URL + board["dir"], str(parentid), postid)
    
  if noko:
    url = noko_url
      
  return renderTemplate('redirect.html', {'url': url, 'message': randomPhrase, 'timetaken': round(timetaken, 2)})

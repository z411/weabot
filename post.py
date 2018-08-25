# coding=utf-8
import math
import os
import shutil
import time
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
      "file_size": 0,
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
  post = FetchOne("SELECT `id`, `email`, `message`, `locked`, `subject`, `timestamp`, `bumped`, `last` FROM `posts` WHERE `id` = %s AND `parentid` = 0 AND `IS_DELETED` = 0 AND `boardid` = %s LIMIT 1" % (post_id, board_id))
  if post:
    return post
  else:
    raise UserError, _("The ID of the parent post is invalid.")

def getThread(postid=0, mobile=False, timestamp=0):
  board = Settings._.BOARD
  total_bytes = 0
  
  database_lock.acquire()
  try:
    if timestamp:
      cond = "`timestamp` = %s" % str(timestamp)
    else:
      cond = "`id` = %s" % str(postid)

    op_post = FetchOne("SELECT IS_DELETED, email, file, file_size, id, image_height, image_width, ip, message, name, subject, thumb, thumb_height, thumb_width, timestamp_formatted, tripcode, parentid, locked, expires, expires_alert, expires_formatted, timestamp FROM `posts` WHERE %s AND `boardid` = %s AND parentid = 0 LIMIT 1" % (cond, board["id"]))
    if op_post:
      op_post['num'] = 1
      if Settings._.MODBROWSE:
        op_post['ip'] = inet_ntoa(long(op_post['ip']))
      if mobile:
        op_post['timestamp_formatted'] = re.compile(r"\(.{1,3}\)", re.DOTALL | re.IGNORECASE).sub(" ", op_post['timestamp_formatted'])
      thread = {"id": op_post["id"], "posts": [op_post], "omitted": 0}
      #thread = {"id": op_post["id"], "posts": [op_post], "omitted": 0, "omitted_img": 0}
      total_bytes += len(op_post["message"])+80

      replies = FetchAll("SELECT IS_DELETED, email, file, file_size, id, image_height, image_width, ip, message, name, subject, thumb, thumb_height, thumb_width, timestamp_formatted, tripcode, parentid, locked, expires, expires_alert, expires_formatted, timestamp FROM `posts` WHERE `parentid` = %s AND `boardid` = %s ORDER BY `id` ASC" % (op_post["id"], board["id"]))
      thread["length"] = 1
      if replies:
        for reply in replies:
          thread["length"] += 1
          reply['num'] = thread["length"]
          if Settings._.MODBROWSE:
            reply['ip'] = inet_ntoa(long(reply['ip']))
          if mobile:
            reply['message'] = formatting.fixMobileLinks(reply['message'])
            reply['timestamp_formatted'] = re.compile(r"\(.{1,3}\)", re.DOTALL | re.IGNORECASE).sub(" ", reply['timestamp_formatted'])
          thread["posts"].append(reply)
          total_bytes += len(reply["message"])+57
      
      # An imageboard needs subject
      if board["board_type"] in ['1', '5']:
        thread["timestamp"] = op_post["timestamp"]
        thread["subject"] = op_post["subject"]
        thread["message"] = op_post["message"]
        thread["locked"] = op_post["locked"]
        thread["size"] = "%d KB" % int(total_bytes / 1000)
      
      #threads = [thread]
    else:
      return None
  finally:
    database_lock.release()
  
  return thread

def getID(threadid, postnum):
  board = Settings._.BOARD
  
  database_lock.acquire()
  try:
    posts = FetchAll("SELECT id FROM `posts` WHERE `parentid`=%s AND `boardid`=%s ORDER BY `id` ASC" % (thread["id"], board["id"]))
    if posts:
      post = posts[int(postnum)-1]
      postid = post["id"]
    else:
      return None
  finally:
    database_lock.release()
  
  return postid
    
def shortenMsg(message, elid='0', elboard='0'):
  """
  Intenta acortar el mensaje si es necesario
  Algoritmo traducido desde KusabaX
  """
  # 100 chars (ancho) * numline (largo)
  #limit = 2250
  #return False, message

  board = Settings._.BOARD
        
  limit = 100 * int(board['numline'])
  
  message_exploded = message.split('<br />')
  if len(message) > limit or len(message_exploded) > int(board['numline']):
    message_shortened = ''
    for i in range(int(board['numline'])):
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
  if board['board_type'] == '1':
    threads_to_fetch = int(board['numthreads'])
    threads_to_limit = threads_to_fetch + 50
  else:
    if board['dir'] == 'o':
      threads_to_fetch = threads_to_limit = 210
    else:
      threads_to_fetch = threads_to_limit = Settings.THREADS_SHOWN_ON_FRONT
  
  database_lock.acquire()
  try:
    # fetch necessary threads and calculate how many posts we need
    allthreads_query = "SELECT id, timestamp, subject, locked, length FROM `posts` WHERE `boardid` = '%s' AND parentid = 0 AND IS_DELETED = 0 ORDER BY `bumped` DESC, `id` ASC LIMIT %d" % \
      (board["id"], threads_to_limit)
    allthreads = FetchAll(allthreads_query)
    posts_to_fetch = 0
    for t in allthreads[:threads_to_fetch]:
      posts_to_fetch += int(t["length"])
    more_threads = allthreads[threads_to_fetch:50]
    
    # get the needed posts for the front page and order them
    posts_query = "SELECT * FROM `posts` WHERE `boardid` = '%s' ORDER BY `bumped` DESC, CASE parentid WHEN 0 THEN id ELSE parentid END ASC, `id` ASC LIMIT %d" % \
      (board["id"], posts_to_fetch)
    posts = FetchAll(posts_query)
    
    threads = []
    if posts:
      thread = None
      post_num = 0
      
      for post in posts:
        if post["parentid"] == '0':
          skipThread = False
          if post["IS_DELETED"] == '0':
            # OP; Make new thread
            if thread is not None:
              thread["length"] = post_num
              threads.append(thread)
            post_num = post["num"] = 1
            thread = {"id": post["id"], "timestamp": post["timestamp"], "subject": post["subject"], "locked": post["locked"], "posts": [post]}
          else:
            skipThread = True
        else:
          if not skipThread:
            post_num += 1
            post["num"] = post_num
            thread["posts"].append(post)
      
      if post_num:
        thread["length"] = post_num
        threads.append(thread)
  finally:
    database_lock.release()
  
  pages = []
  is_omitted = False
  if len(threads) > 0:
    # Todo : Make this better
    if board['board_type'] == '1':
      page_count = 1 # Front page only
      threads_per_page = int(board['numthreads'])
    else:
      if board['dir'] == 'o':
        front_limit = 210
      else:
        front_limit = Settings.THREADS_SHOWN_ON_FRONT
      
      if len(threads) > front_limit:
        is_omitted = True
      
      page_count = int(math.ceil(float(len(threads)) / float(int(board['numthreads']))))
      threads_per_page = int(board['numthreads'])
    
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
    replylimit = int(board['numcont'])
    
    # Create reply list
    parent = thread["posts"].pop(0)
    replies = thread["posts"]
    thread["omitted"] = 0
    #thread["omitted_img"] = 0
    
    # Omit posts
    while(len(replies) > replylimit):
      post = replies.pop(0)
      thread["omitted"] += 1
      #if post["file"]:
      #  thread["omitted_img"] += 1
    
    # Remake thread with necessary replies only
    replies.insert(0, parent)
    thread["posts"] = replies
    
    # Shorten messages
    for post in thread["posts"]:
      post["shortened"], post["message"] = shortenMsg(post["message"])

  # Build page according to page number
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
  
def threadList(mode=0, sort=''):
  board = Settings._.BOARD

  if mode == 1:
    mobile = True
    maxthreads = 20
    cutFactor = 100
  elif mode == 2:
    mobile = True
    maxthreads = 1000
    cutFactor = 50
  elif mode == 3:
    mobile = True
    maxthreads = 1000 # Settings.MAX_THREADS
    cutFactor = 100
  else:
    mobile = False
    maxthreads = 1000 # Settings.MAX_THREADS
    cutFactor = 70

  q_sort = '`bumped` DESC'
  if sort:
    if sort == '1':
      q_sort = '`timestamp` DESC'
    elif sort == '2':
      q_sort = '`timestamp` ASC'
    elif sort == '3':
      q_sort = '`length` DESC'
    elif sort == '4':
      q_sort = '`length` ASC'

  if board['board_type'] == '1':
    filename = "txt_threadlist.html"
    full_threads = FetchAll("SELECT id, timestamp, timestamp_formatted, subject, length, last FROM `posts` WHERE parentid = 0 AND boardid = %(board)s AND IS_DELETED = 0 ORDER BY %(sort)s LIMIT %(limit)s" \
                           % {'board': board["id"], 'sort': q_sort, 'limit': maxthreads})
  else:
    filename = "threadlist.html"
    full_threads = FetchAll("SELECT p.*, coalesce(x.count,1) AS length, coalesce(x.t,p.timestamp) AS last FROM `posts` AS p LEFT JOIN (SELECT parentid, count(1)+1 as count, max(timestamp) as t FROM `posts` " +\
                "WHERE boardid = %(board)s GROUP BY parentid) AS x ON p.id=x.parentid WHERE p.parentid = 0 AND p.boardid = %(board)s AND p.IS_DELETED = 0 ORDER BY %(sort)s LIMIT %(limit)s" \
                 % {'board': board["id"], 'sort': q_sort, 'limit': maxthreads})
  
  # Generate threadlist
  timestamps = []
  for thread in full_threads:
    if board['board_type'] == '1':
      thread["timestamp_formatted"] = thread["timestamp_formatted"].split(" ")[0]
      timestamps.append([thread["last"], formatTimestamp(thread["last"])])
      if mobile:
        timestamps[-1][1] = re.compile(r"\(.{1,3}\)", re.DOTALL | re.IGNORECASE).sub(" ", timestamps[-1][1])
    else:
      if len(thread['message']) > cutFactor:
        thread['shortened'] = True
      else:
        thread['shortened'] = False
      thread['message'] = thread['message'].replace('<br />', ' ')
      thread['message'] = thread['message'].split("<hr />")[0]
      thread['message'] = re.compile(r"<[^>]*?>", re.DOTALL | re.IGNORECASE).sub('', thread['message'])
      thread['message'] = thread['message'].decode('utf-8')[:cutFactor].encode('utf-8')
      thread['message'] = re.compile(r"&(.(?!;))*$", re.DOTALL | re.IGNORECASE).sub('', thread['message']) # Removes incomplete HTML entities
      thread['timestamp_formatted'] = re.compile(r"\(.{1,3}\)", re.DOTALL | re.IGNORECASE).sub(" ", thread['timestamp_formatted'])
      
      # Get last reply if in mobile mode
      if mode == 1:
        thread['timestamp_formatted'] = re.compile(r"\(.{1,3}\)", re.DOTALL | re.IGNORECASE).sub(" ", thread['timestamp_formatted'])
        lastreply = FetchOne("SELECT * FROM `posts` WHERE parentid = %s AND boardid = %s AND IS_DELETED = 0 ORDER BY `timestamp` DESC LIMIT 1" % (thread['id'], board['id']))
        if lastreply:
          if len(lastreply['message']) > 60:
            lastreply['shortened'] = True
          else:
            lastreply['shortened'] = False
          lastreply['message'] = lastreply['message'].replace('<br />', ' ')
          lastreply['message'] = lastreply['message'].split("<hr />")[0]
          lastreply['message'] = re.compile(r"<[^>]*?>", re.DOTALL | re.IGNORECASE).sub('', lastreply['message'])
          lastreply['message'] = lastreply['message'].decode('utf-8')[:60].encode('utf-8')
          lastreply['message'] = re.compile(r"&(.(?!;))*$", re.DOTALL | re.IGNORECASE).sub('', lastreply['message']) # Removes incomplete HTML entities
          lastreply['timestamp_formatted'] = re.compile(r"\(.{1,3}\)", re.DOTALL | re.IGNORECASE).sub(" ", lastreply['timestamp_formatted'])
          thread["lastreply"] = lastreply
        else:
          thread["lastreply"] = None
      elif mode == 2:
        lastreply = FetchOne("SELECT timestamp_formatted FROM `posts` WHERE parentid = %s AND boardid = %s AND IS_DELETED = 0 ORDER BY `timestamp` DESC LIMIT 1" % (thread['id'], board['id']))
        if lastreply:
          lastreply['timestamp_formatted'] = re.compile(r"\(.{1,3}\)", re.DOTALL | re.IGNORECASE).sub(" ", lastreply['timestamp_formatted'])
        thread["lastreply"] = lastreply

  return renderTemplate(filename, {"more_threads": full_threads, "timestamps": timestamps, "mode": mode, "i_sort": sort}, mobile)

def catalog(sort=''):
  board = Settings._.BOARD
  
  if board['board_type'] != '0':
    raise UserError, "No hay catálogo disponible para esta sección."
    
  cutFactor = 500
  
  q_sort = '`bumped` DESC, `id` ASC'
  if sort:
    if sort == '1':
      q_sort = '`timestamp` DESC'
    elif sort == '2':
      q_sort = '`timestamp` ASC'
    elif sort == '3':
      q_sort = '`length` DESC'
    elif sort == '4':
      q_sort = '`length` ASC'
  
  threads = FetchAll("SELECT id, subject, message, length, thumb, expires_formatted FROM `posts` " +\
                     "WHERE parentid = 0 AND boardid = %(board)s AND IS_DELETED = 0 ORDER BY %(sort)s" \
                     % {'board': board["id"], 'sort': q_sort})
  
  for thread in threads:
    if len(thread['message']) > cutFactor:
      thread['shortened'] = True
    else:
      thread['shortened'] = False
    thread['message'] = thread['message'].replace('<br />', ' ')
    thread['message'] = thread['message'].split("<hr />")[0]
    thread['message'] = re.compile(r"<[^>]*?>", re.DOTALL | re.IGNORECASE).sub('', thread['message'])
    thread['message'] = thread['message'].decode('utf-8')[:cutFactor].encode('utf-8')
    thread['message'] = re.compile(r"&(.(?!;))*$", re.DOTALL | re.IGNORECASE).sub('', thread['message']) # Removes incomplete HTML entities
  
  return renderTemplate("catalog.html", {"threads": threads, "i_sort": sort})
  
def regenerateThreadPage(postid):
  """
  Regenerates /res/#.html for supplied thread id
  """
  board = Settings._.BOARD
  
  thread = getThread(postid)
  
  if board['board_type'] in ['1', '5']:
    template_filename = "txt_thread.html"
    outname = Settings.ROOT_DIR + board["dir"] + "/read/" + str(thread["timestamp"]) + ".html"
    title_matome = thread['subject']
    post_preview = cut_home_msg(thread['posts'][0]['message'], 0)
  else:
    template_filename = "board.html"
    outname = Settings.ROOT_DIR + board["dir"] + "/res/" + str(postid) + ".html"
    post_preview = cut_home_msg(thread['posts'][0]['message'], len(board['name']))
    
    if thread['posts'][0]['subject'] != board['subject']:
      title_matome = thread['posts'][0]['subject']
    else:
      title_matome = post_preview
    
  page = renderTemplate(template_filename, {"threads": [thread], "replythread": postid, "matome": title_matome, "preview": post_preview}, False)
  
  f = open(outname, "w")
  try:
    f.write(page)
  finally:
    f.close()
  
def threadPage(postid, mobile=False, timestamp=0):
  board = Settings._.BOARD
  
  # TODO : Encontrar mejor forma para transformar el IP a string sólo cuando se usa Modbrowse
  
  if board['board_type'] in ['1', '5']:
    template_filename = "txt_thread.html"
  else:
    template_filename = "board.html"
  
  threads = [getThread(postid, mobile, timestamp)]
  
  return renderTemplate(template_filename, {"threads": threads, "replythread": postid}, mobile)

def dynamicRead(parentid, ranges, mobile=False):
  import re
  board = Settings._.BOARD
  
  if board['board_type'] != '1':
    raise UserError, "Esta sección no es un BBS y como tal no soporta lectura dinámica."
  
  # get entire thread
  template_fname = "txt_thread.html"
  thread = getThread(timestamp=parentid, mobile=mobile)
  
  if not thread:
    # Try the archive
    fname = Settings.ROOT_DIR + board["dir"] + "/kako/" + str(parentid) + ".json"
    if os.path.isfile(fname):
      import json
      with open(fname) as f:
        thread = json.load(f)
      thread['posts'] = [dict(zip(thread['keys'], row)) for row in thread['posts']]
      template_fname = "txt_archive.html"
    else:
      raise UserError, 'El hilo no existe.'
  
  filtered_thread = {
    "id": thread['id'],
    "timestamp": thread['timestamp'],
    "length": thread['length'],
    "subject": thread['subject'],
    "locked": thread['locked'],
    "posts": [],
  }
  
  if 'size' in thread:
    filtered_thread['size'] = thread['size']
  
  no_op = False
  if ranges.endswith('n'):
    no_op = True
    ranges = ranges[:-1]
  
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
    if mobile:
      range_n = 50
    else:
      range_n = 100
      
    prev_start = start-range_n
    prev_end = start-1
    next_start = end+1
    next_end = end+range_n
    
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
  
  post_preview = cut_home_msg(filtered_thread["posts"][0]["message"], 0)
  
  # render page
  return renderTemplate(template_fname, {"threads": [filtered_thread], "replythread": parentid, "prevrange": prevrange, "nextrange": nextrange, "preview": post_preview}, mobile, noindex=True)

def regenerateBoard(everything=False):
  """
  Update front pages and every thread res HTML page
  """
  board = Settings._.BOARD
  op_posts = []
  
  if everything:
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
  post = FetchOne("SELECT `id`, `timestamp`, `parentid`, `file`, `thumb`, `password`, `length` FROM `posts` WHERE `boardid` = %s AND `id` = %s LIMIT 1" % (board["id"], str(postid)))
  
  # abort if the post doesn't exist
  if not post:
    raise UserError, _("There isn't a post with this ID. It was probably deleted.")
  
  if password:
    if password != post['password']:
      raise UserError, "No tienes permiso para eliminar este mensaje."
    if post["parentid"] == '0' and int(post["length"]) >= Settings.DELETE_FORBID_LENGTH:
      raise UserError, "No puedes eliminar un hilo con tantas respuestas."
    #if (int(time.time()) - int(post["timestamp"])) > 3600:
    #  raise UserError, "No puedes eliminar un post tan viejo."
  
  # just update the DB if we're deleting only the image
  # otherwise delete the whole post
  if imageonly:
    if post["file"]:
      deleteFile(post)
    
    UpdateDb("UPDATE `posts` SET `file` = '', `file_hex` = '', `thumb` = '', `thumb_width` = 0, `thumb_height` = 0 WHERE `boardid` = %s AND `id` = %s LIMIT 1" % (board["id"], str(post['id'])))
  else:
    if int(post["parentid"]) == 0:
      deleteReplies(post)
    
    logTime("Deleting post " + str(postid))
    if deltype != '0' and post["parentid"] != '0':
      # Soft delete (recycle bin)
      UpdateDb("UPDATE `posts` SET `IS_DELETED` = %s WHERE `boardid` = %s AND `id` = %s LIMIT 1" % (deltype, board["id"], post["id"]))
    else:
      # Hard delete
      if post["file"]:
        deleteFile(post)
        
      UpdateDb("DELETE FROM `posts` WHERE `boardid` = %s AND `id` = %s LIMIT 1" % (board["id"], post["id"]))
      if post['parentid'] != '0':
        UpdateDb("UPDATE `posts` SET length = %d WHERE `id` = '%s' AND `boardid` = '%s'" % (threadNumReplies(post["parentid"]), post["parentid"], board["id"]))
    
    if post['parentid'] == '0':
      if board['board_type'] == '1':
        os.unlink(Settings.ROOT_DIR + board["dir"] + "/read/" + post["timestamp"] + ".html")
      else:
        os.unlink(Settings.ROOT_DIR + board["dir"] + "/res/" + post["id"] + ".html")

    regenerateHome()
  
  # rebuild thread and fronts if reply; rebuild only fronts if not
  if post["parentid"] != '0':
    threadUpdated(post["parentid"])
  else:
    regenerateFrontPages()

def deleteReplies(thread):
  board = Settings._.BOARD
  
  # delete files first
  replies = FetchAll("SELECT `parentid`, `file`, `thumb` FROM `posts` WHERE `boardid` = %s AND `parentid` = %s AND `file` != ''" % (board["id"], thread["id"]))
  for post in replies:
    deleteFile(post)
    
  # delete all replies from DB
  UpdateDb("DELETE FROM `posts` WHERE `boardid` = %s AND `parentid` = %s" % (board["id"], thread["id"]))

def deleteFile(post):
  """
  Unlink file and thumb of supplied post
  """
  board = Settings._.BOARD
  

  try:
    os.unlink(Settings.IMAGES_DIR + board["dir"] + "/src/" + post["file"])
  except:
    pass

  # we don't want to delete mime thumbnails
  if post["thumb"].startswith("mime"):
    return
    
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

def trimThreads():
  """
  Delete any threads which have passed the MAX_THREADS setting
  """
  logTime("Trimming threads")
  board = Settings._.BOARD
  archived = False
  
  # Use limit of the board type
  if board['board_type'] == '1':
    limit = Settings.TXT_MAX_THREADS
  else:
    limit = Settings.MAX_THREADS
  
  # trim expiring threads first
  if board['maxage'] != '0':
    t = time.time()
    
    alert_time = int(round(int(board['maxage']) * Settings.MAX_AGE_ALERT))
    time_limit = t + (alert_time * 86400)
    old_ops = FetchAll("SELECT `id`, `timestamp`, `expires`, `expires_alert`, `length` FROM `posts` WHERE `boardid` = %s AND `parentid` = 0 AND IS_DELETED = 0 AND `expires` > 0 AND `expires` < %s LIMIT 50" % (board['id'], time_limit))
    
    for op in old_ops:
      if t >= int(op['expires']):
        # Trim old threads
        if board['archive'] == '1' and int(op["length"]) >= Settings.ARCHIVE_MIN_LENGTH:
          archiveThread(op["id"])
          archived = True
          
        deletePost(op["id"], None)
      else:
        # Add alert to threads approaching deletion
        UpdateDb("UPDATE `posts` SET expires_alert = 1 WHERE `boardid` = %s AND `id` = %s" % (board['id'], op['id']))
  
  # trim inactive threads next
  if board['maxinactive'] != '0':
    t = time.time()
    
    oldest_last = t - (int(board['maxinactive']) * 86400)
    old_ops = FetchAll("SELECT `id`, `length` FROM `posts` WHERE `boardid` = %s AND `parentid` = 0 AND IS_DELETED = 0 AND `last` < %d LIMIT 50" % (board['id'], oldest_last))
    
    for op in old_ops:
      if board['archive'] == '1' and int(op["length"]) >= Settings.ARCHIVE_MIN_LENGTH:
        archiveThread(op["id"])
        archived = True
      
      deletePost(op["id"], None)
      
  # select trim type by board
  if board['board_type'] == '1':
    trim_method = Settings.TXT_TRIM_METHOD
  else:
    trim_method = Settings.TRIM_METHOD
    
  # select order by trim
  if trim_method == 1:
    order = 'last DESC'
  elif trim_method == 2:
    order = 'bumped DESC'
  else:
    order = 'timestamp DESC'
  
  # Trim the last thread
  op_posts = FetchAll("SELECT `id`, `length` FROM `posts` WHERE `boardid` = %s AND `parentid` = 0 AND IS_DELETED = 0 ORDER BY %s" % (board["id"], order))
  if len(op_posts) > limit:
    posts = op_posts[limit:]
    for post in posts:
      if board['archive'] == '1' and int(op["length"]) >= Settings.ARCHIVE_MIN_LENGTH:
        archiveThread(post["id"])
        archived = True
        
      deletePost(post["id"], None)
      pass
  
  if archived:
    regenerateKako()
  
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
    notice_post["message"] = "El hilo ha llegado al límite de respuestas.<br />Si quieres continuarlo, por favor crea otro."
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
  
  # TODO nijigen HACK
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
    page_navigator += '<form method="get" action="' + Settings.BOARDS_URL + board["dir"] + '/' + previous + '"><input value="'+previous_str+'" type="submit" class="psei" /></form>'

  page_navigator += "</td><td>"

  for i in xrange(page_count):
    if i == page_num:
      page_navigator += "[<strong>%d</strong>]" % i
    else:
      if i == 0:
        page_navigator += '[<a href="%s%s/">%d</a>]' % (Settings.BOARDS_URL, board['dir'], i)
      else:
        page_navigator += '[<a href="%s%s/%d.html">%d</a>]' % (Settings.BOARDS_URL, board['dir'], i, i)

    if i > 0 and (i % 10) == 0 and not is_omitted:
      page_navigator += '<br />'
    elif i < 10:
      page_navigator += '&nbsp;'
  
  if is_omitted:
    page_navigator += "[" + omitted_str + "]"
  
  page_navigator += "</td><td>"

  next = (page_num + 1)
  if next == page_count:
    page_navigator += last_str + "</td>"
  else:
    page_navigator += '<form method="get" action="' + Settings.BOARDS_URL + board["dir"] + '/' + str(next) + '.html"><input value="'+next_str+'" type="submit" class="psei" /></form></td>'

  return page_navigator

def flood_check(t,post,boardid):
  board = Settings._.BOARD

  if not post["parentid"]:
    maxtime = t - int(board['threadsecs'])
    #lastpost = FetchOne("SELECT COUNT(*) FROM `posts` WHERE `ip` = '%s' and `parentid` = 0 and `boardid` = '%s' and IS_DELETED = 0 AND timestamp > %d" % (str(post["ip"]), boardid, maxtime), 0)
    
    # NO MATTER THE IP
    lastpost = FetchOne("SELECT COUNT(*) FROM `posts` WHERE `parentid` = 0 and `boardid` = '%s' and IS_DELETED = 0 AND timestamp > %d" % (boardid, maxtime), 0)
    pass
  else:
    maxtime = t - int(board['postsecs'])
    lastpost = FetchOne("SELECT COUNT(*) FROM `posts` WHERE `ip` = '%s' and `parentid` != 0 and `boardid` = '%s' and IS_DELETED = 0 AND timestamp > %d" % (str(post["ip"]), boardid, maxtime), 0)
  
  if int(lastpost[0]):
    if post["parentid"]:
      raise UserError, _("Flood detected. Please wait a moment before posting again.")
    else:
      lastpost = FetchOne("SELECT `timestamp` FROM `posts` WHERE `parentid`=0 and `boardid`='%s' and IS_DELETED = 0 ORDER BY `timestamp` DESC" % (boardid), 0)
      wait = int(int(board['threadsecs']) - (t - int(lastpost[0])))
      raise UserError, "Por favor espera " + str(wait) + " segundos antes de crear otro hilo."

def cut_home_msg(message, boardlength=0):
  short_message = message.replace("<br />", " ")
  short_message = short_message.split("<hr />")[0]
  short_message = re.compile(r"<[^>]*?>", re.DOTALL | re.IGNORECASE).sub("", short_message) # Removes HTML tags
  limit = Settings.HOME_LASTPOSTS_LENGTH - boardlength

  if len(short_message) > limit:
    if isinstance(short_message, unicode):
      short_message = short_message[:limit].encode('utf-8') + "…"
    else:
      short_message = short_message.decode('utf-8')[:limit].encode('utf-8') + "…"
    short_message = re.compile(r"&(.(?!;))*$", re.DOTALL | re.IGNORECASE).sub("", short_message) # Removes incomplete HTML entities
  return short_message

def getLastAge(limit):
  threads = []
  sql = "SELECT posts.id, boards.name AS board_fulln, boards.subname AS board_name, board_type, boards.dir, timestamp, posts.timestamp_formatted, bumped, length, CASE WHEN posts.subject = boards.subject THEN posts.message ELSE posts.subject END AS content FROM posts INNER JOIN boards ON boardid = boards.id WHERE parentid = 0 AND IS_DELETED = 0 AND boards.secret = 0 AND posts.locked = 0 ORDER BY bumped DESC LIMIT %d" % limit
  threads = FetchAll(sql)
  
  for post in threads:
    post['id'] = int(post['id'])
    post['bumped'] = int(post['bumped'])
    post['length'] = int(post['length'])
    post['board_type'] = int(post['board_type'])
    post['timestamp_formatted'] = formatTimestamp(post['bumped'], True)
    post['timestamp_formatted'] = post['timestamp_formatted'][:8] + ' ' + post['timestamp_formatted'][13:]
    post['timestamp'] = int(post['timestamp'])
    post['content'] = cut_home_msg(post['content'], 0)

    if post['board_type'] == 1:
      post['url'] = '/%s/read/%d/l10' % (post['dir'], post['timestamp'])
    else:
      post['url'] = '/%s/res/%d.html' % (post['dir'], post['id'])
      
  return threads
  
def getNewThreads(limit):
  threads = []
  sql = "SELECT posts.id, boards.name AS board_fulln, boards.subname AS board_name, board_type, boards.dir, timestamp, CASE WHEN posts.subject = boards.subject THEN posts.message ELSE posts.subject END AS content FROM posts INNER JOIN boards ON boardid = boards.id WHERE parentid = 0 AND IS_DELETED = 0 AND boards.secret = 0 AND posts.locked = 0 ORDER BY timestamp DESC LIMIT %d" % limit
  threads = FetchAll(sql)
  
  for post in threads:
    post['id'] = int(post['id'])
    post['board_type'] = int(post['board_type'])
    post['timestamp'] = int(post['timestamp'])
    post['timestamp_formatted'] = formatTimestamp(post['timestamp'], True)
    post['timestamp_formatted'] = post['timestamp_formatted'][:8] + ' ' + post['timestamp_formatted'][13:]
    post['content'] = cut_home_msg(post['content'], 0)

    if post['board_type'] == 1:
      post['url'] = '/%s/read/%d' % (post['dir'], post['timestamp'])
    else:
      post['url'] = '/%s/res/%d.html' % (post['dir'], post['id'])
      
  return threads

def regenerateHome():
  """
  Update index.html in the boards directory with useful data for users
  """
  logTime("Updating home")
  t = datetime.datetime.now()

  latest_news = FetchAll("SELECT `timestamp`, `message`, `timestamp_formatted` FROM `news` WHERE `type` = '2' ORDER BY `timestamp` DESC LIMIT " + str(Settings.HOME_NEWS))
  latest_age = getLastAge(Settings.HOME_LASTPOSTS)
  new_threads = getNewThreads(Settings.HOME_LASTPOSTS)
  
  template_values = {
    'header': Settings.SITE_TITLE,
    'slogan': Settings.SITE_SLOGAN,
    'latest_news': latest_news,
    'latest_age': latest_age,
    'latest_age_num': Settings.HOME_LASTPOSTS,
    'new_threads': new_threads,
  }
  
  page_rendered = renderTemplate('home.html', template_values)
  f = open(Settings.HOME_DIR + "home.html", "w")
  try:
    f.write(page_rendered)
  finally:
    f.close()
  
  if Settings.ENABLE_RSS:
    rss_rendered = renderTemplate('home.rss', {'latest_age': latest_age})
    f = open(Settings.HOME_DIR + "bai.rss", "w")
    try:
      f.write(rss_rendered)
    finally:
      f.close()

def regenerateNews():
  """
  Update news.html in the boards directory with older news
  """
  posts = FetchAll("SELECT * FROM `news` WHERE `type` = '1' ORDER BY `timestamp` DESC")
  template_values = {
    'title': 'Noticias',
    'posts': posts,
    'header': Settings.SITE_TITLE,
    'slogan': Settings.SITE_SLOGAN,
    'navbar': False,
  }
  
  page_rendered = renderTemplate('news.html', template_values)
  
  f = open(Settings.HOME_DIR + "noticias.html", "w")
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
        if board['dir'] not in Settings.EXCLUDE_GLOBAL_BANS:
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
  
def regenerateKako():
  board = Settings._.BOARD
  
  threads = FetchAll("SELECT * FROM archive WHERE boardid = %s ORDER BY timestamp DESC" % board['id'])
  page = renderTemplate('kako.html', {'threads': threads})
  with open(Settings.ROOT_DIR + board["dir"] + "/kako/index.html", "w") as f:
    f.write(page)

def make_url(postid, post, parent_post, noko, mobile):
  board = Settings._.BOARD
  
  parentid = post["parentid"]
  if not parentid:
    parentid = postid
      
  if mobile:
    url = Settings.CGI_URL + 'mobile/' + board["dir"]
    if board["board_type"] == '1':
      noko_url = "%s/mobileread/%s/%s/l10" % (Settings.CGI_URL, board["dir"], parent_post['timestamp'])
    else:
      noko_url = "%s/mobileread/%s/%s#%s" % (Settings.CGI_URL, board["dir"], parentid, postid)
  else:
    url = Settings.BOARDS_URL + board["dir"] + "/"
    if board["board_type"] == '1':
      noko_url = "%s/read/%s/l50" % (Settings.BOARDS_URL + board["dir"], str(parent_post['timestamp']))
    else:
      noko_url = "%s/res/%s.html#%s" % (Settings.BOARDS_URL + board["dir"], str(parentid), postid)
    
  if noko:
    url = noko_url
    
  return url

def make_redirect(url, timetaken=None):
  board = Settings._.BOARD
  randomPhrase = getRandomLine('quotes.conf')
  
  return renderTemplate('redirect.html', {'url': url, 'message': randomPhrase, 'timetaken': timetaken})
  
def archiveThread(postid):
  import json
  board = Settings._.BOARD
  
  thread = getThread(postid, False)
  post_preview = cut_home_msg(thread['posts'][0]['message'], 0)
  
  page = renderTemplate("txt_archive.html", {"threads": [thread], "replythread": postid, "preview": post_preview}, False)
  with open(Settings.ROOT_DIR + board["dir"] + "/kako/" + str(thread['timestamp']) + ".html", "w") as f:
    f.write(page)
  
  thread['keys'] = ['num', 'IS_DELETED', 'name', 'tripcode', 'email', 'message', 'timestamp_formatted']
  thread['posts'] = [[row[key] for key in thread['keys']] for row in thread['posts']]
  try:
    with open(Settings.ROOT_DIR + board["dir"] + "/kako/" + str(thread['timestamp']) + ".json", "w") as f:
      json.dump(thread, f, indent=0)
  except:
    raise UserError, "Can't archive: %s" % thread['timestamp']
  
  UpdateDb("REPLACE INTO archive (id, boardid, timestamp, subject, length) VALUES ('%s', '%s', '%s', '%s', '%s')" % (thread['id'], board['id'], thread['timestamp'], _mysql.escape_string(thread['subject']), thread['length']))

def discord_hook(post, url):
  import urllib2
  import json
  
  board = Settings._.BOARD
  
  WEBHOOK_URL = "https://discordapp.com/api/webhooks/428025764974166018/msYu1-R3JRnG-cxrhAu3J7LbIPvzpBlJwbW5PFe5VEQaxVzjros9CXOpjZDahUE42Jgn"

  data = {"content": "",
    "ts": post['timestamp'],
    "embeds": [{
        "title": post['subject'],
        "description": cut_home_msg(post['message'], 30),
        "url": "https://bienvenidoainternet.org" + url,
        "color": 11910504,
        "timestamp": "2018-03-27T03:22:18.572Z",
        "footer": {
          "text": board['name']
        },
        "thumbnail": {
          "url": "https://bienvenidoainternet.org/%s/thumb/%s" % (board['dir'], post['thumb'])
        },
        "author": {
          "name": "Nuevo hilo",
          "icon_url": "https://bienvenidoainternet.org/0/junk/w/shobon.gif"
        }}]
    }
  
  jsondata = json.dumps(data, separators=(',',':'))
  
  #with open('log', 'a') as f:
  #  f.write(jsondata)
  
  opener = urllib2.build_opener()
  opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:59.0) Gecko/20100101 Firefox/59.0')]
  response = opener.open(WEBHOOK_URL, jsondata, 6)
  the_page = response.read()
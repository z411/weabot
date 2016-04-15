# coding=utf-8
import json
import _mysql
import time

from framework import *
from database import *
from post import *

def api(self, path_split):
  if len(path_split) > 2:
    try:
      self.output = api_process(self.formdata, path_split)
    except APIError, e:
      self.output = api_error("error", e.message)
    except UserError, e:
      self.output = api_error("failed", e.message)
  else:
    self.output = api_error("error", "No method specified")

def api_process(formdata, path_split):
  t = time.time()
  values = {'state': 'success'}
  
  if path_split[2] == 'boards':
    boards = FetchAll('SELECT dir, name, board_type FROM `boards` WHERE `secret` = 0 ORDER BY `dir`')
    values['boards'] = boards
  elif path_split[2] == 'last':
    data_limit = formdata.get('limit')
    
    limit = 10
    
    if data_limit:
      try:
        limit = int(data_limit)
      except ValueError:
        raise APIError, "Limit must be numeric"
        
    if limit > 50:
      raise APIError, "Maximum limit is 50"
    
    sql = "SELECT posts.id, boards.dir, timestamp, timestamp_formatted, posts.name, tripcode, email, posts.subject, posts.message, file, file_size, image_height, image_width, thumb, thumb_width, thumb_height, parentid FROM posts INNER JOIN boards ON boardid = boards.id WHERE IS_DELETED = 0 AND boards.secret = 0 ORDER BY timestamp DESC LIMIT %d" % limit
    values['posts'] = FetchAll(sql)
    
    for post in values['posts']:
      post['id'] = int(post['id'])
      post['timestamp'] = int(post['timestamp'])
      post['parentid'] = int(post['parentid'])
      post['file_size'] = int(post['file_size'])
      post['image_width'] = int(post['image_width'])
      post['image_height'] = int(post['image_height'])
      post['thumb_width'] = int(post['thumb_width'])
      post['thumb_height'] = int(post['thumb_height'])
  elif path_split[2] == 'lastage':
    data_limit = formdata.get('limit')
    
    limit = 25
    
    if data_limit:
      try:
        limit = int(data_limit)
      except ValueError:
        raise APIError, "Limit must be numeric"
        
    if limit > 50:
      raise APIError, "Maximum limit is 50"
    
    values['threads'] = getLastAge(limit)
  elif path_split[2] == 'list':
    data_board = formdata.get('dir')
    data_offset = formdata.get('offset')
    data_limit = formdata.get('limit')
    data_replies = formdata.get('replies')
    offset = 0
    limit = 10
    numreplies = 2
    
    if not data_board:
      raise APIError, "Missing parameters"
      
    if data_limit:
      try:
        limit = int(data_limit)
      except ValueError:
        raise APIError, "Limit must be numeric"
        
    if data_offset:
      try:
        offset = int(data_offset)
      except ValueError:
        raise APIError, "Offset must be numeric"
        
    if data_replies:
      try:
        numreplies = int (data_replies)
      except ValueError:
        raise APIError, "Replies must be numeric"
        
    if data_replies and limit > 30:
      raise APIError, "Maximum limit is 30"
        
    board = setBoard(data_board)
    
    #sql = "SELECT id, timestamp, bumped, timestamp_formatted, name, tripcode, email, subject, message, file, thumb FROM posts WHERE boardid = %s AND parentid = 0 AND IS_DELETED = 0 ORDER BY bumped DESC LIMIT %d" % (board['id'], limit)
    
    
    sql = "SELECT p.id, p.timestamp, p.bumped, p.expires, p.expires_formatted, p.timestamp_formatted, p.name, p.tripcode, p.email, p.subject, p.message, p.file, p.file_size, p.image_width, p.image_height, p.thumb, p.thumb_height, p.thumb_width, p.locked, coalesce(x.count,0) AS total_replies, coalesce(x.files,0) AS total_files FROM `posts` AS p LEFT JOIN (SELECT parentid, count(1) as count, count(nullif(file, '')) as files FROM `posts` WHERE boardid = %(board)s GROUP BY parentid) AS x ON p.id=x.parentid WHERE p.parentid = 0 AND p.boardid = %(board)s AND p.IS_DELETED = 0 ORDER BY `bumped` DESC LIMIT %(limit)d OFFSET %(offset)d" % {'board': board["id"], 'limit': limit, 'offset': offset}
                           
    threads = FetchAll(sql)
    
    if numreplies:
      for thread in threads:
        lastreplies = FetchAll("SELECT id, timestamp, timestamp_formatted, name, tripcode, email, subject, message, file, file_size, image_height, image_width, thumb, thumb_width, thumb_height, IS_DELETED FROM `posts` WHERE parentid = %s AND boardid = %s ORDER BY `timestamp` DESC LIMIT %d" % (thread['id'], board['id'], numreplies))
        lastreplies = lastreplies[::-1]
        thread['id'] = int(thread['id'])
        thread['timestamp'] = int(thread['timestamp'])
        thread['bumped'] = int(thread['bumped'])
        thread['expires'] = int(thread['expires'])
        thread['total_replies'] = int(thread['total_replies'])
        thread['total_files'] = int(thread['total_files'])
        thread['file_size'] = int(thread['file_size'])
        thread['image_width'] = int(thread['image_width'])
        thread['image_height'] = int(thread['image_height'])
        thread['thumb_width'] = int(thread['thumb_width'])
        thread['thumb_height'] = int(thread['thumb_height'])
        thread['locked'] = int(thread['locked'])
        
        thread['replies'] = []
        
        for post in lastreplies:
          post['IS_DELETED'] = int(post['IS_DELETED'])
          post['id'] = int(post['id'])
          post['timestamp'] = int(post['timestamp'])
          
          if post['IS_DELETED']:
            empty_post = {'id': post['id'],
                    'IS_DELETED': post['IS_DELETED'],
                    'timestamp': post['timestamp'],
                    }
            thread['replies'].append(empty_post)
          else:  
            post['file_size'] = int(post['file_size'])
            post['image_width'] = int(post['image_width'])
            post['image_height'] = int(post['image_height'])
            post['thumb_width'] = int(post['thumb_width'])
            post['thumb_height'] = int(post['thumb_height'])
          
            thread['replies'].append(post)
    
    values['threads'] = threads
  elif path_split[2] == 'thread':
    data_board = formdata.get('dir')
    data_threadid = formdata.get('id')
    data_offset = formdata.get('offset')
    data_limit = formdata.get('limit')
    offset = 0
    limit = 1000
    
    if not data_board or not data_threadid:
      raise APIError, "Missing parameters"
    
    if data_limit:
      try:
        limit = int(data_limit)
      except ValueError:
        raise APIError, "Limit must be numeric"
        
    if data_offset:
      try:
        offset = int(data_offset)
      except ValueError:
        raise APIError, "Offset must be numeric"
    
    board = setBoard(data_board)
    
    try:
      threadid = int(data_threadid)
    except ValueError:
      raise APIError, "Thread ID must be numeric"
      
    if not threadid:
      raise APIError, "No thread ID"
    
    op_post = FetchOne("SELECT id, timestamp, subject, locked FROM posts WHERE id = '%d' AND boardid = '%s' AND parentid = 0" % (threadid, board["id"]))
    
    if not op_post:
      raise APIError, "Not a thread"
      
    values['id'] = int(op_post['id'])
    values['timestamp'] = int(op_post['timestamp'])
    values['subject'] = op_post['subject']
    values['locked'] = int(op_post['locked'])
    
    total_replies = int(FetchOne("SELECT COUNT(1) FROM posts WHERE boardid = '%s' AND parentid = '%d'" % (board["id"], threadid), 0)[0])
    
    values['total_replies'] = total_replies
    
    sql = "SELECT id, parentid, timestamp, timestamp_formatted, name, tripcode, email, subject, message, file, file_size, image_width, image_height, thumb, thumb_width, thumb_height, IS_DELETED FROM posts WHERE boardid = %s AND (parentid = %s OR id = %s) ORDER BY id ASC LIMIT %d OFFSET %d" % (_mysql.escape_string(board['id']), threadid, threadid, limit, offset)
    posts = FetchAll(sql)
    
    values['posts'] = []
    
    for post in posts:
      post['IS_DELETED'] = int(post['IS_DELETED'])
      post['id'] = int(post['id'])
      post['parentid'] = int(post['parentid'])
      post['timestamp'] = int(post['timestamp'])
      
      if post['IS_DELETED']:
        empty_post = {'id': post['id'],
                'IS_DELETED': post['IS_DELETED'],
                'parentid': post['parentid'],
                'timestamp': post['timestamp'],
                }
        values['posts'].append(empty_post)
      else:  
        post['file_size'] = int(post['file_size'])
        post['image_width'] = int(post['image_width'])
        post['image_height'] = int(post['image_height'])
        post['thumb_width'] = int(post['thumb_width'])
        post['thumb_height'] = int(post['thumb_height'])
        values['posts'].append(post)
  elif path_split[2] == 'delete':
    data_board = formdata.get('dir')
    data_postid = formdata.get('id')
    data_imageonly = formdata.get('imageonly')
    data_password = formdata.get('password')
    
    if not data_board or not data_postid or not data_password:
      raise APIError, "Missing parameters"
      
    imageonly = False
    board = setBoard(data_board)
    
    try:
      postid = int(data_postid)
    except ValueError:
      raise APIError, "Post ID must be numeric"
    
    if data_imageonly and data_imageonly == 1:
      imageonly = True
    
    deletePost(postid, data_password, board['recyclebin'], imageonly)
  else:
    raise APIError, "Invalid method"
  
  values['time'] = int(t)
  values['time_taken'] = time.time() - t
  return json.dumps(values, sort_keys=True, separators=(',',':'))
  
def api_error(errtype, msg):
  values = {'state': errtype, 'message': msg}
  return json.dumps(values)
  
class APIError(Exception):
  pass
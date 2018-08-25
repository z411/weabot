# coding=utf-8
import _mysql
from database import *
from framework import *
from template import *
from img import *
from post import *
from settings import Settings

d_thread = {}
d_post = {}

def anarkia(self, path_split):
  setBoard('anarkia')
  
  if len(path_split) <= 2:
    self.output = main()
    return
    
  #raise UserError, 'Ya fue, baisano...'
  
  if path_split[2] == 'opt':
    self.output = boardoptions(self.formdata)
  elif path_split[2] == 'mod':
    self.output = mod(self.formdata)
  elif path_split[2] == 'bans':
    self.output = bans(self.formdata)
  elif path_split[2] == 'css':
    self.output = css(self.formdata)
  elif path_split[2] == 'type':
    self.output = type(self.formdata)
  elif path_split[2] == 'emojis':
    self.output = emojis(self.formdata)
  else:
    raise UserError, 'ke?'

def main():
  board = Settings._.BOARD
  
  logs = FetchAll("SELECT * FROM `logs` WHERE `staff` = 'Anarko' ORDER BY `timestamp` DESC")
  for log in logs:
    log['timestamp_formatted'] = formatTimestamp(log['timestamp'])
  
  return renderTemplate('anarkia.html', {'mode': 0, 'logs': logs})

def type(formdata):
  board = Settings._.BOARD
  
  if board['board_type'] == '1':
    (type_now, type_do, do_num) = ('BBS', 'IB', '0')
  else:
    (type_now, type_do, do_num) = ('IB', 'BBS', '1')
    
  if formdata.get('transform') == 'do':
    t = 0
    try:
      with open('anarkia_time') as f:
        t = int(f.read())
    except IOError:
      pass
    
    dif = time.time() - t
    if dif > (10 * 60):
    #if True:
      import re
      t = time.time()
      
      board['board_type'] = do_num
      board['force_css'] = Settings.HOME_URL + 'anarkia/style_' + type_do.lower() + '.css'
      updateBoardSettings()
      
      # update posts
      fix_board()
      
      # regenerate
      setBoard('anarkia')
      regenerateBoard(True)
      
      tf = timeTaken(t, time.time())
    
      with open('anarkia_time', 'w') as f:
        t = f.write(str(int(time.time())))
        
      msg = 'Cambiada estructura de sección a %s. (%s)' % (type_do, tf)
      logAction(msg)
      return renderTemplate('anarkia.html', {'mode': 99, 'msg': msg})
    else:
      raise UserError, 'Esta acción sólo se puede realizar cada 10 minutos. Faltan: %d mins.' % (10-int(dif/60))
    
  return renderTemplate('anarkia.html', {'mode': 7, 'type_now': type_now, 'type_do': type_do})

def fix_board():
  board = Settings._.BOARD
  get_fix_dictionary()
  
  if board['board_type'] == '1':
    to_fix = FetchAll("SELECT * FROM posts WHERE message LIKE '%%anarkia/res/%%' AND boardid = %s" % board['id'])
  else:
    to_fix = FetchAll("SELECT * FROM posts WHERE message LIKE '%%anarkia/read/%%' AND boardid = %s" % board['id'])
    
  for p in to_fix:
    try:
      if board['board_type'] == '1':
        newmessage = re.sub(r'/anarkia/res/(\d+).html#(\d+)">&gt;&gt;(\d+)', fix_to_bbs, p['message'])
      else:
        newmessage = re.sub(r'/anarkia/read/(\d+)/(\d+)">&gt;&gt;(\d+)', fix_to_ib, p['message'])
        
      UpdateDb("UPDATE posts SET message = '%s' WHERE boardid = %s AND id = %s" % \
        (_mysql.escape_string(newmessage), board['id'], p['id']))
    except KeyError:
      pass
    
  return True

def fix_to_bbs(matchobj):
  threadid = matchobj.group(1)
  pid = matchobj.group(2)
  new_thread = d_thread[threadid]
  new_post = d_post[new_thread][pid]
  return '/anarkia/read/%s/%s">&gt;&gt;%s' % (new_thread, new_post, new_post)
  
def fix_to_ib(matchobj):
  threadid = matchobj.group(1)
  num = int(matchobj.group(2))
  new_thread = d_thread[threadid]
  new_post = d_post[new_thread][num]
  return '/anarkia/res/%s.html#%s">&gt;&gt;%s' % (new_thread, new_post, new_post)
  
def get_fix_dictionary():
  global d_thread, d_post
  board = Settings._.BOARD
  res = FetchAll("SELECT id, timestamp, parentid FROM posts WHERE boardid = %s ORDER BY CASE parentid WHEN 0 THEN id ELSE parentid END ASC, `id` ASC" % board['id'])
  num = 1
  thread = 0
  for p in res:
    pid = p['id']
    if p['parentid'] == '0':
      num = 1
      
      time = p['timestamp']
      if board['board_type'] == '1':
        d_thread[pid] = time
        thread = time
      else:
        d_thread[time] = pid
        thread = pid
      
      d_post[thread] = {}
      
    if board['board_type'] == '1':
      d_post[thread][pid] = num
    else:
      d_post[thread][num] = pid
    num += 1
      
  return
    
def css(formdata):
  board = Settings._.BOARD
  
  if board['board_type'] == '1':
    basename = 'style_bbs.css'
  else:
    basename = 'style_ib.css'
    
  fname = '%sanarkia/%s' % (Settings.HOME_DIR, basename)
    
  if formdata.get('cssfile'):
    with open(fname, 'w') as f:
      cssfile = f.write(formdata['cssfile'])
      
    msg = 'CSS actualizado.'
    logAction(msg)
    return renderTemplate('anarkia.html', {'mode': 99, 'msg': msg})
    
  with open(fname) as f:
    cssfile = f.read()
  
  return renderTemplate('anarkia.html', {'mode': 6, 'basename': basename, 'cssfile': cssfile})
  
def bans(formdata):
  board = Settings._.BOARD
  
  if formdata.get('unban'):
    unban = int(formdata['unban'])
    boardpickle = pickle.dumps(['anarkia'])
    
    ban = FetchOne("SELECT * FROM `bans` WHERE id = %d" % unban)
    if not ban:
      raise UserError, "Ban inválido."
    if ban['boards'] != boardpickle:
      raise USerError, "Ban inválido."
      
    UpdateDb('DELETE FROM `bans` WHERE id = %s' % ban['id'])
    logAction("Usuario %s desbaneado." % ban['ip'][:4])
    regenerateAccess()
    
  bans = FetchAll('SELECT * FROM `bans` WHERE staff = \'anarko\'')
  for ban in bans:
    ban['added'] = formatTimestamp(ban['added'])
    if ban['until'] == '0':
      ban['until'] = _('Does not expire')
    else:
      ban['until'] = formatTimestamp(ban['until'])
  return renderTemplate('anarkia.html', {'mode': 5, 'bans': bans})
  
def mod(formdata):
  board = Settings._.BOARD
  
  if formdata.get('thread'):
    parentid = int(formdata['thread'])
    posts = FetchAll('SELECT * FROM `posts` WHERE (parentid = %d OR id = %d) AND boardid = %s ORDER BY `id` ASC' % (parentid, parentid, board['id']))
    return renderTemplate('anarkia.html', {'mode': 3, 'posts': posts})
  elif formdata.get('lock'):
    postid = int(formdata['lock'])
    post = FetchOne('SELECT id, locked FROM posts WHERE boardid = %s AND id = %d AND parentid = 0 LIMIT 1' % (board['id'], postid))
    if post['locked'] == '0':
      setLocked = 1
      msg = "Hilo %s cerrado." % post['id']
    else:
      setLocked = 0
      msg = "Hilo %s abierto." % post['id']
            
    UpdateDb("UPDATE `posts` SET `locked` = %d WHERE `boardid` = '%s' AND `id` = '%s' LIMIT 1" % (setLocked, board["id"], post["id"]))
    threadUpdated(post['id'])
    logAction(msg)
    return renderTemplate('anarkia.html', {'mode': 99, 'msg': msg})
  elif formdata.get('del'):
    postid = int(formdata['del'])
    post = FetchOne('SELECT id, parentid FROM posts WHERE boardid = %s AND id = %d LIMIT 1' % (board['id'], postid))
    if post['parentid'] != '0':
      deletePost(post['id'], None, '3', False)
      msg = "Mensaje %s eliminado." % post['id']
      logAction(msg)
      return renderTemplate('anarkia.html', {'mode': 99, 'msg': msg})
    else:
      raise UserError, "jaj no"
  elif formdata.get('restore'):
    postid = int(formdata['restore'])
    post = FetchOne('SELECT id, parentid FROM posts WHERE boardid = %s AND id = %d LIMIT 1' % (board['id'], postid))
    
    UpdateDb('UPDATE `posts` SET `IS_DELETED` = 0 WHERE `boardid` = %s AND `id` = %s LIMIT 1' % (board['id'], post['id']))
    if post['parentid'] != '0':
      threadUpdated(post['parentid'])
    else:
      regenerateFrontPages()
    msg = "Mensaje %s recuperado." % post['id']
    logAction(msg)
    return renderTemplate('anarkia.html', {'mode': 99, 'msg': msg})
  elif formdata.get('ban'):
    postid = int(formdata['ban'])
    post = FetchOne('SELECT id, ip FROM posts WHERE boardid = %s AND id = %d LIMIT 1' % (board['id'], postid))
    
    return renderTemplate('anarkia.html', {'mode': 4, 'post': post})
  elif formdata.get('banto'):
    postid = int(formdata['banto'])
    post = FetchOne('SELECT id, message, parentid, ip FROM posts WHERE boardid = %s AND id = %d LIMIT 1' % (board['id'], postid))
  
    reason = formdata.get('reason').replace('script', '').replace('meta', '')
    if reason is not None:
      if formdata['seconds'] != '0':
        until = str(timestamp() + int(formdata['seconds']))
      else:
        until = '0'
      where = pickle.dumps(['anarkia'])

      ban = FetchOne("SELECT `id` FROM `bans` WHERE `ip` = '" + post['ip'] + "' AND `boards` = '" + _mysql.escape_string(where) + "' LIMIT 1")
      if ban:
        raise UserError, "Este usuario ya esta baneado."
      
      # Blind mode
      if formdata.get('blind') == '1':
        blind = '1'
      else:
        blind = '0'
      
      InsertDb("INSERT INTO `bans` (`ip`, `netmask`, `boards`, `added`, `until`, `staff`, `reason`, `blind`) VALUES ('" + post['ip'] + "', INET_ATON('255.255.255.255'), '" + _mysql.escape_string(where) + "', " + str(timestamp()) + ", " + until + ", 'anarko', '" + _mysql.escape_string(formdata['reason']) + "', '"+blind+"')")
      
      newmessage = post['message'] + '<hr /><span class="banned">A este usuario se le revocó el acceso. Razón: %s</span>' % reason
      
      UpdateDb("UPDATE posts SET message = '%s' WHERE boardid = %s AND id = %s" % (_mysql.escape_string(newmessage), board['id'], post['id']))
      if post['parentid'] != '0':
        threadUpdated(post['parentid'])
      else:
        regenerateFrontPages()
      regenerateAccess()
      
      msg = "Usuario %s baneado." % post['ip'][:4]
      logAction(msg)
      return renderTemplate('anarkia.html', {'mode': 99, 'msg': msg})
  else:
    reports = FetchAll("SELECT * FROM `reports` WHERE board = 'anarkia'")
    threads = FetchAll('SELECT * FROM `posts` WHERE boardid = %s AND parentid = 0 ORDER BY `bumped` DESC' % board['id'])
    return renderTemplate('anarkia.html', {'mode': 2, 'threads': threads, 'reports': reports})
    
def boardoptions(formdata):
  board = Settings._.BOARD
  
  if formdata.get('longname'):
    # submitted
    board['longname'] = formdata['longname'].replace('script', '')
    board['postarea_desc'] = formdata['postarea_desc'].replace('script', '').replace('meta', '')
    board['postarea_extra'] = formdata['postarea_extra'].replace('script', '').replace('meta', '')
    board['anonymous'] = formdata['anonymous'].replace('script', '')
    board['subject'] = formdata['subject'].replace('script', '')
    board['message'] = formdata['message'].replace('script', '')
    board['useid'] = formdata['useid']
    board['slip'] = formdata['slip']
    board['countrycode'] = formdata['countrycode']
    if 'disable_name' in formdata.keys():
      board['disable_name'] = '1'
    else:
      board['disable_name'] = '0'
    if 'disable_subject' in formdata.keys():
      board['disable_subject'] = '1'
    else:
      board['disable_subject'] = '0'
    if 'allow_noimage' in formdata.keys():
      board['allow_noimage'] = '1'
    else:
      board['allow_noimage'] = '0'
    if 'allow_images' in formdata.keys():
      board['allow_images'] = '1'
    else:
      board['allow_images'] = '0'
    if 'allow_image_replies' in formdata.keys():
      board['allow_image_replies'] = '1'
    else:
      board['allow_image_replies'] = '0'

    # Update file types
    UpdateDb("DELETE FROM `boards_filetypes` WHERE `boardid` = %s" % board['id'])
    for filetype in filetypelist():
      if 'filetype'+filetype['ext'] in formdata.keys():
        UpdateDb("INSERT INTO `boards_filetypes` VALUES (%s, %s)" % (board['id'], filetype['id']))

    try:
      board['maxsize'] = int(formdata['maxsize'])
      if board['maxsize'] > 5000:
        board['maxsize'] = 5000
    except:
      raise UserError, _("Max size must be numeric.")

    try:
      board['thumb_px'] = int(formdata['thumb_px'])
      if board['thumb_px'] > 500:
        board['thumb_px'] = 500
    except:
      raise UserError, _("Max thumb dimensions must be numeric.")

    try:
      board['numthreads'] = int(formdata['numthreads'])
      if board['numthreads'] > 15:
        board['numthreads'] = 15
    except:
      raise UserError, _("Max threads shown must be numeric.")

    try:
      board['numcont'] = int(formdata['numcont'])
      if board['numcont'] > 15:
        board['numcont'] = 15
    except:
      raise UserError, _("Max replies shown must be numeric.")

    t = time.time()
    updateBoardSettings()
    setBoard('anarkia')
    regenerateBoard(False)
    tf = timeTaken(t, time.time())
    
    msg = 'Opciones cambiadas. %s' % tf
    logAction(msg)
    return renderTemplate('anarkia.html', {'mode': 99, 'msg': msg})
  else:
    return renderTemplate('anarkia.html', {'mode': 1, 'boardopts': board, 'filetypes': filetypelist(), 'supported_filetypes': board['filetypes_ext']})

def emojis(formdata):
  board = Settings._.BOARD
  board_pickle = _mysql.escape_string(pickle.dumps([board['dir']]))
  
  if formdata.get('new'):
    import re
    ext = {'image/jpeg': 'jpg', 'image/gif': 'gif', 'image/png': 'png'}
    
    if not formdata['name']:
      raise UserError, 'Ingresa nombre.'
    if not re.match(r"^[0-9a-zA-Z]+$", formdata['name']):
      raise UserError, 'Nombre inválido; solo letras/números.'
      
    name = ":%s:" % formdata['name'][:15]
    data = formdata['file']
    
    if not data:
      raise UserError, 'Ingresa imagen.'
    
    # check if it exists
    already = FetchOne("SELECT 1 FROM `filters` WHERE `boards` = '%s' AND `from` = '%s'" % (board_pickle, _mysql.escape_string(name)))
    if already:
      raise UserError, 'Este emoji ya existe.'
    
    # get image information
    content_type, width, height, size, extra = getImageInfo(data)
    
    if content_type not in ext.keys():
      raise UserError, 'Formato inválido.'
    if width > 500 or height > 500:
      raise UserError, 'Dimensiones muy altas.'
    if size > 150000:
      raise UserError, 'Tamaño muy grande.'
      
    # create file names
    thumb_width, thumb_height = getThumbDimensions(width, height, 32)
    
    file_path = Settings.ROOT_DIR + board["dir"] + "/e/" + formdata['name'][:15] + '.' + ext[content_type]
    file_url = Settings.BOARDS_URL + board["dir"] + "/e/" + formdata['name'][:15] + '.' + ext[content_type]
    to_filter = '<img src="%s" width="%d" height="%d" />' % (file_url, thumb_width, thumb_height)
    
    # start processing image
    args = [Settings.CONVERT_PATH, "-", "-limit" , "thread", "1", "-resize", "%dx%d" % (thumb_width, thumb_height), "-quality", "80", file_path]
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    out = p.communicate(input=data)[0]
    
    # insert into DB
    sql = "INSERT INTO `filters` (`boards`, `type`, `action`, `from`, `to`, `staff`, `added`) VALUES ('%s', 0, 1, '%s', '%s', 'Anarko', '%s')" % (board_pickle, _mysql.escape_string(name), _mysql.escape_string(to_filter), timestamp())
    UpdateDb(sql)
    
    msg = "Emoji %s agregado." % name
    logAction(msg)
    return renderTemplate('anarkia.html', {'mode': 99, 'msg': msg})
  elif formdata.get('del'):
    return renderTemplate('anarkia.html', {'mode': 99, 'msg': 'Del.'})
  else:
    filters = FetchAll("SELECT * FROM `filters` WHERE `boards` = '%s' ORDER BY `added` DESC" % board_pickle)
    return renderTemplate('anarkia.html', {'mode': 8, 'emojis': filters})

def filetypelist():
  filetypes = FetchAll('SELECT * FROM `filetypes` ORDER BY `ext` ASC')
  return filetypes

def logAction(action):
  InsertDb("INSERT INTO `logs` (`timestamp`, `staff`, `action`) VALUES (" + str(timestamp()) + ", 'Anarko', '" + _mysql.escape_string(action) + "')")
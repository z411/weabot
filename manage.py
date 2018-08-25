# coding=utf-8
import _mysql
import os
import cgi
import shutil
import imaplib
import poplib

from database import *
from settings import Settings
from framework import *
from formatting import *
from template import *
from post import *
from email.Parser import Parser

def manage(self, path_split):
  page = ''
  validated = False
  administrator = False
  moderator = True
  skiptemplate = False
  
  try:
    if self.formdata['username'] and self.formdata['password']:
      password = getMD5(self.formdata['password'] + Settings.SECRET)
      
      valid_account = FetchOne("SELECT * FROM `staff` WHERE `username` = '" + _mysql.escape_string(self.formdata['username']) + "' AND `password` = '" + _mysql.escape_string(password) + "' LIMIT 1")
      if valid_account:
        setCookie(self, 'weabot_manage', self.formdata['username'] + ':' + valid_account['password'], domain='THIS')
        setCookie(self, 'weabot_staff', 'yes')
        UpdateDb('DELETE FROM `logs` WHERE `timestamp` < ' + str(timestamp() - 604800)) # one week
      else:
        page += _('Incorrect username/password.')
        logAction('', 'Failed log-in. U:'+_mysql.escape_string(self.formdata['username'])+' IP:'+self.environ["REMOTE_ADDR"])
  except:
    pass
  
  try:
    manage_cookie = getCookie(self, 'weabot_manage')
    if manage_cookie != '':
      username, password = manage_cookie.split(':')
      staff_account = FetchOne("SELECT * FROM `staff` WHERE `username` = '" + _mysql.escape_string(username) + "' AND `password` = '" + _mysql.escape_string(password) + "' LIMIT 1")
      if staff_account:
        validated = True
        if staff_account['rights'] == '0' or staff_account['rights'] == '1' or staff_account['rights'] == '2':
          administrator = True
        if staff_account['rights'] == '2':
          moderator = False
        UpdateDb('UPDATE `staff` SET `lastactive` = ' + str(timestamp()) + ' WHERE `id` = ' + staff_account['id'] + ' LIMIT 1')
  except:
    pass
  
  #validated = True
  #moderator = True
  #staff_account = {}
  #staff_account['username'] = ''
  #staff_account['rights'] = '0'
  #staff_account['added'] = '0'
  
  if not validated:
    template_filename = "login.html"
    template_values = {}
  else:
    if len(path_split) > 2:
      if path_split[2] == 'rebuild':
        if not administrator:
          return
        
        try:
          board_dir = path_split[3]
        except:
          board_dir = ''
        
        if board_dir == '':
          template_filename = "rebuild.html"
          template_values = {'boards': boardlist()}
        else:
          everything = ("everything" in self.formdata)
          if board_dir == '!ALL':
            t1 = time.time()
            boards = FetchAll('SELECT `dir` FROM `boards` WHERE secret = 0')
            for board in boards:
              board = setBoard(board['dir'])
              regenerateBoard(everything)
            
            message = _('Rebuilt %(board)s in %(time)s seconds.') % {'board': _('all boards'), 'time': timeTaken(t1, time.time())}
            logAction(staff_account['username'], _('Rebuilt %s') % _('all boards'))
          elif board_dir == '!BBS':
            t1 = time.time()
            boards = FetchAll('SELECT `dir` FROM `boards` WHERE `board_type` = 1')
            for board in boards:
              board = setBoard(board['dir'])
              regenerateBoard(everything)
            
            message = _('Rebuilt %(board)s in %(time)s seconds.') % {'board': _('all boards'), 'time': timeTaken(t1, time.time())}
            logAction(staff_account['username'], _('Rebuilt %s') % _('all boards'))
          elif board_dir == '!IB':
            t1 = time.time()
            boards = FetchAll('SELECT `dir` FROM `boards` WHERE `board_type` = 1')
            for board in boards:
              board = setBoard(board['dir'])
              regenerateBoard(everything)
            
            message = _('Rebuilt %(board)s in %(time)s seconds.') % {'board': _('all boards'), 'time': timeTaken(t1, time.time())}
            logAction(staff_account['username'], _('Rebuilt %s') % _('all boards'))
          elif board_dir == '!HOME':
            t1 = time.time()
            regenerateHome()
            message = _('Rebuilt %(board)s in %(time)s seconds.') % {'board': _('home'), 'time': timeTaken(t1, time.time())}
            logAction(staff_account['username'], _('Rebuilt %s') % _('home'))
          elif board_dir == '!NEWS':
            t1 = time.time()
            regenerateNews()
            message = _('Rebuilt %(board)s in %(time)s seconds.') % {'board': _('news'), 'time': timeTaken(t1, time.time())}
            logAction(staff_account['username'], _('Rebuilt %s') % _('news'))
          elif board_dir == '!KAKO':
            t1 = time.time()
            boards = FetchAll('SELECT `dir` FROM `boards` WHERE archive = 1')
            for board in boards:
              board = setBoard(board['dir'])
              regenerateKako()
            
            message = _('Rebuilt %(board)s in %(time)s seconds.') % {'board': 'kako', 'time': timeTaken(t1, time.time())}
            logAction(staff_account['username'], _('Rebuilt %s') % 'kako')
          elif board_dir == '!HTACCESS':
            t1 = time.time()
            if regenerateAccess():
              message = _('Rebuilt %(board)s in %(time)s seconds.') % {'board': _('htaccess'), 'time': timeTaken(t1, time.time())}
              logAction(staff_account['username'], _('Rebuilt %s') % _('htaccess'))
            else:
              message = _('htaccess regeneration deactivated by sysop.')
          else:
            t1 = time.time()
            board = setBoard(board_dir)
            regenerateBoard(everything)
            
            message = _('Rebuilt %(board)s in %(time)s seconds.') % {'board': '/' + board['dir'] + '/', 'time': timeTaken(t1, time.time())}
            logAction(staff_account['username'], 'Rebuilt /' + board['dir'] + '/')
          
          template_filename = "message.html"
      elif path_split[2] == 'mod':
        if not moderator:
          return

        try:
          board = setBoard(path_split[3])
        except:
          board = ""

        if not board:
          template_filename = "mod.html"
          template_values = {"mode": 1, 'boards': boardlist()}
        elif self.formdata.get("thread"):
          parentid = int(self.formdata["thread"])
          posts = FetchAll('SELECT id, timestamp, timestamp_formatted, name, message, IS_DELETED, locked, subject, length, INET_NTOA(ip) AS ip FROM `posts` WHERE (parentid = %d OR id = %d) AND boardid = %s ORDER BY `id` ASC' % (parentid, parentid, board['id']))
          template_filename = "mod.html"
          template_values = {"mode": 3, "dir": board["dir"], "posts": posts}
        else:
          threads = FetchAll("SELECT * FROM `posts` WHERE boardid = %s AND parentid = 0 ORDER BY `bumped` DESC" % board["id"])
          template_filename = "mod.html"
          template_values = {"mode": 2, "dir": board["dir"], "threads": threads}
      elif path_split[2] == 'staff':
        if staff_account['rights'] != '0':
          return
        action_taken = False
        
        if len(path_split) > 3:
          if path_split[3] == 'add' or path_split[3] == 'edit':
            member = None
            member_username = ''
            member_rights = '3'
            
            if path_split[3] == 'edit':
              if len(path_split) > 4:
                member = FetchOne('SELECT * FROM `staff` WHERE `id` = ' + _mysql.escape_string(path_split[4]) + ' LIMIT 1')
                if member:
                  member_username = member['username']
                  member_rights = member['rights']
                  action = 'edit/' + member['id']
                  
                  try:
                    if self.formdata['username'] != '':
                      if self.formdata['rights'] in ['0', '1', '2', '3']:
                        action_taken = True
                        if not ':' in self.formdata['username']:
                          UpdateDb("UPDATE `staff` SET `username` = '" + _mysql.escape_string(self.formdata['username']) + "', `rights` = " + self.formdata['rights'] + " WHERE `id` = " + member['id'] + " LIMIT 1")
                          message = _('Staff member updated.')
                          logAction(staff_account['username'], _('Updated staff account for %s') % self.formdata['username'])
                        else:
                          message = _('The character : can not be used in usernames.')
                        template_filename = "message.html"
                  except:
                    pass
            else:
              action = 'add'
              try:
                if self.formdata['username'] != '' and self.formdata['password'] != '':
                  username_taken = FetchOne('SELECT * FROM `staff` WHERE `username` = \'' + _mysql.escape_string(self.formdata['username']) + '\' LIMIT 1')
                  if not username_taken:
                    if self.formdata['rights'] in ['0', '1', '2', '3']:
                      action_taken = True
                      if not ':' in self.formdata['username']:
                        password = getMD5(self.formdata['password'] + Settings.SECRET)

                        InsertDb("INSERT INTO `staff` (`username`, `password`, `added`, `rights`) VALUES ('" + _mysql.escape_string(self.formdata['username']) + "', '" + _mysql.escape_string(password) + "', " + str(timestamp()) + ", " + self.formdata['rights'] + ")")
                        message = _('Staff member added.')
                        logAction(staff_account['username'], 'Added staff account for ' + self.formdata['username'])
                      else:
                        message = _('The character : can not be used in usernames.')
                      
                      template_filename = "message.html"
                  else:
                    action_taken = True
                    message = _('That username is already in use.')
                    template_filename = "message.html"
              except:
                pass

            if not action_taken:
              action_taken = True

              if action == 'add':
                submit = 'Agregar'
              else:
                submit = 'Editar'
              
              template_filename = "staff.html"
              template_values = {'mode': 1,
                    'action': action,
                    'member': member,
                    'member_username': member_username,
                    'member_rights': member_rights,
                    'submit': submit}
          elif path_split[3] == 'delete':
            if not moderator:
              return

            action_taken = True
            message = '<a href="' + Settings.CGI_URL + 'manage/staff/delete_confirmed/' + path_split[4] + '">' + _('Click here to confirm the deletion of that staff member') + '</a>'
            template_filename = "message.html"
          elif path_split[3] == 'delete_confirmed':
            if not moderator:
              return
              
            try:
              action_taken = True
              member = FetchOne('SELECT `username` FROM `staff` WHERE `id` = ' + _mysql.escape_string(path_split[4]) + ' LIMIT 1')
              if member:
                UpdateDb('DELETE FROM `staff` WHERE `id` = ' + _mysql.escape_string(path_split[4]) + ' LIMIT 1')
                message = 'Staff member deleted.'
                template_filename = "error.html"
                logAction(staff_account['username'], _('Deleted staff account for %s') % member['username'])
              else:
                message = _('Unable to locate a staff account with that ID.')
                template_filename = "error.html"
            except:
              pass
              
        if not action_taken:
          staff = FetchAll('SELECT * FROM `staff` ORDER BY `rights`')
          for member in staff:
            if member['rights'] == '0':
              member ['rights'] = _('Super-administrator')
            elif member['rights'] == '1':
              member ['rights'] = _('Administrator')
            elif member['rights'] == '2':
              member ['rights'] = _('Developer')
            elif member['rights'] == '3':
              member ['rights'] = _('Moderator')
            if member['lastactive'] != '0':
              member['lastactive'] = formatTimestamp(member['lastactive'])
            else:
              member['lastactive'] = _('Never')
          template_filename = "staff.html"
          template_values = {'mode': 0, 'staff': staff}
      elif path_split[2] == 'delete':
        if not moderator:
          return
          
        do_ban = False
        try:
          if self.formdata['ban'] == 'true':
            do_ban = True
        except:
          pass
        
        template_filename = "delete.html"
        template_values = {'do_ban': do_ban, 'curboard': path_split[3], 'postid': path_split[4]}
      elif path_split[2] == 'delete_confirmed':
        if not moderator:
          return
          
        do_ban = self.formdata.get('ban')
        permanently = self.formdata.get('perma')
        imageonly = self.formdata.get('imageonly')
        
        board = setBoard(path_split[3])
        postid = int(path_split[4])
        post = FetchOne('SELECT id, message, parentid, INET_NTOA(ip) AS ip FROM posts WHERE boardid = %s AND id = %s' % (board['id'], postid))
        
        if not permanently:
          deletePost(path_split[4], None, '2', imageonly)
        else:
          deletePost(path_split[4], None, '0', imageonly)
        regenerateHome()
            
        # Borrar denuncias
        UpdateDb("DELETE FROM `reports` WHERE `postid` = '"+_mysql.escape_string(path_split[4])+"'")
        boards = FetchAll('SELECT `name`, `dir` FROM `boards` ORDER BY `dir`')
      
        if imageonly:
          message = 'Archivo de post /%s/%s eliminado.' % (board['dir'], post['id'])
        elif permanently or post["parentid"] == '0':
          message = 'Post /%s/%s eliminado permanentemente.' % (board['dir'], post['id'])
        else:
          message = 'Post /%s/%s enviado a la papelera.' % (board['dir'], post['id'])
        template_filename = "message.html"
        logAction(staff_account['username'], message + ' Contenido: ' + post['message'] + ' IP: ' + post['ip'])
      
        if do_ban:
          message = _('Redirecting to ban page...') + '<meta http-equiv="refresh" content="0;url=' + Settings.CGI_URL + 'manage/ban?ip=' + post['ip'] + '" />'
          template_filename = "message.html"
      elif path_split[2] == 'lock':
        setLocked = 0
        
        # Nos vamos al board y ubicamos el post
        board = setBoard(path_split[3])
        post = FetchOne('SELECT `parentid`, `locked` FROM `posts` WHERE `boardid` = ' + board['id'] + ' AND `id` = \'' + _mysql.escape_string(path_split[4]) + '\' LIMIT 1')
        if not post:
          message = _('Unable to locate a post with that ID.')
          template_filename = "error.html"
        else:
          if post['parentid'] != '0':
            message = _('Post is not a thread opener.')
            template_filename = "error.html"
          else:
            if post['locked'] == '0':
              # Cerrar si esta abierto
              setLocked = 1
            else:
              # Abrir si esta cerrado
              setLocked = 0
            
            UpdateDb("UPDATE `posts` SET `locked` = %d WHERE `boardid` = '%s' AND `id` = '%s' LIMIT 1" % (setLocked, board["id"], _mysql.escape_string(path_split[4])))
            threadUpdated(path_split[4])
          if setLocked == 1:
            message = _('Thread successfully closed.')
            logAction(staff_account['username'], _('Closed thread %s') % ('/' + path_split[3] + '/' + path_split[4]))
          else:
            message = _('Thread successfully opened.')
            logAction(staff_account['username'], _('Opened thread %s') % ('/' + path_split[3] + '/' + path_split[4]))
          template_filename = "message.html"
      elif path_split[2] == 'permasage':
        setPermasaged = 0
        
        # Nos vamos al board y ubicamos el post
        board = setBoard(path_split[3])
        post = FetchOne('SELECT `parentid`, `locked` FROM `posts` WHERE `boardid` = ' + board['id'] + ' AND `id` = \'' + _mysql.escape_string(path_split[4]) + '\' LIMIT 1')
        if not post:
          message = 'Unable to locate a post with that ID.'
          template_filename = "error.html"
        elif post['locked'] == '1':
          message = 'Solo se puede aplicar permasage en un hilo abierto.'
          template_filename = "error.html"
        else:
          if post['parentid'] != '0':
            message = 'Post is not a thread opener.'
            template_filename = "error.html"
          else:
            if post['locked'] == '2':
              # Sacar permasage
              setPermasaged = 0
            else:
              # Colocar permasage
              setPermasaged = 2
            
            UpdateDb("UPDATE `posts` SET `locked` = %d WHERE `boardid` = '%s' AND `id` = '%s' LIMIT 1" % (setPermasaged, board["id"], _mysql.escape_string(path_split[4])))
            regenerateFrontPages()
            threadUpdated(path_split[4])
          
          if setPermasaged == 2:
            message = 'Thread successfully permasaged.'
            logAction(staff_account['username'], 'Enabled permasage in thread /' + path_split[3] + '/' + path_split[4])
          else:
            message = 'Thread successfully un-permasaged.'
            logAction(staff_account['username'], 'Disabled permasage in thread /' + path_split[3] + '/' + path_split[4])
          template_filename = "message.html"
      elif path_split[2] == 'move':
        if not moderator:
          return

        oldboardid = ""
        oldthread = ""
        newboardid = ""
        try:
          oldboardid = path_split[3]
          oldthread = path_split[4]
          newboardid = path_split[5]
        except:
          pass

        try:
          oldboardid = self.formdata['oldboardid']
          oldthread = self.formdata['oldthread']
          newboardid = self.formdata['newboardid']
        except:
          pass

        if oldboardid and oldthread and newboardid:
          message = "import"
          import shutil
          message += "ok"
          
          board = setBoard(oldboardid)
          oldboard = board['dir']
          oldboardsubject = board['subject']
          
          # get old posts
          posts = FetchAll("SELECT * FROM `posts` WHERE (`id` = {0} OR `parentid` = {0}) AND `boardid` = {1} ORDER BY id ASC".format(oldthread, board['id']))
          
          # switch to new board
          board = setBoard(newboardid)
          newboard = board['dir']
          
          refs = {}
          moved_files = []
          moved_thumbs = []
          moved_cats = []
          newthreadid = 0
          newthread = 0
          num = 1
          
          message = "from total: %s<br>" % len(posts)
          template_filename = "message.html"
          
          for p in posts:
            # save old post ID
            old_id = p['id']
            is_op = bool(p['parentid'] == '0')
            
            # copy post object but without ID and target boardid
            post = Post()
            post.post = p
            post.post.pop("id")
            post["boardid"] = board['id']
            post["parentid"] = newthreadid
            
            # save the files we need to move if any
            if post['IS_DELETED'] == '0':
              if post['file']:
                moved_files.append(post['file'])
              if post['thumb']:
                moved_thumbs.append(post['thumb'])
                if is_op:
                  moved_cats.append(post['thumb'])
            
            # fix subject if necessary
            if post['subject'] and post['subject'] == oldboardsubject:
              post['subject'] = board['subject']
            
            # insert new post and get its new ID
            new_id = post.insert()
            
            # save the reference (BBS = post number, IB = new ID)
            refs[old_id] = num if board['board_type'] == '1' else new_id
            
            # this was an OP
            message += "newthread = %s parentid = %s<br>" % (newthreadid, p['parentid'])
            if is_op:
              oldthread = old_id
              newthreadid = new_id
              oldbumped = post["bumped"]
              
              # BBS = new thread timestamp, IB = new thread ID
              newthread = post['timestamp'] if board['board_type'] == '1' else new_id
            
            # log it
            message += "%s -> %s<br>" % (old_id, new_id)
            
            num += 1
            
          # fix anchors
          for old, new in refs.iteritems():
            old_url = "/{oldboard}/res/{oldthread}.html#{oldpost}\">&gt;&gt;{oldpost}</a>".format(oldboard=oldboard, oldthread=oldthread, oldpost=old)
            
            if board['board_type'] == '1':
              new_url = "/{newboard}/read/{newthread}/{newpost}\">&gt;&gt;{newpost}</a>".format(newboard=newboard, newthread=newthread, newpost=new)
            else:
              new_url = "/{newboard}/res/{newthread}.html#{newpost}\">&gt;&gt;{newpost}</a>".format(newboard=newboard, newthread=newthread, newpost=new)
            
            sql = "UPDATE `posts` SET `message` = REPLACE(message, '{old}', '{new}') WHERE `boardid` = {newboardid} AND (`id` = {newthreadid} OR `parentid` = {newthreadid})".format(old=old_url, new=new_url, newboardid=board['id'], newthreadid=newthreadid)
            message += sql + "<br>"
            UpdateDb(sql)
          
          # copy files
          for file in moved_files:
            if not os.path.isfile(Settings.IMAGES_DIR + newboard + "/src/" + file):
              shutil.copyfile(Settings.IMAGES_DIR + oldboard + "/src/" + file, Settings.IMAGES_DIR + newboard + "/src/" + file)
          for thumb in moved_thumbs:
            if not os.path.isfile(Settings.IMAGES_DIR + newboard + "/thumb/" + thumb):
              shutil.copyfile(Settings.IMAGES_DIR + oldboard + "/thumb/" + thumb, Settings.IMAGES_DIR + newboard + "/thumb/" + thumb)
            if not os.path.isfile(Settings.IMAGES_DIR + newboard + "/mobile/" + thumb):
              shutil.copyfile(Settings.IMAGES_DIR + oldboard + "/mobile/" + thumb, Settings.IMAGES_DIR + newboard + "/mobile/" + thumb)
          for cat in moved_cats:
            try:
              if not os.path.isfile(Settings.IMAGES_DIR + newboard + "/cat/" + thumb):
                shutil.copyfile(Settings.IMAGES_DIR + oldboard + "/cat/" + thumb, Settings.IMAGES_DIR + newboard + "/cat/" + thumb)
            except:
              pass

          # lock original, set expiration to 1 day
          exp = timestamp()+86400
          exp_format = datetime.datetime.fromtimestamp(exp).strftime("%d/%m")
          sql = "UPDATE `posts` SET `locked`=1, `expires`={exp}, `expires_formatted`=\"{exp_format}\" WHERE `boardid`=\"{oldboard}\" AND id=\"{oldthread}\"".format(exp=exp,exp_format=exp_format,oldboard=oldboardid,oldthread=oldthread)
          UpdateDb(sql)
       
          # insert notice message
          if 'msg' in self.formdata:
            board = setBoard(oldboard)
            
            if board['board_type'] == '1':
              thread_url = "/{newboard}/read/{newthread}".format(newboard=newboard, newthread=newthread)
            else:
              thread_url = "/{newboard}/res/{newthread}.html".format(newboard=newboard, newthread=newthread)
            
            notice_post = Post(board["id"])
            notice_post["parentid"] = oldthread
            if board['board_type'] == "0":
              notice_post["subject"] = "Aviso"
            notice_post["name"] = "Sistema"
            notice_post["message"] = "El hilo ha sido movido a <a href=\"{url}\">/{newboard}/{newthread}</a>.".format(url=thread_url, newboard=newboard, newthread=newthread)
            notice_post["timestamp"] = timestamp()+1
            notice_post["timestamp_formatted"] = "Hilo movido"
            notice_post["bumped"] = oldbumped
            notice_post.insert()
            
          # regenerate
          regenerateFrontPages()
          regenerateThreadPage(newthreadid)
          regenerateThreadPage(oldthread)

          message += "done"
          
          logAction(staff_account['username'], "Movido hilo %s/%s a %s/%s." % (oldboard, oldthread, newboard, newthread))
        else:
          template_filename = "move.html"
          template_values = {'boards': boardlist(), 'oldboardid': oldboardid, 'oldthread': oldthread}
      elif path_split[2] == 'ban':
        if not moderator:
          return
      
        if len(path_split) > 4:
          board = setBoard(path_split[3])
          post = FetchOne('SELECT `ip` FROM `posts` WHERE `boardid` = ' + board['id'] + ' AND `id` = \'' + _mysql.escape_string(path_split[4]) + '\' LIMIT 1')
          formatted_ip = inet_ntoa(long(post['ip']))
          #Creo que esto no deberia ir aqui... -> UpdateDb('UPDATE `posts` SET `banned` = 1 WHERE `boardid` = ' + board['id'] + ' AND `id` = \'' + _mysql.escape_string(path_split[4]) + '\'')
          if not post:
            message = _('Unable to locate a post with that ID.')
            template_filename = "error.html"
          else:
            message = '<meta http-equiv="refresh" content="0;url=' + Settings.CGI_URL + 'manage/ban?ip=' + formatted_ip + '" />Espere...'
            template_filename = "message.html"
        else:
          #if path_split[3] == '':
          try:
            ip = self.formdata['ip']
          except:
            ip = ''
          try:
            netmask = insnetmask = self.formdata['netmask']
            if netmask == '255.255.255.255':
              insnetmask = ''
          except:
            netmask = instnetmask = ''
          #else:
          #  ip = path_split[3]
          if ip != '':
            try:
              reason = self.formdata['reason']
            except:
              reason = None
            if reason is not None:
              if self.formdata['seconds'] != '0':
                until = str(timestamp() + int(self.formdata['seconds']))
              else:
                until = '0'
              where = ''
              if 'board_all' not in self.formdata.keys():
                where = []
                boards = FetchAll('SELECT `dir` FROM `boards`')
                for board in boards:
                  keyname = 'board_' + board['dir']
                  if keyname in self.formdata.keys():
                    if self.formdata[keyname] == "1":
                      where.append(board['dir'])
                if len(where) > 0:
                  where = pickle.dumps(where)
                else:
                  self.error(_("You must select where the ban shall be placed"))
                  return

              if 'edit' in self.formdata.keys():
                UpdateDb("DELETE FROM `bans` WHERE `id` = '" + _mysql.escape_string(self.formdata['edit']) + "' LIMIT 1")
              else:
                ban = FetchOne("SELECT `id` FROM `bans` WHERE `ip` = '" + _mysql.escape_string(ip) + "' AND `boards` = '" + _mysql.escape_string(where) + "' LIMIT 1")
                if ban:
                  self.error(_('There is already an identical ban for this IP.') + '<a href="'+Settings.CGI_URL+'manage/ban/' + ip + '?edit=' + ban['id']+'">' + _('Edit') + '</a>')
                  return
              
              # Blind mode
              if 'blind' in self.formdata.keys() and self.formdata['blind'] == '1':
                blind = '1'
              else:
                blind = '0'
              
              # Banear sin mensaje
              InsertDb("INSERT INTO `bans` (`ip`, `netmask`, `boards`, `added`, `until`, `staff`, `reason`, `note`, `blind`) VALUES (INET_ATON('" + _mysql.escape_string(ip) + "') & INET_ATON('"+_mysql.escape_string(netmask)+"'), INET_ATON('"+_mysql.escape_string(insnetmask)+"'), '" + _mysql.escape_string(where) + "', " + str(timestamp()) + ", " + until + ", '" + _mysql.escape_string(staff_account['username']) + "', '" + _mysql.escape_string(self.formdata['reason']) + "', '" + _mysql.escape_string(self.formdata['note']) + "', '"+blind+"')")
              
              regenerateAccess()
              if 'edit' in self.formdata.keys():
                message = _('Ban successfully edited.')
                action = 'Edited ban for ' + ip
              else:
                message = _('Ban successfully placed.')
                action = 'Banned ' + ip
                if until != '0':
                  action += ' until ' + formatTimestamp(until)
                else:
                  action += ' permanently'
              logAction(staff_account['username'], action)
              template_filename = 'message.html'
            else:
              startvalues = {'where': [],
                             'netmask': '255.255.255.255',
                             'reason': '',
                             'note': '',
                             'message': '(GET OUT)',
                             'seconds': '0',
                             'blind': '1'}
              edit_id = 0
              if 'edit' in self.formdata.keys():
                edit_id = self.formdata['edit']
                ban = FetchOne("SELECT `id`, INET_NTOA(`ip`) AS 'ip', CASE WHEN `netmask` IS NULL THEN '255.255.255.255' ELSE INET_NTOA(`netmask`) END AS 'netmask', boards, added, until, staff, reason, note, blind FROM `bans` WHERE `id` = '" + _mysql.escape_string(edit_id) + "' ORDER BY `added` DESC")
                if ban:
                  if ban['boards'] == '':
                    where = ''
                  else:
                    where = pickle.loads(ban['boards'])
                  if ban['until'] == '0':
                    until = 0
                  else:
                    until = int(ban['until']) - timestamp()
                  startvalues = {'where': where,
                                 'netmask': ban['netmask'],
                                 'reason': ban['reason'],
                                 'note': ban['note'],
                                 'seconds': str(until),
                                 'blind': ban['blind']}
                else:
                  edit_id = 0
              
              template_filename = "bans.html"
              template_values = {'mode': 1,
                'boards': boardlist(),
                'ip': ip,
                'startvalues': startvalues,
                'edit_id': edit_id}
      elif path_split[2] == 'bans':
        if not moderator:
          return
          
        action_taken = False
        if len(path_split) > 4:
          if path_split[3] == 'delete':
            ip = FetchOne("SELECT INET_NTOA(`ip`) AS 'ip' FROM `bans` WHERE `id` = '" + _mysql.escape_string(path_split[4]) + "' LIMIT 1", 0)[0]
            if ip != '':
              # Delete ban
              UpdateDb('DELETE FROM `bans` WHERE `id` = ' + _mysql.escape_string(path_split[4]) + ' LIMIT 1')
              regenerateAccess()
              message = _('Ban successfully deleted.')
              template_filename = "message.html"
              logAction(staff_account['username'], _('Deleted ban for %s') % ip)
            else:
              message = _('There was a problem while deleting that ban.  It may have already been removed, or recently expired.')
              template_filename = "error.html"
            
        if not action_taken:
          bans = FetchAll("SELECT `id`, INET_NTOA(`ip`) AS 'ip', CASE WHEN `netmask` IS NULL THEN '255.255.255.255' ELSE INET_NTOA(`netmask`) END AS 'netmask', boards, added, until, staff, reason, note, blind FROM `bans` ORDER BY `added` DESC")
          if bans:
            for ban in bans:
              if ban['boards'] == '':
                ban['boards'] = _('All boards')
              else:
                where = pickle.loads(ban['boards'])
                if len(where) > 1:
                  ban['boards'] = '/' + '/, /'.join(where) + '/'
                else:
                  ban['boards'] = '/' + where[0] + '/'
              ban['added'] = formatTimestamp(ban['added'])
              if ban['until'] == '0':
                ban['until'] = _('Does not expire')
              else:
                ban['until'] = formatTimestamp(ban['until'])
              if ban['blind'] == '1':
                ban['blind'] = 'Sí'
              else:
                ban['blind'] = 'No'
          template_filename = "bans.html"
          template_values = {'mode': 0, 'bans': bans}
      elif path_split[2] == 'changepassword':
        form_submitted = False
        try:
          if self.formdata['oldpassword'] != '' and self.formdata['newpassword'] != '' and self.formdata['newpassword2'] != '':
            form_submitted = True
        except:
          pass
        if form_submitted:
          if getMD5(self.formdata['oldpassword'] + Settings.SECRET) == staff_account['password']:
            if self.formdata['newpassword'] == self.formdata['newpassword2']:
              UpdateDb('UPDATE `staff` SET `password` = \'' + getMD5(self.formdata['newpassword'] + Settings.SECRET) + '\' WHERE `id` = ' + staff_account['id'] + ' LIMIT 1')
              message = _('Password successfully changed.  Please log out and log back in.')
              template_filename = "message.html"
            else:
              message = _('Passwords did not match.')
              template_filename = "error.html"
          else:
            message = _('Current password incorrect.')
            template_filename = "message.html"
        else:
          template_filename = "changepassword.html"
          template_values = {}
      elif path_split[2] == 'board':
        if not administrator:
          return
        
        if len(path_split) > 3:
          board = setBoard(path_split[3])
          form_submitted = False
          try:
            if self.formdata['name'] != '':
              form_submitted = True
          except:
            pass
          if form_submitted:
            # Update board settings
            board['name'] = self.formdata['name']
            board['longname'] = self.formdata['longname']
            board['subname'] = self.formdata['subname']
            board['anonymous'] = self.formdata['anonymous']
            board['subject'] = self.formdata['subject']
            board['message'] = self.formdata['message']
            if board['dir'] != 'anarkia':
              board['board_type'] = self.formdata['type']
            board['useid'] = self.formdata['useid']
            board['slip'] = self.formdata['slip']
            board['countrycode'] = self.formdata['countrycode']
            if 'recyclebin' in self.formdata.keys():
              board['recyclebin'] = '1'
            else:
              board['recyclebin'] = '0'
            if 'disable_name' in self.formdata.keys():
              board['disable_name'] = '1'
            else:
              board['disable_name'] = '0'
            if 'disable_subject' in self.formdata.keys():
              board['disable_subject'] = '1'
            else:
              board['disable_subject'] = '0'
            if 'secret' in self.formdata.keys():
              board['secret'] = '1'
            else:
              board['secret'] = '0'
            if 'locked' in self.formdata.keys():
              board['locked'] = '1'
            else:
              board['locked'] = '0'
            board['postarea_desc'] = self.formdata['postarea_desc']
            if 'allow_noimage' in self.formdata.keys():
              board['allow_noimage'] = '1'
            else:
              board['allow_noimage'] = '0'
            if 'allow_images' in self.formdata.keys():
              board['allow_images'] = '1'
            else:
              board['allow_images'] = '0'
            if 'allow_image_replies' in self.formdata.keys():
              board['allow_image_replies'] = '1'
            else:
              board['allow_image_replies'] = '0'
            if 'allow_spoilers' in self.formdata.keys():
              board['allow_spoilers'] = '1'
            else:
              board['allow_spoilers'] = '0'
            if 'allow_oekaki' in self.formdata.keys():
              board['allow_oekaki'] = '1'
            else:
              board['allow_oekaki'] = '0'
            if 'archive' in self.formdata.keys():
              board['archive'] = '1'
            else:
              board['archive'] = '0'
            board['postarea_extra'] = self.formdata['postarea_extra']
            board['force_css'] = self.formdata['force_css']
            
            # Update file types
            UpdateDb("DELETE FROM `boards_filetypes` WHERE `boardid` = %s" % board['id'])
            for filetype in filetypelist():
              if 'filetype'+filetype['ext'] in self.formdata.keys():
                UpdateDb("INSERT INTO `boards_filetypes` VALUES (%s, %s)" % (board['id'], filetype['id']))

            try:
              board['numthreads'] = int(self.formdata['numthreads'])
            except:
              raise UserError, _("Max threads shown must be numeric.")

            try:
              board['numcont'] = int(self.formdata['numcont'])
            except:
              raise UserError, _("Max replies shown must be numeric.")

            try:
              board['numline'] = int(self.formdata['numline'])
            except:
              raise UserError, _("Max lines shown must be numeric.")

            try:
              board['thumb_px'] = int(self.formdata['thumb_px'])
            except:
              raise UserError, _("Max thumb dimensions must be numeric.")
              
            try:
              board['maxsize'] = int(self.formdata['maxsize'])
            except:
              raise UserError, _("Max size must be numeric.")
              
            try:
              board['maxage'] = int(self.formdata['maxage'])
            except:
              raise UserError, _("Max age must be numeric.")
            
            try:
              board['maxinactive'] = int(self.formdata['maxinactive'])
            except:
              raise UserError, _("Max inactivity must be numeric.")

            try:
              board['threadsecs'] = int(self.formdata['threadsecs'])
            except:
              raise UserError, _("Time between new threads must be numeric.")

            try:
              board['postsecs'] = int(self.formdata['postsecs'])
            except:
              raise UserError, _("Time between replies must be numeric.")

            updateBoardSettings()
            message = _('Board options successfully updated.') + ' <a href="'+Settings.CGI_URL+'manage/rebuild/'+board['dir']+'">'+_('Rebuild')+'</a>'
            template_filename = "message.html"
            logAction(staff_account['username'], _('Updated options for /%s/') % board['dir'])
          else:
            template_filename = "boardoptions.html"
            template_values = {'mode': 1, 'boardopts': board, 'filetypes': filetypelist(), 'supported_filetypes': board['filetypes_ext']}
        else:
          # List all boards
          template_filename = "boardoptions.html"
          template_values = {'mode': 0, 'boards': boardlist()}
      elif path_split[2] == 'recyclebin':
        if not administrator:
          return
        
        message = None
        if len(path_split) > 5:
          if path_split[4] == 'restore':
            board = setBoard(path_split[5])

            post = FetchOne('SELECT `parentid` FROM `posts` WHERE `boardid` = ' + board['id'] + ' AND `id` = \'' + _mysql.escape_string(path_split[6]) + '\' LIMIT 1')
            if not post:
              message = _('Unable to locate a post with that ID.') + '<br />'
              template_filename = "error.html"
            else:
              UpdateDb('UPDATE `posts` SET `IS_DELETED` = 0 WHERE `boardid` = ' + board['id'] + ' AND `id` = \'' + _mysql.escape_string(path_split[6]) + '\' LIMIT 1')
              if post['parentid'] != '0':
                threadUpdated(post['parentid'])
              else:
                regenerateFrontPages()
                
              message = _('Post successfully restored.')
              logAction(staff_account['username'], _('Restored post %s') % ('/' + path_split[5] + '/' + path_split[6]))
            
          if path_split[4] == 'delete':
            board = setBoard(path_split[5])
            post = FetchOne('SELECT `parentid` FROM `posts` WHERE `boardid` = ' + board['id'] + ' AND `id` = \'' + _mysql.escape_string(path_split[6]) + '\' LIMIT 1')
            if not post:
              message = _('Unable to locate a post with that ID.')
            else:
              deletePost(path_split[6], None)
              
              if post['parentid'] != '0':
                threadUpdated(post['parentid'])
              else:
                regenerateFrontPages()
                
              message = _('Post successfully permadeleted.')
              logAction(staff_account['username'], _('Permadeleted post %s') % ('/' + path_split[5] + '/' + path_split[6]))
        
        # Delete more than 1 post
        if 'deleteall' in self.formdata.keys():
          return # TODO
          deleted = 0
          for key in self.formdata.keys():
            if key[:2] == '!i':
              dir = key[2:].split('/')[0] # Board where the post is
              postid = key[2:].split('/')[1] # Post to delete
              
              # Delete post start
              post = FetchOne('SELECT `parentid`, `dir` FROM `posts` INNER JOIN `boards` ON posts.boardid = boards.id WHERE `dir` = \'' + _mysql.escape_string(dir) + '\' AND posts.id = \'' + _mysql.escape_string(postid) + '\' LIMIT 1')
              if not post:
                message = _('Unable to locate a post with that ID.')
              else:
                board = setBoard(dir)
                deletePost(int(postid), None)
                if post['parentid'] != '0':
                  threadUpdated(post['parentid'])
                else:
                  regenerateFrontPages()
                deleted += 1
              # Delete post end
          
          logAction(staff_account['username'], _('Permadeleted %s post(s).') % str(deleted))
          message = _('Permadeleted %s post(s).') % str(deleted)
        
        ## Start
        import math
        pagesize = float(Settings.RECYCLEBIN_POSTS_PER_PAGE)
        
        try:
          currentpage = int(path_split[3])
        except:
          currentpage = 0
        
        skip = False
        if 'type' in self.formdata.keys():
          type = int(self.formdata["type"])
        else:
          type = 0
        
        # Generate board list
        boards = FetchAll('SELECT `name`, `dir` FROM `boards` ORDER BY `dir`')
        for board in boards:
          if 'board' in self.formdata.keys() and self.formdata['board'] == board['dir']:
            board['checked'] = True
          else:
            board['checked'] = False
        
        # Get type filter
        if type != 0:
          type_condition = "= " + str(type)
        else:
          type_condition = "!= 0"
        
        # Table
        if 'board' in self.formdata.keys() and self.formdata['board'] != 'all':
          cboard = self.formdata['board']
          posts = FetchAll("SELECT posts.id, posts.timestamp, timestamp_formatted, IS_DELETED, INET_NTOA(posts.ip) as ip, posts.message, dir, boardid FROM `posts` INNER JOIN `boards` ON boardid = boards.id WHERE `dir` = '%s' AND IS_DELETED %s ORDER BY `timestamp` DESC LIMIT %d, %d" % (_mysql.escape_string(self.formdata['board']), _mysql.escape_string(type_condition), currentpage*pagesize, pagesize))
          try:
            totals = FetchOne("SELECT COUNT(id) FROM `posts` WHERE IS_DELETED %s AND `boardid` = %s" % (_mysql.escape_string(type_condition), _mysql.escape_string(posts[0]['boardid'])), 0)
          except:
            skip = True
        else:
          cboard = 'all'
          posts = FetchAll("SELECT posts.id, posts.timestamp, timestamp_formatted, IS_DELETED, posts.ip, posts.message, dir FROM `posts` INNER JOIN `boards` ON boardid = boards.id WHERE IS_DELETED %s ORDER BY `timestamp` DESC LIMIT %d, %d" % (_mysql.escape_string(type_condition), currentpage*pagesize, pagesize))
          totals = FetchOne("SELECT COUNT(id) FROM `posts` WHERE IS_DELETED %s" % _mysql.escape_string(type_condition), 0)
        
        template_filename = "recyclebin.html"
        template_values = {'message': message,
         'type': type,
         'boards': boards,
         'skip': skip}
       
        if not skip:
          # Calculate number of pages
          total = int(totals[0])
          pages = int(math.ceil(total / pagesize))
          
          # Create delete form
          if 'board' in self.formdata.keys():
            board = self.formdata['board']
          else:
            board = None
          
          navigator = ''
          if currentpage > 0:
            navigator += '<a href="'+Settings.CGI_URL+'manage/recyclebin/'+str(currentpage-1)+'?type='+str(type)+'&amp;board='+cboard+'">&lt;</a> '
          else:
            navigator += '&lt; '
          
          for i in range(pages):
            if i != currentpage:
              navigator += '<a href="'+Settings.CGI_URL+'manage/recyclebin/'+str(i)+'?type='+str(type)+'&amp;board='+cboard+'">'+str(i)+'</a> '
            else:
              navigator += str(i)+' '
            
          if currentpage < (pages-1):
            navigator += '<a href="'+Settings.CGI_URL+'manage/recyclebin/'+str(currentpage+1)+'?type='+str(type)+'&amp;board='+cboard+'">&gt;</a> '
          else:
            navigator += '&gt; '
          
          template_values.update({'currentpage': currentpage,
            'curboard': board,
            'posts': posts,
            'navigator': navigator})
        # End recyclebin
      elif path_split[2] == 'lockboard':
        if not administrator:
          return
        
        try:
          board_dir = path_split[3]
        except:
          board_dir = ''
        
        if board_dir == '':
          template_filename = "lockboard.html"
          template_values = {'boards': boardlist()}
      elif path_split[2] == 'boardlock':
        board = setBoard(path_split[3])
        if int(board['locked']):
          # Si esta cerrado... abrir
          board['locked'] = 0
          updateBoardSettings()
          message = _('Board opened successfully.')
          template_filename = "message.html"
        else:
          # Si esta abierta, cerrar
          board['locked'] = 1
          updateBoardSettings()
          message = _('Board closed successfully.')
          template_filename = "message.html"
      elif path_split[2] == 'addboard':
        if not administrator:
          return
        
        action_taken = False
        board_dir = ''
        
        try:
          if self.formdata['name'] != '':
            board_dir = self.formdata['dir']
        except:
          pass

        if board_dir != '':
          action_taken = True
          board_exists = FetchOne('SELECT * FROM `boards` WHERE `dir` = \'' + _mysql.escape_string(board_dir) + '\' LIMIT 1')
          if not board_exists:
            os.mkdir(Settings.ROOT_DIR + board_dir)
            os.mkdir(Settings.ROOT_DIR + board_dir + '/res')
            if not os.path.exists(Settings.IMAGES_DIR + board_dir):
              os.mkdir(Settings.IMAGES_DIR + board_dir)
            os.mkdir(Settings.IMAGES_DIR + board_dir + '/src')
            os.mkdir(Settings.IMAGES_DIR + board_dir + '/thumb')
            os.mkdir(Settings.IMAGES_DIR + board_dir + '/mobile')
            os.mkdir(Settings.IMAGES_DIR + board_dir + '/cat')
            if os.path.exists(Settings.ROOT_DIR + board_dir) and os.path.isdir(Settings.ROOT_DIR + board_dir):
              UpdateDb('INSERT INTO `boards` (`dir`, `name`) VALUES (\'' + _mysql.escape_string(board_dir) + '\', \'' + _mysql.escape_string(self.formdata['name']) + '\')')
              board = setBoard(board_dir)
              f = open(Settings.ROOT_DIR + board['dir'] + '/.htaccess', 'w')
              try:
                f.write('DirectoryIndex index.html')
              finally:
                f.close()
              regenerateFrontPages()
              message = _('Board added')
              template_filename = "message.html"
              logAction(staff_account['username'], _('Added board %s') % ('/' + board['dir'] + '/'))
            else:
              message = _('There was a problem while making the directories.')
              template_filename = "error.html"
          else:
            message = _('There is already a board with that directory.')
            template_filename = "error.html"

        if not action_taken:
          template_filename = "addboard.html"
          template_values = {}
      elif path_split[2] == 'trim':
        board = setBoard(path_split[3])
        trimThreads()
        
        self.output = "done trimming"
        return
      elif path_split[2] == 'setexpires':
        board = setBoard(path_split[3])
        parentid = int(path_split[4])
        days = int(path_split[5])
        t = time.time()
        
        expires = int(t) + (days * 86400)
        date_format = '%d/%m'
        expires_formatted = datetime.datetime.fromtimestamp(expires).strftime(date_format)
        
        sql = "UPDATE posts SET expires = timestamp + (%s * 86400), expires_formatted = FROM_UNIXTIME((timestamp + (%s * 86400)), '%s') WHERE boardid = %s AND id = %s" % (str(days), str(days), date_format, board["id"], str(parentid))
        UpdateDb(sql)
        
        self.output = "done " + sql
        return
        
      elif path_split[2] == 'fixflood':
        board = setBoard('zonavip')
        threads = FetchAll("SELECT * FROM posts WHERE boardid = %s AND parentid = 0 AND subject LIKE 'querido mod%%'" % board['id'])
        for thread in threads:
          self.output += "%s<br>" % thread['id']
          #deletePost(thread['id'], None)
        return
      elif path_split[2] == 'fixico':
        board = setBoard(path_split[3])
        
        threads = FetchAll("SELECT * FROM posts WHERE boardid = %s AND parentid = 0 AND message NOT LIKE '<img%%'" % board['id'])
        for t in threads:
          img_src = '<img src="%s" alt="ico" /><br />' % getRandomIco()
          newmessage = img_src + t["message"]
          #UpdateDb("UPDATE posts SET message = '%s' WHERE boardid = %s AND id = %s" % (_mysql.escape_string(newmessage), board['id'], t['id']))
          
        self.output = repr(threads)
        return
      elif path_split[2] == 'fixkako':
        board = setBoard(path_split[3])
        
        threads = FetchAll('SELECT * FROM archive WHERE boardid = %s ORDER BY timestamp DESC' % board['id'])
        for item in threads:
          t = time.time()
          self.output += item['timestamp'] + '<br />'
          fname = Settings.ROOT_DIR + board["dir"] + "/kako/" + str(item["timestamp"]) + ".json"
          if os.path.isfile(fname):
            import json
            with open(fname) as f:
              thread = json.load(f)
            thread['posts'] = [dict(zip(thread['keys'], row)) for row in thread['posts']]
            template_fname = "txt_archive.html"
            
            post_preview = cut_home_msg(thread['posts'][0]['message'], 0)
            page = renderTemplate("txt_archive.html", {"threads": [thread], "preview": post_preview}, False)
            with open(Settings.ROOT_DIR + board["dir"] + "/kako/" + str(thread['timestamp']) + ".html", "w") as f:
              f.write(page)
              
            self.output += 'done' + str(time.time() - t) + '<br />'
          else:
            self.output += 'El hilo no existe.<br />'
      elif path_split[2] == 'fixexpires':
        board = setBoard(path_split[3])
        
        if int(board["maxage"]):
          date_format = '%d/%m'
          date_format_y = '%m/%Y'
          if int(board["maxage"]) >= 365:
            date_format = date_format_y
          sql = "UPDATE posts SET expires = timestamp + (%s * 86400), expires_formatted = FROM_UNIXTIME((timestamp + (%s * 86400)), '%s') WHERE boardid = %s AND parentid = 0" % (board["maxage"], board["maxage"], date_format, board["id"])
          UpdateDb(sql)
        
          alert_time = int(round(int(board['maxage']) * Settings.MAX_AGE_ALERT))
          sql = "UPDATE posts SET expires_alert = CASE WHEN UNIX_TIMESTAMP() > (expires - %d*86400) THEN 1 ELSE 0 END WHERE boardid = %s AND parentid = 0" % (alert_time, board["id"])
          UpdateDb(sql)
        else:
          sql = "UPDATE posts SET expires = 0, expires_formatted = '', expires_alert = 0 WHERE boardid = %s AND parentid = 0" % (board["id"])
          UpdateDb(sql)
        
        self.output = "done"
        return
      elif path_split[2] == 'fixid':
        board = setBoard(path_split[3])
        posts = FetchAll('SELECT * FROM `posts` WHERE `boardid` = %s' % board['id'])
        self.output = "total: %d<br />" % len(posts)
        
        for post in posts:
            new_timestamp_formatted = formatTimestamp(post['timestamp'])
            tim = 0
                
            if board["useid"] != '0':
                new_timestamp_formatted += ' ID:' + iphash(post['ip'], '', tim, '1', False, False, False, '0')
            
            self.output += "%s - %s <br />" % (post['id'], new_timestamp_formatted)
            
            query = "UPDATE `posts` SET timestamp_formatted = '%s' WHERE boardid = '%s' AND id = '%s'" % (new_timestamp_formatted, board['id'], post['id'])
            UpdateDb(query)
            
        return
      elif path_split[2] == 'fixname':
        board = setBoard(path_split[3])
        posts = FetchAll('SELECT * FROM `posts` WHERE `boardid` = %s' % board['id'])
        new_name = board['anonymous']
        self.output = new_name + "<br />"
        for post in posts:
          self.output += "%s<br />" % (post['id'])
          query = "UPDATE `posts` SET `name` = '%s' WHERE boardid = '%s' AND id = '%s'" % (new_name, board['id'], post['id'])
          UpdateDb(query)
        return
      elif path_split[2] == 'setsub':
        board = setBoard(path_split[3])
        thread = FetchOne('SELECT * FROM `posts` WHERE `parentid` = 0 AND `boardid` = %s' % board['id'])
        subject = str(path_split[4])
        self.output = subject + "->" + thread['id'] + "<br />"
        query = "UPDATE `posts` SET `subject` = '%s' WHERE boardid = '%s' AND id = '%s'" % (subject, board['id'], thread['id'])
        UpdateDb(query)
        return
      elif path_split[2] == 'fixlength':
        board = setBoard(path_split[3])
        threads = FetchAll('SELECT * FROM `posts` WHERE parentid = 0 AND `boardid` = %s' % board['id'])
        for t in threads:
          length = threadNumReplies(t['id'])
          UpdateDb('UPDATE posts SET length = %d WHERE boardid = %s AND id = %s' % (length, board['id'], t['id']))
        
        self.output='done'
        return
      elif path_split[2] == 'archive':
        t = time.time()
        board = setBoard(path_split[3])
        postid = int(path_split[4])
        archiveThread(postid)
        self.output = "todo ok %s" % str(time.time() - t)
      elif path_split[2] == 'filters':
        action_taken = False
        if len(path_split) > 3 and path_split[3] == 'add':
          if "add" in self.formdata.keys():
            edit_id = 0
            if 'edit' in self.formdata.keys():
              edit_id = int(self.formdata['edit'])
            
            # We decide what type of filter it is.
            # 0: Word / 1: Name/Trip
            filter_type = int(self.formdata["type"])
            filter_action = int(self.formdata["action"])
            filter_from = ''
            filter_tripcode = ''
            
            # I don't like pickles... oh well.
            where = ''
            if 'board_all' not in self.formdata.keys():
              where = []
              boards = FetchAll('SELECT `dir` FROM `boards`')
              for board in boards:
                keyname = 'board_' + board['dir']
                if keyname in self.formdata.keys():
                  if self.formdata[keyname] == "1":
                    where.append(board['dir'])
              if len(where) > 0:
                where = _mysql.escape_string(pickle.dumps(where))
              else:
                self.error(_("You must select what board the filter will affect"))
                return
            
            if filter_type == 0:
              # Word filter
              if len(self.formdata["word"]) > 0:
                filter_from = _mysql.escape_string(cgi.escape(self.formdata["word"]))
              else:
                self.error(_("You must enter a word."))
                return
            elif filter_type == 1:
              # Name/trip filter
              can_add = False
              if len(self.formdata["name"]) > 0:
                filter_from = _mysql.escape_string(self.formdata["name"])
                can_add = True
              if len(self.formdata["trip"]) > 0:
                filter_tripcode = _mysql.escape_string(self.formdata["trip"])
                can_add = True
              if not can_add:
                self.error(_("You must enter a name and/or a tripcode."))
                return
            
            # Action
            sql_query = ''
            filter_reason = ''
            if len(self.formdata["reason"]) > 0:
              filter_reason = _mysql.escape_string(self.formdata["reason"])
            if filter_action == 0:
              # Cancel post
              sql_query = "INSERT INTO `filters` (`id`, `boards`, `type`, `action`, `from`, `from_trip`, `reason`, `added`, `staff`) VALUES (%d, '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')" % \
                          (edit_id, where, str(filter_type), str(filter_action), filter_from, filter_tripcode, filter_reason, str(timestamp()), _mysql.escape_string(staff_account['username']))
            elif filter_action == 1:
              # Change to
              if len(self.formdata["changeto"]) > 0:
                filter_to = _mysql.escape_string(self.formdata["changeto"])
                sql_query = "INSERT INTO `filters` (`id`, `boards`, `type`, `action`, `from`, `from_trip`, `reason`, `to`, `added`, `staff`) VALUES (%d, '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')" % \
                          (edit_id, where, str(filter_type), str(filter_action), filter_from, filter_tripcode, filter_reason, filter_to, str(timestamp()), _mysql.escape_string(staff_account['username']))
              else:
                self.error(_("You must enter a word to change to."))
                return
            elif filter_action == 2:
              # Ban
              filter_seconds = '0'
              if len(self.formdata["seconds"]) > 0:
                filter_seconds = _mysql.escape_string(self.formdata["seconds"])
              if "blind" in self.formdata.keys() and self.formdata["blind"] == '1':
                filter_blind = '1'
              else:
                filter_blind = '2'

              sql_query = "INSERT INTO `filters` (`id`, `boards`, `type`, `action`, `from`, `from_trip`, `reason`, `seconds`, `blind`, `added`, `staff`) VALUES (%d, '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')" % \
                          (edit_id, where, str(filter_type), str(filter_action), filter_from, filter_tripcode, filter_reason, filter_seconds, filter_blind, str(timestamp()), _mysql.escape_string(staff_account['username']))
            elif filter_action == 3:
              # Redirect URL
              if len(self.formdata['redirect_url']) > 0:
                redirect_url = _mysql.escape_string(self.formdata['redirect_url'])
                redirect_time = 0
                try:
                  redirect_time = int(self.formdata['redirect_time'])
                except:
                  pass
              else:
                self.error(_("You must enter a URL to redirect to."))
                return
            
              sql_query = "INSERT INTO `filters` (`id`, `boards`, `type`, `action`, `from`, `from_trip`, `reason`, `redirect_url`, `redirect_time`, `added`, `staff`) VALUES (%d, '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')" % \
                          (edit_id, where, str(filter_type), str(filter_action), filter_from, filter_tripcode, filter_reason, redirect_url, str(redirect_time), str(timestamp()), _mysql.escape_string(staff_account['username']))
            # DO QUERY!
            if edit_id > 0:
              UpdateDb("DELETE FROM `filters` WHERE `id` = %s" % str(edit_id))
              UpdateDb(sql_query)
              message = 'Filter edited.'
            else:
              filt = FetchOne("SELECT `id` FROM `filters` WHERE `boards` = '%s' AND `type` = '%s' AND `from` = '%s'" % (where, str(filter_type), filter_from))
              if not filt:
                UpdateDb(sql_query)
                message = 'Filter added.'
              else:
                message = 'This filter already exists here:' + ' <a href="'+Settings.CGI_URL+'manage/filters/add?edit='+filt['id']+'">edit</a>'
            action_taken = True
            template_filename = "message.html"
          else:
            # Create add form
            edit_id = 0
            if 'edit' in self.formdata.keys() and int(self.formdata['edit']) > 0:
              # Load values
              edit_id = int(self.formdata['edit'])
              filt = FetchOne("SELECT * FROM `filters` WHERE `id` = %s LIMIT 1" % str(edit_id))
              if filt['boards'] == '':
                where = ''
              else:
                where = pickle.loads(filt['boards'])
              startvalues = {'type': filt['type'],
                             'trip': filt['from_trip'],
                             'where': where,
                             'action': filt['action'],
                             'changeto': cgi.escape(filt['to'], True),
                             'reason': filt['reason'],
                             'seconds': filt['seconds'],
                             'blind': filt['blind'],
                             'redirect_url': filt['redirect_url'],
                             'redirect_time': filt['redirect_time'],}
              if filt['type'] == '1':
                startvalues['name'] = filt['from']
                startvalues['word'] = ''
              else:
                startvalues['name'] = ''
                startvalues['word'] = filt['from']
            else:
              startvalues = {'type': '0',
                             'word': '',
                             'name': '',
                             'trip': '',
                             'where': [],
                             'action': '0',
                             'changeto': '',
                             'reason': _('Forbidden word'),
                             'seconds': '0',
                             'blind': '1',
                             'redirect_url': 'http://',
                             'redirect_time': '5'}
                           
            if edit_id > 0:
              submit = "Editar Filtro"
            else:
              submit = "Agregar filtro"
            
            action_taken = True
            template_filename = "filters.html"
            template_values = {'mode': 1,
              'edit_id': edit_id,
              'boards': boardlist(),
              'startvalues': startvalues,
              'submit': submit}
        elif len(path_split) > 4 and path_split[3] == 'delete':
          delid = int(path_split[4])
          UpdateDb("DELETE FROM `filters` WHERE id = '%s' LIMIT 1" % str(delid))
          message = _('Deleted filter %s.') % str(delid)
          template_filename = "message.html"
          action_taken = True
          
        if not action_taken:       
          filters = FetchAll("SELECT * FROM `filters` ORDER BY `added` DESC")
          for filter in filters:
            if filter['boards'] == '':
              filter['boards'] = _('All boards')
            else:
              where = pickle.loads(filter['boards'])
              if len(where) > 1:
                filter['boards'] = '/' + '/, /'.join(where) + '/'
              else:
                filter['boards'] = '/' + where[0] + '/'
            if filter['type'] == '0':
              filter['type_formatted'] = _('Word:') + ' <b>' + cgi.escape(filter['from']) + '</b>'
            elif filter['type'] == '1':
              filter['type_formatted'] = _('Name/Tripcode:')+' '
              if filter['from'] != '':
                filter['type_formatted'] += '<b class="name">' + filter['from'] + '</b>'
              if filter['from_trip'] != '':
                filter['type_formatted'] += '<span class="trip">' + filter['from_trip'] + '</span>'
            else:
              filter['type_formatted'] = '?'
            if filter['action'] == '0':
              filter ['action_formatted'] = _('Abort post')
            elif filter['action'] == '1':
              filter ['action_formatted'] = _('Change to:') + ' <b>' + cgi.escape(filter['to']) + '</b>'
            elif filter['action'] == '2':
              if filter['blind'] == '1':
                blind = _('Yes')
              else:
                blind = _('No')
              filter ['action_formatted'] = _('Autoban:') + '<br />' + \
                      (_('Length:')+' <i>%s</i><br />'+_('Blind:')+' <i>%s</i>') % (filter['seconds'], blind)
            elif filter['action'] == '3':
              filter ['action_formatted'] = (_('Redirect to:')+' %s ('+_('in %s secs')+')') % (filter['redirect_url'], filter['redirect_time'])
            else:
              filter ['action_formatted'] = '?'
            filter['added'] = formatTimestamp(filter['added'])
            
          template_filename = "filters.html"
          template_values = {'mode': 0, 'filters': filters}
      elif path_split[2] == 'logs':
        if staff_account['rights'] != '0' and staff_account['rights'] != '2':
          return

        logs = FetchAll('SELECT * FROM `logs` ORDER BY `timestamp` DESC')
        for log in logs:
          log['timestamp_formatted'] = formatTimestamp(log['timestamp'])
        template_filename = "logs.html"
        template_values = {'logs': logs}
      elif path_split[2] == 'logout':
        message = _('Logging out...') + '<meta http-equiv="refresh" content="0;url=' + Settings.CGI_URL + 'manage" />'
        setCookie(self, 'weabot_manage', '', domain='THIS')
        setCookie(self, 'weabot_staff', '')
        template_filename = "message.html"
      elif path_split[2] == 'quotes':
        # Quotes for the post screen
        if "save" in self.formdata.keys():
          try:
            f = open('quotes.conf', 'w')
            f.write(self.formdata["data"])
            f.close()
            message = 'Datos guardados.'
            template_filename = "message.html"
          except:
            message = 'Error al guardar datos.'
            template_filename = "error.html"
        try:
          f = open('quotes.conf', 'r')
          data = cgi.escape(f.read(1048576), True)
          f.close()
          template_filename = "quotes.html"
          template_values = {'data': data}
        except:
          message = 'Error al leer datos.'
          template_filename = 'message.html'
      elif path_split[2] == 'recent_images':
        try:
          if int(self.formdata['images']) > 100:
            images = '100'
          else:
            images = self.formdata['images']
          posts = FetchAll('SELECT * FROM `posts` INNER JOIN `boards` ON boardid = boards.id WHERE CHAR_LENGTH(`thumb`) > 0 ORDER BY `timestamp` DESC LIMIT ' + _mysql.escape_string(images))
        except:
          posts = FetchAll('SELECT * FROM `posts` INNER JOIN `boards` ON boardid = boards.id WHERE CHAR_LENGTH(`thumb`) > 0 ORDER BY `timestamp` DESC LIMIT 10')
        template_filename = "recent_images.html"
        template_values = {'posts': posts}
      elif path_split[2] == 'news':
        if not administrator:
          return
        
        type = 1
        if 'type' in self.formdata:
          type = int(self.formdata['type'])
          
        if type > 2:
          raise UserError, "Tipo no soportado"
        
        # canal del home
        if len(path_split) > 3:
          if path_split[3] == 'add':
            t = datetime.datetime.now()
              
            # Insertar el nuevo post
            title = ''
            message = self.formdata["message"].replace("\n", "<br />")
            
            # Titulo
            if 'title' in self.formdata:
              title = self.formdata["title"]
              
            # Post anonimo
            if 'anonymous' in self.formdata.keys() and self.formdata['anonymous'] == '1':
              to_name = "Staff ★"
            else:
              to_name = "%s ★" % staff_account['username']
            timestamp_formatted = formatDate(t)
            if type > 0:
              timestamp_formatted = re.sub(r"\(.+", "", timestamp_formatted)
            else:
              timestamp_formatted = re.sub(r"\(...\)", " ", timestamp_formatted)
            
            UpdateDb("INSERT INTO `news` (type, staffid, staff_name, title, message, name, timestamp, timestamp_formatted) VALUES (%d, '%s', '%s', '%s', '%s', '%s', '%d', '%s')" % (type, staff_account['id'], staff_account['username'], _mysql.escape_string(title), _mysql.escape_string(message), to_name, timestamp(t), timestamp_formatted))
            
            regenerateNews()
            regenerateHome()
            message = _("Added successfully.")
            template_filename = "message.html"
          if path_split[3] == 'delete':
            # Eliminar un post
            id = int(path_split[4])
            UpdateDb("DELETE FROM `news` WHERE id = %d AND type = %d" % (id, type))
            regenerateNews()
            regenerateHome()
            message = _("Deleted successfully.")
            template_filename = "message.html"
        else:
          posts = FetchAll("SELECT * FROM `news` WHERE type = %d ORDER BY `timestamp` DESC" % type)
          template_filename = "news.html"
          template_values = {'action': type, 'posts': posts}
      elif path_split[2] == 'newschannel':
        #if not administrator:
        #  return
        
        if len(path_split) > 3:
          if path_split[3] == 'add':
            t = datetime.datetime.now()
            # Delete old posts
            #posts = FetchAll("SELECT `id` FROM `news` WHERE `type` = '1' ORDER BY `timestamp` DESC LIMIT "+str(Settings.MODNEWS_MAX_POSTS)+",30")
            #for post in posts:
            #  UpdateDb("DELETE FROM `news` WHERE id = " + post['id'] + " AND `type` = '0'")
              
            # Insert new post
            message = ''
            try:
              # Cut long lines
              message = self.formdata["message"]
              message = clickableURLs(cgi.escape(message).rstrip()[0:8000])
              message = onlyAllowedHTML(message)
              if Settings.USE_MARKDOWN:
                message = markdown(message)
              if not Settings.USE_MARKDOWN:
                message = message.replace("\n", "<br />")
            except:
              pass
            
            # If it's preferred to remain anonymous...
            if 'anonymous' in self.formdata.keys() and self.formdata['anonymous'] == '1':
              to_name = "Staff ★"
            else:
              to_name = "%s ★" % staff_account['username']
            timestamp_formatted = formatDate(t)
            
            UpdateDb("INSERT INTO `news` (type, staffid, staff_name, title, message, name, timestamp, timestamp_formatted) VALUES ('0', '%s', '%s', '%s', '%s', '%s', '%d', '%s')" % (staff_account['id'], staff_account['username'], _mysql.escape_string(self.formdata['title']), _mysql.escape_string(message), to_name, timestamp(t), timestamp_formatted))
            
            message = _("Added successfully.")
            template_filename = "message.html"
          if path_split[3] == 'delete':            
            if not administrator:
              # We check that if he's not admin, he shouldn't be able to delete other people's posts
              post = FetchOne("SELECT `staffid` FROM `news` WHERE id = '"+_mysql.escape_string(path_split[4])+"' AND type = '0'")
              if post['staffid'] != staff_account['id']:
                self.error(_('That post is not yours.'))
                return
            
            # Delete!
            UpdateDb("DELETE FROM `news` WHERE id = '" + _mysql.escape_string(path_split[4]) + "' AND type = '0'")
            message = _("Deleted successfully.")
            template_filename = "message.html"
        else:
          # If he's not admin, show only his own posts
          if administrator:
            posts = FetchAll("SELECT * FROM `news` WHERE type = '0' ORDER BY `timestamp` DESC")
          else:
            posts = FetchAll("SELECT * FROM `news` WHERE staffid = '"+staff_account['id']+"' AND type = '0' ORDER BY `timestamp` DESC")
          
          template_filename = "news.html"
          template_values = {'action': 'newschannel', 'posts': posts}
      elif path_split[2] == 'reports':
        if not moderator:
          return
        
        message = None
        import math
        pagesize = float(Settings.REPORTS_PER_PAGE)
        totals = FetchOne("SELECT COUNT(id) FROM `reports`")
        total = int(totals['COUNT(id)'])
        pages = int(math.ceil(total / pagesize))
        
        try:
          currentpage = int(path_split[3])
        except:
          currentpage = 0
        
        if len(path_split) > 4:
          if path_split[4] == 'ignore':
            # Delete report
            UpdateDb("DELETE FROM `reports` WHERE `id` = '"+_mysql.escape_string(path_split[5])+"'")
            message = _('Report %s ignored.') % path_split[5]
        if 'ignore' in self.formdata.keys():
          ignored = 0
          if 'board' in self.formdata.keys() and self.formdata['board'] != 'all':
            reports = FetchAll("SELECT `id` FROM `reports` WHERE `board` = '%s' ORDER BY `timestamp` DESC LIMIT %d, %d" % (_mysql.escape_string(self.formdata['board']), currentpage*pagesize, pagesize))
          else:
            reports = FetchAll("SELECT `id` FROM `reports` ORDER BY `timestamp` DESC LIMIT %d, %d" % (currentpage*pagesize, pagesize))
          
          for report in reports:
            keyname = 'i' + report['id']
            if keyname in self.formdata.keys():
              # Ignore here
              UpdateDb("DELETE FROM `reports` WHERE `id` = '"+_mysql.escape_string(report['id'])+"'")
              ignored += 1
              
          message = _('Ignored %s report(s).') % str(ignored)
        
        # Generate board list
        boards = FetchAll('SELECT `name`, `dir` FROM `boards` ORDER BY `dir`')
        for board in boards:
          if 'board' in self.formdata.keys() and self.formdata['board'] == board['dir']:
            board['checked'] = True
          else:
            board['checked'] = False
        
        # Tabla
        if 'board' in self.formdata.keys() and self.formdata['board'] != 'all':
          reports = FetchAll("SELECT id, timestamp, timestamp_formatted, postid, parentid, link, board, INET_NTOA(ip) AS ip, reason, reporterip FROM `reports` WHERE `board` = '%s' ORDER BY `timestamp` DESC LIMIT %d, %d" % (_mysql.escape_string(self.formdata['board']), currentpage*pagesize, pagesize))
        else:
          reports = FetchAll("SELECT id, timestamp, timestamp_formatted, postid, parentid, link, board, INET_NTOA(ip) AS ip, reason, reporterip FROM `reports` ORDER BY `timestamp` DESC LIMIT %d, %d" % (currentpage*pagesize, pagesize))
        
        if 'board' in self.formdata.keys():
          curboard = self.formdata['board']
        else:
          curboard = None
          
        #for report in reports:
        #  if report['parentid'] == '0':
        #    report['link'] = Settings.BOARDS_URL + report['board'] + '/res/' + report['postid'] + '.html#' + report['postid']
        #  else:
        #    report['link'] = Settings.BOARDS_URL + report['board'] + '/res/' + report['parentid'] + '.html#' + report['postid']

        navigator = ''
        if currentpage > 0:
          navigator += '<a href="'+Settings.CGI_URL+'manage/reports/'+str(currentpage-1)+'">&lt;</a> '
        else:
          navigator += '&lt; '
        
        for i in range(pages):
          if i != currentpage:
            navigator += '<a href="'+Settings.CGI_URL+'manage/reports/'+str(i)+'">'+str(i)+'</a> '
          else:
            navigator += str(i)+' '
          
        if currentpage < (pages-1):
          navigator += '<a href="'+Settings.CGI_URL+'manage/reports/'+str(currentpage+1)+'">&gt;</a> '
        else:
          navigator += '&gt; '
        
        template_filename = "reports.html"
        template_values = {'message': message,
          'boards': boards,
          'reports': reports,
          'currentpage': currentpage,
          'curboard': curboard,
          'navigator': navigator}
      # Show by IP
      elif path_split[2] == 'ipshow':
        if not moderator:
          return
          
        if 'ip' in self.formdata.keys():
          # If an IP was given...
          if self.formdata['ip'] != '':
            formatted_ip = str(inet_aton(self.formdata['ip']))
            posts = FetchAll("SELECT posts.*, boards.dir, boards.board_type, boards.subject AS default_subject FROM `posts` JOIN `boards` ON boards.id = posts.boardid WHERE ip = '%s' ORDER BY posts.timestamp DESC" % _mysql.escape_string(formatted_ip))
            if posts:
              ip = self.formdata['ip']
              template_filename = "ipshow.html"
              template_values = {"mode": 1, "ip": ip, "host": getHost(ip), "country": getCountry(ip), "tor": addressIsTor(ip), "posts": posts}
            else:
              message = "No hay posts."
              template_filename = "error.html"
        else:
          # Generate form
          template_filename = "ipshow.html"
          template_values = {"mode": 0}
      elif path_split[2] == 'ipdelete':
        if not moderator:
          return
        
        # Delete by IP
        if 'ip' in self.formdata.keys():
          # If an IP was given...
          if self.formdata['ip'] != '':
            where = []
            if 'board_all' not in self.formdata.keys():
              # If he chose boards separately, add them to a list
              boards = FetchAll('SELECT `id`, `dir` FROM `boards`')
              for board in boards:
                keyname = 'board_' + board['dir']
                if keyname in self.formdata.keys():
                  if self.formdata[keyname] == "1":
                    where.append(board)
            else:
              # If all boards were selected="selected", all them all to the list
              where = FetchAll('SELECT `id`, `dir` FROM `boards`')
            
            # If no board was chosen
            if len(where) <= 0:
              self.error(_("Select a board first."))
              return
              
            deletedPostsTotal = 0
            ip = inet_aton(self.formdata['ip'])
            deletedPosts = 0
            for theboard in where:
              board = setBoard(theboard['dir'])
              isDeletedOP = False
              
              # delete all starting posts first
              op_posts = FetchAll("SELECT `id`, `message` FROM posts WHERE parentid = 0 AND boardid = '" + board['id'] + "' AND ip = " + str(ip))
              for post in op_posts:
                deletePost(post['id'], None)
                
                deletedPosts += 1
                deletedPostsTotal += 1
              
              replies = FetchAll("SELECT `id`, `message`, `parentid` FROM posts WHERE parentid != 0 AND boardid = '" + board['id'] + "' AND ip = " + str(ip))
              for post in replies:
                deletePost(post['id'], None, '2')
                
                deletedPosts += 1
                deletedPostsTotal += 1
              
              regenerateHome()
              
              if deletedPosts > 0:
                message = '%(posts)s post(s) were deleted from %(board)s.' % {'posts': str(deletedPosts), 'board': '/' + board['dir'] + '/'}
                template_filename = "message.html"
                #logAction(staff_account['username'], '%(posts)s post(s) were deleted from %(board)s. IP: %(ip)s' % \
                #  {'posts': str(deletedPosts),
                #   'board': '/' + board['dir'] + '/',
                #   'ip': self.formdata['ip']})
          else:
            self.error(_("Please enter an IP first."))
            return
          
          message = 'In total %(posts)s from IP %(ip)s were deleted.' % {'posts': str(deletedPosts), 'ip': self.formdata['ip']}
          template_filename = "message.html"
        else:  
          # Generate form...
          template_filename = "ipdelete.html"
          template_values = {'boards': boardlist()}
    else:
      # Main page.
      reports = FetchOne("SELECT COUNT(1) FROM `reports`", 0)[0]
      posts = FetchAll("SELECT * FROM `news` WHERE type = '0' ORDER BY `timestamp` DESC")
      
      template_filename = "manage.html"
      template_values = {'reports': reports, 'posts': posts}

  if not skiptemplate:
    try:
      if template_filename == 'message.html' or template_filename == 'error.html':
        template_values = {'message': message}
    except:
      template_filename = 'message.html'
      template_values = {'message': '???'}
      
    template_values.update({
      'title': 'Manage',
      'validated': validated,
      'page': page,
    })
    
    if validated:
      template_values.update({
        'username': staff_account['username'],
        'site_title': Settings.SITE_TITLE,
        'rights': staff_account['rights'],
        'administrator': administrator,
        'added': formatTimestamp(staff_account['added']),
      })
    
    self.output += renderTemplate("manage/" + template_filename, template_values)

def logAction(staff, action):
  InsertDb("INSERT INTO `logs` (`timestamp`, `staff`, `action`) VALUES (" + str(timestamp()) + ", '" + _mysql.escape_string(staff) + "\', \'" + _mysql.escape_string(action) + "\')")

def boardlist():
  boards = FetchAll('SELECT * FROM `boards` ORDER BY `board_type`, `dir`')
  return boards
  
def filetypelist():
  filetypes = FetchAll('SELECT * FROM `filetypes` ORDER BY `ext` ASC')
  return filetypes

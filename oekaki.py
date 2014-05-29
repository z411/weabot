# coding=utf-8
import _mysql
import os
import cgi
import random

from database import *
from settings import Settings
from framework import *
from formatting import *
from template import *
from post import *

def oekaki(self, path_split):
  """
  Este script hace todo lo que tiene que hacer con los
  archivos de Oekaki.
  """
  page = ''
  skiptemplate = False
  
  if len(path_split) > 2:
    # Inicia el applet. Lo envia luego a este mismo script, a "Finish".
    if path_split[2] == 'paint':
      # Veamos que applet usar
      applet = self.formdata['oek_applet'].split('|')
      
      if applet[1] == 'y':
        applet_str = 'pro'
      else:
        applet_str = ''
      
      if applet[2] == 'y':
        use_selfy = True
      else:
        use_selfy = False
      
      # Sacamos el timestamp que usaremos
      t = datetime.datetime.now()
      ts = str(timestamp(t)) + str(random.randint(10, 99))
      
      # Obtenemos el board
      board = setBoard(self.formdata['board'])
      
      # Veamos a quien le estamos respondiendo
      try:
        parentid = int(self.formdata['parent'])
      except:
        parentid = 0
      
      # Vemos si el usuario quiere una animacion
      if 'oek_animation' in self.formdata.keys():
        animation = True
        animation_str = 'animation'
      else:
        animation = False
        animation_str = ''
      
      # Nos aseguramos que la entrada es numerica
      try:
        width = int(self.formdata['oek_x'])
        height = int(self.formdata['oek_y'])
      except:
        raise UserError, 'Valores de tamaño inválidos'
      
      params = {
        'dir_resource': Settings.BOARDS_URL + 'oek_temp/',
        'tt.zip': 'tt_def.zip',
        'res.zip': 'res.zip',
        'MAYSCRIPT': 'true',
        'scriptable': 'true',
        'tools': applet_str,
        'layer_count': '5',
        'undo': '90',
        'undo_in_mg': '15',
        'url_save': Settings.BOARDS_URL + 'oek_temp/save.php?ts=' + ts,
        'poo': 'false',
        'send_advance': 'true',
        'send_language': 'utf8',
        'send_header': '',
        'send_header_image_type': 'false',
        'thumbnail_type': animation_str,
        'image_jpeg': 'false',
        'image_size': '92',
        'compress_level': '4'
      }
      
      if 'oek_edit' in self.formdata.keys():
        # Si hay que editar, cargar la imagen correspondiente en el canvas
        params['image_canvas'] = Settings.BOARDS_URL + board['dir'] + '/src/' + self.formdata['oek_edit']
        params['image_width'] = self.formdata['oek_edit_x']
        params['image_height'] = self.formdata['oek_edit_y']
      else:
        params['image_width'] = str(width)
        params['image_height'] = str(height)
        
      # Darle las dimensiones al exit script
      params['url_exit'] = Settings.CGI_URL + 'oekaki/finish/' + board['dir'] + '/' + str(parentid) + '/' + str(ts) + '/' + params['image_width'] + '/' + params['image_height']
      
      page += '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">' + \
      '<html xmlns="http://www.w3.org/1999/xhtml"><head><style type="text/css">html, body{margin: 0; padding: 0;height:100%;} .full{width:100%;height:100%;}</style>'
      if use_selfy:
        page += '<script type="text/javascript" src="'+Settings.HOME_URL+'static/js/palette_selfy.js"></script>';
      page += '</head><body bgcolor="#AEAED9"><table class="full"><tbody><tr><td class="full">'
      
      page += '<applet id="oekaki" code="c.ShiPainter.class" archive="' + Settings.BOARDS_URL + 'oek_temp/spainter_all.jar" width="100%" height="100%" mayscript="">'
      for key in params.keys():
        page += '<param name="' + key + '" value="' + cleanString(params[key]) + '" />' + "\n"
      page += '</applet></td>'
      if use_selfy:
        page += '<td><script type="text/javascript">palette_selfy();</script></td>'
      page += '</tr></tbody></table></body></html>'
    
    elif path_split[2] == 'finish':
      # path splits:
      # 3: Board
      # 4: Parentid
      # 5: Timestamp
      # 6: Width
      # 7: Height
      if path_split > 7:
        # Al terminar de dibujar, llegamos aqui. Damos la opcion de postearlo.
        board = setBoard(path_split[3])
        try:
          parentid = int(path_split[4])
        except:
          parentid = None
        
        try:
          ts = int(path_split[5])
        except:
          ts = 0
          raise UserError, 'Timestamp inválido'
        
        try:
          width = int(path_split[6])
          height = int(path_split[7])
        except:
          raise UserError, 'Valores de tamaño inválidos'
        
        try:
          timetaken = timestamp() - int(path_split[5][:-2])
        except:
          timetaken = 0
        
        page += renderTemplate("board.html", {"threads": None, "oek_finish": ts, "timetaken": timetaken, "replythread": parentid, "oek_file_x": width, "oek_file_y": height})
      
    elif path_split[2] == 'animation':
      try:
        board = setBoard(path_split[3])
        file = int(path_split[4])
      except:
        raise UserError, 'Board o archivo de animación inválido.'
      
      params = {
        'pch_file': Settings.BOARDS_URL + board['dir'] + '/src/' + str(file) + '.pch',
        'run': 'true',
        'buffer_progress': 'false',
        'buffer_canvas': 'true',
        'speed': '2',
        'res.zip': Settings.BOARDS_URL + 'oek_temp/res/' +'res.zip',
        'tt.zip': Settings.BOARDS_URL + 'oek_temp/res/' + 'tt.zip',
        'tt_size': '31'
      }
      page += '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">' + \
      '<html xmlns="http://www.w3.org/1999/xhtml">\n<head><style type="text/css">html, body{margin: 0; padding: 0;height:100%;} .full{width:100%;height:100%;}</style>\n<title>Bienvenido a Internet | Oekaki</title>\n</head>\n' + \
      '<body bgcolor="#CFCFFF" text="#800000" link="#003399" vlink="#808080" alink="#11FF11">\n' + \
      '<table cellpadding="0" cellspacing="0" class="full"><tr><td class="full">\n'
      page += '<applet name="pch" code="pch2.PCHViewer.class" archive="' + Settings.BOARDS_URL + 'oek_temp/PCHViewer123.jar" width="100%" height="100%">'
      for key in params.keys():
        page += '<param name="' + key + '" value="' + cleanString(params[key]) + '" />' + "\n"
      page += '<div align="center">Java must be installed and enabled to use this applet. Please refer to our Java setup tutorial for more information.</div>'
      page += '</applet>\n</td></tr></table>\n</body>\n</html>'

  if not skiptemplate:
    """template_values = {
      'title': 'Manage',
      'validated': validated,
      'page': page,
      'navbar': False,
    }
    
    if validated:
      template_values.update({
        'username': staff_account['username'],
        'rights': staff_account['rights'],
        'administrator': administrator,
        'added': formatTimestamp(staff_account['added']),
      })
    
    self.output += renderTemplate('manage.html', template_values)"""
    self.output = page

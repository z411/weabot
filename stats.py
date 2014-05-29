# coding=utf-8
import datetime
import time

from database import *
from settings import Settings
from framework import *

def getTimestamp(board):
  if board == "!ALL":
    boardname = "all"
  else:
    boardname = "b_" + board

  try:
    f = open(Settings.STATIC_DIR + 'swf/' + boardname + '.timestamp', 'r')
    try:
      timestamp = f.read(100)
    finally:
      f.close()
  except:
    timestamp = 0

  return int(timestamp)

def regenerate(lookback):
  # TODO : Cargar los sages desde settings, hacer todo mas modular y rapido
  
  boards = FetchAll("SELECT `id`, `dir` FROM `boards`")
  last_week = int(lookback)

  content = "<table id=\"sortable\" border=\"2\"><thead><tr><th></th><th><b><a>Posts</a></b></th><th><b><a>Usuarios</a></b></th><th><b><a>Posts por d&iacute;a</a></b></th></tr></thead><tbody>"
  for board in boards:
    stats = FetchOne("SELECT COUNT(1), COUNT(DISTINCT(`ip`)), (SELECT COUNT(1) FROM `posts` WHERE boardid = '" + board['id'] + "' AND timestamp > '" + str(timestamp() - 604800) + "') FROM `posts` WHERE boardid = '" + board['id'] + "' AND IS_DELETED = 0", 0)
    content += '<tr><td><b>/' + board['dir'] + '/</b></td>' + \
            '<td>' + stats[0] + '</td>' + \
            '<td>' + stats[1] + '</td>' + \
            '<td>' + str(round(float(stats[2]) / 7.0, 1)) + '</td></tr>'
  content += "</tbody></table>"
  f = open(Settings.STATIC_DIR + 'swf/all_boardlist.table', 'w')
  try:
    f.write(content)
  finally:
    f.close()

  # Generate posts per day
  query = FetchAll("select floor(timestamp/86400)*86400,count(1),count(case file when '' then NULL else 1 end),count(case when email='sage' or email='cejas' then 1 else NULL end) from posts where timestamp > '"+str(last_week)+"' AND IS_DELETED = 0 group by floor(timestamp/86400) order by floor(timestamp/86400);", 0)
  json = {"elements": [None,None,None], "title": {"text": "Posts por dia (ultimas 2 semanas)"}, "x_axis": {"labels": { "labels": []}}, "y_axis": {"max": 10}}
  json["elements"][0] = {"values": [], "type": "line", "font-size": 10, "text": "Posts", "colour": "#0000FF", "width": 4}
  json["elements"][1] = {"values": [], "type": "line", "font-size": 10, "text": "Imagenes", "colour": "#00AA00", "width": 2}
  json["elements"][2] = {"values": [], "type": "line", "font-size": 10, "text": "Sages", "colour": "#FF0000", "width": 1}

  max_y = 10
  for day in query:
    if int(int(day[1])) > max_y:
      max_y = int(day[1])

    time = datetime.datetime.fromtimestamp(int(day[0]) + 86400).strftime("%d/%m")
    json["x_axis"]["labels"]["labels"].append(time)
    json["elements"][0]["values"].append(int(day[1]))
    json["elements"][1]["values"].append(int(day[2]))
    json["elements"][2]["values"].append(int(day[3]))

  json["y_axis"]["max"] = max_y

  f = open(Settings.STATIC_DIR + 'swf/all_posts.json', 'w')
  try:
    f.write(str(json).replace("'", "\""))
  finally:
    f.close()

  # Generate users
  query = FetchOne("select floor(timestamp/86400)*86400,count(case when tripcode !='' then 1 else NULL end),count(case when name !='' and tripcode='' then 1 else NULL end),count(case when name='' and tripcode='' then 1 else NULL end) from posts where timestamp > '"+str(last_week)+"' AND IS_DELETED = 0", 0)
  json = {"elements": [{"type": "pie", "tip": "#val# de #total#\n#percent# de 100%", "values":
    [{"value": int(query[3]), "label": "Anonimo", "colour": "#00BB00", "label-colour": "#00BB00"},
     {"value": int(query[2]), "label": "Namefags", "colour": "#BB0000", "label-colour": "#FF0000"},
     {"value": int(query[1]), "label": "Tripfags", "colour": "#0000BB", "label-colour": "#0000FF"}]}], "title": {"text": "Posts por tipo de usuario (ultimas 2 semanas)" }}

  f = open(Settings.STATIC_DIR + 'swf/all_userpie.json', 'w')
  try:
    f.write(str(json).replace("'", "\""))
  finally:
    f.close()

  # Generate top 10 users list
  query = FetchAll("select name,tripcode,count(1) from posts WHERE IS_DELETED = 0 group by name,tripcode order by count(1) desc limit 20",0)
  content = '<table border="2"><tr><th>Nombre</th><th>Posts</th></tr>'
  for user in query:
    if user[1] != '':
      tripcode = '!' + user[1]
    else:
      tripcode = ''

    content += '<tr><td><b>' + user[0] + '</b>' + tripcode + ' </td>' + \
            '<td>' + user[2] + '</td></tr>'
  content += "</table>"

  f = open(Settings.STATIC_DIR + 'swf/all_userlist.table', 'w')
  try:
    f.write(content)
  finally:
    f.close()

  # Write timestamp
  f = open(Settings.STATIC_DIR + 'swf/all.timestamp', 'w')
  try:
    f.write(str(timestamp()))
  finally:
    f.close()

def flashObject(dataf):
  return '<object>' + \
	 '<param name="movie" value="'+Settings.STATIC_URL+'swf/open-flash-chart.swf?data-file='+Settings.STATIC_URL+'swf/' + dataf + '" /><param name="allowScriptAccess" value="always" />' + \
         '<embed src="'+Settings.STATIC_URL+'swf/open-flash-chart.swf?data-file='+Settings.STATIC_URL+'swf/'+ dataf + '" allowScriptAccess="always" width="600" height="300" type="application/x-shockwave-flash" />' + \
         '</object>'

def tableObject(dataf):
  f = open(Settings.STATIC_DIR + 'swf/' + dataf, 'r')
  try:
    table = f.read(1048576)
  finally:
    f.close()

  return table

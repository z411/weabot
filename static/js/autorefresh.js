var lastTime = 0;
var refreshInterval;
var refreshMaxTime = 30;
var refreshTime;
var manual = 0;
var unread = {};
var serviceType = 0; // 1 = Home, 2 = BBS, 3 = IB
var last_threads = 0;
var last_serverTime = 0;
var thread_length = 0;
var thread_lastreply = 0;
var thread_title = "";
var thread_first_length = 0;
var http_request = new XMLHttpRequest();

function checkNew(e) {
  e.preventDefault();
  manual = 1;
  loadJSON();
  if (chk.checked)
    refreshMaxTime = 25;
}

function loadJSON() {
  if (chk.checked)
    stopCounter("...");
  if (manual)
    document.getElementById("counter").innerText = "...";
  var data_file;
  if (serviceType == 1) {
    data_file = "/cgi/api/lastage?time=" + lastTime + "&limit=" + document.getElementById("limit").value;
  } else if (serviceType == 2 || serviceType == 3) {
    board = document.getElementsByName("board")[0].value;
    parent = document.getElementsByName("parent")[0].value;
    if (serviceType == 3) {
      default_subject = document.getElementsByName("default_subject")[0].value;
    }
    data_file = "/cgi/api/thread?dir=" + board + "&id=" + parent + "&offset=" + thread_length + "&time=" + lastTime;
  } else {
    return false;
  }
  http_request.open("GET", data_file, true);
  http_request.send();
}

function setRead(threadId) {
  if (threadId in unread) {
    unread[threadId] = false;
    updatePostList(last_threads, last_serverTime);
  }
}

function updatePostList(threads, serverTime) {
  if (refreshMaxTime <= 120)
    refreshMaxTime += 5;
  var arrayLength = threads.length;
  if (!arrayLength) return;

  html = "";
  last_threads = threads;
  last_serverTime = serverTime;

  var newposts = 0;
  var newTitle = "Bienvenido a Internet BBS/IB";
  var new_unread = false;
  var news = [];

  for (var i = 0; i < arrayLength; i++) {
    thread = threads[i];

    if (thread.bumped >= lastTime) {
      unread[thread.id] = true;
      news.push('- ' + thread.board_fulln + ': ' + thread.content);
      new_unread = true;
    }
    if (unread[thread.id]) html += '<span class="new">';
    html += '<a href="' + thread.url + '" class="thread"><span class="brd">[' + thread.board_name + ']</span> <span class="cont">' + thread.content + '</span> <span class="rep">(' + thread.length + ')</span></a>';
    
    if (unread[thread.id]) {
      html += '</span>';
      newposts++;
    }
  }
  if (newposts) {
    newTitle = '(' + newposts + ') ' + newTitle;
  }

  if (new_unread) {
    document.getElementById("newposts").style = "color:red";
    notif('Bienvenido a Internet BBS/IB', 'Hay nuevos mensajes:\n' + news.join('\n'));
    refreshMaxTime = 10;
    if (document.getElementById('autosound').checked) {
      document.getElementById("machina").volume = 0.6;
      document.getElementById("machina").volume = 0.6;
      document.getElementById("machina").play();
    }
  }

  window.parent.document.title = newTitle;
  document.title = newTitle;
  document.getElementById("postlist").innerHTML = html;
}

function updateThread(posts, total_replies, serverTime) {
  thread_div = document.getElementsByClassName("thread")[0];
  if (serviceType == 2)
    last_elem = document.getElementsByClassName("size")[0];
  else
    last_elem = document.getElementsByClassName("cut")[0];

  for (var i = 0; i < posts.length; i++) {
    post = posts[i];
    var div = document.createElement('div');
    if (serviceType == 2) div.className = "reply";
    else div.className = "replycont";
    if (post.email) {
      if (post.tripcode) s_name = '<a href="mailto:' + post.email + '"><span class="name"><b>' + post.name + '</b> ' + post.tripcode + '</span></a>';
      else s_name = '<a href="mailto:' + post.email + '"><span class="name"><b>' + post.name + '</b></span></a>';
    } else {
      if (post.tripcode) s_name = '<span class="name"><b>' + post.name + '</b> ' + post.tripcode + '</span>';
      else s_name = '<span class="name"><b>' + post.name + '</b></span>';
    }
    if (serviceType == 2) {
      if (post.file) {
        s_img = '<a href="/' + board + '/src/' + post.file + '" target="_blank" class="thumb"><img src="/' + board + '/thumb/' + post.thumb + '" width="' + post.thumb_width + '" height="' + post.thumb_height + '" /><br />' + Math.round(post.file_size/1024) + 'KB ' + post.file.substring(post.file.lastIndexOf(".")+1, post.file.length).toUpperCase() + '</a>';
      } else s_img = '';
      if (post.IS_DELETED == 1) div.innerHTML = '<h4 class="deleted">' + (thread_length + i + 1) + ' : Mensaje eliminado por el usuario.</h4>';
      else if (post.IS_DELETED == 2) div.innerHTML = '<h4 class="deleted">' + (thread_length + i + 1) + ' : Mensaje eliminado por miembro del staff.</h4>';
           else
             div.innerHTML = '<h4>' + (thread_length + i + 1) + ' : ' + s_name + ' : <span class="date" data-unix="' + post.timestamp + '">' + post.timestamp_formatted + '</span> <span class="del"><a href="/cgi/report/' + board + '/' + post.id + '/' + (thread_length + i + 1) + '" rel="nofollow">rep</a> <a href="#">del</a></span></h4>' + s_img + '<div class="msg">' + post.message + '</div>';
    } else {
      if (post.file) {
        if (post.image_width != 0) {
          s_img = '<div class="fs"><a href="/' + board + '/src/' + post.file + '" class="expimg" data-id="' + post.id + '" data-thumb="/' + board + '/thumb/' + post.thumb + '" data-w="' + post.image_width + '" data-h="' + post.image_height + '" data-tw="' + post.thumb_width + '" data-th="' + post.thumb_height + '">' + post.file + '</a>-(' + post.file_size+ ' B, ' + post.image_width + 'x' + post.image_height + ') <span class="thumbmsg">Mostrando miniatura</span></div>';
        } else {
          s_img = '<div class="fs"><a href="/' + board + '/src/' + post.file + '" target="_blank">' + post.file + '</a>-(' + post.file_size+ ' B)</div>';
        }
        s_img += '<a target="_blank" href="/' + board + '/src/' + post.file + '" id="thumb' + post.id + '"><img class="thumb" alt="' + post.id + '" src="/' + board + '/thumb/' + post.thumb + '" width="' + post.thumb_width + '" height="' + post.thumb_height + '" /></a>';
        s_msg = '<blockquote style="margin-left:' + (post.thumb_width+40) + 'px;">' + post.message + '</blockquote>';
      } else {
        s_img = '';
        s_msg = '<blockquote>' + post.message + '</blockquote>';
      }
      if (post.IS_DELETED == 0) {
        div.innerHTML = '<table border="0"><tr><td class="ell">…</td><td class="reply" id="reply' + post.id + '"><div class="info"><input type="checkbox" name="delete" value="' + post.id + '" /><span class="subj">' + (post.subject ? post.subject : default_subject) + '</span> Nombre ' + s_name + ' ' + '<span class="date" data-unix="' + post.timestamp + '">' + post.timestamp_formatted + '</span> <span class="reflink"><a href="#' + post.id + '">No.</a><a href="#" class="postid">' + post.id + '</a></span> <a class="rep" href="/cgi/report/' + board + '/' + post.id + '" rel="nofollow">rep</a></div>' + s_img + s_msg + '</td></tr></table>';
      }
    }

    thread_div.insertBefore(div, last_elem);
    thread_div.setAttribute('data-length',(thread_length + i + 1));
  }

  if (posts.length > 0) {
    if (!manual)
      refreshMaxTime = 10;
    if (!document.hasFocus())
      if (posts.length > 1)
        notif(thread_title, posts.length + ' nuevos mensajes');
      else
        notif(thread_title, 'Un nuevo mensaje');
  } else {
    if (refreshMaxTime <= 60)
      refreshMaxTime += 5;
  }

  thread_length = parseInt(total_replies) + 1;
  //document.getElementsByClassName("thread")[0].firstChild.children[0].innerHTML = "("+thread_length+")";
  new_unread = thread_length - thread_first_length;

  if (new_unread)
    document.title = "(" + new_unread + ") " + thread_title;
  else
    document.title = thread_title;
}

function notif(title, msg) {
  var n = new Notification(title, {
    body: msg
  });
  setTimeout(n.close.bind(n), 10000);
}

function counter() {
  if (refreshTime < 1) {
    loadJSON();
  } else {
    refreshTime--;
    if (serviceType == 1)
      document.getElementById("counter").innerHTML = "– " + (refreshTime + 1);
    else
      document.getElementById("counter").innerHTML = (refreshTime + 1);
  }
}

function detectService() {
  if (document.body.className === "threadpage") {
    if (!document.getElementById("n")) return;
    thread_title = document.title;
    thread_length = parseInt(document.getElementsByClassName("thread")[0].dataset.length);
    thread_first_length = thread_length;
    replylist = document.getElementsByClassName("reply");
    lastr = replylist[replylist.length - 1].textContent;
    thread_lastreply = parseInt(lastr.substr(0, lastr.indexOf(" :")));
    if (thread_length == thread_lastreply) {
      serviceType = 2;
      document.getElementById("n").addEventListener("click", checkNew);
      var footer = document.getElementsByClassName("lastposts")[0];
      var in1 = document.createElement("input");
      in1.id = "autorefresh";
      in1.setAttribute("type", "checkbox");
      in1.addEventListener("click", autoRefresh);
      in1.style.display = "none";
      var in2 = document.createElement("label");
      in2.id = "n2";
      in2.setAttribute("for", "autorefresh");
      in2.style.marginRight = "4px";
      in2.style.cursor = "pointer";
      in2.textContent = "Auto refresh";
      var in3 = document.createElement("span");
      in3.id = "counter";
      in3.style.position = "absolute";
      in3.textContent = "OFF";
      footer.appendChild(document.createTextNode(" | "));
      footer.appendChild(in1);
      footer.appendChild(in2);
      footer.appendChild(in3);
      return true;
    } else {
      return false;
    }
  } else if (document.body.className === "res") {
    serviceType = 3;
    thread_title = document.title;
    thread_length = parseInt(document.getElementsByClassName("thread")[0].dataset.length);
    thread_first_length = thread_length;
    replylist = document.getElementsByClassName("thread");
    replylist += document.getElementsByClassName("reply");
    var footer = document.getElementsByClassName("nav")[0];
    var mnl = document.createElement("a");
    mnl.id = "n";
    mnl.href = "#";
    mnl.textContent = "Ver nuevos posts";
    var in1 = document.createElement("input");
    in1.id = "autorefresh";
    in1.setAttribute("type", "checkbox");
    in1.addEventListener("click", autoRefresh);
    in1.style.display = "none";
    var in2 = document.createElement("label");
    in2.setAttribute("for", "autorefresh");
    in2.style.cursor = "pointer";
    in2.title = "Ver nuevos posts automáticamente";
    in2.textContent = "Auto";
    var in4 = document.createElement("span");
    in4.id = "counter";
    in4.textContent = "OFF";
    footer.appendChild(document.createTextNode(" ["));
    footer.appendChild(mnl);
    document.getElementById("n").addEventListener("click", checkNew);
    footer.appendChild(document.createTextNode("] ["));
    footer.appendChild(in1);
    footer.appendChild(in2);
    footer.appendChild(document.createTextNode("] "));
    footer.appendChild(in4);
    return true;
  } else if (document.body.className === "home") {
    serviceType = 1;
    return true;
  } else {
    return false;
  }
}

function startCounter() {
  refreshTime = refreshMaxTime;
  counter();
  refreshInterval = setInterval(counter, 1000);
}

function stopCounter(str) {
  clearInterval(refreshInterval);
  document.getElementById("counter").innerHTML = str;
}

function autoRefresh(e) {
  chk_snd = document.getElementById("autosound");
  if (document.getElementById("autorefresh").checked) {
    if (chk_snd)
      chk_snd.disabled = false;
    Notification.requestPermission();
    lastTime = Math.floor(Date.now() / 1000);
    refreshTime = refreshMaxTime;
    startCounter();
  } else {
    if (chk_snd)
      document.getElementById("autosound").disabled = true;
    stopCounter("OFF");
  }
}

http_request.onreadystatechange = function() {
  if (http_request.readyState == 4) {
    var jsonObj = JSON.parse(http_request.responseText);
    if (jsonObj.state == "success") {
      if (serviceType == 1)
        updatePostList(jsonObj.threads, jsonObj.time);
      else if (serviceType == 2 || serviceType == 3)
        updateThread(jsonObj.posts, jsonObj.total_replies, jsonObj.time);
      lastTime = jsonObj.time;
      if (chk.checked)
        startCounter();
    }
    if (!chk.checked) {
      document.getElementById("counter").innerText = "OFF";
    }
    manual = 0;
  }
}
document.addEventListener("DOMContentLoaded", function() {
  if (!detectService()) return;

  chk = document.getElementById("autorefresh");
  chk_snd = document.getElementById("autosound");

  if (localStorage.getItem("autorefresh" + serviceType)) {
    document.getElementById("autorefresh").checked = true;
    autoRefresh();
  }
  if (!chk_snd) return;
  if (localStorage.getItem("mainpage_nosound"))
    document.getElementById("autosound").checked = false;
});

window.addEventListener("unload", function() {
  if (!serviceType) return;
  
  chk = document.getElementById("autorefresh");
  chk_snd = document.getElementById("autosound");

  if (chk.checked)
    localStorage.setItem("autorefresh" + serviceType, true);
  else
    localStorage.removeItem("autorefresh" + serviceType);
  if (!chk_snd) return;
  if (!document.getElementById("autosound").checked)
    localStorage.setItem("mainpage_nosound", true);
  else
    localStorage.removeItem("mainpage_nosound");
});
function sendPost(e) {
  e.preventDefault();
  var button = document.getElementById("post");
  button.disabled = true;
  var sendpost = new XMLHttpRequest();
  var postform = document.getElementById("postform");
  sendpost.open("POST", "/cgi/api/post", true);
  console.log(new FormData(postform));
  sendpost.send(new FormData(postform));
  sendpost.onreadystatechange = function() {
    console.log(sendpost.readyState);
    if (sendpost.readyState == 4) {
      button.disabled = false;
      var response = JSON.parse(sendpost.responseText);
      console.log(response);
      if (response.state == "success") {
        checkNew(e);
      } else
        alert(response.message);
    }
  }
}

function postClick(e) {
  insert(">>" + parseInt(this.innerHTML, 10) + "\n");
  e.preventDefault();
}

function insert(text) {
	var textarea=document.forms.postform.message;
	if(textarea) {
		if(textarea.createTextRange && textarea.caretPos) { // IE 
			var caretPos=textarea.caretPos;
			caretPos.text=caretPos.text.charAt(caretPos.text.length-1)==" "?text+" ":text;
		} else if(textarea.setSelectionRange) { // Firefox
			var start=textarea.selectionStart;
			var end=textarea.selectionEnd;
			textarea.value=textarea.value.substr(0,start)+text+textarea.value.substr(end);
			textarea.setSelectionRange(start+text.length,start+text.length);
		} else {
			textarea.value+=text+" ";
		}
		textarea.focus();
	}
  return false;
}

function get_password(name) {
  if(localStorage.hasOwnProperty(name))
    return localStorage.getItem(name);

	var chars="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
	var pass='';
	for(var i=0;i<8;i++) {
		var rnd = Math.floor(Math.random()*chars.length);
		pass += chars.substring(rnd, rnd+1);
	}
	localStorage.setItem(name, pass);
	return(pass);
}

function save_inputs(e) {
  var e = e || window.event;
  var form = e.target || e.srcElement;
  if(typeof(form.fielda) !== 'undefined') localStorage.setItem("weabot_name", form.fielda.value);
  if(typeof(form.fielda) !== 'undefined') localStorage.setItem("weabot_email", form.fieldb.value);
}

function set_inputs() {
  with(document.getElementById("postform")) {
    if(typeof(fielda) !== "undefined" && !fielda.value) fielda.value = localStorage.getItem("weabot_name");
    if(typeof(fielda) !== "undefined" && !fieldb.value) fieldb.value = localStorage.getItem("weabot_email");
    if(!password.value) password.value = get_password("weabot_password");
    addEventListener("submit", save_inputs);
  }
}

function showMenu(e) {
  e.preventDefault();
  if (document.getElementById("mnu-opened"))
    closeMenu(e);
  this.id = "mnu-opened";
  var brd = postform.board.value;
  var post = this.parentNode.parentNode;
  if (document.body.className === "txt") {
    var id = post.id.substr(1);
    var num = parseInt(post.getElementsByClassName("num")[0].innerText, 10);
  } else {
    var id = post.getElementsByClassName("num")[0].innerText;
    var num = ((post.className === "first") ? 1 : 0);
  }
  var menu = document.createElement("div");
  menu.id = "mnu-list";
  menu.style.top = (e.pageY + 5) + "px";
  menu.style.left = (e.pageX + 5) + "px";
  document.body.appendChild(menu);
  menu = document.getElementById("mnu-list");
  var rep = document.createElement("a");
  rep.href = "#";
  rep.innerText = "Denunciar post";
  rep.addEventListener("click", function(e) {
    var reason = prompt("Razón de denuncia:");
    if (reason === "")
      while(reason === "")
        reason = prompt("Error: Ingresa una razón.");
    if (reason) {
      var rep_req = new XMLHttpRequest();
      var report = "/cgi/report/" + brd + "/" + id + ((num) ? "/" + num : "") + "?reason=" + reason;
      rep_req.open("GET", report, true);
      rep_req.send();
      rep_req.onreadystatechange = function() {
        if (rep_req.readyState == 4 && rep_req.status == 200)
          alert("Denuncia enviada.");
      }
    }
  });
  menu.appendChild(rep);
  var del = document.createElement("a");
  del.href = "#";
  del.innerText = "Eliminar post";
  del.addEventListener("click", function(e) {
    if(confirm("¿Seguro que deseas borrar el mensaje "+((num) ? num : id)+"?")) {
      var del_req = new XMLHttpRequest();
      var del_form = "/cgi/api/delete?dir=" + brd + "&id=" + id + "&password=" + postform.password.value;
      del_req.open("GET", del_form, true);
      del_req.send();
      del_req.onreadystatechange = function() {
        if (del_req.readyState == 4) {
          var response = JSON.parse(del_req.responseText);
          if (response.state == "success") {
            if (num == 1) {
              alert("Hilo eliminado.");
              document.location = "/cgi/mobile/" + brd;
            } else {
              alert("Mensaje eliminado.");
              location.reload();
            }
          } else if (response.state == "failed")
            alert(response.message);
        }
      }
    }
  });
  menu.appendChild(del);
  var file = post.getElementsByClassName("thm")[0];
  if (file) {
    var dfile = document.createElement("a");
    dfile.href = "#";
    dfile.innerText = "Eliminar archivo";
    dfile.addEventListener("click", function(e) {
      if(confirm("¿Seguro que deseas borrar el archivo del mensaje "+((num) ? num : id)+"?")) {
        var fdel_req = new XMLHttpRequest();
        var fdel_form = "/cgi/api/delete?dir=" + brd + "&id=" + id + "&password=" + postform.password.value + "&imageonly=true";
        fdel_req.open("GET", fdel_form, true);
        fdel_req.send();
        fdel_req.onreadystatechange = function() {
          if (fdel_req.readyState == 4) {
            var response = JSON.parse(fdel_req.responseText);
            if (response.state == "success") {
              alert("Archivo eliminado.");
              post.removeChild(file);
            } else if (response.state == "failed")
              alert(response.message);
          }
        }
      }
    });
    menu.appendChild(dfile);
  }
  e.stopPropagation();
  this.removeEventListener("click", showMenu);
  document.addEventListener("click", closeMenu);
}

function closeMenu(e) {
  var menu = document.getElementById("mnu-list");
  menu.parentElement.removeChild(menu);
  document.removeEventListener("click", closeMenu);
  var btn = document.getElementById("mnu-opened");
  btn.addEventListener("click", showMenu);
  btn.removeAttribute("id");
  e.preventDefault();
}

function searchSubjects() {
  var filter = document.getElementById("search").value.toLowerCase();
  var nodes = document.getElementsByClassName("list")[0].getElementsByTagName("a");
  for (i = 0; i < nodes.length; i++) {
    if (nodes[i].innerHTML.toLowerCase().split(/<\/?br[^>]*>\s*/im)[0].includes(filter))
      nodes[i].removeAttribute("style");
    else
      nodes[i].style.display = "none";
  }
}

function searchCatalog() {
  var filter = document.getElementById("catsearch").value.toLowerCase();
  var nodes = document.getElementsByClassName("cat");
  for (i = 0; i < nodes.length; i++) {
    if (nodes[i].innerText.toLowerCase().substring(nodes[i].innerText.indexOf("R)")+2).includes(filter))
      nodes[i].removeAttribute("style");
    else
      nodes[i].style.display = "none";
  }
}

var lastTime = 0;
var refreshInterval;
var refreshMaxTime = 30;
var refreshTime;
var manual = 0;
var serviceType = 0;
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
  if (manual) {
    document.getElementById("n").style.color = "gray";
    document.getElementById("n").innerText = "Revisando...";
  }
  var data_file;
  if (serviceType)
    data_file = "/cgi/api/thread?dir=" + postform.board.value + "&id=" + postform.parent.value + "&offset=" + thread_length + "&time=" + lastTime;
  else
    return false;
  http_request.open("GET", data_file, true);
  http_request.send();
}

function updateThread(posts, total_replies, serverTime) {
  thread_div = document.getElementById("thread");
  last_elem = document.getElementById("n");

  for (var i = 0; i < posts.length; i++) {
    post = posts[i];
    brd = postform.board.value;
    var div = document.createElement('div');
    div.className = "pst";
    div.id = "p" + post.id;
    if (post.IS_DELETED == 0) {
      s_name = post.name;
      if (post.tripcode)
        s_name += ' ' + post.tripcode;
      s_time = post.timestamp_formatted.replace(/\(.{1,3}\)/g, " ");
      if (post.file)
        s_img = '<a href="/' + brd + '/src/' + post.file + '" target="_blank" class="thm"><img src="/' + brd + '/mobile/' + post.thumb + '" /><br />' + Math.round(post.file_size/1024) + 'KB ' + post.file.substring(post.file.lastIndexOf(".")+1, post.file.length).toUpperCase() + '</a>';
    }
    else
      s_img = '';
    if (serviceType == 1) {
      var pad = "0000" + (thread_length + i + 1);
      pad = pad.substr(pad.length-4);
      if (post.IS_DELETED == 0)
        div.innerHTML = '<h3><a href="#" class="num">' + pad + '</a> ' + s_name + '</h3>' + s_img + '<div class="msg">' + post.message + '</div><h4>' + s_time + '<a href="#" class="mnu">|||</a></h4>';
      else if (post.IS_DELETED == 1)
        div.innerHTML = '<h3 class="del"><a href="#" class="num">' + pad + '</a> : Eliminado por el usuario.</h3>';
      else
        div.innerHTML = '<h3 class="del"><a href="#" class="num">' + pad + '</a> : Eliminado por miembro del staff.</h3>';
    } else {
      if (post.IS_DELETED == 0) {
        div.innerHTML = '<h3>' + s_name + ' ' + s_time + ' <a href="#" class="num" name="' + post.id + '">' + post.id + '</a><a href="#" class="mnu">|||</a></h3>' + s_img + '<div class="msg">' + post.message + '</div>';
      } else if (post.IS_DELETED == 1) {
        div.innerHTML = '<h3 class="del"><a name="' + post.id + '"></a>No.' + post.id + ' eliminado por el usuario.</h3>';
      } else {
        div.innerHTML = '<h3 class="del"><a name="' + post.id + '"></a>No.' + post.id + ' eliminado por miembro del staff.</h3>';
      }
    }

    div.getElementsByClassName("mnu")[0].addEventListener("click", showMenu);
    div.getElementsByClassName("num")[0].addEventListener("click", postClick);
    thread_div.insertBefore(div, last_elem);
    document.getElementsByTagName("h1")[0].getElementsByTagName("span")[0].innerText = "(" + (thread_length + i + 1) + ")"
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
  new_unread = thread_length - thread_first_length;

  if (new_unread)
    document.title = '(' + new_unread + ') ' + thread_title;
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
    document.getElementById("counter").innerHTML = (refreshTime + 1);
  }
}

function detectService() {
  if (document.getElementById("thread")) {
    thread_title = document.getElementsByTagName("h1")[0].innerHTML.split(" \<span\>")[0] + " - " + document.title;
    thread_length = parseInt(document.getElementsByTagName("h1")[0].getElementsByTagName("span")[0].innerText.slice(1, -1), 10);
    thread_first_length = thread_length;
    if (document.body.className === "txt") {
      serviceType = 1;
      replylist = document.getElementsByClassName("pst");
      thread_lastreply = parseInt(replylist[replylist.length - 1].getElementsByClassName("num")[0].innerText);
      if (thread_length == thread_lastreply) {
        serviceType = 1;
        document.getElementById("n2").setAttribute("style", "border-top:1px solid #c6c7c8;border-left:1px solid #c6c7c8;display:inline-block;text-align:center;width:50%;");
        return true;
      } else {
        return false;
      }
    } else if (document.body.className === "img") {
      serviceType = 2;
      document.getElementById("n").innerText = "Ver nuevos posts";
      document.getElementById("n2").setAttribute("style", "border-top:1px solid #333;border-left:1px solid #333;display:inline-block;text-align:center;width:50%;");
      replylist = document.getElementsByClassName("first");
      replylist += document.getElementsByClassName("pst");
      return true;
    }
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
      updateThread(jsonObj.posts, jsonObj.total_replies, jsonObj.time);
      lastTime = jsonObj.time;
      if (chk.checked)
        startCounter();
    }
    if (manual) {
      document.getElementById("n").style.color = "inherit";
      document.getElementById("n").innerText = "Ver nuevos posts";
    }
    manual = 0;
  }
}

document.addEventListener("DOMContentLoaded", function(e) {
  var ids = document.getElementsByClassName("num");
  for(var i=0;i<ids.length;i++) {
    ids[i].addEventListener("click", postClick);
  }
  
  var form = document.getElementById("postform");
  if (form) {
    set_inputs();
    /*if (document.getElementById("post").value == "Responder")
      form.addEventListener("submit", sendPost);*/
  }
  
  if (document.getElementById("search"))
    document.getElementById("search").addEventListener("keyup", searchSubjects);
  if (document.getElementById("catsearch"))
    document.getElementById("catsearch").addEventListener("keyup", searchCatalog);

  if (document.getElementById("thread")) {
    var mnu = document.createElement('a');
    mnu.href = "#";
    mnu.className = "mnu";
    mnu.innerHTML = "|||";
    if (document.body.className === "txt")
      var ft = document.getElementsByTagName("h4");
    else if (document.body.className === "img")
      var ft = document.getElementsByTagName("h3");
    for(var i=0;i<ft.length;i++) {
      if (!ft[i].classList.contains("del")) {
        var cln = mnu.cloneNode(true);
        cln.addEventListener("click", showMenu);
        ft[i].appendChild(cln);
      }
    }
  }
  
  if (!detectService()) return;
  document.title = thread_title;
  document.getElementById("n").style.display = "inline-block";
  document.getElementById("n").style.width = "50%";
  document.getElementById("n").addEventListener("click", checkNew);
  var lbl = document.createElement("label");
  lbl.id = "auto";
  lbl.style.display = "block";
  lbl.style.padding = "6px 0";
  var btn = document.createElement("input");
  btn.id = "autorefresh";
  btn.setAttribute("type", "checkbox");
  btn.addEventListener("click", autoRefresh);
  var cnt = document.createElement("span");
  cnt.id = "counter";
  cnt.textContent = "OFF";
  document.getElementById("n2").appendChild(lbl);
  document.getElementById("auto").appendChild(btn);
  document.getElementById("auto").appendChild(document.createTextNode(" Auto "));
  document.getElementById("auto").appendChild(cnt);
  
  chk = document.getElementById("autorefresh");
  if (localStorage.getItem("autorefreshmobile")) {
    chk.checked = true;
    autoRefresh();
  }
});

window.addEventListener("unload", function() {
  chk = document.getElementById("autorefresh");
  if (!serviceType) return;

  if (chk.checked)
    localStorage.setItem("autorefreshmobile", true);
  else
    localStorage.removeItem("autorefreshmobile");
});
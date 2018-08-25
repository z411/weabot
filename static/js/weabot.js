var style_cookie = 'weabot_style_ib';
var ispage = false;
var style_cookie;

function set_stylesheet(styletitle) {
  var css=document.getElementById("css");
  if(css) {
    css.href = "/static/css/" + styletitle.toLowerCase() + ".css";
    localStorage.setItem(style_cookie, styletitle);
  }
}

if(style_cookie && localStorage.hasOwnProperty(style_cookie)) {
  set_stylesheet(localStorage.getItem(style_cookie));
}

var hiddenthreads = Array();

/* IE/Opera fix, because they need to go learn a book on how to use indexOf with arrays */
if (!Array.prototype.indexOf) {
  Array.prototype.indexOf = function(elt /*, from*/) {
	var len = this.length;
	var from = Number(arguments[1]) || 0;
	from = (from < 0) ? Math.ceil(from) : Math.floor(from);
	if (from < 0) from += len;
	for (; from < len; from++) {
    if (from in this && this[from] === elt) return from;
	}
	return -1;
  };
}

function timeAgo(e) {
  var time = Math.round(Date.now()/1000);
  var el = time - this.dataset.unix;
  if (el==0) this.title = "Hace un instante";
  else if (el==1) this.title = "Hace un segundo";
  else if (el<60) this.title = "Hace " + el + " segundos";
  else if (el<120) this.title = "Hace un minuto";
  else if (el<3600) this.title = "Hace " + Math.round(el/60) + " minutos";
  else if (el<7200) this.title = "Hace una hora";
  else if (el<86400) this.title = "Hace " + Math.round(el/3600) + " horas";
  else if (el<172800) this.title = "Hace un día";
  else if (el<2628000) this.title = "Hace " + Math.round(el/86400) + " días";
  else if (el<5256000) this.title = "Hace un mes";
  else if (el<31536000) this.title = "Hace " + Math.round(el/2628000) + " meses";
  else if (el>31535999) this.title = "Hace más de un año";
}

function localTime(timestamp, id) {
  id = id || 0;
  var lcl = new Date(timestamp*1000);
  lcl = ("0"+lcl.getDate()).slice(-2) + "/" + ("0" + (lcl.getMonth()+1)).slice(-2) + "/" + lcl.getFullYear().toString().slice(-2) + "(" + week[lcl.getDay()] + ")" + ("0"+lcl.getHours()).slice(-2) + ":" + ("0"+lcl.getMinutes()).slice(-2) + ":" + ("0"+lcl.getSeconds()).slice(-2)
  if (id) lcl = lcl + " " + id;
  return lcl;
}

function postClick(e) { insert(">>" + this.textContent + "\n"); e.preventDefault(); }

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
		} else { textarea.value+=text+" "; }
		textarea.focus();
	}
  return false;
}

function quote(b, a) { 
	var v = eval("document." + a + ".message");
	v.value += ">>" + b + "a\ndfs";
	v.focus();
}

function checkhighlight() {
	var match;
	if(match=/#i([0-9]+)/.exec(document.location.toString()))
	if(!document.forms.postform.message.value)
	insert(">>"+match[1]+"\r\n");
	if(match=/#([0-9]+)/.exec(document.location.toString()))
	highlight(match[1]);
}

function highlight(post, checknopage) {
	if (checknopage && ispage) return;
	var cells = document.getElementsByClassName("reply");
	for(var i=0;i<cells.length;i++) if(cells[i].className == "reply highlight") cells[i].className = "reply";
	var reply = document.getElementById("reply" + post);
	if(reply) {
		reply.className = "reply highlight";
		var match = /^([^#]*)/.exec(document.location.toString());
		document.location = match[1] + "#" + post;
	}
}

function expandimg(e) {
  var post_id = this.dataset.id;
  var img_url = this.href;
  var thumb_url = this.dataset.thumb;
  var img_w = parseInt(this.dataset.w);
  var img_h = parseInt(this.dataset.h);
  var thumb_w = parseInt(this.dataset.tw);
  var thumb_h = parseInt(this.dataset.th);
  var format = img_url.substring(img_url.lastIndexOf("."), img_url.length);
  var exp_vid = 0;

  if(window.innerWidth > 850) var ratio = Math.min((window.innerWidth-130) / img_w, 1);
  else var ratio = Math.min((window.innerWidth-100) / img_w, 1);

  if(thumb_w < 1) return true;
  
  var img_cont = document.getElementById("thumb" + post_id);
  var post_block = img_cont.parentElement.parentElement.getElementsByTagName("blockquote")[0];
  var img;
  
  for(var i = 0; i < img_cont.childNodes.length; i++)
    if(img_cont.childNodes[i].nodeName.toLowerCase() == "img") {
      img = img_cont.childNodes[i];
    } else if(img_cont.childNodes[i].nodeName.toLowerCase() == "video") {
      img = img_cont.childNodes[i];
      exp_vid = 1;
    }
  
  if(img) {
    if( (format == ".webm") && (exp_vid == 0) ) var new_img = document.createElement("video");
    else var new_img = document.createElement("img");
    new_img.setAttribute("class", "thumb");
    new_img.setAttribute("alt", "" + post_id);
    
    if( (img.getAttribute("width") == ("" + thumb_w)) && (img.getAttribute("height") == ("" + thumb_h)) ) {
      // thumbnail -> fullsize
      if(format == ".webm") {
        new_img.setAttribute("controls", "");
        new_img.setAttribute("loop", "");
        new_img.setAttribute("autoplay", "");
      }
      new_img.setAttribute("src", "" + img_url);
      new_img.setAttribute("width", img_w);
      new_img.setAttribute("height", img_h);
      new_img.setAttribute("style", "max-width:"+Math.floor((img_w*ratio))+"px;max-height:"+Math.floor((img_h*ratio))+"px;");
      post_block.setAttribute("style", "");
      img_cont.style.display = 'table';
    } else {
      // fullsize -> thumbnail
      if(format == ".webm") {
        new_img.removeAttribute("controls");
        new_img.removeAttribute("loop");
        new_img.removeAttribute("autoplay");
      }
      new_img.setAttribute("src", "" + thumb_url);
      new_img.setAttribute("width", thumb_w);
      new_img.setAttribute("height", thumb_h);
      post_block.setAttribute("style", "margin-left:"+(parseInt(thumb_w)+40)+"px;max-width:"+(1000-parseInt(thumb_w))+"px");
      img_cont.removeAttribute("style");
    }

    while(img_cont.lastChild) img_cont.removeChild(img_cont.lastChild);
    
    img_cont.appendChild(new_img);
    e.preventDefault();
  }
} 

function get_password(name) {
  if(localStorage.hasOwnProperty(name)) return localStorage.getItem(name);

	var chars="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
	var pass='';
	for(var i=0;i<8;i++) {
		var rnd = Math.floor(Math.random()*chars.length);
		pass += chars.substring(rnd, rnd+1);
	}
	localStorage.setItem(name, pass);
	return(pass);
}

function togglethread(e) {
  e.preventDefault();
  if(this.parentElement.id.startsWith("unhide")) {
    var threadid = this.parentElement.id.substr(6);
  } else if(this.parentElement.parentElement.id.startsWith("thread")) {
    var threadid = this.parentElement.parentElement.id.substr(6);
  } else { return; }
  if (hiddenthreads.toString().indexOf(threadid) !== -1) {
    document.getElementById("unhide" + threadid).style.display = "none";
    document.getElementById("thread" + threadid).removeAttribute("style");
    hiddenthreads.splice(hiddenthreads.indexOf(threadid), 1);
  } else {
    document.getElementById("unhide" + threadid).removeAttribute("style");
    document.getElementById("thread" + threadid).style.display = "none";
    hiddenthreads.push(threadid);
  }
  if (hiddenthreads == "") localStorage.removeItem("hiddenthreads");
  else localStorage.setItem("hiddenthreads", hiddenthreads.join("!"));
}

function save_inputs(e) {
  var e = e || window.event;
  var form = e.target || e.srcElement;
  if(typeof(form.fielda) !== "undefined") localStorage.setItem("weabot_name", form.fielda.value);
  if(typeof(form.fielda) !== "undefined") localStorage.setItem("weabot_email", form.fieldb.value);
}

function set_inputs(id) {
	if (document.getElementById(id)) {
		with(document.getElementById(id)) {
			if(typeof(fielda) !== "undefined" && !fielda.value) fielda.value = localStorage.getItem("weabot_name");
			if(typeof(fielda) !== "undefined" && !fieldb.value) fieldb.value = localStorage.getItem("weabot_email");;
			if(!password.value) password.value = get_password("weabot_password");
			if(localStorage.getItem("weabot_noko")) noko.checked="true";
      addEventListener("submit", save_inputs);
		}
	}
}

function set_delpass(id) {
	if (document.getElementById(id) && document.getElementById(id).password) {
		with(document.getElementById(id)) {
			if(!password.value) password.value = get_password("weabot_password");
		}
	}
}

function catalogSearch() {
  var filter = document.getElementById("cat_search").value.toLowerCase();
  var nodes = document.getElementsByTagName("p");
  for (i = 0; i < nodes.length; i++) {
    if (nodes[i].innerText.toLowerCase().includes(filter))
      nodes[i].parentNode.removeAttribute("style");
    else nodes[i].parentNode.style.display = "none";
  }
}

function catalogThumbs(e) {
  btn = document.getElementById("cat_size");
  chk = localStorage.hasOwnProperty("cat_enlarge");
  if (e) {
    if (!chk) localStorage.setItem("cat_enlarge", true);
    else localStorage.removeItem("cat_enlarge");
    e.preventDefault();
  }
  chk = localStorage.hasOwnProperty("cat_enlarge");
  var threads = document.getElementsByClassName("thread");
  if (chk) {
    btn.innerText = "Reducir";
    for (j = 0; j < threads.length; j++) {
      img = threads[j].getElementsByTagName("a")[0];
      threads[j].className = "thread enlarged";
      img.innerHTML = img.innerHTML.replace("/cat/", "/thumb/");
    }
  } else {
    btn.innerText = "Aumentar";
    for (j = 0; j < threads.length; j++) {
      img = threads[j].getElementsByTagName("a")[0];
      threads[j].className = "thread";
      img.innerHTML = img.innerHTML.replace("/thumb/", "/cat/");
    }
  }
}

function catalogTeasers(e) {
  btn = document.getElementById("cat_hide");
  chk = localStorage.hasOwnProperty("cat_hidetext");
  if (e) {
    if (!chk) localStorage.setItem("cat_hidetext", true);
    else localStorage.removeItem("cat_hidetext");
    e.preventDefault();
  }
  chk = localStorage.hasOwnProperty("cat_hidetext");
  var threads = document.getElementsByClassName("thread");
  if (chk) {
    btn.innerText = "Mostrar";
    for (k = 0; k < threads.length; k++) {
      var teaser = threads[k].getElementsByTagName("p")[0];
      teaser.style.display = "none";
    }
  } else {
    btn.innerText = "Ocultar";
    for (k = 0; k < threads.length; k++) {
      var teaser = threads[k].getElementsByTagName("p")[0];
      teaser.removeAttribute("style");
    }
  }
}

function catalogMenu(e) {
  var brd = document.getElementsByName("board")[0].value;
  var id = this.dataset.id;
  this.insertAdjacentHTML('afterbegin', '<div id="thread_ctrl" style="margin-bottom:3px;">[<a href="/cgi/report/' + brd + '/' + id + '">Denunciar</a>] [<a href="#" class="hh">Ocultar</a>]');
  this.getElementsByClassName("hh")[0].addEventListener("click", function(e) {
    document.getElementById("cat" + id + brd).style.display = "none";
    hiddenthreads.push(id + brd);
    localStorage.setItem("hiddenthreads", hiddenthreads.join("!"))
    if (document.getElementById("hidden_label")) { hidden_num++; document.getElementById("hidden_num").innerText = hidden_num; }
    else { hidden_num = 1; catalogHidden(); }
  });
}

function catalogMenuClose(e) { document.getElementById("thread_ctrl").remove(); }

function catalogHidden() {
  var menu = document.getElementById("ctrl");
  menu.insertAdjacentHTML('beforeend', ' <span id="hidden_label">[Hilos ocultos: <span id="hidden_num">' + hidden_num + '</span> - ');
  var lbl = document.getElementById("hidden_label");
  var shw = document.createElement("a");
  shw.href = "#"; shw.innerText = "Deshacer";
  shw.addEventListener("click", function(e) {
    e.preventDefault();
    for(var i=0;i<hiddenthreads.length;i++){
      try {document.getElementById("cat" + hiddenthreads[i]).removeAttribute("style");}
      catch(err) { continue; } }
    lbl.parentElement.removeChild(lbl); hidden_num = 0;
    var aux = hiddenthreads.join("!");
    var exp = new RegExp("\\b[0-9]+" + document.getElementsByName("board")[0].value + "\\b", "g");
    aux = aux.replace(exp, "!"); aux = aux.replace(/!+/g, "!"); aux = aux.replace(/(^!|!$)/g, "");
    if (aux == "") { localStorage.removeItem("hiddenthreads"); hiddenthreads = []; }
    else { localStorage.setItem("hiddenthreads", aux); hiddenthreads = aux.split("!"); }
  });
  lbl.appendChild(shw); lbl.appendChild(document.createTextNode("]"));
}

document.addEventListener("DOMContentLoaded", function(e) {
  checkhighlight();

  if(localStorage.hasOwnProperty("hiddenthreads")) {
    hiddenthreads = localStorage.getItem("hiddenthreads").split("!");
    if (document.getElementById("catalog")) {
      hidden_num = 0;
      for(var i=0;i<hiddenthreads.length;i++){
        try {
          document.getElementById("cat" + hiddenthreads[i]).style.display = "none";
          hidden_num++;
        } catch(err) { continue; }
      }
      if (hidden_num) { catalogHidden(); }
    } else {
      for(var i=0;i<hiddenthreads.length;i++){
        try {
          document.getElementById("unhide" + hiddenthreads[i]).removeAttribute("style");
          document.getElementById("thread" + hiddenthreads[i]).style.display = "none";
        } catch(err) { continue; }
      }
    }
  }

  var dts = document.getElementsByClassName("date");
  if (dts[0]) {
    week = ["dom", "lun", "mar", "mie", "jue", "vie", "sab"];
    if (document.getElementsByName("board")[0].value == "2d")
      week = ["日", "月", "火", "水", "木", "金", "土"];
    for(var d=0;d<dts.length;d++) {
      dts[d].addEventListener('mouseover', timeAgo);
      if (dts[d].innerText.includes("ID:")) var id = dts[d].innerText.split(" ")[1];
      dts[d].innerText = localTime(dts[d].dataset.unix, id);
    }
  }
  var ids = document.getElementsByClassName("postid");
  for(var i=0;i<ids.length;i++) {
    ids[i].addEventListener('click', postClick);
  }
  var tts = document.getElementsByClassName("tt");
  for(var i=0;i<tts.length;i++) {
    tts[i].addEventListener('click', togglethread);
  }
  var tts = document.getElementsByClassName("expimg");
  for(var i=0;i<tts.length;i++) {
    tts[i].addEventListener('click', expandimg);
  }
  var sss = document.getElementsByClassName("ss");
  for(var i=0;i<sss.length;i++) {
    sss[i].addEventListener('click', function() {
      set_stylesheet(this.textContent);
      document.getElementById("cur_stl").removeAttribute("id");
      this.id = "cur_stl";
    });
    if (sss[i].innerText == localStorage.getItem(style_cookie)) sss[i].id = "cur_stl";
  }

  if (!document.getElementsByName("board")[0].value == "")
    document.getElementById(document.getElementsByName("board")[0].value).className = "cur_brd";
  set_inputs('postform');
  set_delpass('delform');

  if (document.getElementById("catalog")) {
    document.getElementById("cat_size").addEventListener("click", catalogThumbs);
    if (localStorage.hasOwnProperty("cat_enlarge")) catalogThumbs();
    document.getElementById("cat_hide").addEventListener("click", catalogTeasers);
    if (localStorage.hasOwnProperty("cat_hidetext")) catalogTeasers();
    document.getElementById("cat_search").addEventListener("keyup", catalogSearch);
    var thr = document.getElementsByClassName("thread");
    for(var i=0;i<thr.length;i++) {
      thr[i].addEventListener("mouseenter", catalogMenu);
      thr[i].addEventListener("mouseleave", catalogMenuClose);
    }
  }

  window.addEventListener("hashchange", checkhighlight);
});

function oek_edit(image, postnum, width, height) {
  parent = document.getElementById("oek_edit");
  if(parent.lastChild) return;
  input_x = document.createElement("input");
  input_x.setAttribute("type", "hidden");
  input_x.setAttribute("name", "oek_edit_x");
  input_x.setAttribute("value", width);
  parent.appendChild(input_x);
  input_y = document.createElement("input");
  input_y.setAttribute("type", "hidden");
  input_y.setAttribute("name", "oek_edit_y");
  input_y.setAttribute("value", height);
  parent.appendChild(input_y);
  input_img = document.createElement("input");
  input_img.setAttribute("type", "hidden");
  input_img.setAttribute("name", "oek_edit");
  input_img.setAttribute("value", image);
  parent.appendChild(input_img);
  parent.appendChild(document.createTextNode(' (Editing #'+postnum+' ['));
  link_cancel = document.createElement("a");
  link_cancel.setAttribute("href", "#postbox");
  link_cancel.setAttribute("onclick", "oek_cancel();");
  link_cancel.appendChild(document.createTextNode("X"));
  parent.appendChild(link_cancel);
  parent.appendChild(document.createTextNode(']) '));
  document.getElementById("oek_size").style.display = "none";
}
function oek_cancel(image, postnum) {
  parent = document.getElementById("oek_edit");
  if(!parent.lastChild) return;
  while(parent.lastChild) parent.removeChild(parent.lastChild);
  document.getElementById("oek_size").style.display = "inline";
}
var style_cookie = 'weabot_style_txt';
var style_cookie;

function set_stylesheet(styletitle) {
  var css=document.getElementById("css");
  css.href = "/static/css/txt/" + styletitle.toLowerCase() + ".css";
  localStorage.setItem(style_cookie, styletitle);
}

if(style_cookie && localStorage.hasOwnProperty(style_cookie)) {
  set_stylesheet(localStorage.getItem(style_cookie));
}

function timeAgo(timestamp) {
  var time = Math.round(Date.now()/1000);
  var el = time - timestamp;
  if (el==0) return "un instante";
  else if (el==1) return "un segundo";
  else if (el<60) return el + " segundos";
  else if (el<120) return "un minuto";
  else if (el<3600) return Math.round(el/60) + " minutos";
  else if (el<7200) return "una hora";
  else if (el<86400) return Math.round(el/3600) + " horas";
  else if (el<172800) return "un día";
  else if (el<2628000) return Math.round(el/86400) + " días";
  else if (el<5256000) return "un mes";
  else if (el<31536000) return Math.round(el/2628000) + " meses";
  else if (el>31535999) return "más de un año";
}

function localTime(timestamp, id) {
  id = id || 0;
  var lcl = new Date(timestamp*1000);
  lcl = ("0"+lcl.getDate()).slice(-2) + "/" + ("0" + (lcl.getMonth()+1)).slice(-2) + "/" + lcl.getFullYear().toString().slice(-2) + "(" + week[lcl.getDay()] + ")" + ("0"+lcl.getHours()).slice(-2) + ":" + ("0"+lcl.getMinutes()).slice(-2) + ":" + ("0"+lcl.getSeconds()).slice(-2)
  if (id) lcl = lcl + " " + id;
  return lcl;
}

/* IE/Opera fix, because they need to go learn a book on how to use indexOf with arrays */
if (!Array.prototype.indexOf) {
  Array.prototype.indexOf = function(elt /*, from*/) {
	var len = this.length;
	var from = Number(arguments[1]) || 0;
	from = (from < 0) ? Math.ceil(from) : Math.floor(from);
	if (from < 0) from += len;
	for (; from < len; from++) { if (from in this && this[from] === elt) return from; }
	return -1;
  };
}

function get_password(name) {
  if(localStorage.hasOwnProperty(name))
    return localStorage.getItem(name);
	var chars="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
	var pass= "";
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

function set_inputs(formid) {
	if (document.getElementById(formid)) {
		with(document.getElementById(formid)) {
			if(typeof(fielda) !== 'undefined' && !fielda.value) fielda.value = localStorage.getItem("weabot_name");
			if(typeof(fielda) !== 'undefined' && !fieldb.value) fieldb.value = localStorage.getItem("weabot_email");
			if(!password.value) password.value = get_password("weabot_password");
      if(typeof preview !== 'undefined') {
        preview.formid = formid;
        preview.addEventListener('click', preview_post);
      }
      addEventListener("submit", save_inputs);
		}
	}
}

function set_delpass(id) {
	if (document.getElementById(id).password) {
		with(document.getElementById(id)) {
			if(!password.value) password.value = get_password("weabot_password");
		}
	}
}
// Textboard data
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
function first_postform() {
  forml = document.getElementsByTagName('form');
  for(i=0;i<forml.length;i++)
    if(forml[i].id.startsWith('postform')) return forml[i];
}
function delete_post(e) {
  var ids = this.parentElement.firstChild.href.split("/");
  var post = ids.pop();
  var realid = ids.pop();
  
	if(confirm("¿Seguro que deseas borrar el mensaje "+post+"?")) {
		var script="/cgi/delete";
		var password=first_postform().password.value;
    var board=first_postform().board.value;

		document.location=script
		+"?board="+board
		+"&password="+password
		+"&delete="+realid;
	}
  e.preventDefault();
}

function postClick(e) {
  insert(">>" + this.innerHTML + "\n");
  e.preventDefault();
}

function preview_post(e) {
  var formid = e.target.formid;
  var thread = '0';
  if(formid.startsWith('postform')) thread = formid.substr(8);
  
	var form=document.getElementById(formid);
	var preview=document.getElementById("preview"+thread);
	var board=first_postform().board.value;
  var main=document.getElementById("options");

	if(!form||!preview||!form.message.value) return;
  if(main) main.style.display="";

  preview.style.display="";
	preview.innerHTML="<em>Cargando...</em>";

	var text;
	text="message="+encodeURIComponent(form.message.value);
	text+="&board="+board;
	if(thread) text+="&parentid="+thread;
  
	var xmlhttp=get_xmlhttp();
	xmlhttp.open("POST", "/cgi/preview");
	xmlhttp.onreadystatechange=function() {
		if(xmlhttp.readyState==4) preview.innerHTML=xmlhttp.responseText;
	}
	if(is_ie()||xmlhttp.setRequestHeader) xmlhttp.setRequestHeader("Content-Type","application/x-www-form-urlencoded");
	xmlhttp.send(text);
}

function toggleThreads(e) {
  document.getElementById("header").style.display = "none";
  document.getElementById("content").className = "grid";
}

function searchSubjects(e) {
  var filter = document.getElementById("search").value.toLowerCase();
  var nodes = document.getElementsByClassName('thread');
  for (i = 0; i < nodes.length; i++) {
    if (nodes[i].innerText.toLowerCase().includes(filter)) nodes[i].parentNode.removeAttribute("style");
    else nodes[i].parentNode.style.display = "none";
  }
}

function get_xmlhttp() {
	var xmlhttp;
	try { xmlhttp=new ActiveXObject("Msxml2.XMLHTTP"); }
	catch(e1) {
		try { xmlhttp=new ActiveXObject("Microsoft.XMLHTTP"); }
		catch(e1) { xmlhttp=null; }
	}
	if(!xmlhttp && typeof XMLHttpRequest!='undefined') xmlhttp=new XMLHttpRequest();
	return(xmlhttp);
}

function is_ie() {
	return(document.all&&!document.opera);
}

document.addEventListener("DOMContentLoaded", function() {
  var dts = document.getElementsByClassName("date");
  if (dts[0].dataset.unix) {
    week = ["dom", "lun", "mar", "mie", "jue", "vie", "sab"];
    if (document.getElementsByName("board")[0].value == "world")
      week = ["sun", "mon", "tue", "wed", "thu", "fri", "sat"];
    for(var d=0;d<dts.length;d++) {
      dts[d].addEventListener('mouseover', function(e) {
        this.title = "Hace " + timeAgo(this.dataset.unix);
      });
      if (dts[d].innerText.includes("ID:")) var id = dts[d].innerText.split(" ")[1];
      dts[d].innerText = localTime(dts[d].dataset.unix, id);
    }
  }

  var ids = document.getElementsByClassName("num");
  for(var i=0;i<ids.length;i++) {
    ids[i].addEventListener('click', postClick);
  }

  var forms = document.getElementsByTagName('form');
  for(var i=0;i<forms.length;i++) {
    if(forms[i].id.startsWith("postform")) set_inputs(forms[i].id);
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

  var dds = document.getElementsByClassName("del");
  for(var i=0;i<dds.length;i++) {
    dds[i].children[1].addEventListener("click", delete_post);
  }
  
  if (document.body.className === "mainpage")
    document.getElementById(document.getElementsByName("board")[0].value).className = "cur_brd";
  if (document.body.className === "threads") {
    document.getElementById("search").addEventListener("keyup", searchSubjects);
    document.getElementById("compact").addEventListener("click", toggleThreads);
  }

  set_inputs('threadform');
});
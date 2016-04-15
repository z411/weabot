function check_version(ver) {
	if(ver != "1")
    alert("El sitio ha sido actualizado, por lo que debes forzar una recarga de caché en tu navegador.\nEsto usualmente se hace dejando presionado Shift y luego presionando el botón Actualizar, o manualmente limpiando el caché.");
}
var style_cookie;

/* IE/Opera fix, because they need to go learn a book on how to use indexOf with arrays */
if (!Array.prototype.indexOf) {
  Array.prototype.indexOf = function(elt /*, from*/) {
	var len = this.length;

	var from = Number(arguments[1]) || 0;
	from = (from < 0)
		 ? Math.ceil(from)
		 : Math.floor(from);
	if (from < 0)
	  from += len;

	for (; from < len; from++) {
	  if (from in this &&
		  this[from] === elt)
		return from;
	}
	return -1;
  };
}

/**
*
*  UTF-8 data encode / decode
*  http://www.webtoolkit.info/
*
**/

var Utf8 = {

	// public method for url encoding
	encode : function (string) {
		string = string.replace(/\r\n/g,"\n");
		var utftext = "";

		for (var n = 0; n < string.length; n++) {

			var c = string.charCodeAt(n);

			if (c < 128) {
				utftext += String.fromCharCode(c);
			}
			else if((c > 127) && (c < 2048)) {
				utftext += String.fromCharCode((c >> 6) | 192);
				utftext += String.fromCharCode((c & 63) | 128);
			}
			else {
				utftext += String.fromCharCode((c >> 12) | 224);
				utftext += String.fromCharCode(((c >> 6) & 63) | 128);
				utftext += String.fromCharCode((c & 63) | 128);
			}

		}

		return utftext;
	},

	// public method for url decoding
	decode : function (utftext) {
		var string = "";
		var i = 0;
		var c = c1 = c2 = 0;

		while ( i < utftext.length ) {

			c = utftext.charCodeAt(i);

			if (c < 128) {
				string += String.fromCharCode(c);
				i++;
			}
			else if((c > 191) && (c < 224)) {
				c2 = utftext.charCodeAt(i+1);
				string += String.fromCharCode(((c & 31) << 6) | (c2 & 63));
				i += 2;
			}
			else {
				c2 = utftext.charCodeAt(i+1);
				c3 = utftext.charCodeAt(i+2);
				string += String.fromCharCode(((c & 15) << 12) | ((c2 & 63) << 6) | (c3 & 63));
				i += 3;
			}

		}

		return string;
	}

}

function replaceAll( str, from, to ) {
	var idx = str.indexOf( from );
	while ( idx > -1 ) {
		str = str.replace( from, to );
		idx = str.indexOf( from );
	}
	return str;
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
	if (checknopage && ispage) {
		return;
	}
	var cells = document.getElementsByTagName("td");
	for(var i=0;i<cells.length;i++) if(cells[i].className == "reply highlight") cells[i].className = "reply";

	var reply = document.getElementById("reply" + post);
	if(reply) {
		reply.className = "reply highlight";
		var match = /^([^#]*)/.exec(document.location.toString());
		document.location = match[1] + "#" + post;
	}
}

function expandimg(post_id, img_url, thumb_url, img_w, img_h, thumb_w, thumb_h) {
  if(thumb_w < 1)
    return true;
  
  var img_cont = document.getElementById("thumb" + post_id);
  //var post_block = document.getElementById("reply"+post_id).getElementsByTagName("blockquote")[0];
  var post_block = img_cont.parentElement.parentElement.getElementsByTagName("blockquote")[0];
  var img;
  
  for(var i = 0; i < img_cont.childNodes.length; i++)
    if(img_cont.childNodes[i].nodeName.toLowerCase() == "img")
      img = img_cont.childNodes[i];
  
  if(img) {
    var new_img = document.createElement("img");
    new_img.setAttribute("class", "thumb");
    new_img.setAttribute("className", "thumb");
    new_img.setAttribute("alt", "" + post_id);
    
    if( (img.getAttribute("width") == ("" + thumb_w)) && (img.getAttribute("height") == ("" + thumb_h)) ) {
      // thumbnail -> fullsize
      new_img.setAttribute("src", "" + img_url);
      //new_img.setAttribute("width", 5);
      //new_img.setAttribute("height", 5);
      new_img.setAttribute("style", "max-width: "+(window.innerWidth-130)+"px;");
      post_block.setAttribute("style", "");
    } else {
      // fullsize -> thumbnail
      new_img.setAttribute("src", "" + thumb_url);
      new_img.setAttribute("width", "" + thumb_w);
      new_img.setAttribute("height", "" + thumb_h);
      post_block.setAttribute("style", "margin-left: "+(parseInt(thumb_w)+40)+"px;");
    }
    
    while(img_cont.lastChild)
      img_cont.removeChild(img_cont.lastChild);
    
    img_cont.appendChild(new_img);
    return false;
  }
  return true;
} 

function get_password(name) {
	var pass = getCookie(name);
	if(pass) return pass;

	var chars="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
	var pass='';

	for(var i=0;i<8;i++) {
		var rnd = Math.floor(Math.random()*chars.length);
		pass += chars.substring(rnd, rnd+1);
	}
	set_cookie(name, pass, 365);
	return(pass);
}

function getCookie(name) {
	with(document.cookie) {
		var regexp=new RegExp("(^|;\\s+)"+name+"=(.*?)(;|$)");
		var hit=regexp.exec(document.cookie);
		if(hit&&hit.length>2) return Utf8.decode(unescape(replaceAll(hit[2],'+','%20')));
		else return '';
	}
}
function set_cookie(name,value,days) {
	if(days) {
		var date=new Date();
		date.setTime(date.getTime()+(days*24*60*60*1000));
		var expires="; expires="+date.toGMTString();
	} else expires="";
	document.cookie=name+"="+value+expires+"; path=/";
}

function set_stylesheet(styletitle) {
	set_cookie(style_cookie,styletitle,365);

	var links=document.getElementsByTagName("link");
	var found=false;
	for(var i=0;i<links.length;i++) {
		var rel=links[i].getAttribute("rel");
		var title=links[i].getAttribute("title");
		
		if(rel.indexOf("style")!=-1&&title) {
			links[i].disabled=true; // IE needs this to work. IE needs to die.
			if(styletitle==title) { links[i].disabled=false; found=true; }
		}
	}
	if(!found) set_preferred_stylesheet();
}

function set_preferred_stylesheet() {
	var links=document.getElementsByTagName("link");
	for(var i=0;i<links.length;i++) {
		var rel=links[i].getAttribute("rel");
		var title=links[i].getAttribute("title");
		if(rel.indexOf("style")!=-1&&title) links[i].disabled=(rel.indexOf("alt")!=-1);
	}
}

function get_active_stylesheet() {
	var links=document.getElementsByTagName("link");
	for(var i=0;i<links.length;i++) {
		var rel=links[i].getAttribute("rel");
		var title=links[i].getAttribute("title");
		if(rel.indexOf("style")!=-1&&title&&!links[i].disabled) return title;
	}
	
	return null;
}

function get_preferred_stylesheet() {
	var links=document.getElementsByTagName("link");
	for(var i=0;i<links.length;i++) {
		var rel=links[i].getAttribute("rel");
		var title=links[i].getAttribute("title");
		if(rel.indexOf("style")!=-1&&rel.indexOf("alt")==-1&&title) return title;
	}
	
	return null;
}

function delandbanlinks() {
	if (typeof weabot_staff == "undefined") return;
	
	var dnbelements = document.getElementsByTagName('span');
	var dnbelement;
	var dnbinfo;
	for(var i=0;i<dnbelements.length;i++){
		dnbelement = dnbelements[i];
		if (dnbelement.getAttribute('class')) {
			if (dnbelement.getAttribute('class').substr(0, 3) == 'dnb') {
				dnbinfo = dnbelement.getAttribute('class').split('|');
				
				// Let's create elements!
				dnbelements[i].appendChild(document.createTextNode("["));
				link_del = document.createElement("a");
				link_del.setAttribute("href", cgi_url + 'manage/delete/' + dnbinfo[1] + '/' + dnbinfo[2]);
				link_del.setAttribute("title", "Eliminar");
				link_del.appendChild(document.createTextNode("D"));
				dnbelements[i].appendChild(link_del);
				
        dnbelements[i].appendChild(document.createTextNode(" "));
        link_amp = document.createElement("a");
				link_amp.setAttribute("href", cgi_url + 'manage/delete/' + dnbinfo[1] + '/' + dnbinfo[2] + '?ban=true');
				link_amp.setAttribute("title", "Eliminar & Banear");
				link_amp.appendChild(document.createTextNode("&"));
				dnbelements[i].appendChild(link_amp);
				
				dnbelements[i].appendChild(document.createTextNode(" "));
        link_amp = document.createElement("a");
				link_amp.setAttribute("href", cgi_url + 'manage/ban/' + dnbinfo[1] + '/' + dnbinfo[2]);
				link_amp.setAttribute("title", "Banear");
				link_amp.appendChild(document.createTextNode("B"));
				dnbelements[i].appendChild(link_amp);

				if (dnbinfo[3] == 'y') {
				  // Modbrowse
				  dnbelements[i].appendChild(document.createTextNode(" "));
				  link_mod = document.createElement("a");
				  link_mod.setAttribute("href", cgi_url + 'manage/modbrowse/' + dnbinfo[1] + '/' + dnbinfo[2]);
				  link_mod.setAttribute("title", "Modbrowse");
				  link_mod.appendChild(document.createTextNode("M"));
				  dnbelements[i].appendChild(link_mod);

          // Lock
 				  dnbelements[i].appendChild(document.createTextNode(" "));
 				  link_lock = document.createElement("a");
  			  link_lock.setAttribute("href", cgi_url + 'manage/lock/' + dnbinfo[1] + '/' + dnbinfo[2]);
				  if (dnbinfo[4] == '1') {
				    // If it's closed...agregar L-
				    link_lock.setAttribute("title", "Abrir");
 	  			  link_lock.setAttribute("onclick", "return confirm('¿Abrir este hilo?');");
	  			  link_lock.appendChild(document.createTextNode("L-"));
				  } else {
				    link_lock.setAttribute("title", "Cerrar");
 	  			  link_lock.setAttribute("onclick", "return confirm('¿Cerrar este hilo?');");
	  			  link_lock.appendChild(document.createTextNode("L+"));
				  }
				  dnbelements[i].appendChild(link_lock);
				  
				  // Permasage
				  dnbelements[i].appendChild(document.createTextNode(" "));
 				  link_sage = document.createElement("a");
  			  link_sage.setAttribute("href", cgi_url + 'manage/permasage/' + dnbinfo[1] + '/' + dnbinfo[2]);
          if (dnbinfo[4] == '2') {
				    // Si esta con permasage...agregar PS+
				    link_sage.setAttribute("title", "Desactivar Permasage");
 	  			  link_sage.setAttribute("onclick", "return confirm('¿Desactivar permasage?');");
	  			  link_sage.appendChild(document.createTextNode("PS-"));
				  } else {
				    link_sage.setAttribute("title", "Activar Permasage");
 	  			  link_sage.setAttribute("onclick", "return confirm('¿Activar permasage?');");
	  			  link_sage.appendChild(document.createTextNode("PS+"));
				  }
				  dnbelements[i].appendChild(link_sage);
				}
				dnbelements[i].appendChild(document.createTextNode("]"));
			}
			else if (dnbelement.getAttribute('class').substr(0, 15) == 'modboardoptions') {
				dnbinfo = dnbelement.getAttribute('class').split('|');
				link_close = document.createElement("a");
 			  link_close.setAttribute("href", cgi_url + 'manage/boardlock/' + dnbinfo[1]);
				if (dnbinfo[2] == 'True') {
					// Locked
 	  			link_close.setAttribute("onclick", "return confirm('¿Abrir board?');");
 	  			link_close.appendChild(document.createTextNode("Abrir Board"));
				} else {
					// Open
 	  			link_close.setAttribute("onclick", "return confirm('¿Cerrar board?');");
 	  			link_close.appendChild(document.createTextNode("Cerrar Board"));
				}
				dnbelements[i].appendChild(link_close);
			}
		}
	}
}
function togglethread(threadid) {
  if (hiddenthreads.toString().indexOf(threadid) !== -1) {
    document.getElementById('unhidethread' + threadid).style.display = 'none';
    document.getElementById('thread' + threadid).style.display = 'block';
    hiddenthreads.splice(hiddenthreads.indexOf(threadid), 1);
  } else {
    document.getElementById('unhidethread' + threadid).style.display = 'block';
    document.getElementById('thread' + threadid).style.display = 'none';
    hiddenthreads.push(threadid);
  }
  set_cookie('hiddenthreads', hiddenthreads.join('!'), 30);
  return false;
}
function set_inputs(id) {
	if (document.getElementById(id)) {
		with(document.getElementById(id)) {
			if(typeof(fielda) !== 'undefined' && !fielda.value) fielda.value = getCookie("weabot_name");
			if(!fieldb.value) fieldb.value = getCookie("weabot_email");
			if(!password.value) password.value = get_password("weabot_password");
			if(getCookie("weabot_noko")=="1") noko.checked="true";
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

window.onunload=function(e) {
	if(style_cookie) {
		var title=get_active_stylesheet();
		set_cookie(style_cookie,title,365);
	}
}

window.onload=function(e) {
  checkhighlight();
  delandbanlinks();
  for(var i=0;i<hiddenthreads.length;i++){
    try {
      document.getElementById('unhidethread' + hiddenthreads[i]).style.display = 'block';
      document.getElementById('thread' + hiddenthreads[i]).style.display = 'none';
    } catch(err) {
      continue;
    }
  }
}

if(style_cookie) {
	var cookie = getCookie(style_cookie);
	var title = cookie ? cookie : get_preferred_stylesheet();

	set_stylesheet(title);
}

if (getCookie('weabot_staff')=='yes') {
	weabot_staff = true;
}

var hiddenthreads = getCookie('hiddenthreads').split('!');

function oek_edit(image, postnum, width, height) {
  parent = document.getElementById("oek_edit");
  if(parent.lastChild)
    return;
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
  if(!parent.lastChild)
    return;
  while(parent.lastChild)
    parent.removeChild(parent.lastChild);

  document.getElementById("oek_size").style.display = "inline";
}

function reportPost(board, postnum) {
  var w = 460
  var h = 200
  var left = (screen.width/2)-(w/2);
  var top = (screen.height/2)-(h/2);
  window.open(cgi_url + 'report/' + board + '/' + postnum, 'Report Post','toolbar=no,menubar=no,resizable=no,scrollbars=no,status=no,location=no,width='+w+',height='+h+',top='+top+',left='+left);
}

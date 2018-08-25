console.log("%c¡Es calidad BaI!", "font-size: 50px; font-weight: bold;");

function toggle_style(e) {
  if (get_active_stylesheet() == 'Nostalgia')
    set_stylesheet('Home');
  else
    set_stylesheet('Nostalgia');
  
  e.preventDefault();
}

function check_news() {
  var last_t = 0;
  if(localStorage.last_t)
    last_t = localStorage.last_t;
  
  var items = document.getElementsByClassName('ni');
  var dates = document.getElementsByClassName('ni-d');
  for(var i=0; i<items.length; i++)
    if(parseInt(items[i].dataset.t) > last_t) {
      items[i].className += ' urgent';
      dates[i].innerHTML = '<img src="/new.gif" style="width:18px;height:7px;"><br />' + dates[i].innerHTML;
    }
    
  localStorage.last_t = Date.now() / 1000 | 0;
}

var style_cookie='home_style';

function set_stylesheet(styletitle) {
  localStorage.setItem(style_cookie, styletitle);

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

function get_active_stylesheet() {
	var links=document.getElementsByTagName("link");
	for(var i=0;i<links.length;i++) {
		var rel=links[i].getAttribute("rel");
		var title=links[i].getAttribute("title");
		if(rel.indexOf("style")!=-1&&title&&!links[i].disabled) return title;
	}
	
	return null;
}

if(style_cookie && localStorage.hasOwnProperty(style_cookie))
  set_stylesheet(localStorage.getItem(style_cookie));

document.addEventListener('DOMContentLoaded', function () {
  document.getElementById('change_style').addEventListener('click', toggle_style);
  document.getElementById('autorefresh').addEventListener('click', autoRefresh);
  check_news();
});

var lastTime = 0;
var refreshInterval;
var refreshMaxTime = 10;
var refreshTime;
var unread = {};
var serviceType = 0; // 1 = Home, 2 = BBS thread
var last_threads = 0;
var last_serverTime = 0;
var thread_length = 0;
var thread_lastreply = 0;
var thread_title = "";
var thread_first_length = 0;
var http_request = new XMLHttpRequest();

function loadJSON() {
  stopCounter("...");
  var data_file;
  if(serviceType == 1) {
    data_file = "/cgi/api/lastage?time=" + lastTime;
  } else if (serviceType == 2) {
    board = document.getElementsByName("board")[0].value;
    parent = document.getElementsByName("parent")[0].value;
    data_file = "/cgi/api/thread?dir="+board+"&id="+parent+"&offset="+thread_length+"&time=" + lastTime;
  } else { return false; }
  http_request.open("GET", data_file, true);
  http_request.send();
}
function setRead(threadId)
{
  if(threadId in unread) {
    unread[threadId] = false;
    updatePostList(last_threads, last_serverTime);
  }
}
function updatePostList(threads, serverTime) {
  html = "";
  last_threads = threads;
  last_serverTime = serverTime;
  var arrayLength = threads.length;
  var newposts = 0;
  var newTitle = "Bienvenido a Internet BBS/IB";
  var new_unread = false;
  var line;
  
  for(var i=0; i < arrayLength; i++) {
    thread = threads[i];
	line = (i+1) % 2
    
    if(thread.bumped >= lastTime)
    {
      unread[thread.id] = true;
      new_unread = true;
    }
    if(unread[thread.id]) html += '<span style="font-weight:bold;color:red;">';
    html += '<div class="line' + line + '"><small>' + thread.board_name + ': </small><a href="' + thread.url + '" onclick="setRead('+thread.id+');">' + thread.content + '</a> (' + thread.length + ')</div>';
    if(unread[thread.id]) { html += '</span>'; newposts++; }
  }
  if(newposts) {
    newTitle = '(' + newposts + ') ' + newTitle;
  }
  
  if(new_unread) {
    html += '<div style="font-weight:bold;color:red;text-align:center;font-size:large;">!!! NUEVOS AGE !!!</div>'
    refreshMaxTime = 10;
    if(document.getElementById('autosound').checked)
      document.getElementById("machina").play();
  } else {
    if(refreshMaxTime <= 120)
      refreshMaxTime += 5;
  }
  
  window.parent.document.title = newTitle;
  document.title = newTitle;
  document.getElementById("postlist").innerHTML = html;
}

function updateThread(posts, total_replies, serverTime) {
  allreplies = document.getElementsByClassName("allreplies")[0]
  for(var i=0; i < posts.length; i++)
  {
    post = posts[i];
    var div = document.createElement('div');
    div.class = "reply";
    if(post.email)
      s_name = '<span class="postername"><a href="mailto:'+post.email+'">'+post.name+'</a></span>';
    else
      s_name = '<span class="postername">'+post.name+'</span>';
    div.innerHTML = '<h3><span class="replynum">'+(thread_length+i+1)+'</span> : '+s_name+' : <span class="timestamp">'+post.timestamp_formatted+'</span></h3><div class="replytext">'+post.message+'</div>';
    allreplies.appendChild(div);
  }
  
  if(posts.length > 0) {
    refreshMaxTime = 10;
  } else {
    if(refreshMaxTime <= 60)
      refreshMaxTime += 5;
  }
  
  thread_length = parseInt(total_replies)+1;
  document.getElementsByClassName("thread")[0].firstChild.children[0].innerHTML = "("+thread_length+")";
  
  new_unread = thread_length - thread_first_length;
  
  document.title = '(' + new_unread + ') ' + thread_title
}
function counter() {
  if(refreshTime < 1)
  {
    loadJSON();
  } else {
    refreshTime--;
    document.getElementById("counter").innerHTML = (refreshTime+1);
  }
}
function detectService() {
  if(document.body.className === "threadpage") {
    serviceType = 1;
    length_str = document.getElementsByClassName("thread")[0].firstChild.children[0].innerText;
    thread_length = parseInt(length_str.substring(1, length_str.length-1));
    thread_first_length = thread_length;
    
    replylist = document.getElementsByClassName("reply");
    thread_lastreply = parseInt(replylist[replylist.length-1].firstChild.children[0].innerText);
    
    thread_title = document.title;
    
    if(thread_length == thread_lastreply) {
      serviceType = 2;
      document.getElementsByClassName("lastposts")[0].firstChild.innerHTML += ' | <input id="autorefresh" type="checkbox" onclick="autoRefresh()" /><label for="autorefresh"> Auto refresh</label> <span id="counter"></span>';
      return true;
    } else {
      return false;
    }
  } else if(document.body.className === "home") {
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
function autoRefresh() {
  chk_snd = document.getElementById("autosound");
  if(document.getElementById('autorefresh').checked) {
    if(chk_snd)
      chk_snd.disabled = false;
    lastTime = Math.floor(Date.now() / 1000);
    //loadJSON();
    refreshTime = refreshMaxTime;
    startCounter();
  } else {
    if(chk_snd)
      document.getElementById("autosound").disabled = true;
    stopCounter("");
  }
}

http_request.onreadystatechange = function(){
   if (http_request.readyState == 4){
      var jsonObj = JSON.parse(http_request.responseText);
      if(jsonObj.state == "success") {
        if(serviceType == 1)
          updatePostList(jsonObj.threads, jsonObj.time);
        else if(serviceType == 2)
          updateThread(jsonObj.posts, jsonObj.total_replies, jsonObj.time);
        
        lastTime = jsonObj.time;
        startCounter();
      }
   }
}
window.addEventListener('load', function() {
  if (!detectService()) return;
  
  chk = document.getElementById('autorefresh');
  chk_snd = document.getElementById('autosound');
  
  if(localStorage.getItem("autorefresh"+serviceType)) {
    document.getElementById('autorefresh').checked = true;
    autoRefresh();
  }
  if(!chk_snd) return;
  if(localStorage.getItem("mainpage_nosound"))
    document.getElementById('autosound').checked = false;
});
window.addEventListener('unload', function() {
  chk = document.getElementById('autorefresh');
  chk_snd = document.getElementById('autosound');
  if(!serviceType) return;
  
  if(chk.checked)
    localStorage.setItem("autorefresh"+serviceType, true);
  else
    localStorage.removeItem("autorefresh"+serviceType);
  if(!chk_snd) return;
  if(!document.getElementById('autosound').checked)
    localStorage.setItem("mainpage_nosound", true);
  else
    localStorage.removeItem("mainpage_nosound");
});
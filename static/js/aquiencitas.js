var cur_url;
var linklist;
var linki;
var is_bbs;
var plimit = 5;
function getPostRange(t, n) {
  var posts, replies, s, ss, ee, rev = false;
  posts = [];
  replies = t.getElementsByClassName("reply");
  s = n.split('-');
  ss = parseInt(s[0]);
  ee = ss;
  if(s.length == 2) ee = parseInt(s[1]);
  if(ee<ss) { tmp=ss;ss=ee;ee=tmp; rev=true; }
  for(j = 0; j < replies.length; j++) {
    num = parseInt(replies[j].dataset.n);
    if(num > ee) break;
    if(num >= ss && num <= ee) {
      if(rev)
        posts.unshift(replies[j]);
      else
        posts.push(replies[j]);
    }
  }
  return posts;
}
function findAncestor (el) {
  while ((el = el.parentElement) && !el.className.startsWith("thread") && !el.className.startsWith("cont"));
  return el;
}
function getPostDivs(e) {
  if(is_bbs) {
    divs = [];
    t = findAncestor(e);
    s = e.getAttribute('href').split('/');
    r = s[s.length-1];
    rs = r.split(',');
    linki = 0;
    for(i=0;i<rs.length;i++) {
      divs.push.apply(divs, getPostRange(t, rs[i]));
    }
    return divs;
  } else {
    ele = document.getElementById('reply' + e.getAttribute('href').split('#')[1]);
    return [ele,];
  }
}
function get_pid(e) {
  return is_bbs ? e.dataset.n : e.id.substr(5);
}
function fill_links(e) {
  var divs = getPostDivs(e);
  if(!divs[0]) return;
  
  this_id = get_pid(e.parentNode.parentNode);
  
  for(i=0;i<divs.length;i++) {
    tid = get_pid(divs[i]);
    if (linklist[tid])
      continue;
    if (this_id == tid)
      continue;
    t = (is_bbs ? divs[i].getElementsByTagName("h4")[0] : divs[i]);
    bl = document.createElement('a');
    bl.href = cur_url + (is_bbs ? "/" : "#") + this_id;
    bl.textContent = '>>' + this_id;
    bl.addEventListener('mouseover', who_are_you_quoting, false);
    bl.addEventListener('mouseout', remove_quote_preview, false);
    if (!(qb = t.getElementsByClassName('quoted')[0])) {
        qb = document.createElement((is_bbs ? 'span' : 'div'));
        qb.className = 'quoted';
        qb.textContent = ' Citado por: ';
        qb.appendChild(bl);
        if(is_bbs) {
          t.insertBefore(qb, t.getElementsByClassName("del")[0]);
          t.insertBefore(document.createTextNode(' '), t.getElementsByClassName("del")[0]);
        } else {
          t.insertBefore(qb, t.getElementsByTagName("blockquote")[0]);
        }
    } else {
        qb.appendChild(document.createTextNode(' '));
        qb.appendChild(bl);
    }
    linklist[tid] = true;
  }
}
function who_are_you_quoting(e) {
    var parent, d, clr, src, cnt, left, top, width, maxWidth;
    e = e.target || window.event.srcElement;
    var divs = getPostDivs(e);
    if(!divs[0]) return;
    
    maxWidth = 500;
    cnt = document.createElement('div');
    cnt.id = 'q-p';
    width = divs[0].offsetWidth;
    if (width > maxWidth) {
        width = maxWidth;
    }
    
    for(i=0;i<divs.length&&i<plimit;i++) {
      src = divs[i].cloneNode(true);
      src.id = 'q-p-s';
      if (src.tagName == 'DIV') {
          src.setAttribute('class', 'q-p-op');
          clr = document.createElement('div');
          clr.setAttribute('class', 'newthr');
          src.appendChild(clr);
      }
      cnt.appendChild(src);
    }
    left = 0;
    top = e.offsetHeight + 1;
    parent = e;
    do {
        left += parent.offsetLeft;
        top += parent.offsetTop;
    } while (parent = parent.offsetParent);
    if ((d = document.body.offsetWidth - left - width) < 0) {
        left += d;
    }
    cnt.setAttribute('style', 'left:' + left + 'px;top:' + top + 'px;');
    document.body.appendChild(cnt);
}
function remove_quote_preview(e) {
    var cnt;
    if (cnt = document.getElementById('q-p')) {
        document.body.removeChild(cnt);
    }
}
function quotePreview() {
    var i, q, replies, quotes;
    
    if(document.body.className && document.body.className != "res")
      is_bbs = true;
    else
      is_bbs = false;
    
    if(is_bbs)
      replies = document.getElementsByClassName('msg');
    else
      replies = document.getElementsByTagName('blockquote');
    
    urls = window.location.pathname.split("/");
    cur_url = urls[0] + "/" + urls[1] + "/" + urls[2] + "/" + urls[3];
    
    for (x = 0; x < replies.length; x++) {
      quotes = replies[x].getElementsByTagName('a');
      linklist = {};
      
      for (i = 0; i < quotes.length; i++) {
        q = quotes[i];
        if(q.textContent.length < 3 || !q.textContent.startsWith(">>")) continue;
        
        q.addEventListener('mouseover', who_are_you_quoting, false);
        q.addEventListener('mouseout', remove_quote_preview, false);
        
        fill_links(q);
      }
    }
}
document.addEventListener('DOMContentLoaded', quotePreview, false);
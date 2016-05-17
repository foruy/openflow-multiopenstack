function getid(id){
  return document.getElementById(id)
}

var Ajax;
function CreateAjax(){
    if (window.XMLHttpRequest){ 
        Ajax = new XMLHttpRequest(); 
    }
    else if (window.ActiveXObject){
        Ajax = new ActiveXObject("Microsoft.XMLHTTP"); 
    }
}

function SendData(url_,sendtext_){
      Ajax.open("POST",url_,true); 
      var  csr= document.getElementsByName("csrfmiddlewaretoken"); 
      var csrf_token = csr[0].value;
      Ajax.setRequestHeader("X-CSRFToken",csrf_token);
      Ajax.onreadystatechange = checkreturn; 
      Ajax.send(sendtext_);
}

function CheckAjaxStatus(Ajax_){
    if(Ajax_.readyState == 4)
        if(Ajax_.status == 200)
            return true;
    return false;
}

function checkreturn(){
  if(!CheckAjaxStatus(Ajax))return;
		console.log(Ajax.responseText);
		var info = eval("(" + Ajax.responseText + ")");
		console.log(info);
		if(200 == info.status){    
			if(info.id == "phoneValidity"){
				document.getElementById('phone_msg').style.background = 'url(/static/daoli/images/yes.png) no-repeat';
				document.getElementById(info.id).textContent="";
			}
			else if(info.id == "usernameValidity"){
                                var usermsg = getid('username_msg');
                                usermsg.style.background = 'url(/static/daoli/images/yes.png) no-repeat';
				document.getElementById(info.id).textContent="";
			}
			else if(info.id == "emailValidity"){
				document.getElementById('email_msg').style.background = 'url(/static/daoli/images/yes.png) no-repeat';
				document.getElementById(info.id).textContent="";
			}
        	}  
        	else{
			if(info.id == "phoneValidity"){
				document.getElementById('phone_msg').style.background = 'url(/static/daoli/images/no.png) no-repeat';
				document.getElementById(info.id).style.color="red";
				document.getElementById(info.id).textContent="Mobile has been used";
			}
			else if(info.id == "usernameValidity"){
                                var usermsg = getid('username_msg');
                                usermsg.style.background = 'url(/static/daoli/images/no.png) no-repeat';
				document.getElementById(info.id).style.color="red";
				document.getElementById(info.id).textContent="Someone use it";
			}
			else if(info.id == "emailValidity"){
				document.getElementById('email_msg').style.background = 'url(/static/daoli/images/no.png) no-repeat';
				document.getElementById(info.id).style.color="red";
				document.getElementById(info.id).textContent="Email has been registered";
			}
       		}
}

function isTrue(obj){
		var pattern = new Object;
		pattern.phone = new RegExp(/^[0-9]{4,}$/); 
		pattern.email = new RegExp(/^[a-zA-Z0-9_-][a-zA-Z0-9._-]*@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+$/); 
		pattern.username = new RegExp(/^[a-zA-Z0-9._-]{4,20}$/);
		pattern.password = new RegExp(/^[\@A-Za-z0-9\!\#\$\%\^\&\*\.\~]{6,20}$/);
		return  obj.value.match(pattern[obj.name]);
}


function check(obj,id,msg_id){
		if(obj.value == ""){
                        document.getElementById(msg_id).style.background = 'url(/static/daoli/images/no.png) no-repeat';
			document.getElementById(id).style.color="red";
			document.getElementById(id).textContent="You can't leave this empty";
			return;
		}
		else if(isTrue(obj) == null){
                        document.getElementById(msg_id).style.background = 'url(/static/daoli/images/no.png) no-repeat';
			if(id == 'usernameValidity'){
		 		document.getElementById(id).style.color="red";
		 		document.getElementById(id).textContent="Incorrect format";
			}
			else if(id == 'emailValidity'){
		 		document.getElementById(id).style.color="red";
		 		document.getElementById(id).textContent="Incorrect format";
			}
			else if(id == 'phoneValidity'){
		 		document.getElementById(id).style.color="red";
		 		document.getElementById(id).textContent="Incorrect format";
			}
			return;
		}
			var disc = new Object;
			disc.checkonly_type = obj.name;
			disc.check_dest = obj.value;
			disc.id = id;
			var json = JSON.stringify(disc);
		  CreateAjax();
		  SendData("/dashboard/check_only/",json);
}

function notnull(obj,id,msg_id)
{
	if(obj.value == ""){
		document.getElementById(msg_id).style.background = 'url(/static/daoli/images/no.png) no-repeat';	
		document.getElementById(id).style.color="red";
		document.getElementById(id).textContent="You can't leave this empty";
	}
	else{
		document.getElementById(msg_id).style.background = 'url(/static/daoli/images/yes.png) no-repeat';	
		document.getElementById(id).textContent="";
	}
}
function check_password(obj,id,msg_id){
	if(obj.value == ""){
                document.getElementById(msg_id).style.background = 'url(/static/daoli/images/no.png) no-repeat';
		document.getElementById(id).style.color="red";
		document.getElementById(id).textContent="You can't leave this empty";
	}	
	else if(isTrue(obj) == null){	
                document.getElementById(msg_id).style.background = 'url(/static/daoli/images/no.png) no-repeat';
		document.getElementById(id).style.color="red";
		document.getElementById(id).textContent="Incorrect format";
	}
	else{
		document.getElementById('passwordValidity').textContent="";
		document.getElementById('password_msg').style.background = 'url(/static/daoli/images/yes.png) no-repeat';
   }
}
function check_password_again(obj,id,msg_id){
	if(obj.value == ""){
                document.getElementById(msg_id).style.background = 'url(/static/daoli/images/no.png) no-repeat';
		document.getElementById(id).style.color="red";
		document.getElementById(id).textContent="You can't leave this empty";
	}	
        else if((obj.value == document.getElementById("password").value) && obj.value != '' ){
        	document.getElementById('password_again_msg').style.background = 'url(/static/daoli/images/yes.png) no-repeat';
        	document.getElementById('againValidity').textContent="";
        }
        else{
        	document.getElementById('password_again_msg').style.background = 'url(/static/daoli/images/no.png) no-repeat';
         	document.getElementById('againValidity').style.color="red";
         	document.getElementById('againValidity').textContent="Twice inconsistent";
        }
}

!
function(a) {
    function b(a) {
        return "string" == typeof a ? j.getElementById(a) : a
    }

    function c(a) {
        return a ? a.trim() : a
    }

    function d(a, b) {
        return a && a.className.match(new RegExp("(\\s|^)" + b + "(\\s|$)"))
    }

    function e(a, b) {
        a && !d(a, b) && (a.className += " " + b)
    }

    function f(a, b) {
        if (d(a, b)) {
            var c = new RegExp("(\\s|^)" + b + "(\\s|$)");
            a.className = a.className.replace(c, " ")
        }
    }

    function get_csrf_token(){
        var a = document.getElementsByName("csrfmiddlewaretoken"); 
        var csrf_token = a[0].value;
        return csrf_token; 
    }

    function g(a, b, c) {
        var d = new XMLHttpRequest;
        d.open(a.method, a.url, !0), d.setRequestHeader("Content-Type", a.contentType), d.setRequestHeader("X-CSRFToken", get_csrf_token()), d.onreadystatechange = function() {
		if(4 == d.readyState){
			if(200 == d.status){
				b && b(d.responseText);	
			}
		else if(201 == d.status){
			alert("SMS wrong");
			document.getElementById("mobileBtn").textContent="Participate";
			document.getElementById("mobileBtn").removeAttribute("disabled");
			document.getElementById("mobileBtn").style.background="#00b7ee";
			document.getElementById("mobileBtn").style.color="#FFF";
		}
		else if(204 == d.status){
		        alert("Verification wrong");
			document.getElementById("mobileBtn").textContent="Participate";
			document.getElementById("mobileBtn").removeAttribute("disabled");
			document.getElementById("mobileBtn").style.background="#00b7ee";
			document.getElementById("mobileBtn").style.color="#FFF";
		}
		else if(210 == d.status){
			alert("Connect time out");
   			window.location.reload();	
		}
		else {c && c(d);}}
        }, d.send(JSON.stringify(a.data))
    }

    function h(o) {
        var a, b, d, g = !0,
            h = {};
        for (var i in o) a = !0, d = o[i], b = c(d.value || d.element && d.element.value), h[i] = b, d.requiwhite && (a = !! b, !a && d.validity && (d.validity.textContent = d.requiwhiteErrorMessage)), a && d.pattern && (a = d.pattern.test(b), !a && d.validity && (d.validity.textContent = d.patternErrorMessage)), a && d.custom && (a = d.custom(b), !a && d.validity && (d.validity.textContent = d.customErrorMessage)), g && (g = a), d.validity && (d.validity.style.display = a ? "none" : "block"), a && f(d.element, "error-field"), !a && e(d.element, "error-field"),console.log(h[i]); 
		return g && h
    }

    function i(a) {
        if (a.global) alert(a.global);
        else if (a.field) for (var b in a.field) o[b] && (e(o[b].element, "error-field"), o[b].validity && (o[b].validity.textContent = a.field[b]), o[b].validity && (o[b].validity.style.display = "block"))
    }
    var j = a.document,
        n = b("mobileBtn"),
        p = {
            name: {
                element: b("username"),
                validity: b("usernameValidity"),
                requiwhite: !0,
                requiwhiteErrorMessage: "You can't leave this empty",
                custom: function(a) {
                    return /^[^.]+$/.test(a) && (/^[a-zA-Z0-9._-]{4,20}$/.test(a))
                },
                customErrorMessage: "Incorrect format. Please 1-20 words"
            },
            email: {
                element: b("email"),
                validity: b("emailValidity"),
                requiwhite: !0,
                requiwhiteErrorMessage: "You can't leave this empty",
                pattern: /^[a-zA-Z0-9_-][a-zA-Z0-9._-]*@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+$/,
                patternErrorMessage: "Incorrect format"
            },
            password: {
                element: b("password"),
                validity: b("passwordValidity"),
                requiwhite: !0,
                requiwhiteErrorMessage: "You can't leave this empty",
                pattern: /^[\@A-Za-z0-9\!\#\$\%\^\&\*\.\~]{6,20}$/,
                patternErrorMessage: "Incorrect format"
            },
/*
           password_again: {
                element: b("password_again"),
                validity: b("againValidity"),
                requiwhite: !0,
                requiwhiteErrorMessage: "You can't leave this empty",
                pattern: /^[a-zA-Z0-9_-]{6,20}$/,
              	custom: function(a) {
                    return (p["password_again"].element.value ==p["password"].element.value) ? true : false ;
                },
                customErrorMessage: "Twice inconsistent"
            },
*/
            phone: {
                element: b("phone"),
                validity: b("phoneValidity"),
                requiwhite: !0,
                requiwhiteErrorMessage: "You can't leave this empty",
                pattern: /^[0-9]{4,}$/,
                patternErrorMessage: "Incorrect format"
            },
            company: {
                element: b("company"),
                validity: b("companyValidity"),
                requiwhite: !0,
                requiwhiteErrorMessage: "You can't leave this empty",
                pattern: /^.{4,100}$/,
                patternErrorMessage: "Incorrect format"
            },
            reason: {
                element: b("reason"),
                validity: b("reasonValidity"),
                requiwhite: !0,
                requiwhiteErrorMessage: "You can't leave this empty"
            }
        };
    	n.addEventListener("click", function() {
        var b = h(p);
	 b.type = "phone";
	 console.log(b);
        b && (n.setAttribute("disabled", "disabled"),document.getElementById("mobileBtn").style.background = "url(/static/daoli/images/registerload.gif)no-repeat",
        document.getElementById("mobileBtn").textContent="wait...",document.getElementById("mobileBtn").style.color="black",
        g({
            url:"/dashboard/register/",
            method: "POST",
            contentType: "application/json",
            data: b
        }, function(b) {
            n.removeAttribute("disabled");
    
           a.location.replace("/dashboard/jump")
        }, function() {
            n.removeAttribute("disabled"), alert("Network conditions, please re-register");
            window.location.reload();	
        }))
    })
}(window);


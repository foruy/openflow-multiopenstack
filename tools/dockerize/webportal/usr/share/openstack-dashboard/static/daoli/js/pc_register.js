//xuanze yanzhengfangshi
/*document.getElementById("mobiletab").style.color ="white";    
document.getElementById("mobiletab").style.background = "url(/static/dashboard/img/after.png)no-repeat";    
//document.getElementById("tabmobile").setAttribute("disabled", "disabled");  
    document.getElementById("mobiletab").addEventListener("click",function(){
        document.getElementById("mobiletab").style.color ="white";    
        document.getElementById("mobiletab").style.background = "url(/static/dashboard/img/after.png)no-repeat";    
        document.getElementById("qqtab").style.color ="black";    
        document.getElementById("qqtab").style.background = "url(/static/dashboard/img/before.png)no-repeat";    
        document.getElementById("wechattab").style.color ="black";    
        document.getElementById("wechattab").style.background = "url(/static/dashboard/img/before.png)no-repeat";    
        //换头
        document.getElementById("tabmobile").style.display ="block";    
        document.getElementById("tabqq").style.display ="none";    
        //document.getElementById("tabwechat").style.display ="none"; 
        //换Btn
        document.getElementById("mobileBtn").style.display ="block";    
        document.getElementById("qqBtn").style.display ="none";    
        document.getElementById("wechatBtn").style.display ="none";   
		//清空表单
        document.getElementById("reg_form").reset();
	
   }) 
	 */
    /*
    
    document.getElementById("qqtab").addEventListener("click",function(){
        document.getElementById("mobiletab").style.color ="black";    
        document.getElementById("mobiletab").style.background = "url(/static/dashboard/img/before.png)no-repeat";   
        document.getElementById("qqtab").style.color ="white";    
        document.getElementById("qqtab").style.background = "url(/static/dashboard/img/after.png)no-repeat";    
        document.getElementById("wechattab").style.color ="black";    
        document.getElementById("wechattab").style.background = "url(/static/dashboard/img/before.png)no-repeat";  
        //换头
        document.getElementById("tabmobile").style.display ="none";    
        document.getElementById("tabqq").style.display ="block";    
        //document.getElementById("tabwechat").style.display ="none";   
        //换Btn
        document.getElementById("mobileBtn").style.display ="none";    
        document.getElementById("qqBtn").style.display ="block";    
        document.getElementById("wechatBtn").style.display ="none";  
		//清空表单
        document.getElementById("reg_form").reset();
   })     
    document.getElementById("wechattab").addEventListener("click",function(){
        document.getElementById("mobiletab").style.color ="black";    
        document.getElementById("mobiletab").style.background = "url(/static/dashboard/img/before.png)no-repeat";    
        document.getElementById("qqtab").style.color ="black";    
        document.getElementById("qqtab").style.background = "url(/static/dashboard/img/before.png)no-repeat";   
        document.getElementById("wechattab").style.color ="white";    
        document.getElementById("wechattab").style.background = "url(/static/dashboard/img/after.png)no-repeat";    
        //换头
        document.getElementById("tabmobile").style.display ="none";    
        document.getElementById("tabqq").style.display ="none";    
       // document.getElementById("tabwechat").style.display ="block";   
        //换Btn
        document.getElementById("mobileBtn").style.display ="none";    
        document.getElementById("qqBtn").style.display ="none";    
        document.getElementById("wechatBtn").style.display ="block"; 
		//清空表单
        document.getElementById("reg_form").reset();
		
  })

*/
var wait = 60;
function time(o) { 
    if (wait == 0) { 
        o.removeAttribute("disabled");           
        o.textContent="免费获取验证码"; 
        wait = 60; 
    } 
    else {
        o.setAttribute("disabled", true); 
        //o.value=wait+"秒后可以重新发送";
        o.textContent=wait+"秒后可以重新发送";
        wait--; 
        setTimeout(function() { 
        time(o) 
        }, 
        1000) 
     } 
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
			Ajax.setRequestHeader("X-CSRFToken",csrf_token)
      Ajax.onreadystatechange = checkreturn; 
      Ajax.send(sendtext_);
}

function SendData2(url_,sendtext_){
		  Ajax.open("POST",url_,true); 
      var  csr= document.getElementsByName("csrfmiddlewaretoken"); 
      var csrf_token = csr[0].value;
      Ajax.setRequestHeader("X-CSRFToken",csrf_token)
      Ajax.send(sendtext_);
}

function CheckAjaxStatus(Ajax_){
    if(Ajax_.readyState == 4)
        if(Ajax_.status == 200)
            return true;
    return false;
}
//server fanhui jieguopanduan
function checkreturn(){
  if(!CheckAjaxStatus(Ajax))return;
		console.log(Ajax.responseText);
		var info = eval("(" + Ajax.responseText + ")");
		console.log(info);
		console.log(info.status);
		console.log(info.id);
				if(200 == info.status){    
            document.getElementById(info.id).style.color="green";
            document.getElementById(info.id).textContent="可以使用";
        }  
        else{
            document.getElementById(info.id).style.color="red";
            document.getElementById(info.id).textContent="已经被使用";
        }
}

function isTrue(obj){
		var pattern = new Object;
		pattern.phone = new RegExp(/^1[0-9]{10}$/); 
		pattern.email = new RegExp(/^[a-zA-Z0-9_-][a-zA-Z0-9._-]*@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+$/); 
		pattern.username = new RegExp(/^[a-zA-Z0-9_-]{1,100}$/);
		return  obj.value.match(pattern[obj.name]);
}


function check(obj,id){
		if(isTrue(obj) == null){
			document.getElementById(id).style.color="red";
			document.getElementById(id).textContent="格式不正确";
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

function checknum(obj,id){
                var isPhone = document.getElementById("phone").value.match(new RegExp(/^1[0-9]{10}$/));
                if(isPhone == null){
                        document.getElementById(id).style.color="red";
                        document.getElementById(id).textContent="不能为空";
                        return;
                }
                time(obj);
                var disc = new Object;
                disc.check_type = "SMS";
                disc.check_dest = document.getElementById("phone").value;
                var json = JSON.stringify(disc);
    CreateAjax();
          SendData2("/dashboard/send_check_code/",json);
}


function checkimg(obj,id){
		if(obj.value==""){
			document.getElementById(id).style.color="red";
			document.getElementById(id).textContent="不能为空";
			return;
	  }	
		var disc = new Object;
		disc.check_type = "img"
		disc.check_dest = obj.value;
	  disc.id = id;	
		var json = JSON.stringify(disc);
		console.log(json);
    CreateAjax();
	  SendData2("/dashboard/to_check_code/",json);
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
        var a = document.getElementById("csrfmiddlewaretoken"); 
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
			alert("短信验证失败");
   			//window.location.reload();
                        document.getElementById("changeimg").src="/dashboard/send_check_img?"+Math.random();
			document.getElementById("checknum").value="";
			document.getElementById("mobileBtn").textContent="申请参加公测";
			document.getElementById("mobileBtn").removeAttribute("disabled");
		}
		else if(204 == d.status){
		        alert("Verification wrong");
                        document.getElementById("changeimg").src="/dashboard/send_check_img?"+Math.random();
			document.getElementById("imgcheck").value="";
			document.getElementById("mobileBtn").textContent="申请参加公测";
			document.getElementById("mobileBtn").removeAttribute("disabled");
		}
		else if(210 == d.status){
			alert("服务器链接超时");
   			window.location.reload();	
		}
		else {c && c(d);}}
        }, d.send(JSON.stringify(a.data))
    }

    function h(o) {
        var a, b, d, g = !0,
            h = {};
        for (var i in o) a = !0, d = o[i], b = c(d.value || d.element && d.element.value), h[i] = b, d.requiwhite && (a = !! b, !a && d.validity && (d.validity.textContent = d.requiwhiteErrorMessage)), a && d.pattern && (a = d.pattern.test(b), !a && d.validity && (d.validity.textContent = d.patternErrorMessage)), a && d.custom && (a = d.custom(b), !a && d.validity && (d.validity.textContent = d.customErrorMessage)), g && (g = a), d.validity && (d.validity.style.display = a ? "none" : "block"), a && f(d.element, "error-field"), !a && e(d.element, "error-field"); 
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
                requiwhiteErrorMessage: "请填写姓名",
                custom: function(a) {
                    return /^[^.]+$/.test(a) && (/^[a-zA-Z\s.]{1,100}$/.test(a))
                },
                customErrorMessage: "全中文（长度1-6）或全英文（字母、空格、点号，长度1-100）"
            },
            email: {
                element: b("email"),
                validity: b("emailValidity"),
                requiwhite: !0,
                requiwhiteErrorMessage: "请填写邮箱",
                pattern: /^[a-zA-Z0-9_-][a-zA-Z0-9._-]*@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+$/,
                patternErrorMessage: "邮箱不合法"
            },
            email_again: {
                element: b("email_again"),
                validity: b("againValidity"),
                requiwhite: !0,
                requiwhiteErrorMessage: "请填写邮箱",
                pattern: /^[a-zA-Z0-9_-][a-zA-Z0-9._-]*@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+$/,
              	custom: function(a) {
                    return (p["email_again"].element.value ==p["email"].element.value) ? true : false ;
                },
                customErrorMessage: "两次填写不一致"
            },
            phone: {
                element: b("phone"),
                validity: b("phoneValidity"),
                requiwhite: !0,
                requiwhiteErrorMessage: "请填写手机号码",
                pattern: /^1[0-9]{10}$/,
                patternErrorMessage: "手机号码不合法"
            },
		imgcheck: {
                element: b("imgcheck"),
                validity: b("checkimgValidity"),
                required: !0,
                requiredErrorMessage: "请填写验证码",
                pattern: /^[a-zA-Z0-9_-][a-zA-Z0-9._-]{1,10}$/,
                patternErrorMessage: "不能为空"
            },
            checknum: {
                element: b("checknum"),
                validity: b("checknumValidity"),
                requiwhite: !0,
                requiwhiteErrorMessage: "请填写验证码",
                pattern: /^[0-9]{6}$/,
                patternErrorMessage: "验证码有误"
            },
            organization: {
                element: b("organization"),
                validity: b("organizationValidity"),
                requiwhite: !0,
                requiwhiteErrorMessage: "请填写企业或团队名称",
                pattern: /^.{1,100}$/,
                patternErrorMessage: "企业（团队）名称在100个字符以内"
            },
            reason: {
                element: b("reason"),
                validity: b("reasonValidity"),
                requiwhite: !0,
                requiwhiteErrorMessage: "请填写申请原因"
            }
        };
    n.addEventListener("click", function() {
        var b = h(p);
	  b.type = "phone";
	 console.log(b);
        b && (n.setAttribute("disabled", "disabled"),document.getElementById("mobileBtn").style.background = "url(/static/dashboard/img/registerload.gif)no-repeat",
        document.getElementById("mobileBtn").textContent="请稍候...",document.getElementById("mobileBtn").style.color="black",
        g({
            url:"/dashboard/register_form/",
            method: "POST",
            contentType: "application/json",
            data: b
        }, function(b) {
            n.removeAttribute("disabled");
    
           alert("申请成功，注意查收邮件"), a.location.replace("https://124.202.141.71")
        }, function() {
            n.removeAttribute("disabled"), alert("网络状况不佳，请稍候再试")
        }))
    })
}(window);


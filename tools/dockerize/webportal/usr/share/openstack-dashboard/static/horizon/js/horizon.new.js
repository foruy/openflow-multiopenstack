horizon.new = {
  icons: ["vpc","firewall","instance","monitor","billing","record","book","hybrid","build","storage","mysql","migration","tpm"],
  init_new: function(){
    var css = {"margin-left":"0", "padding-left": "40px", "width": "227px", "white-space": "no-wrap", "overflow": "hidden"};
    $(".sidebar ul").find("a").css(css).each(function(i,el){
      $(el).css("background", "url(/static/dashboard/img/sidebar_" + horizon.new.icons[i] + ".png) no-repeat 3% center");
    });
    $(".sidebar ul").find("a.active").css("background-color","#ffffff");
    $('body').prepend('<div id="head_tip" style="padding:0 20px;height:24px;background-color:#ccc"><h5 style="margin:0;color:#000;text-align:center;font-weight:100;padding-top:4px">' + gettext("Your instances\' initial SSH username & password: username=root; password=daoli123.") + '&nbsp;' + gettext("Please change your instances\' initial password immediately upon login") + '</h5></div><div style="position:absolute;left:49%"><p id="tip_switch" title="' + gettext("Show/Hide VM Login Help Info") + '" style="width:20px;height:16px;margin:0 auto;"><img src="/static/daoli/images/line_off.png" style="vertical-align:top" /></p></div>');
    if(horizon.cookies.get('tips')){$("#head_tip").hide();}
    $("#tip_switch").click(function(){
      if($("#head_tip").css("display")=='none'){
        $("#head_tip").fadeIn();
        horizon.cookies.put('tips',false);
      } else {
        $("#head_tip").fadeOut();
        horizon.cookies.put('tips',true)
      }
    });
  }
};

horizon.addInitFunction(function(){
  horizon.new.init_new();
});

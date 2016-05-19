// DaoliCloud GUI
;
(function (global, $) {

    // 各大功能命名空间，独立的功能放到独立的命名空间
    var zoom, // 实现缩放功能
        gui, // 存放对外可见的参数和功能
        config, // 存放全局配置参数
        tool; // 实现拖曳创建Instance

    // 全局配置参数
    config = {
        timeout: 2000,  // 默认延迟 2 秒处理

        // 缩放的范围
        domain: [0.5, 5],

        // 图片宽高
        image: {
            width: 44,
            height: 44
        },

        // 文字样式
        text: {
            "text-anchor": "middle",
        //    "font-family": "sans-serif",
            "font-family":"FangSong",
            "font-size": "large",
            "font-style":"normal"
        },

        // 图片样式
        css: {
            vm: "/static/dashboard/img/gui_pc.png",
            docker: "/static/dashboard/img/gui_container.png",
            wordpress: "/static/dashboard/img/gui_wordpress.png",
            container: "/static/dashboard/img/gui_container.png",
            apache: "/static/dashboard/img/gui_apache.png",
            java: "/static/dashboard/img/gui_java.png",
            lmap: "/static/dashboard/img/gui_lmap.png",
            mysql: "/static/dashboard/img/gui_mysql.png",
            ssh: "/static/dashboard/img/gui_ssh.png",
            nginx: "/static/dashboard/img/gui_nginx.png",
            python: "/static/dashboard/img/gui_python.png",
            tomcat: "/static/dashboard/img/gui_tomcat.png",
            ruby: "/static/dashboard/img/gui_ruby.png",
            nodejs: "/static/dashboard/img/gui_nodejs.png",
            php: "/static/dashboard/img/gui_php.png",
            perl: "/static/dashboard/img/gui_perl.png",
            mongodb: "/static/dashboard/img/gui_mongodb.png",
            go: "/static/dashboard/img/gui_go.png",
            postgresql: "/static/dashboard/img/gui_postgresql.png",
            redis: "/static/dashboard/img/gui_redis.png"
        },

        // 图片显示名称映射
        typeMap: {
            vm: "VM",
            docker: "Docker",
            wordpress: "WordPress",
            container: "Container",
            apache: "Apache",
            java: "Java",
            lmap: "Lamp",
            mysql: "MySQL",
            ssh: "SSH",
            nginx: "Nginx",
            python: "Python",
            tomcat: "Tomcat",
            ruby: "Ruby",
            nodejs: "Nodejs",
            php: "PHP",
            perl: "Perl",
            mongodb: "MongoDB",
            go:"Go",
            postgresql:"Postgresql",
            redis:"Redis"
        },

        // 加载
        status: {
            BUILD: {
                image: "/static/dashboard/img/gui_loading.gif",
                text: "loading"
            },
            ERROR: {
                image: "/static/dashboard/img/gui_error.png",
                text: "error"
            }
        },

        // load窗口
        loadModel: {
            width: 400,
            height: 400
        }
    };

    // 实现缩放功能
    // (Gaofeng)：关于缩放，有两种方式类型：（1）通过滚动鼠标滚轮；（2）使用Slider控件。
    // 这两种缩放功能是独立，互不依赖，但对于其命名，我感觉有点混乱，有待下一次重构。
    // 另外，在缩放功能中，有个附加功能：上下左右移动画布。该功能也有两种方式类型：
    // (1)通过鼠标左键拖曵——上下左右；（2）通过点击Slider控件上方的上下左右控件。
    zoom = {
        // 用于区别触发缩放功能的类型：（1）鼠标滚动缩放，（2）Slider缩放
        // 此标志为了防止缩放两次。
        roll_click: true,

        // 点击roll button按钮，实现上下左右移动
        rollButton: function() {
            var roll_buttons = $("#roll_button div");
            var position = ["0px", "0px"].join(" ");
            var translate = [0, 0];
            var d = 80; // 每次幅度80

            // 为上下左右添加事件（mouseover，mouseout，click）和参数
            for (var i = 0, n = roll_buttons.length; i < n; i++) {
                switch (roll_buttons[i].id) {
                    case "roll_buttonN":
                        position = ["0px", "-44px"].join(" ");
                        translate = [0, -d];
                        zoom.rollMouseEvent("#roll_buttonN", position, translate);
                        break;
                    case "roll_buttonS":
                        position = ["0px", "-132px"].join(" ");
                        translate = [0, d];
                        zoom.rollMouseEvent("#roll_buttonS", position, translate);
                        break;
                    case "roll_buttonE":
                        position = ["0px", "-88px"].join(" ");
                        translate = [d, 0];
                        zoom.rollMouseEvent("#roll_buttonE", position, translate);
                        break;
                    case "roll_buttonW":
                        position = ["0px", "-176px"].join(" ");
                        translate = [-d, 0];
                        zoom.rollMouseEvent("#roll_buttonW", position, translate);
                        break;
                }
            }
        },

        // 上下左右事件
        // 鼠标移到id上面，背景图片position偏移位置
        // 鼠标点击id，位置发生translate移动
        rollMouseEvent: function(id, position, translate) {
            $(id).mouseover(function() {
                $("#roll_button").css('background-position', position);
            });

            $(id).mouseout(function() {
                $("#roll_button").css('background-position', "0px 0px");
            });

            $(id).click(function() {
                var trans = zoom.coordinate(gui.share.g1.attr("transform"));
                var s = zoom.scale(gui.share.g1.attr('transform'));
                gui.share.g1.attr("transform", "translate(" + zoom.coordinateAdd(trans, translate) + ")scale(" + s + ")");
            });
        },

        // 提取整个画布的偏移量
        coordinate: function(translate) {
            if (translate) {
                var m;

                if (translate.indexOf(",") == -1) {
                    // ie问题
                    m = translate.split(' ');
                } else {
                    m = translate.split(',');
                }

                var x = m[0].split('(');
                var t = m[1].split(')');
                return [x[1], t[0]];
            } else {
                return [0, 0];
            }
        },

        // 偏移量相加，放回新的偏移量
        coordinateAdd: function(trans1, trans2) {
            x = parseInt(trans1[0]) + parseInt(trans2[0]);
            y = parseInt(trans1[1]) + parseInt(trans2[1]);
            return [x, y].join(',');
        },

        // 鼠标滚轮缩放
        roll_zoom: function() {
            gui.share.g1.attr("transform", "translate(" + d3.event.translate + ")scale(" + d3.event.scale + ")");
            zoom.roll_click = false;
            var value = (zoom.scale(gui.share.g1.attr('transform')) - config.domain[0]) / (config.domain[1] - config.domain[0]) * 100;
            $("#slider").slider('value', value);
        },

        // 初始化 Slider 的 Range
        roll_zoom_init: function() {
            $("#slider").slider({
                orientation: "vertical",
                range: "min"
            });
            var value = (zoom.scale(gui.share.g1.attr('transform')) - config.domain[0]) / config.domain[1] * 100;
            $("#slider").slider('value', value);
        },

        // 获取缩放的比例，默认为1
        scale: function(scales) {
            if (scales) {
                return scales.split("scale(")[1].split(')')[0];
            } else {
                return 1;
            }
        },

        // roll中slider值改变，缩放画布
        roll_move: function() {
            var value1 = $('#slider').slider('value');
            $('#slider').bind('slidechange', function(event, ui) {
                if (zoom.roll_click) {
                    var value2 = $('#slider').slider('value');
                    zoom.roll_action(value1, value2);
                    value1 = value2;
                }
            });
        },

        // 根据roll中slider值，缩放画布
        roll_action: function(value1, value2) {
            if (value1 != value2) {
                var tran_d_x = (value2 - value1) / 100 * (config.domain[1] - config.domain[0]) * (-500),
                    tran_d_y = (value2 - value1) / 100 * (config.domain[1] - config.domain[0]) * (-250);
                var trans = zoom.coordinate(gui.share.g1.attr("transform"));
                var s = value2 / 100 * (config.domain[1] - config.domain[0]) + config.domain[0];
                gui.share.g1.attr("transform", "translate(" + zoom.coordinateAdd(trans, [tran_d_x, tran_d_y]) + ")scale(" + s + ")");
            }
        },

        // 初始化画布大小，缩放
        init: function(svg, width, height) {
            gui.share.g1.append("rect")
                .classed('overlay', false)
                .attr("width", width)
                .attr("height", height)
                .attr('opacity', 0);

            // 给svg绑定缩放事件
            svg.call(d3.behavior.zoom().scaleExtent(config.domain).on("zoom", zoom.roll_zoom))
                .on('dblclick.zoom', null);

            this.rollButton(); // 为roll button绑定上下左右等移动事件
            this.roll_zoom_init(); // 初始化Slider的Range
            this.roll_move(); // 为Slider绑定事件——当Slider值发生改变时，缩放画布

            // 当鼠标放到Slider缩放控件上时，如果发生缩放事件，则认为缩放类型为Slider缩放，并由Slider进行缩放；
            // 否则，认为缩放类型是鼠标缩放
            $("#slider").mouseover(function(e) {
                zoom.roll_click = true;
            });

            // 为 Slider 中的 + 控件绑定缩放事件——点击此控件，可以放大画布
            $("#slider_plus").bind({
                mouseover: function(e) {
                    $(this).css('background-position', "0px -243px");
                },

                mouseout: function(e) {
                    $(this).css('background-position', "0px -221px");
                },

                click: function(e) {
                    e.stopPropagation();
                    svg.call(d3.behavior.zoom().scaleExtent(config.domain).on("zoom", zoom.roll_zoom));
                    var value = $("#slider").slider("value");
                    var value2;
                    zoom.roll_click = false;

                    if ((value + 20) <= 100) {
                        value2 = value + 20;
                    } else {
                        value2 = 100;
                    }

                    zoom.roll_action(value, value2);
                    $("#slider").slider("value", value2);
                }
            });

            // 为 Slider 中的 - 控件绑定缩放事件——点击此控件，可以缩放画布
            $("#slider_minus").bind({
                mouseover: function(e) {
                    $(this).css('background-position', "0px -287px");
                },

                mouseout: function(e) {
                    $(this).css('background-position', "0px -265px");
                },

                click: function(e) {
                    e.stopPropagation();
                    var value = $("#slider").slider("value");
                    var value2;
                    zoom.roll_click = false;

                    if ((value - 20) >= 1) {
                        value2 = value - 20;
                    } else {
                        value2 = 1;
                    }

                    zoom.roll_action(value, value2);
                    $("#slider").slider("value", value2);
                }
            });
        },
    };

    // 主要存放供其它组件共享的参数和功能，此对象会被导出到全局空间，供外部查看
    gui = {
        // 各组件间的共享变量
        share: {
            // 是否点击了图标
            select_node: null,
            // 是否点击剪刀
            select_scissor: false,
            // 是否点击划线
            select_drawline: false,
            // 设置tip停留
            interval: null,
            // 用于控制links中id值
            links_length: 0,
        },

        // 初始化GUI
        init: function() {
            var width = document.getElementById("play").offsetWidth,
                height = document.getElementById("play").offsetHeight;
            gui.share.width = width;
            gui.share.height = height;

            var svg = d3.select("#play").append("svg")
                .attr("width", width)
                .attr("height", height)
                .attr("pointer-events", 'all')
                .style('overflow', 'hidden')
                .append('g');
            var g1 = svg.append("g").attr('id', 'g1');
            gui.share.g1 = g1;

            // 初始化缩放功能
            zoom.init(svg, width, height);

            gui.share.g_links = g1.append("g");
            gui.share.g_nodes = g1.append("g");

            // tool拖拽创建虚拟机
            tool.init();

            // 加载Instances数据
            this.load_data(width, height);

            // 为Instance的 Start、Stop 或 Delete 绑定事件
            $("#gui_check").click(gui._events.instance_action.start_stop);
            $("#gui_button_delete").click(gui._events.instance_action.terminate);
            //$("#gui_button_delete").click(gui._events.instance_action.click_info);
            $("#gui_button_delete_yes").click(gui._events.instance_action.sure_info_yes);
            $("#gui_button_delete_no").click(gui._events.instance_action.sure_info_no);
        },

        // 格式化数据，保留唯一关系，即消重（比如links={"A":"B","B":"A"}格式化成links=[{"A","B"}]）
        formatData: function(links) {
            var linknew = [];

            for (var i in links) {
                for (var j in links[i]) {
                    linknew.push({
                        source: i,
                        target: links[i][j]
                    });
                }
            }

            for (var i in linknew) {
                for (var j in linknew) {
                    if (linknew[j].source == linknew[i].target && linknew[j].target == linknew[i].source) {
                        linknew.splice(j, 1);
                    }
                }
            }
            return linknew;
        },

        // 根据links中的uuid找到虚拟机信息，此时links就是各个虚拟机之间的关系
        linkFormate: function(links, nodes) {
            function finduuid(nodes, id) {
                var i = 0;
                for (i = 0; i < nodes.length; i++) {
                    if (nodes[i].id == id) {
                        return nodes[i];
                    }
                }
                return null;
            }
            var newlinks = [];
            var num = 0;
            for (var i = 0; i < links.length; i++) {
                if (finduuid(nodes, links[i].source) && finduuid(nodes, links[i].target)) {
                    links[i].source = finduuid(nodes, links[i].source);
                    links[i].target = finduuid(nodes, links[i].target);
                    links[i].id = num;
                    num++;
                    newlinks.push(links[i]);
                } else {
                    console.log("[links]", "not find", links[i]);
                }
            }
            return newlinks;
        },

        // 通过 ID 找到相应的 Node 信息
        getNode: function (node_id, nodes) {
            if (!nodes) {
                nodes = gui.share.nodes;
            }
            for (var i = 0; i < nodes.length; i++) {
                if (nodes[i].id == node_id) {
                    return nodes[i];
                }
            }
            return null;
        },

        // 通过 ID 移除某个 Node 节点信息
        removeNode: function (node_id, nodes) {
            if (!nodes) {
                nodes = gui.share.nodes;
            }
            for (var i = 0; i < nodes.length; i++) {
                if (nodes[i].id == id) {
                    nodes.splice(i, 1);
                    break;
                }
            }
        },

        // 请求Instances数据，并根据数据动态显示到页面上
        load_data: function(width, height) {

            tool.renderLoad(50, $(".draw").width(), $(".draw").height(), $(".draw").offset());
            tool.loading(1);

            // 求线段的中点
            function middle(point1, point2) {
                var x = (point2[0] - point1[0]) / 2 + point1[0];
                var y = (point2[1] - point1[1]) / 2 + point1[1];
                return [x, y];
            }

            // AJAX 成功时的回调函数
            function _success(o) {
                tool.loading(0);
                var nodes = o.servers,
                    links = o.groups;
                gui.share.nodes = nodes;
                gui.share.links = links;
                console.log("nodes", nodes, "links", links);
                gui.share.links = gui.formatData(gui.share.links);
                //console.log("links", gui.share.links);
                gui.share.links = gui.linkFormate(gui.share.links, gui.share.nodes);
                //console.log("links", gui.share.links);
                gui.share.links_length = gui.share.links.length;

                // First: Draw all lines（logical relation）.
                var force = d3.layout.force()
                    .nodes(gui.share.nodes)
                    .links(gui.share.links)
                    .linkDistance([200])
                    .alpha(0.1)
                    .size([width, height])
                    .gravity(0.01)
                    .charge(-150)
                    .chargeDistance(-350)
                    .start();
                gui.share.force = force;

                // Second: To listen the drag event on the lines.
                var drag = d3.behavior.drag()
                    .origin(function(d) {
                    return {
                        x: d.x,
                        y: d.y
                    };
                })
                    .on('drag', function dragmove(d) {
                    d.x = d3.event.x;
                    d.y = d3.event.y;
                    d3.select(this).attr('transform', "translate(" + d3.event.x + "" + ',' + "" + d3.event.y + ")");
                    force.start();
                })
                    .on('dragstart', function(d) {
                    d3.event.sourceEvent.stopPropagation();
                });

                gui.share.drag = drag;
                // Fourth: Add the event listener.
                force.on('tick', function() {
                    gui.share.g_nodes.selectAll('g').attr('transform', function(d) {
                        return "translate(" + d.x + "," + d.y + ")"
                    });
                    gui.share.g_links.selectAll('line').attr('x1', function(d) {
                        return d.source.x;
                    })
                        .attr('y1', function(d) {
                        return d.source.y + 22;
                    })
                        .attr('x2', function(d) {
                        return d.target.x;
                    })
                        .attr('y2', function(d) {
                        return d.target.y + 22;
                    });

                    gui.share.g_links.selectAll('path').attr("d", function(d) {
                        var x1 = d.source.x,
                            y1 = d.source.y + 22,
                            x3 = d.target.x,
                            y3 = d.target.y + 22;

                        var p1 = [x1, y1],
                            p3 = [x3, y3],
                            p2 = [(x1 + x3 + y3 - y1) / 2, (y1 + y3 + x1 - x3) / 2],
                            p4 = [(x1 + x3 - y3 + y1) / 2, (y1 + y3 - x1 + x3) / 2];

                        var p5 = middle(p1, p3);
                        var p6 = middle(p2, p5);
                        var p7 = middle(p4, p5);

                        return "M" + p1 + " Q" + p6 + " " + p3 + "M" + p3 + " Q" + p7 + " " + p1;
                    });
                });

                gui.share.force = force;

                $('#scissor').click(gui._events.scissor.click);
                $('#cursor').click(gui._events.cursor.click);
                $('#line').click(gui._events.line_ico.click);
                $('#tip_closed').click(gui._events.tip_closed.click);
                $("#tip").bind({
                    mouseover: gui._events.tip.mouseover,
                    mouseout: gui._events.tip.mouseout,
                });

                // Used to add the new relationship
                var drag_line = gui.share.g1.insert("svg:line", ":nth-child(2)")
                    .style('stroke', "black")
                    .style('stroke-width', 4)
                    .attr("x1", 0)
                    .attr("y1", 0)
                    .attr("x2", 0)
                    .attr("y2", 0);
                gui.share.drag_line = drag_line;

                gui.share.g1.on('mousemove', gui._events.g1.mousemove)
                    .on('click', gui._events.g1.click);
                gui.render(gui.share.nodes, gui.share.links);
                gui.timer();
            }

            function requestData() {
                // 通过AJAX请求数据
                $.ajax({
                    type: "get",
                    url: "/dashboard/project/show",
                    async: true,
                    success: _success,
                    error: function(o) {
                        gui.handleJSError(o, function (o) {
                            console.log("error", o);
                            tool.loading(0);
                        });
                    }
                });

                //if ($.cookie("reloaded")) {
                //    $.cookie("reloaded", "");
                //}
            }

            requestData();
            //if (!$.cookie("reloaded")) {
            //    $.cookie("reloaded", true);
            //    setTimeout(function(){
            //        location.reload();
            //    }, 2000);
            //} else {
            //    requestData();
            //}
        },

        // 辅助功能函数——查找已有的links，返回其 index
        findLink: function(link, links) {
            for (var i in links) {
                if (links[i].source == link.source && links[i].target == link.target) {
                    return i;
                } else if (links[i].source == link.target && links[i].target == link.source) {
                    return i;
                }
            }
            return -1;
        },

        // 辅助功能函数——从现在的Links中删除指定的link，即删除两Instances之间的连线关系
        deleteLink: function(link, links) {
            for (var i in links) {
                if (links[i] == link) {
                    links.splice(i, 1);
                }
            }
        },

        // 辅助功能函数——发送创建或删除Instances间的连线信息给服务器后端，使服务器清除数据库中的记录
        sendLinks: function(url, link) {
            var success = false;
            $.ajax({
                type: "get",
                //url: url + "?src=" + link.src + "&dst=" + link.dst,
                url: url + "?suid=" + link.suid + "&spid=" + link.spid + "&duid=" + link.duid + "&dpid=" + link.dpid,
                async: false,
                //data:link,
                success: function(o) {
                    success = true;
                },
                error: function(o) {
                    gui.handleJSError(o, function (o) {
                        success = false;
                    });
                }
            });
            return success;
        },

        // 辅助功能函数--通过虚拟机的id，向服务器查询虚拟机的状态
        getServers: function(ids, successfunc, errorfunc) {
            var csrftoken = $.cookie('csrftoken');

            function csrfSafeMethod(method) {
                // these HTTP methods do not require CSRF protection
                return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
            };

            $.ajaxSetup({
                beforeSend: function(xhr, settings) {
                    if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                        xhr.setRequestHeader("X-CSRFToken", csrftoken);
                    }
                }
            });

            $.ajax({
                type: "post",
                url: "/dashboard/project/get_servers/",
                async: true,
                data: {
                    "ids": ids,
                },
                dataType: "json",
                success: function(o) {
                    if (successfunc)
                        successfunc(o);
                },
                error: function(o) {
                    gui.handleJSError(o, errorfunc);
                }
            });
        },

        // Start, Stop or Terminate a instance by the instance's id.
        _handle_instance: function(instance_id, _type, successfunc, errorfunc, passwd) {
            var csrftoken = $.cookie('csrftoken');

            function csrfSafeMethod(method) {
                // these HTTP methods do not require CSRF protection
                return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
            };

            $.ajaxSetup({
                beforeSend: function(xhr, settings) {
                    if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                        xhr.setRequestHeader("X-CSRFToken", csrftoken);
                    }
                }
            });

            args = {
                type: "post",
                url: "/dashboard/project/"+_type+"/"+instance_id+"/",
                async: true,
                success: function(o) {
                    if (successfunc)
                        successfunc(o);
                },
                error: function(o) {
                    gui.handleJSError(o, errorfunc);
                }
            };
            if (passwd) {
                args.data = {password: passwd};
                args.dataType = "json";
                //args.data = "password="+passwd;
            }

            $.ajax(args);
        },

        // Start a instance by the instance's id
        start: function (instance_id, successfunc, errorfunc) {
            gui._handle_instance(instance_id, "start", successfunc, errorfunc);
        },

        // Stop a instance by the instance's id
        stop: function (instance_id, successfunc, errorfunc) {
            gui._handle_instance(instance_id, "stop", successfunc, errorfunc);
        },

        // Terminate a instance by the instance's id
        terminate: function (instance_id, successfunc, errorfunc, password) {
            gui._handle_instance(instance_id, "terminate", successfunc, errorfunc, password);
        },

        // 辅助功能函数--创建虚拟机完成后，更新虚拟机信息
        updateNodes: function(nodes) {
            for (var i = 0; i < nodes.length; i++) {
                if (nodes[i].status == "building") {
                    nodes[i].status = "BUILD";
                }

                if (nodes[i].status == "BUILD") {
                    //console.log(nodes[i].id, "BUILD");
                    //gui.getServers(nodes[i].id,gui.updateNodes,gui.updateNodes);
                    gui.delayGetServer(nodes[i].id);
                    //gui.timer();
                    return;
                } else {
                    for (var j = 0; j < gui.share.nodes.length; j++) {
                        if (gui.share.nodes[j].id == nodes[i].id) {
                            gui.share.nodes[j].status = nodes[i].status;
                            gui.share.nodes[j].gip = nodes[i].gip;
                            gui.share.nodes[j].ip = nodes[i].ip;
                            gui.share.nodes[j].port = nodes[i].port;
                            gui.share.nodes[j].type = nodes[i].type;
                            gui.share.nodes[j].dc = nodes[i].dc;
                            if (nodes[i].wordpress_port) {
                                gui.share.nodes[j].wordpress_port = nodes[i].wordpress_port;
                            }
                            if (nodes[i].webservice_port) {
                                gui.share.nodes[j].webservice_port = nodes[i].webservice_port;
                            }
                            if (nodes[i].disk_name){
                                gui.share.nodes[j].disk_name = nodes[i].disk_name;
                                gui.share.nodes[j].disk_size = nodes[i].disk_size;
                              }

                            d3.select("#node_status").text(nodes[i].status);
                            gui._events.instance_action._correct_status(nodes[i].status);

                            gui.render(gui.share.nodes, gui.share.links);
                            horizon.clearAllMessages();
                            //horizon.alert("success", gettext('Success to create the instance'), ' ');
                            horizon.autoDismissAlerts();
                            return;
                        }
                    }
                }
            }
        },

        // 通用JS请求错误处理
        handleJSError: function (o, errorfunc) {
            if (o.status == 401) {
                //gui.alert("error", gettext("Page timeout. Please re-authorize by login again!"));
                //var tmp = location.href.split("?")[0].split("/").splice(3);
                //tmp.unshift("/dashboard/login/?next=");
                //location.replace(tmp.join("/"));
                location.replace("/dashboard/login/");
                return;
            } else if (o.status == 423) {
                gui.alert("warning", gettext("The operation is too frequent, and please wait a moment!"));
                return;
            }

            if (errorfunc) {
                errorfunc(o);
            }
        },

        // 辅助功能函数--定时器，延迟一次getServer请求
        timer: function() {
            function judge() {
                var buildNum = 0;
                for (var i = 0; i < gui.share.nodes.length; i++) {
                    if (gui.share.nodes[i].status == "BUILD") {
                        buildNum++;
                        gui.getServers(gui.share.nodes[i].id, gui.updateNodes, gui.updateNodes);
                    }
                }
                if (!buildNum) {
                    gui.render(gui.share.nodes, gui.share.links);
                }
            };
            setTimeout(judge, 2000);
        },

        // 辅助功能函数--在getSever请求后，有些虚拟还未创建完成，在回调函数中使用
        delayGetServer: function(id, timeout) {
            function handle() {
                gui.getServers(id, gui.updateNodes, gui.updateNodes);
            };
            if (timeout === undefined) {
                timeout = config.timeout;
            }
            setTimeout(handle, timeout);
        },

        // 辅助功能函数--获得dc信息包括 规格，是否能在创建虚拟机（规格的详细信息可以扩充）
        getDCs: function(successfunc, errorfunc) {
            var csrftoken = $.cookie('csrftoken');

            function csrfSafeMethod(method) {
                // these HTTP methods do not require CSRF protection
                return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
            };

            //$.ajaxSetup({
            //  beforeSend: function(xhr, settings) {
            //      if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            //          xhr.setRequestHeader("X-CSRFToken", csrftoken);
            //      }
            //  }
            //});

            $.ajax({
                type: "get",
                url: "/dashboard/project/get_dcs/",
                async: true,
                success: function(o) {
                    if (successfunc)
                        successfunc(o);
                },
                error: function(o) {
                    gui.handleJSError(o, errorfunc);
                }
            });
        },

        quotas: function(errfunc, sucfunc) {
            $.ajax({
                type: "get",
                url: "/dashboard/project/instances/quotas/",
                dataType: "json",
                async: false,
                success: function(data) {
                    sucfunc(data);
                },
                error: function(o, err) {
                    if (o.status == 401)
                        location.reload();
                    errfunc('Quota exceeded.');
                }
            });
        },

        getNetType: function() {
            $.ajax({
                type: "get",
                url: "/dashboard/project/instances/network_type/",
                success: function(data) {
                    //console.log(data.net_type);
                    if (data.net_type == '0') {
                        //console.log(data.net_type);
                        return;
                    } else {
                        $("#id_net_type").find("option[value=" + data.net_type + "]").attr("selected", "selected");
                    }
                },
                error: function (o) {
                    gui.handleJSError(o);
                }
            });
        },

        getVirginiaDc: function() {
            for (var i = 0; i < gui.share.dcs.length; i++) {
                if (gui.share.dcs[i]["name"] == "Virginia-Docker-Zone") {
                    return gui.share.dcs[i]["id"];
                }
            }
            return "";
        },

        // 辅助功能函数--拖拽之后创建虚拟机
        launch: function(project_id, data, func1, func2) {
            var csrftoken = $.cookie('csrftoken');

            function csrfSafeMethod(method) {
                // these HTTP methods do not require CSRF protection
                return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
            };
            $.ajaxSetup({
                beforeSend: function(xhr, settings) {
                    if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                        xhr.setRequestHeader("X-CSRFToken", csrftoken);
                    }
                }
            });
            // project_id is dc's id
            //_data = {
            //  source_type: "image_id",
            //  image_id: "aaaaaaaaaaa",
            //  availability_zone: "aaa",
            //  name: "aaaa",
            //  count: 1,
            //  flavors: 3,
            //};

            $.ajax({
                type: "post",
                url: "/dashboard/project/launch/" + project_id,
                data: data,
                dataType: "json",
                async: true,
                success: function(o) {
                    if (func1) {
                        func1(o);
                    }
                },
                error: function(o) {
                    gui.handleJSError(o, func2);
                }
            });

        },

        // 根据nodes,links绘制图
        render: function(nodes, links) {
            //if (!nodes) {
            //  nodes = gui.share.nodes;
            //}
            //if (!likes) {
            //  likes = gui.share.links;
            //}

            // links
            var gLinks = gui.share.g_links.selectAll("g")
                .data(links, function(d) {
                return d.id;
            })
                .enter()
                .append("g")
                .on("click", gui._events.g_links.click)
                .on("mouseover", gui._events.g_links.mouseover)
                .on("mouseout", gui._events.g_links.mouseout);
            var gLines = gLinks.append("line")
                .classed("link", true);
            var gPaths = gLinks.append("path")
                .attr("opacity", 0);
            gui.share.g_links.selectAll("g")
                .data(links, function(d) {
                return d.id;
            })
                .exit()
                .remove();

            // nodes
            var gNodes = gui.share.g_nodes.selectAll("g")
                .data(nodes)
                .enter()
                .append("g")
                .call(gui.share.drag)
                .on("click", gui._events.g_nodes.click)
                .on("mouseover", gui._events.g_nodes.mouseover)
                .on("mouseout", gui._events.g_nodes.mouseout);
            gNodes.append("image")
                .attr(config.image)
                .attr('x', -config.image.width / 2)
                .attr('xlink:href', function(d) {
                if (config.status[d.status]) {
                    return config.status[d.status]["image"];
                } else {
                    if (config.css[d.type]) {
                        return config.css[d.type];
                    }
                    // (Gaofeng) FixBug: always return a value
                    return "";
                }
            });
            gNodes.append("text")
                .text(function(d) {
                if (config.status[d.status]) {
                    return config.status[d.status]["text"];
                } else {
                    return d.ip;
                }
            })
                .attr('y', config.image.height + 7)
                .attr(config.text);

            var gNodeUpdate = gui.share.g_nodes.selectAll("g")
                .data(nodes);
            gNodeUpdate.selectAll("image")
                .attr(config.image)
                .attr('x', -config.image.width / 2)
                .attr('xlink:href', function(d) {
                if (config.status[d.status]) {
                    return config.status[d.status]["image"];
                } else {
                    if (config.css[d.type]) {
                        return config.css[d.type];
                    }
                    // (Gaofeng) FixBug: always return a value
                    return "";
                }
            });
            gNodeUpdate.selectAll("text")
                .text(function(d) {
                if (config.status[d.status]) {
                    return config.status[d.status]["text"];
                } else {
                    return d.ip;
                }
            })
                .attr('y', config.image.height + 15)
                .attr(config.text);
            gui.share.g_nodes.selectAll("g")
                .data(nodes)
                .exit()
                .remove();

            gui.share.force.start();
        },

        // 更新画布
        _reDraw: function() {
            gui.share.g_edges = this.share.g_edges.data(gui.share.links, function(d) {
                return d.id
            });
            var g = gui.share.g_edges.enter().insert('g', ":nth-child(3)")
                .on('click', gui._events.g_edges.click)
                .on('mouseover', gui._events.g_edges.mouseover)
                .on('mouseout', gui._events.g_edges.mouseout);
            g.append("line").classed("link", true);
            g.append("path").attr("opacity", "0");

            gui.share.edges = gui.share.g_edges.selectAll("line");
            gui.share.g_path = gui.share.g_edges.selectAll("path");

            gui.share.g_edges.exit().remove();
            gui.share.force.start();
        },

        // 重新加载页面
        reload: function () {
            location.replace(document.referrer);
        },

        alert: function (_type, message, timeout) {
            horizon.clearAllMessages();
            //horizon.alert("success", gettext('Success to create the instance'), ' ');
            if (_type !== undefined) {
                horizon.alert(_type, message);
            }
            //horizon.autoDismissAlerts();

            if (timeout === undefined) {
                horizon.autoDismissAlerts();
                return;
            }
            setTimeout(function(){horizon.autoDismissAlerts();}, timeout);
        },

        // 事件集合 click，mouseover，mouseout，mousemove
        // 由于要绑定到DOM上的事件太多，因此我们把这些事件的回调函数集成起来管理。
        // _events 的属性名（如：scissor）是在绑定的DOM名，其值是个事件集，其中，属性名是事件名，值是相应的回调函数。
        _events: {
            instance_action: {
                dialog: {
                     hide:true,
                     modal:true,
                     resizable: false,
                     draggable: false,
                     title:'Confirm Delete Instance',
                     width:470,
                     height:250,
                },
                attrs: {
                    init_height: 220,
                    tip_height: 240,
                },

                _correct_status: function(node_status) {
                    if (node_status == "ACTIVE") {
                        $("#gui_check").attr("checked", "checked");
                    } else {
                        $("#gui_check").removeAttr("checked");
                    }
                },

                start_stop: function () {
                    function success(o) {
                        gui.delayGetServer(node_id, 0);
                        if (node_status == "ACTIVE") {
                            //horizon.alert("success", success_stop_message);
                            gui.alert("success", success_stop_message);
                        } else {
                            //horizon.alert("success", success_start_message);
                            gui.alert("success", success_start_message);
                        }
                    }

                    function error(o) {
                        if (o.status == 401) {
                            gui.alert("error", gettext("Page timeout. Please re-authorize by login again!"));
                            return;
                        }

                        gui._events.instance_action._correct_status(node_status);

                        if (node_status == "ACTIVE") {
                            //horizon.alert("error", error_stop_message);
                            gui.alert("error", error_stop_message);
                        } else {
                            //horizon.alert("error", error_start_message);
                            gui.alert("error", error_start_message);
                        }

                        console.log(node_status+":", o);
                    }

                    var node_status = d3.select("#node_status").text();
                    var node_id = d3.select("#node_id").attr("node-id");
                    var node = gui.getNode(node_id);

                    // 如果此节点被禁用，将不再进行下一步操作
                    if (node.disabled) {
                        gui._events.instance_action._correct_status(node_status);
                        return;
                    }

                    if (node_status == "ACTIVE") {
                        gui.stop(node_id, success, error);
                        var success_stop_message = gettext('Successfully switch off the instance: ') + node_id;
                        var error_stop_message = gettext('Failed to switch off the instance: ') + node_id;
                    } else if (node_status == "SHUTOFF") {
                        var success_start_message = gettext('Successfully switch on the instance: ') + node_id;
                        var error_start_message = gettext('Failed to switch on the instance: ') + node_id;
                        gui.start(node_id, success, error);
                    } else {
                        horizon.alert("error", gettext("Status is not recognized!"));
                    }

                    // 禁用此节点，30秒之后再解除禁用
                    node.disabled = true;
                    $("#gui_check").css({"cursor": "not-allowed"});
                    setTimeout(function () {
                        node.disabled = false;
                        $("#gui_check").css({"cursor": "pointer"});
                    }, 30000); // 30s
                },

                click_info: function(){
                        $("#delete-passwd input").val("");
                        //$("#sure_info").dialog({
                        //                hide:true,
                        //                modal:true,
                        //                resizable: false,
                        //                draggable: false,
                        //                title:'Confirm Delete Instance',
                        //                width:470,
                        //                height:250,
                        //});
                        gui._events.instance_action.dialog.height = gui._events.instance_action.attrs.init_height;
                        gui._events.instance_action.dialog.title = $("#sure_info").attr("my_title");
                        $("#sure_info").dialog(gui._events.instance_action.dialog);
                        $("#error-passwd").hide();
                },

                sure_info_yes:function (e) {
                    gui._events.instance_action.terminate();
                },

                sure_info_no: function(){
                      $("#sure_info").dialog("close");
                },

                terminate: function () {
                    //var delete_dialog = $("#sure_info").dialog({
                    //                   modal:true,
                    //                   resizable: false,
                    //                   draggable: false,
                    //                   title:'Confirm Delete Instance',
                    //                   width:470,
                    //                   height:250,
                    //});

                    function success(o) {
                        //gui.alert("success", gettext("Successfully delete the instance: ") + node_id);
                        $("#play").html("");
                        location.reload();
                    }

                    function error(o) {
                        gui.handleJSError(o, function (o) {
                            if (o.status == 403) {
                                //delete_dialog.dialog("option", {height:270});
                                gui._events.instance_action.dialog.height = gui._events.instance_action.attrs.tip_height;
                                $("#sure_info").dialog(gui._events.instance_action.dialog);

                                //errorPassWd_P.text(errorPassWd.attr("error-noempty"));
                                //errorPassWd.show();

                                return;
                            }

                            gui.alert("error", gettext("Failed to delete the instance: ") + node_id);
                            console.log("Terminate:", o);
                        });
                    }

                    //var passwd = $("#passwd").val().trim();
                    //var errorPassWd = $("#error-passwd");
                    //var errorPassWd_P = $("p", errorPassWd);
                    //
                    //if (!passwd) {
                    //    //delete_dialog.dialog("option", {height:270});
                    //    gui._events.instance_action.dialog.height = gui._events.instance_action.attrs.tip_height;
                    //    $("#sure_info").dialog(gui._events.instance_action.dialog);
                    //    errorPassWd_P.text(errorPassWd.attr("error-empty"));
                    //    errorPassWd.show();
                    //    return;
                    //}

                    //var node_id = d3.select("#node_id").attr("node-id");
                    //var node_status = d3.select("#node_status").text();
                    var node_id = $("#node_id").attr("node-id");
                    var node_status = $("#node_status").text();

                    if (node_status != "ACTIVE" && node_status != "SHUTOFF" && node_status != "ERROR") {
                        gui.alert("error", gettext("The instance is building! Please wait a moment and delete it."));
                        return;
                    }

                    $("#sure_info").dialog("close");
                    // (Gaofeng) I don't know why this statement MUST be executed. If not executed, this element,
                    //  <div class="ui-widget-overlay"></div>, isn't deleted. In addition, the statement,
                    //  $(".ui-widget-overlay").remove(), doesn't work.
                    $("body>div").last().remove();

                    gui.alert("info", gettext("Please wait and the instance is deleting ..."));
                    gui.terminate(node_id, success, error)
                    //gui.terminate(node_id, success, error, passwd);
                },
            },

            scissor: {
                click: function() {
                    $("#play").hover(function() {
                        $(this).css({
                            cursor: "url(/static/dashboard/img/gui_scissors.ico),auto"
                        });
                    });
                    d3.select("#tip").classed("hidden", true);
                    gui.share.g_links.selectAll('line').classed('linkscissor', true);
                    gui.share.select_scissor = true;
                    gui.share.select_node = null;
                    gui.share.select_drawline = false;
                },
            },

            cursor: {
                click: function() {
                    $('#play').hover(function() {
                        $(this).css({
                            cursor: "pointer"
                        });

                    });
                    gui.share.g_links.selectAll('line').classed('linkscissor', false);
                    gui.share.select_node = null;
                    gui.share.select_scissor = false;
                    gui.share.select_drawline = false;
                },
            },

            line_ico: {
                click: function() {
                    $('#play').hover(function() {
                        $(this).css({
                            cursor: "url(/static/dashboard/img/gui_wired_top.cur),auto"
                        });

                    });
                    d3.select("#tip").classed("hidden", true);
                    gui.share.g_links.selectAll('line').classed('linkscissor', false);
                    gui.share.select_drawline = true;
                    gui.share.select_scissor = false;
                },
            },

            tip_closed: {
                click: function() {
                    d3.select("#tip").classed('hidden', true);
                },
            },

            tip: {
                mouseover: function() {
                    d3.select("#tip").classed("hidden", false);
                    if (gui.share.interval) {
                        window.clearInterval(gui.share.interval);
                        gui.share.interval = null;
                    }
                },
                mouseout: function() {
                    d3.select("#tip").classed("hidden", true);
                },
            },

            g1: {
                mousemove: function() {
                    d3.event.preventDefault();

                    if (!gui.share.select_node) {
                        if (gui.share.select_drawline) {
                            $('#play').css({
                                cursor: "url(/static/dashboard/img/gui_wired_top.cur),auto"
                            });
                        }
                        return;
                    }

                    $('#play').css({
                        cursor: "url(/static/dashboard/img/gui_wired_bottom.cur),auto"
                    });

                    gui.share.drag_line
                        .attr("x1", gui.share.select_node.x)
                        .attr("y1", gui.share.select_node.y + 22)
                        .attr("x2", d3.mouse(this)[0])
                        .attr("y2", d3.mouse(this)[1]);
                },
                click: function() {
                    d3.event.preventDefault();

                    if (gui.share.select_node) {
                        $('#play').css({
                            cursor: "url(/static/dashboard/img/gui_wired_top.cur),auto"
                        });

                        gui.share.drag_line
                            .attr("x1", 0)
                            .attr("y1", 0)
                            .attr("x2", 0)
                            .attr("y2", 0);
                        gui.share.select_node = null;
                    }
                },
            },

            g_nodes: {
                mouseover: function(d) {
                    //console.log("g_nodesmouseover",d);
                    var e = d3.event || window.event;
                    if (e.stopPropagation) {
                        e.stopPropagation();
                    } else {
                        e.cancelBubble = true;
                    }
                    e.preventDefault();
                    d3.event.preventDefault();

                    if (!gui.share.select_scissor && !gui.share.select_drawline) {
                        var xPosition = parseFloat($(this).find('image').offset().left);
                        var yPosition = parseFloat($(this).offset().top);
                        /*$("#tip").css('left', xPosition - $("#tip").width() - $(this).find('image').attr('width') / 1.5);
                        $("#tip").css('top', yPosition - $("#tip").height() / 2);*/
                        $("#tip").css('left', xPosition - 545);
                        $("#tip").css('top', yPosition - 190);

                        var tips = d3.select("#tip").classed('hidden', false);
                        tips.select("#node_id").attr("node-id", d.id);
                        tips.select("#node_name").text(d.name);
                        tips.select("#node_server_name").text(function() {
                            return config.typeMap[d.type];
                        });
                        tips.select("#node_ip").text(d.ip);
                        tips.select("#node_gip").text(d.gip)
                        tips.select("#node_port").text(d.port);
                        tips.select("#node_dc").text(d.dc);
                        tips.select("#node_status").text(d.status);
                        // var wordpress_port=Math.round(Math.random()*10000+50000);
                        if (d.type == "wordpress") {
                            tips.select("#node_wordpress").style("display", "table-row");
                            tips.select("#node_wordpress_port").text(d.wordpress_port);
                        } else {
                            tips.select("#node_wordpress")
                                .style("display", "none");
                        }
                        if(d.webservice_port)
                        {
                            tips.select("#node_webservice").style("display", "table-row");
                            tips.select("#node_webservice_port").text(d.webservice_port);
                        }
                        else{
                            tips.select("#node_webservice").style("display", "none");

                        }

                        if (d.status == "ACTIVE") {
                            $("#gui_check").attr("checked", "checked");
                        } else {
                            $("#gui_check").removeAttr("checked");
                        }

                        if (d.disk_name){
                           tips.select("#disk-name").text(d.disk_name);
                           tips.select("#disk-size").text(d.disk_size);

                           d3.select("#disk-name-tr").classed('hidden', false);
                           d3.select("#disk-size-tr").classed('hidden', false);
                        } else {
                           d3.select("#disk-name-tr").classed('hidden', true);
                           d3.select("#disk-size-tr").classed('hidden', true);
                        }

                        if (gui.share.interval) {
                            window.clearInterval(gui.share.interval);
                            gui.share.interval = null;
                        }

                        // 检查当前Node节点是否被禁用
                        if (d.disabled) {
                            $("#gui_check").css({"cursor": "not-allowed"});
                        } else {
                            $("#gui_check").css({"cursor": "pointer"});
                        }
                    }
                },
                mouseout: function(d) {
                    //console.log("g_nodesmouseout",d);
                    var e = d3.event || window.event;
                    if (e.stopPropagation) {
                        e.stopPropagation();
                    } else {
                        e.cancelBubble = true;
                    }
                    e.preventDefault();
                    d3.event.preventDefault();

                    gui.share.interval = window.setTimeout(function() {
                        d3.select("#tip").classed('hidden', true);
                    }, 1000);
                },
                click: function(d) {
                    //console.log("g_nodesclick",d);
                    var e = d3.event || window.event;
                    if (e.stopPropagation) {
                        e.stopPropagation();
                    } else {
                        e.cancelBubble = true;
                    }
                    e.preventDefault();
                    d3.event.preventDefault();

                    if (gui.share.select_drawline) {
                        console.log(gui.share.select_node);
                        if (gui.share.select_node && gui.share.select_node != d) {
                            var add_link = {
                                source: gui.share.select_node,
                                target: d
                            };
                            // var create_link = {
                            //  src: gui.share.select_node.id,
                            //  dst: d.id
                            // };
                            var create_link = {
                                suid: gui.share.select_node.id,
                                spid: gui.share.select_node.pid,
                                duid: d.id,
                                dpid: d.pid
                            };
                            if (gui.findLink(add_link, gui.share.links) == -1) {
                                // 如果状态不是ACTIVE，不允许连线
                                //if (add_link.source.status != "ACTIVE" || add_link.target.status != "ACTIVE") {
                                //    horizon.clearAllMessages();
                                //    horizon.alert("error", gettext("Failed to connect two instances, because one may not be active"));
                                //    return;
                                //}
                                //如果状态是unknow，不允许连线
                                if (add_link.source.status == "UNKNOWN" || add_link.target.status == "UNKNOWN") {
                                    horizon.clearAllMessages();
                                    horizon.alert("error", gettext("Failed to connect two instances ,One server may be down"));
                                    return;
                                }
                                if (add_link.source.status == "ERROR" || add_link.target.status == "ERROR") {
                                    horizon.clearAllMessages();
                                    horizon.alert("error", gettext("Failed to connect two instances, because one may not be ERROR"));
                                    return;
                                }
                                if (gui.sendLinks("/dashboard/project/create", create_link)) {
                                    gui.share.links.push({
                                        id: gui.share.links_length,
                                        source: gui.share.select_node,
                                        target: d
                                    });
                                    gui.share.links_length++;
                                    gui.render(gui.share.nodes, gui.share.links);
                                } else {
                                    //horizon.clearAllMessages();
                                    //horizon.alert("error", gettext('Failed to connect two instances'));
                                }
                            }
                            gui.share.select_node = null;
                            gui.share.drag_line
                                .attr("x1", 0)
                                .attr("y1", 0)
                                .attr("x2", 0)
                                .attr("y2", 0);
                        } else {
                            gui.share.select_node = d;
                            gui.share.drag_line
                                .attr("x1", gui.share.select_node.x)
                                .attr("y1", gui.share.select_node.y + 22)
                                .attr("x2", gui.share.select_node.x)
                                .attr("y2", gui.share.select_node.y + 22);
                        }
                    }
                },
            },

            g_links: {
                click: function(d) {
                    var e = d3.event || window.event;
                    if (e.stopPropagation) {
                        e.stopPropagation();
                    } else {
                        e.cancelBubble = true;
                    }
                    e.preventDefault();
                    d3.event.preventDefault();

                    if (gui.share.select_scissor) {
                        // var delete_link = {
                        //  'src': d.source.id,
                        //  'dst': d.target.id
                        // };
                        console.log(d.source)
                        var delete_link = {
                            suid: d.source.id,
                            spid: d.source.pid, 
                            duid: d.target.id,
                            dpid: d.target.pid
                            
                        };
                        if (d.source.status == "UNKNOWN" || d.target.status == "UNKNOWN") {
                            horizon.clearAllMessages();
                            horizon.alert("error", gettext("One server may be down"));
                            return;
                        }

                        if (gui.sendLinks("/dashboard/project/delete", delete_link)) {
                            gui.deleteLink(d, gui.share.links);
                            gui.render(gui.share.nodes, gui.share.links);
                        } else {
                            //horizon.clearAllMessages();
                            //horizon.alert("error", gettext("Failed to cut off the connection"));
                        }
                    }
                },
                mouseover: function(d) {
                    var e = d3.event || window.event;
                    if (e.stopPropagation) {
                        e.stopPropagation();
                    } else {
                        e.cancelBubble = true;
                    }
                    e.preventDefault();
                    d3.event.preventDefault();

                    if (gui.share.select_scissor) {
                        d3.select(this).select('line')
                            .classed('link', false)
                            .classed('linkscissor', false)
                            .attr('stroke', "red")
                            .attr('stroke-width', 4);
                    }
                },
                mouseout: function(d) {
                    var e = d3.event || window.event;
                    if (e.stopPropagation) {
                        e.stopPropagation();
                    } else {
                        e.cancelBubble = true;
                    }
                    e.preventDefault();

                    if (gui.share.select_scissor) {
                        d3.select(this).select('line')
                            .classed('link', true)
                            .classed('linkscissor', false);
                    }
                },
            },
        },

        // Add the initialise function
        // After the init function of gui finishes, the added functions will be
        // called in order when they be registered.
        _funcs: [],
        addInit: function(f) {
            gui._funcs.push(f);
        },

        // Run the init functions
        _runInit: function() {
            for (var i in this._funcs) {
                try {
                    this._funcs[i]();
                } catch (e) {}
            }
        },
    };

    tool = {
        // 箭头&提示
        toolAceTip: function() {
            var is = $("#tool .separate_line ~ i");
            for (var i = 0; i < is.length; i++) {
                if (!$(is[i]).attr("id")) {
                    $(is[i]).mouseover(function(e) {
                        e.preventDefault();
                        var offset = $(this).offset();
                        $("#toolAce").css("visibility", "visible");
                        $("#toolAce").offset(function() {
                            var newPos = new Object();
                            newPos.left = offset.left;
                            newPos.top = offset.top + 20;
                            return newPos;
                        });
                        $("#toolTip").css("visibility", "visible");
                        $("#toolTip").css("font-style", "normal");
                        $("#toolTip").css("font-weight", "normal");
                        $("#toolTip").offset(function() {
                            var newPos = new Object();
                            newPos.left = offset.left;
                            newPos.top = offset.top - 35;
                            return newPos;
                        }).html(config.typeMap[$(this).children("div").attr("image_type")]);
                    }).mouseout(function() {
                        $("#toolAce").css("visibility", "hidden");
                        $("#toolTip").css("visibility", "hidden");
                    })
                }
            }
        },
        // 辅助功能函数--控制load开始与结束
        loading: function(start) {
            gui.share.deg = 0;

            function rotate() {
                if (gui.share.deg < 360) {
                    gui.share.deg += 1;
                } else {
                    gui.share.deg = 0;
                }
                d3.select("#gui_load").attr("transform", "rotate(" + gui.share.deg + ",200,200)");
                if (start) {
                    $("#gui_loading").show();
                    $("#gui_model").show();
                    gui.share.intervalLoad = setTimeout(rotate, 1);
                } else {
                    clearTimeout(gui.share.intervalLoad);
                    $("#gui_loading").hide();
                    $("#gui_model").hide();
                }
            };
            rotate();

        },
        // 辅助功能函数--渲染load（包括图层，以及中间那个圆）
        renderLoad: function(innerRadius, modelWidth, modelHeight, value) {
            $("#gui_loading").show();
            $("#gui_model").show();
            d3.select("#gui_loading").select("svg").remove();
            var svg = d3.select("#gui_loading")
                .append("svg")
                .attr("width", config.loadModel.width)
                .attr("height", config.loadModel.height);
            svg.append("defs")
                .append("filter")
                .attr("id", "inner-glow")
                .append("feGaussianBlur")
                .attr("in", "SourceGraphic")
                .attr("stdDeviation", "7 7");

            function resizeRelation() {
                var lefts = value.left + modelWidth / 2 - config.loadModel.width / 2;
                var tops = value.top + modelHeight / 2 - config.loadModel.height / 2;
                if (tops < 0) {
                    tops = 0;
                }
                $("#gui_loading").offset({
                    left: lefts,
                    top: tops,
                });
                //console.log($("#gui_loading").offset());
            }
            resizeRelation();
            $("#gui_model")
                .css("width", modelWidth)
                .css("height", modelHeight)
                .offset({
                left: value.left,
                top: value.top,
            });
            var fullAngle = 2 * Math.PI;
            var endAngle = fullAngle;
            var data = [{
                    startAngle: 0,
                    endAngle: 0.3 * endAngle
                }, {
                    startAngle: 0.33 * endAngle,
                    endAngle: 0.63 * endAngle
                }, {
                    startAngle: 0.66 * endAngle,
                    endAngle: 0.96 * endAngle
                },

            ];
            var arc = d3.svg.arc().outerRadius(62)
                .innerRadius(innerRadius);
            svg.select("g").remove();
            var inner = svg.append("g")
                .append("g")
                .attr("id", "inner");
            inner.append("path")
                .attr("id", "inner-glowing-arc")
                .attr("transform", "translate(200,200)")
                .attr("d", d3.svg.arc()
                .innerRadius(50)
                .outerRadius(65)
                .startAngle(0)
                .endAngle(fullAngle))
                .style("fill", "rgba(13,215,247, .9)")
                .attr("filter", "url(#inner-glow)");

            inner.append("circle")
                .attr("id", "#inner-circle")
                .attr("cx", 200)
                .attr("cy", 200)
                .attr("r", 40)
                .style("fill", "white")
                .style("stroke", "white")
                .style("stroke-width", "0");

            inner.append("use")
                .attr("xlink:href", "#inner-circle")
                .attr("filter", "url(#inner-glow)");

            inner.append("g")
                .attr('transform', "translate(200,200)")
                .attr("id", "gui_load")
                .selectAll("path.arc")
                .data(data)
                .enter()
                .append("path")
                .attr("class", "arc")
                .attr("fill", "rgb(13,215,247)")
                .attr("d", function(d, i) {
                return arc(d, i);
            })
                .attr("transform", "translate(200,200)");
            $("#gui_loading").hide();
            $("#gui_model").hide();
        },

        // 可拖的参数
        draggable: {
            helper: "clone",
            revert: false,
            opacity: 0.8,
            cursor: "move",
        },

        // 可拖放的参数
        droppable: {
            activeClass: "dragPlay",
            hoverClass: "dragPlay",
            revert: "valid", //revert target when quotas exceeded
            drop: function() {
                tool.drop();
            }
        },
        drop: function() {
            // whether quotas exceeded
            gui.quotas(function(err){
                alert(err);
            },function(data){
            $("#toolAce").css("visibility", "hidden");
            $("#toolTip").css("visibility", "hidden");
            tool.renderLoad(50, $(window).width(), $(window).height(), {
                top: 0,
                left: 0
            });
            tool.loading(1);
            //gui.getNetType();
            gui.getDCs(function(o) {
                tool.loading(0);
                gui.share.dcs = o.dcs;
                tool.message_box.select.loadDCs();
                $("#message_box").dialog(tool.message_box.dialog);
            }, function(o) {
                tool.loading(0);
                var message;
                if (o.status == 401) {
                    message = gettext("Page timeout. Please re-authorize by login again!");
                } else {
                    message = gettext("Sorry! Failed to load data, and you can refresh this page!")
                }
                horizon.alert("error", message);
                console.log("error", o);
            });
            });
        },
        // 与message_box有关的，弹出窗口，下拉选择，确定按钮
        message_box: {
            dialog: {
                modal: true,
                resizable: false,
                draggable: false,
                beforeclose: function(event, ui) {
                    tool.message_box.inputsure.clearinfos();
                }
            },
            select: {
                dc: function() {
                    var options = "";
                    if (gui.share.dcs.length) {
                        for (var i = 0; i < gui.share.dcs.length; i++) {
                            // if (gui.share.dcs[i]["disabled"]) {
                            //  options += "<optgroup label=" + gui.share.dcs[i]["name"] + "></optgroup>";
                            // } else if (gui.share.dcs[i]["id"] == gui.share.image_dc) {
                            //  options += "<option value=" + gui.share.dcs[i]["id"] + ">" + gui.share.dcs[i]["name"] + "</option>";
                            // } else {
                            //  options += "<optgroup label=" + gui.share.dcs[i]["name"] + "></optgroup>";
                            // }
                            if (!gui.share.dcs[i]["disabled"]) {
                                var j = 0;
                                for (j = 0; j < gui.share.imageIdc.length; j++) {
                                    if (gui.share.dcs[i]["id"] == gui.share.imageIdc[j]["image_dc"]) {
                                        options += "<option value=" + gui.share.dcs[i]["id"] + ">" + gui.share.dcs[i]["name"] + "</option>";
                                        break;
                                    }

                                }
                                if (j == gui.share.imageIdc.length) {
                                    options += "<optgroup label=" + gui.share.dcs[i]["name"] + "></optgroup>";
                                }
                            } else {
                                options += "<optgroup label=" + gui.share.dcs[i]["name"] + "></optgroup>";
                            }
                        }
                    }
                    return options;
                },
                zones: function(id) {
                    var options = "";
                    if (gui.share.dcs.length) {
                        for (var i = 0; i < gui.share.dcs.length; i++) {
                            if (gui.share.dcs[i]["id"] == id) {
                                for (var j = 0; j < gui.share.dcs[i]["zones"].length; j++) {
                                    if (tool.isDockerContainer(gui.share.image_category, gui.share.dcs[i]["zones"][j]["type"])) {
                                        options += "<option value=" + gui.share.dcs[i]["zones"][j]["name"] + ">" + gui.share.dcs[i]["zones"][j]["name"] + "</option>";
                                    } else {
                                        options += "<optgroup label=" + gui.share.dcs[i]["zones"][j]["name"] + "></optgroup>";
                                    }

                                }
                                break;
                            }
                        }
                    }
                    return options;
                },
                flavors: function(id) {
                    var options = "";
                    if (gui.share.dcs.length) {
                        for (var i = 0; i < gui.share.dcs.length; i++) {
                            if (gui.share.dcs[i]["id"] == id) {
                                for (var j = 0; j < gui.share.dcs[i]["flavors"].length; j++) {
                                    options += "<option value=" + gui.share.dcs[i]["flavors"][j][0] + ">" + gui.share.dcs[i]["flavors"][j][1] + "</option>";
                                }
                            }
                        }
                    }
                    return options;
                },

                device: function(value) {
                    if (value) {
                        $("#id_device").show();
                    } else {
                        $("#id_device").hide();
                    }
                },

                _isBeijingDC: function (idc_id) {
                    for (var i = 0; i < gui.share.dcs.length; i++) {
                        if ((gui.share.dcs[i]["name"].slice(0, 7).toLowerCase() == "beijing") && gui.share.dcs[i]["id"] == idc_id) {
                            return true;
                        }
                    }
                    return false;
                },

                check: function(value) {
                    if (value == gui.getVirginiaDc()) {
                        //$("#id_boot_source").attr({"disabled": "disabled", "checked": false});
                        //$("#id_device").hide();

                        $("#id_is_backup").attr({"checked": false});
                    } else if (tool.message_box.select._isBeijingDC(value)) {
                        // 如果是IDC是北京节点，将不显示添加磁盘功能，因为北京节点不支持磁盘功能。
                        //$("#id_boot_source").attr({"disabled": "disabled", "checked": false});
                        //$("#id_device").hide();

                        $("#id_is_backup").attr({"checked": false});
                    }
                    else {
                        //$("#id_boot_source").removeAttr("disabled");

                        $("#id_is_backup").attr({"checked": true});
                    }
                },
                loadDCs: function() {

                    // 数据中心
                    $("#id_dc").empty();
                    $("#id_dc").append(tool.message_box.select.dc());

                    // 可用域
                    //$("#id_zone").empty();
                    //$("#id_zone").append(tool.message_box.select.zones($("#id_dc").val()));

                    // 规格
                    $("#id_flavor").empty();
                    $("#id_flavor").append(tool.message_box.select.flavors($("#id_dc").val()));

                    $("#id_dc").bind("selectchange", function(e) {
                        //$("#id_zone").empty();
                        //$("#id_zone").append(tool.message_box.select.zones($(e.target).val()));
                        $("#id_flavor").empty();
                        $("#id_flavor").append(tool.message_box.select.flavors($(e.target).val()));
                        tool.message_box.select.check($(e.target).val());
                    });
                    $("#id_dc").change(function() {
                        $("#id_dc").trigger("selectchange");
                    });

                    tool.message_box.select.check($("#id_dc").val());

                    // 存储
                    $("#id_boot_source").change(function() {
                        tool.message_box.select.device($(this).prop("checked"));
                    });
                }
            },
            inputsure: {
                infos: function() {
                    var info = {
                        data: {},
                        project_id: ""
                    };
                    info.project_id = $("#id_dc").val();
                    for (var i = 0; i < gui.share.imageIdc.length; i++) {
                        if (gui.share.imageIdc[i]["image_dc"] == info.project_id) {
                            info.data.image_id = gui.share.imageIdc[i]["image_id"];
                        }
                    }
                    info.data.source_type = "image_id";
                    //info.data.image_id = gui.share.imageIdc[0]["image_id"]; #hid
                    //info.data.image_id = gui.share.image_id;
                    //info.data.availability_zone = $("#id_zone").val();
                    info.data.name = $("#id_name").val();
                    info.data.count = parseInt($("#id_count").val());
                    info.data.flavors = $("#id_flavor").val();
                    //                       info.data.address = $("#id_ip_address").val();

                    info.data.net_type = $("#id_net_type").attr("value");
                    info.data.create_volume = $("#id_boot_source").prop("checked");
                    if (info.data.create_volume) {
                        info.data.volume_name = $("#id_device_name").val();
                        info.data.volume_size = $("#id_device_size").val();
                        if ($("#id_is_backup").attr("checked")) {
                            info.data.is_backup = 1;
                        } else {
                            info.data.is_backup = 0;
                        }
                    }
                    return info;
                },
                clearinfos: function() {
                    $("#id_name").val("");
                    $("#id_count").val("1");
                    //  $("#id_ip_address").val("");
                    $("#id_boot_source").attr("checked", false);
                    $("#id_device_name").val("volume");
                    $("#id_device_size").val("1");
                    $("#id_device").hide();
                    var msgs = $("p[id$='_msg']");
                    for (var i = 0; i < msgs.length; i++) {
                        if ($(msgs[i]).attr("myerror")) {
                            $(msgs[i]).html("$nbsp;");
                        }
                        $(msgs[i]).css('visibility', "hidden");
                    }
                    $("#id_is_backup").attr("checked", false);
                },
                _sure: function() {
                    var csrftoken = $.cookie('csrftoken');

                    function csrfSafeMethod(method) {
                        // these HTTP methods do not require CSRF protection
                        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
                    };
                    $.ajaxSetup({
                        beforeSend: function(xhr, settings) {
                            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                                xhr.setRequestHeader("X-CSRFToken", csrftoken);
                            }
                        }
                    });
                    var info = tool.message_box.inputsure.infos();
                    var sendInfos = info.infos;
                    var url = info.url;
                    console.log(info);
                    $.ajax({
                        type: "post",
                        url: "/dashboard/project/createImage/",
                        data: sendInfos,
                        dataType: "json",
                        async: false,
                        success: function(o) {
                            $("#message_box").dialog("close");
                            var node = o;
                            //console.log(typeof(node));
                            gui.share.nodes.push(node);
                            //gui.reDraw();
                            //gui.timer.start(gui.render(gui.share.nodes,gui.share.links));
                            gui.render(gui.share.nodes, gui.share.links);
                            gui.timer();
                            horizon.clearAllMessages();
                            horizon.alert("success", gettext('Successfully create the instance'), ' ');
                            horizon.autoDismissAlerts();
                        },
                        error: function(o) {
                            gui.handleJSError(o, function (o) {
                                $("#message_box").dialog("close");
                                horizon.clearAllMessages();
                                horizon.alert("error", gettext('Failed to create the instance'));
                                //console.log('error', o);
                            });
                        }
                    });

                },
                sure: function() {
                    // var info = tool.message_box.inputsure.infos();
                    if (tool.validateSure()) {
                      // Quota
                      gui.quotas(function(err){
                        horizon.clearAllMessages();
                        horizon.alert("error", err);
                      },function(data){
                        var info = tool.message_box.inputsure.infos();
                        if (data.total - data.used - info.data.count < 0) {
                          var avail = data.total - data.used;
                          $("#id_count").focus();
                          $("#id_count_msg").css("visibility", "visible").html("Total:" + data.total + ", Available:" + avail);
                        } else {
                        tool.message_box.inputsure.clearinfos();
                        $("#message_box").dialog("close");
                        gui.launch(info.project_id, info.data, function(o) {
                            var node = o;
                            for (var i = 0; i < node.length; i++) {
                                if (node[i].status == "building") {
                                    node[i].status = "BUILD";
                                }
                                gui.share.nodes.push(node[i]);
                            }
                            gui.render(gui.share.nodes, gui.share.links);
                            gui.timer();
                        }, function(o) {
                            console.log("error", o);
                            $("#message_box").dialog("close");
                            horizon.clearAllMessages();
                            horizon.alert("error", gettext('Failed to create the instance'));
                        });
                      }
                    });
                    }
                },
                cancel: function() {
                    tool.message_box.inputsure.clearinfos();
                    $("#message_box").dialog("close");
                }
            },
        },

        // 拖的过程中共享的变量
        drag: function(event) {
            tool.message_box.dialog.title = config.typeMap[$(event.target).attr("image_type")];
            var image = $(event.target).attr("image_id").split(" ");
            var imageIdc = [];
            for (var i = 0; i < image.length; i++) {
                var t = image[i].split(":");
                var m = {};
                m.image_id = t[0];
                m.image_dc = t[1];
                imageIdc.push(m);
            }
            gui.share.imageIdc = imageIdc;
            //console.log(tool.message_box.dialog.title,gui.share.imageIdc);
        },

        // 根据镜像的类别判断，哪个dc
        isDockerContainer: function(str1, str2) {
            var s1 = str1.trim();
            var s2 = str2.trim();
            if (s1 == "docker" && s2 == "docker") {
                return true;
            } else if (s1 == "docker" && s2 == "container") {
                return true;
            } else if (s1 == "container" && s2 == "docker") {
                return true;
            } else if (s1 == "container" && s2 == "container") {
                return true;
            } else if (s1 == "vm" && s2 == "vm") {
                return true;
            } else {
                return false;
            }
        },
        validate: function(id, regular) {
            $(id).bind({
                focus: function() {
                    /*                  if (id == "#id_ip_address") {
                        if ($(id).val() == null || /^$/.test($(id).val())) {
                            $(id + "_msg").css("visibility", "visible");
                            return false;
                        }
                    }
*/
                    if (!regular.test($(id).val())) {
                        $(id + "_msg").css("visibility", "visible");
                        if ($(id + "_msg").attr("myerror")) {
                            $(id + "_msg").html($(id + "_msg").attr("myerror"));
                        }
                    } else {
                        $(id + "_msg").css("visibility", "hidden");
                        if ($(id + "_msg").attr("myerror")) {
                            $(id + "_msg").html("&nbsp;");
                        }
                    }
                },

                blur: function() {
                    if (!regular.test($(id).val())) {
                        $(id + "_msg").css("visibility", "visible");
                        if ($(id + "_msg").attr("myerror")) {
                            $(id + "_msg").html($(id + "_msg").attr("myerror"));
                        }
                    } else {
                        $(id + "_msg").css("visibility", "hidden");
                        if ($(id + "_msg").attr("myerror")) {
                            $(id + "_msg").html("&nbsp;");
                        }
                    }
                }
                /*
                blur: function() {
                    if (id == "#id_ip_address") {
                        if ($(id).val() == null || /^$/.test($(id).val())) {
                            $(id + "_msg").css("visibility", "hidden");
                            return false;
                        }
                    }
                    if (!regular.test($(id).val())) {
                        $(id + "_msg").css("visibility", "visible");
                        if ($(id + "_msg").attr("myerror")) {
                            $(id + "_msg").html($(id + "_msg").attr("myerror"));
                        }
                    } else if (id == "#id_ip_address") {
                        var send_msg = {
                            address: $(id).val()
                        };
                        $.ajax({
                            type: "post",
                            data: send_msg,
                            dataType: "json",
                            headers: {
                                "X-CSRFToken": $.cookie('csrftoken')
                            },
                            url: "/dashboard/project/instances/network/",
                            success: function(data) {
                                $(id + "_msg").text("Other subnets must be 172.16-131/16 or 10/8");
                                $(id + "_msg").css("visibility", "hidden");
                            },
                                                        error: function (o) {
                                $(id + "_msg").text("Someone already has that IP.");
                                $(id + "_msg").css("visibility", "visible");
                                                        }
                        });
                    } else {
                        $(id + "_msg").css("visibility", "hidden");
                        if ($(id + "_msg").attr("myerror")) {
                            $(id + "_msg").html("&nbsp;");
                        }
                    }

                }
*/



            });
        },
        validateReg: function() {
            tool.validate("#id_count", /^[1-9]\d*$/);
            tool.validate("#id_name", /^[a-zA-Z][a-zA-Z0-9_-]{2,24}$/);
            tool.validate("#id_device_size", /^([1-9]|[1-9][0-9]|100)$/);
            tool.validate("#id_device_name", /^[a-zA-Z][a-zA-Z0-9_-]{2,24}$/);
            //          tool.validate("#id_ip_address", /^(25[0-5]|2[0-4]\d|[0-1]?\d?\d)(\.(25[0-5]|2[0-4]\d|[0-1]?\d?\d)){3}$/);
            //tool.validate("#id_ip_address", /^((192\.168|172\.([1][6-9]|[2]\d|3[01]))(\.([2][0-4]\d|[2][5][0-5]|[01]?\d?\d)){2}|10(\.([2][0-4]\d|[2][5][0-5]|[01]?\d?\d)){3})$/);
            //               tool.validate("#id_ip_address", /^10(\.([2][0-4]\d|[2][5][0-5]|[01]?\d?\d)){3}|(192\.168|172\.(1[6-9]|[2-9]\d|1([0-2]\d|3[01])))(\.([2][0-4]\d|[2][5][0-5]|[01]?\d?\d)){2}$/);
        },
        validateSure: function() {
            var msgs = $("p[id$='_msg']");
            for (var i = 0; i < msgs.length; i++) {
                if ($(msgs[i]).css('visibility') == "visible") {
                    var id = $(msgs[i]).attr("id")
                    $("#" + id.substring(0, id.length - 4)).focus();
                    return 0;
                }
            }
            var inputs = $("input[type='text']");
            for (var i = 0; i < inputs.length; i++) {
                if ($(inputs[i]).attr("id") == "id_ip_address") {
                    continue;
                }
                if ($(inputs[i]).val() == "") {
                    $("#" + $(inputs[i]).attr("id")).focus();
                    return 0;
                }
            }
            return 1;
        },
        init: function() {
            // 执行箭头提示
            tool.toolAceTip();

            $("#play").droppable(tool.droppable);
            // 确定按钮
            $("#id_sure").click(tool.message_box.inputsure.sure);

            // 取消按钮
            $("#id_cancel").click(tool.message_box.inputsure.cancel);

            //
            tool.validateReg();

            // 点击
            $("#tool .gui_drag").click(function(e) {
                e = window.event || e;
                tool.drag(e);
                tool.drop();
            }).dblclick(function(e) {
                e = window.event || e;
                tool.drag(e);
                tool.drop();
            });

            // 拖拽
            $("#tool .gui_drag").draggable(tool.draggable);
            $("#tool .gui_drag").bind("drag", tool.drag);
            $("#tool .gui_drag").draggable(function() {
                $("#tool .gui_drag").trigger("drag");
            });
        },
    };

    global.gui = gui;
    $(function() {
        gui.init();
        gui._runInit();
    });
})(window, jQuery);

// (function () {
// gui.addInit(function(){throw Erro("aaaaaaaaaaaaa")});
// gui.addInit(function(){console.log("bbbbbbbbbb")});
// })();

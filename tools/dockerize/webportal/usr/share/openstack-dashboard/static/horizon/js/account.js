;
(function (global, $) {
	var model, account, config;

	// 规格,样式等配置
	config = {
		svg: {
			// 内容区域
			content_width: 380,
			content_height: 250,

			// 内边距
			margin: {
				left: 20,
				right: 170,
				top: 50,
				bottom: 50
			},

			// 饼图半径
			radius: {
				innerRadius: 0,
				outerRadius: 120
			},

			// 提示图标大小
			legend_width: 16,
			legend_height: 16,
		},

		// 默认的文字样式
		text: {
			"text-anchor": "middle",
			"font-size": "16px",
			"dy": "0.8em",
			"font-weight": "500",
		},

		// table映射
		table: {
			caption: {
				disks:$("#tableHead_trans").attr("pie_disks"),// "Diskss",
				disk: "Disks",
				containers:$("#tableHead_trans").attr("pie_containers"),// "Containersss",
				container: "Containers",
				nass: "Naas",
				other: "Other",
				vm: "VM",
				vM: "VM",
				network: "Network",
				publicip: "Public IP",
				publicIP: "Public IP",
				dbaas: "DBaaS",
				dBaas: "DBaaS",
				lBas: "LBaaS",
			},

			// 表头顺序
			thMap: {
				name: $("#tableHead_trans").attr("name"),//"Name",
				mountedContainer:$("#tableHead_trans").attr("mountedcontainer"),// "MountedContainer",
				price: {
					defaultprice:$("#tableHead_trans").attr("price"),// "Price($/H)",
					containers:$("#tableHead_trans").attr("price"),// "Price($/H)",
					disks:$("#tableHead_trans").attr("disk_price"),// "Price($/(H*G))"
				},
				//runtime: "Runtime",
				runtime:$("#tableHead_trans").attr("chargingtime"),   // "ChargingTime",
				size: "Size(G)",
				cost:$("#tableHead_trans").attr("cost"),// "Cost($)",
				zone:$("#tableHead_trans").attr("datacenter"),// "DataCenter",
				datacenter:$("#tableHead_trans").attr("datacenter"),// "DataCenter",
				//size:"Size(G)",
				status:$("#tableHead_trans").attr("status"),// "Status",
                create_time:$("#tableHead_trans").attr("createtime"),//"CreateTime",
			}
		}
	};

	// 数据层
	model = {
		// 初始化请求数据（可以尝试用d3的数据请求，能直接转换成数组）
		getData: function (url) {
			var data;
			// 通过AJAX请求数据
			$.ajax({
				type: "get",
				url: url,
				async: false,
				success: function (o) {
					data = o;
				},
				error: function (o) {
					data = null;
				}
			});
			return data;
		},

		// 数据格式化
		dataFormate: function (o) {
			var data = {};
			data.total_cost = o.total_cost;
			data.balance = o.balance;
			data.info = o.info;

			// 1级
			data.first = {
				CostData: [],
				TimeData: []
			};
			var cost = 0;
			for (var i in data.info) {
				for (var j = 0; j < data.info[i].length; j++) {
					data.info[i][j].cost = +data.info[i][j].cost;
					cost += data.info[i][j].cost;
				}
				// 格式化成这种形式
				var firstCostData = {
					"category": i,
					"cost": cost.toFixed(4),
				}
				cost = 0;
				data.first.CostData.push(firstCostData);
			}
			return data;
		},

		// 数据层初始化函数
		init: function () {

			// 共享数据
			account.share.data = model.getData("/dashboard/project/bill/all");
			if (account.share.data) {
				// 格式化数据
				account.share.data = model.dataFormate(account.share.data);
				return account.share.data;
			} else {
				return null;
			}
		},

	};

	// 具体视图层-消费
	account = {
		share: {},
		init: function () {
			var data = model.init();

			if (data) {
				$("#account-total .account-total span").html(data.total_cost);
				$("#account-total .account-left span").html(data.balance);

				// 分2种情况
				// 第一种存在消费
				// 第二种没有消费，但是存在历史的消费数据
				if (data.total_cost > 0) {
				//	account.render("#account-pie", data.first.CostData, "Distribution of resource use", "cost", "category");
				    account.render("#account-pie", data.first.CostData, $("#tableHead_trans").attr("pie_title"), "cost", "category");
					account.renderTable("#table_detail", "containers", account.share.data.info["containers"]);
				}else{
					account.render("#account-pie",data.first.CostData, "Distribution of resource use","cost", "category","none");
					account.renderTable("#table_detail", "containers", account.share.data.info["containers"]);
				}
			}
		},

		// 渲染table
		// id-表示一个div（此table是被div包裹着的）
		// caption-表示标题
		// data 要显示的数据
		renderTable: function (id, caption, data) {
			if (data.length) {
				$(id + " table .header").attr("colspan", data[0].length - 1); // id不显示
				$(id + " table .caption .title").text(config.table.caption[caption] + ":");

				// 清空表头
				$(id + " table .tableHead").children().remove();

				// 根据数据里的键值，查找表头，
				function findTh(data, title) {
					for (var i in data) {
						//console.log(data[""+title+""],data[""+title+""].toString());
						if (typeof (data["" + title + ""]) != "undefined") {
							if (data["" + title + ""].toString() != "") {
								return true;
							}
						}
					}
					return false;
				}

				// 表头显示的信息
				var thShowName = [],
					// 实际数据传输时的信息
					thSaveName = [];

				// 按照设定的序数，匹配
				for (var i in config.table.thMap) {

					// 匹配键值
					if (findTh(data[0], i)) {

						if (i == "price") {
							if (config.table.thMap.price[caption]) {
								thShowName.push(config.table.thMap.price[caption]);
							} else {
								thShowName.push(config.table.thMap.price["defaultprice"]);
							}
						} else {
							thShowName.push(config.table.thMap[i]);
						}
						thSaveName.push(i);
					}
				}

				// 添加表头
				var th = "<th>" + thShowName.join("</th><th>") + "</th>";
				$(id + " table .tableHead").append(th);

				// 表内容部分
				var tbody = $(id + " tbody");

				// 清空内容
				tbody.children().remove();

				// 匹配显示顺序
				for (var i = 0; i < data.length; i++) {
					var tdElement = [];
					for (var j = 0; j < thSaveName.length; j++) {
						tdElement.push(data[i]["" + thSaveName[j]] + "");
					};
					// console.log(tdElement);
					var tr = "<tr><td>" + tdElement.join("</td><td>") + "</td></tr>";
					tbody.append(tr);
				};

				// 包裹table的div的id
				$(id).show("slow");

			} else {
				$(id).hide();
			}

		},

		// 排序这块用estjs库，就非常方便了！
		sortTable: function (id) {
			var table = $(id + " table .tableHead")
		},

		// 渲染图形
		// id-包裹svg的div
		// data-数据
		// title-标题
		// property-以何种尺度进行对比：比如cost，time
		// name-表示数据的键
		// isnone-消费为空，但还是存在历史的消费记录
		render: function (id, data, title, property, name,isnone) {
			// 创建svg画布
			var svg = d3.select(id).append("svg").attr({
				"width": config.svg.content_width + config.svg.margin.left + config.svg.margin.right + 50,
				"height": config.svg.content_height + config.svg.margin.top + config.svg.margin.bottom
			});

			// 标题显示（居底中间）
			var gTitle = svg.append("g")
				.attr("transform", "translate(" + (config.svg.margin.left + config.svg.content_width / 2) + "," + (config.svg.margin.top + config.svg.content_height + config.svg.margin.bottom / 2) + ")")
				.append("text")
				.attr(config.text)
				.attr("text-anchor", "middle")
				.text(title);

			// 创建pie的组
			var g = svg.append("g")
				.attr("transform", "translate(" + (config.svg.margin.left + config.svg.content_width / 2) + "," + (config.svg.margin.top + config.svg.content_height / 2) + ")");

			// 定义扇形圆
			var arc_generator = d3.svg.arc()
				.innerRadius(config.svg.radius.innerRadius)
				.outerRadius(config.svg.radius.outerRadius);

			// 定义每个扇形的角度，以property衡量
			var angle_data = d3.layout.pie().sort(null).value(function (d) {
				return d["" + property + ""];
			});

			// 定义颜色（10种）
			var color = d3.scale.category10();

			// 判断消费额是否为空
			if(isnone!="none"){

				// 创建每组扇形（文字和扇形块）
				var pie = g.selectAll("g")
					.data(angle_data(data))
					.enter()
					.append("g")
					.attr("cursor","pointer").style("opacity","0.7")
					.on({
						"mouseover": account.event.path.mouseover,
						"mouseout": account.event.path.mouseout,
						"click": account.event.path.click,
					});
				// 添加扇形块
				pie.append("path")
					.style('fill', function (d, i) {
						return color(i);
					})
					.transition().duration(1100).attrTween("d", function (d) {
						var start = {
							startAngle: 0,
							endAngle: 0
						}
						var interpolate = d3.interpolate(start, d);
						return function (t) {
							return arc_generator(interpolate(t));
						}
					});

				// 添加文字
				pie.append("text")
					.text(function (d) {
						if (d.endAngle == d.startAngle) {
							return "";
						} else {
							var padpercent = parseFloat(d.endAngle - d.startAngle) / (2 * Math.PI);
							return (padpercent * 100).toFixed(2) + "%";
						}
					}).attr({
						"transform": function (d) {
							return "translate(" + arc_generator.centroid(d) + ")";
						}
					})
					.attr(config.text)
					.style('fill', function (d, i) {
						if (d.endAngle == d.startAngle) {
							return color(i);
						} else {
							return "black";
						}
					});
			}else{
				// 创建空的扇形
				var pie = g.append("g");

				// 添加空的扇形块
				pie.append("path")
					.style('fill', function (d, i) {
						return "white";
					})
					.attr({
						"stroke":"black",
						"stroke-width":"1",
						"opacity":'0.6',
					})
					.transition().duration(1100).attrTween("d", function () {
						var start = {
							startAngle: 0,
							endAngle: 0,
						}
						var end={
							startAngle: 0,
							endAngle: 2*Math.PI,
						}
						var interpolate = d3.interpolate(start, end);
						return function (t) {
							return arc_generator(interpolate(t));
						}
					});

				// 添加文字
				pie.append("text")
					.text(function () {
						return "no consumption";
					})
					.attr(config.text)
					.style('fill',"black");
			};

			// 创建标记组
			var g_lengend = svg.append("g")
				.attr("transform", "translate(" + (config.svg.content_width + config.svg.margin.left) + "," + (config.svg.margin.top / 2 + config.svg.content_height / 2) + ")");

			var g_lengends = g_lengend.selectAll("g")
					.data(angle_data(data))
					.enter()
					// 以中间向两边增加标记组，保证标记组在居中
					.append("g")
					.attr("cursor","pointer")
					.attr({
						"transform": function (d, i) {
							var t = (i == 0 ? i : ((i % 2) ? i : (i - 1)));
							var distance = config.svg.legend_height * t + config.svg.legend_height;
							if (i == 0) {
								distance = 0;
							} else if (!(i % 2)) {
								distance = -distance;
							}
							return "translate(0," + distance + ")";
						},
					})
					.on({
						"click": account.event.path.click
					});

				// 每个标记组中的颜色矩形
				g_lengends.append("rect").attr({
					"width": config.svg.legend_width,
					"height": config.svg.legend_height,
				}).style("fill",
					function (d, i) {
						return color(i);
					});

				// 个标记组中的文字提示
				g_lengends.append("text").attr(config.text).attr({
					"text-anchor": "start",
					"transform": "translate(" + config.svg.legend_width * 2 + ",0)",
				}).text(function (d) {
                    // return config.table.caption[d.data["" + name + ""]] + " : " + d.data["" + property + ""] + "$";
					return config.table.caption[d.data["" + name + ""]] + " : " + d.data["" + property + ""] + $("#tableHead_trans").attr("cost_logo");
				});
		},

		// 事件
		event: {
			path: {
				mouseover: function () {
					d3.event.preventDefault();
					d3.select(this).style("opacity", "0.8");
				},
				mouseout: function () {
					d3.event.preventDefault();
					d3.select(this).style("opacity", "0.7");
				},
				click: function (d) {
					d3.event.preventDefault();
					console.log(d);
					account.renderTable("#table_detail", d.data.category, account.share.data.info[d.data.category]);
				}
			}
		}
	};

	// Window暴露出来
	global.account = account;
	$(function () {
		account.init();
	});
})(window, jQuery);

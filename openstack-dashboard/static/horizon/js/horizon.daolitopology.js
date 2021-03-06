horizon.dly_topology = {
  model: null,
  color: null,
  svg: '#topology_canvas',
  svg_container: '#topologyCanvasContainer',
  balloon_tmpl: null,
  balloon_server_tmpl: null,
  balloon_id: null,
  topology_pos: {x: 0, y: 78},
  balloon_pos: {x: 190, y: 35},
  subnet_size: {pos: 480, offset: 50},
  prefix: null,
  zoom: [0.5, 3],
  init: function() {
    var self = this;
    $(self.svg_container).spin(horizon.conf.spinner_options.modal);
    self.color = d3.scale.category10();
    self.balloon_tmpl = Hogan.compile($('#balloon_container').html());
    self.balloon_server_tmpl = Hogan.compile($('#balloon_server').html());

    $(document)
      .on('click', 'a.closeTopologyBalloon', function(e) {
        e.preventDefault();
        self.delete_balloon();
      })
      .on('click', '.topologyBalloon', function(e) {
        e.stopPropagation();
      })
      .click(function() {
        self.delete_balloon();
      });

    self.load_network_info();
  },
  load_network_info: function() {
    var self = this;
    $.getJSON($('#networktopology').data('networktopology') + '?' + $.now(),
      function(data) {
        self.model = data;
        self.draw_topology();
      }
    );
  },
  get_color: function(i) {
    return this.color(i);
  },
  zoom_event: function() {
    var self = this;
    return d3.behavior.zoom()
      .scaleExtent(self.zoom)
      .on("zoom", function(e) {
        d3.select(self.svg).attr('transform',
          "translate(" + d3.event.translate + ") scale(" + d3.event.scale + ")");
      });
  },
  draw_topology: function() {
    var self = this;
    $(self.svg_container).spin(false);
    d3.select(self.svg_container).call(self.zoom_event());
    var svg = d3.select(self.svg);
    svg
      .attr('width', "100%")
      .attr('height', self.subnet_size.pos + self.model.services.length * self.subnet_size.offset);

    var subnet = svg.selectAll('g.subnet')
      .data(self.model.subnets);

    subnet.enter()
      .append('g')
      .attr('class', 'subnet')
      .attr('transform', "translate(" + self.topology_pos.x + " " + self.topology_pos.y + ")")
      .each(function(d, i) {
        this.appendChild(d3.select('#dly_topology_template > .dly_subnet')
                           .node().cloneNode(true));
        
        var $this = d3.select(this).select('.dly_subnet_rect');
        $this
          .attr('x', i * 40)
          .attr('height', self.subnet_size.pos + self.model.services.length * self.subnet_size.offset)
          .style('fill', self.get_color(i))
          .on('mouseover', function() {
            $this.transition().style('fill', function() {
              return d3.rgb(self.get_color(i)).brighter(0.5);
            });
          })
          .on('mouseout', function() {
            $this.transition().style('fill', function() {
              return self.get_color(i);
            });
          });
      });

    subnet
      .select('.dly_subnet_cidr')
      .attr('y', function(d, i) {
        return -(5 + i * 40);
      })
      .text(function(d) {
        return d[1] + " (Virtual Private Network)";
      });

    subnet.exit().remove();

    var service = svg.selectAll('g.service')
        .data(self.model.services);

    service.enter()
      .append("g")
      .attr('class', 'service')
      .attr('transform', "translate(" + self.topology_pos.x + " " + self.topology_pos.y + ")")
      .each(function(o, i) {
        this.appendChild(d3.select('#dly_topology_template > .dly_service')
                           .node().cloneNode(true));
        var router = d3.select(this).select('.dly_router');
        router
          .attr('transform', 'translate(' + (180 + i * 180) + ' 55)');
        router
          .select('.dly_r_line')
          .attr('d', 'M 35 58 L 35 ' + (125 + i * 130));

        d3.select(this)
          .select('.dly_idc')
          .attr('transform', 'translate(' + (40 + i * 180) + ' ' + (55 + i * 130) + ')');

        for(var k=0; k < o.service.length; k++) {
          d3.select(this)
            .select('.dly_router_addr')
            .append('tspan')
            .attr('x', '35')
            .text(o.service[k].address);
        }

        var $idc = $(this).find('.dly_idc');
        $.each(self.model.subnets, function(j, sub) {
            var service_sub = d3.select('#dly_topology_template > .dly_service_subnet')
                                .node().cloneNode(true);

            d3.select(service_sub).select('.dly_ss_ball')
              .on('mouseenter', function() {
                var $this = $(this);
                var servers = [];
                for(var k=0; k < self.model.servers.length; k++) {
                  var server = self.model.servers[k];
                  if(server.idc == o.idc_id && server.sub == sub[0]) {
                    var object = {};
                    object.id = server.id;
                    object.name = server.name;
                    object.status = server.status;
                    object.address = server.address;
                    object.status_css = (server.status === "ACTIVE") ? 'active' : 'down';
                    servers.push(object);
                  }
                }
                self.show_balloon(o, servers, $this);
              })
              .on('click', function() {
                d3.event.stopPropagation();
              })
              .select('.dly_ss_rect')
              .attr('y', j * 30 + 155)
              .style('fill', self.color(j));

            d3.select(service_sub).select('.dly_ss_gt')
              .attr('fill', self.get_color(j))
              .attr('y', j * 30 + 150);

            d3.select(service_sub).select('.dly_ss_text')
              .attr('y', j * 30 + 150)
              .text(sub[1]);

            var px = -20 - i * 180 + j * 40;
            var py = 155 + j * 30;
            d3.select(service_sub).select('.dly_ss_path')
              .attr('d', 'M ' + px + ' ' + py + ' L 100 ' + py)
              .attr('stroke', self.get_color(j));

            $idc.append(service_sub);
          });
      });
  },
  show_balloon: function(obj, datum, element) {
    var self = this;
    if (self.balloon_id) {
      self.delete_balloon();
    }
    var balloon_tmpl = self.balloon_tmpl;
    var balloon_server_tmpl = self.balloon_server_tmpl;
    var balloon_id = 'bl_' + obj.idc_id;
    var html_data = {
      balloon_id: balloon_id,
      id: obj.id,
      name: obj.name,
      idc_label: gettext("Instances"),
    };
    html_data.server = datum;
    var html = balloon_tmpl.render(html_data, {
      table1: balloon_server_tmpl
    });
    $(self.svg_container).append(html);
    //var x = element.position().left + self.balloon_pos.x;
    //var y = element.position().top - self.balloon_pos.y;
    var x = element.position().left + 190;
    var y = element.position().top - 20;
    $('#' + balloon_id).css({
      'left': x + 'px',
      'top': y + 'px',
    }).show();

    self.balloon_id = balloon_id;
  },
  delete_balloon: function() {
    var self = this;
    if(self.balloon_id) {
      $('#' + self.balloon_id).remove();
      self.balloon_id = null;
    }
  }
};

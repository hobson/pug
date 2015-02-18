// requires:
// <script type="text/javascript" src="//cdnjs.cloudflare.com/ajax/libs/d3/3.5.3/d3.min.js"></script>
// <script type="text/javascript" src="cdnjs.cloudflare.com/ajax/libs/underscore.js/1.7.0/underscore-min.js"></script>


function normalize_values(data) {
    var i = 0;
    if (!data[0].hasOwnProperty("value")) {
        if (data[0].hasOwnProperty("weight")) {
            for (i=0; i<data.length; ++i) {
                data[i]["value"] = data[i]["weight"]; } }
        else {
            if (data[0].hasOwnProperty("length")) {
                for (i=0; i<data.length; ++i) {
                    data[i]["value"] = 1.0 / (Math.max(+data[i]["length"], 0.000001)); } } } }
    return data;
    }

function autoscale(data) {
    // TODO: use d3.extent() for better efficiency?
    var x_min = d3.min(data, function (d) { return +d.value; });
    var x_max = d3.max(data, function (d) { return +d.value; });
    // FIXME: check for x_min == x_max and do something about it (perturb them all by some random scale factor close to 1 and bias close to zero)
    var x_mid = d3.median(data, function (d) { return +d.value; });
    var x_ave = d3.mean(data, function (d) { return +d.value; });
    var exp = Math.LN2 / Math.log((x_max - x_min) / (x_mid - x_min));
    // console.log('min, mid, max: ' + [x_min, x_mid, x_max] + ' gives exponent: ' + exp);
    return {"pow_scale": d3.scale.pow().exponent(exp).domain([x_min, x_max]).range([0.0, Math.pow(1.0 - 0.15, 1 / 4.0)]),
            "x_min": x_min, "x_mid": x_mid, "x_ave": x_ave, "x_max": x_max};
}

function autoscale_and_length(data, width, height) {
    var ans = autoscale(data.links);

    var N_nodes = data.nodes.length;
    var N_edges = data.links.length;
    var scale_length = 50.0 * (width + height) * Math.pow(ans.pow_scale(ans.x_ave) / ans.pow_scale(ans.x_mid), 2.0) / Math.pow(N_edges, 0.75) / Math.pow(N_nodes, 0.25);

    console.log('scaled min, mid, mean, max: ' + [ans.pow_scale(ans.x_min), ans.pow_scale(ans.x_mid), ans.pow_scale(ans.x_ave), ans.pow_scale(ans.x_max)]);
    console.log("scale_length: " + scale_length + " for " + N_edges + ", " +  N_nodes + " edges and nodes");
    return [ans.pow_scale, scale_length];
}

function draw_force_directed_graph(graph, width, height, tag, process_group, process_name, friction, stiffness, charge, radius, opacity) {
    width = typeof width !== 'undefined' ? width : 1000;
    height = typeof height !== 'undefined' ? height : 600;
    tag = typeof tag !== 'undefined' ? tag : "div.content";
    groups = typeof groups !== 'undefined' ? groups : Array(11);
    process_group = typeof process_group !== 'undefined' ? process_group : function (d) { return '' + d; };
    process_name = typeof process_name !== 'undefined' ? process_name : function (d) { return '' + d; };
    radius = typeof radius !== 'undefined' ? radius : (width + height) / 200.0;
    friction = typeof friction !== 'undefined' ? friction : 0.1;
    stiffness = typeof stiffness !== 'undefined' ? stiffness : 0.5;
    opacity = typeof opacity !== 'undefined' ? opacity : 0.5;
    charge = typeof charge !== 'undefined' ? charge : -200;

    var stroke_width = radius / 4.0;

    graph.links = normalize_values(graph.links);

    pow_scale_and_length = autoscale_and_length(graph, width, height);
    var pow_scale = pow_scale_and_length[0];
    var scale_length = pow_scale_and_length[1] ;


    for(var indx in graph.nodes) {
        graph.nodes[indx].r = radius; }

    var color = d3.scale.ordinal().domain(d3.range(10)).range(['#17becf', '#8c564b', '#1f77b4', '#d62728', '#2ca02c', '#ff7f0e', '#9467bd',  '#e377c2', '#7f7f7f', '#bcbd22']);

    var force = d3.layout.force()
        .friction(1.0 - friction)
        .charge(charge)
        .linkDistance(scale_length)
        .linkStrength(function (d) { return stiffness * Math.pow(pow_scale(d.value), 3); } )
        .size([width, height]);

    var svg = d3.select(tag).append("svg")
        .attr("width", width)
        .attr("height", height);

    force
        .nodes(graph.nodes)
        .links(graph.links)
        .start();

    var link = svg.selectAll(".link")
        .data(graph.links)
        .enter().append("line")
            .attr("class", "link")
            .style("stroke", "#888")
            .style("stroke-width", function(d) { return (stroke_width * Math.pow(pow_scale(d.value), 4.0) + .25); })
            .style("opacity", function(d) { return (stroke_width * Math.pow(pow_scale(d.value), 4.0) + .15); }); 
    var node = svg.selectAll(".node")
        .data(graph.nodes)
        .enter().append("circle")
            .attr("class", "node")
            .attr("r", function (d) { return d.r } )
        .style("fill", function(d) { return color(d.group); })
        .style("opacity", opacity)
        .call(force.drag)
        .on('mouseover', function(d) { var nodeSelected = d3.select(this).style({opacity: '1.0'});})
        .on('mouseout', function(d) { var nodeSelected = d3.select(this).style({opacity: '' + opacity});});


    node.append("title")
        .text(function(d) { 
            var group_string = "" + process_group(d.group); 
            if (group_string.length <= 0) { 
                return "" + process_name(d.name); } 
            else { 
                return process_name(d.name) + "\n" + group_string; }
            });

    force.on("tick", function() {
        link.attr("x1", function(d) { return d.source.x; })
            .attr("y1", function(d) { return d.source.y; })
            .attr("x2", function(d) { return d.target.x; })
            .attr("y2", function(d) { return d.target.y; });

        node.attr("cx", function(d) { return d.x; })
            .attr("cy", function(d) { return d.y; });
        });
}

function graph_to_matrix(graph, directional, add_diagonal) {
    directional = typeof directional !== 'undefined' ? directional : true;
    add_diagonal = typeof add_diagonal !== 'undefined' ? add_diagonal : false;

    var matrix = [], N_nodes = graph.nodes.length;
    matrix['N'] = N_nodes;
    
    // Compute row and column numbers for each node.
    graph.nodes.forEach(function(node, i) {
        node.index = i;
        // accumulate values from each edge (link) starting with a value of 0
        node.value = 0;
        // create a matrix row for each node
        matrix[i] = d3.range(N_nodes).map(function(j) { return {x: j, y: i, z: 0}; });
      });
    console.log(graph.nodes.length);

    // Links (edge) become cells in the matrix
    graph.links.forEach(function(link) {
        matrix[link.source][link.target].z += link.value;
        graph.nodes[link.target].value += link.value;
        if (add_diagonal) matrix[link.target][link.target].z += link.value;
        if (directional != true) {
            matrix[link.target][link.source].z += link.value;
            graph.nodes[link.source].value += link.value;
            if (add_diagonal) matrix[link.source][link.source].z += link.value;
            }
        });
    return matrix;
    }

function graph_sum_source(graph, source_node) {
    var sum = 0.0;
    for (var i=0; i<graph.links.length; i++) {
        if (+graph.links[i].source == +source_node) {
            sum = sum + graph.links[i].value;
            
            }
        }
    return sum;
    }

function draw_matrix_heat_map(graph, width, height, tag) { //, process_group, process_name, friction, stiffness, charge, radius, opacity) {
    width = typeof width !== 'undefined' ? width : 900;
    height = typeof height !== 'undefined' ? height : width;
    height = width; // FIXME: allow rectangular display shapes as well as rectangular graph data 
    tag = typeof tag !== 'undefined' ? tag : "body"; //"div.content";
    // groups = typeof groups !== 'undefined' ? groups : Array(11);
    // process_group = typeof process_group !== 'undefined' ? process_group : function (d) { return '' + d; };
    // process_name = typeof process_name !== 'undefined' ? process_name : function (d) { return '' + d; };
    // radius = typeof radius !== 'undefined' ? radius : (width + height) / 200.0;
    // friction = typeof friction !== 'undefined' ? friction : 0.1;
    // stiffness = typeof stiffness !== 'undefined' ? stiffness : 0.5;
    // opacity = typeof opacity !== 'undefined' ? opacity : 0.5;
    // charge = typeof charge !== 'undefined' ? charge : -200;


    pow_scale_and_length = autoscale_and_length(graph, width, height);
    var pow_scale = pow_scale_and_length[0];
    var scale_length = pow_scale_and_length[1];

    var margin = {
        top: height / 10, bottom: height / 100,
        left: width / 10,  right: width  / 100
        };

    var x = d3.scale.ordinal().rangeBands([0, width]),
        z = pow_scale, //d3.scale.linear().domain([0, 1]).clamp(true),
        c = d3.scale.category10().domain(d3.range(10));
        // c = d3.scale.ordinal().domain(d3.range(10)).range(['#17becf', '#8c564b', '#1f77b4', '#d62728', '#2ca02c', '#ff7f0e', '#9467bd',  '#e377c2', '#7f7f7f'

    var z_format = d3.format(".2r");

    var svg = d3.select(tag).append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .style("margin-left", -margin.left + "px")
        .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    matrix = graph_to_matrix(graph);

    console.log(matrix);
    console.log(matrix[0]);
    console.log('matrix sum=' + matrix[0].reduce( function(prev, current, index, array) { return { z: prev.z + current.z}; }).z);  //, function(d) { return d.z; } ));
    console.log('graph sum=' + graph_sum_source(graph, 0));

    // Presort the column, row orderings.
    var sort_choices = {
        lex: d3.range(matrix.N).sort(function(a, b) { return d3.ascending(graph.nodes[a].name, graph.nodes[b].name); }),
        value: d3.range(matrix.N).sort(function(a, b) { return graph.nodes[b].value - graph.nodes[a].value; }),
        group: d3.range(matrix.N).sort(function(a, b) { return graph.nodes[b].group - graph.nodes[a].group; })
    };

    // Default column & row sort order is alphabetical (actually lexographical).
    x.domain(sort_choices.lex);

    svg.append("rect")
        .attr("class", "background")
        .attr("width", width)
        .attr("height", height);

    var row = svg.selectAll(".row")
        .data(matrix)
        .enter().append("g")
        .attr("class", "row")
        .attr("transform", function(d, i) { return "translate(0," + x(i) + ")"; })
        .each(row);

    // horizontal line for the "x-axis"
    row.append("line").attr("x2", width);

    function order(value) {
        x.domain(sort_choices[value]);

        var t = svg.transition().duration(5000);

        t.selectAll(".row")
            .delay(function(d, i) { return x(i) * 4; })
            .attr("transform", function(d, i) { return "translate(0," + x(i) + ")"; })
          .selectAll(".cell")
            .delay(function(d) { return x(d.x) * 4; })
            .attr("x", function(d) { return x(d.x); });

        t.selectAll(".column")
            .delay(function(d, i) { return x(i) * 4; })
            .attr("transform", function(d, i) { return "translate(" + x(i) + ")rotate(-90)"; });
      }

    // label each row
    row.append("text")
        .attr("x", -6)
        .attr("y", x.rangeBand() / 2)
        .attr("dy", ".32em")
        .attr("text-anchor", "end")
        .text(function(d, i) { return graph.nodes[i].name; });

      var column = svg.selectAll(".column")
          .data(matrix)
        .enter().append("g")
          .attr("class", "column")
          .attr("transform", function(d, i) { return "translate(" + x(i) + ")rotate(-90)"; });

      column.append("line")
          .attr("x1", -width);

      column.append("text")
          .attr("x", 6)
          .attr("y", x.rangeBand() / 2)
          .attr("dy", ".32em")
          .attr("text-anchor", "start")
          .text(function(d, i) { return graph.nodes[i].name; });

      function row(row) {
        var cell = d3.select(this).selectAll(".cell")
            .data(row.filter(function(d) { return d.z; }))
          .enter().append("rect")
            .attr("class", "cell")
            .attr("x", function(d) { return x(d.x); })
            .attr("width", x.rangeBand())
            .attr("height", x.rangeBand())

            .style("fill-opacity", function(d) { return z(d.z); })
            .style("fill", function(d) { return graph.nodes[d.x].group == graph.nodes[d.y].group ? c(graph.nodes[d.x].group) : null; })
            .on("mouseover", mouseover)
            .on("mouseout", mouseout);

        cell.append("title").text(function(d) { return "" + z_format(d.z); });
      }

      function mouseover(p) {
        d3.selectAll(".row text").classed("active", function(d, i) { return i == p.y; });
        d3.selectAll(".column text").classed("active", function(d, i) { return i == p.x; });
      }

      function mouseout() {
        d3.selectAll("text").classed("active", false);
      }

      d3.select("#matrixsortorder").on("change", function() {
        clearTimeout(timeout);
        order(this.value);
      });

      var timeout = setTimeout(function() {
        order("lex");
        d3.select("#order").property("selectedIndex", 0).node().focus();
      }, 2000);
}

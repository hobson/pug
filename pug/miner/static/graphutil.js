function autoscale(data) {
    var N_edges = data.length;
    // TODO: use d3.extent() for better efficiency?
    var x_min = d3.min(data, function (d) { return +d.value; });
    var x_max = d3.max(data, function (d) { return +d.value; });
    var x_mid = d3.median(data, function (d) { return +d.value; });
    var exp = Math.LN2 / Math.log((x_max - x_min) / (x_mid - x_min));
    console.log('min, mid, max: ' + [x_min, x_mid, x_max] + ' gives exponent: ' + exp);
    return d3.scale.pow().exponent(exp).domain([x_min, x_max]).range([0.0, 1.0]);
}

function autoscale_and_length(data, width, height) {
    var N_edges = data.links.length;
    var x_min = d3.min(data.links, function (d) { return +d.value; });
    var x_max = d3.max(data.links, function (d) { return +d.value; });
    var x_mid = d3.median(data.links, function (d) { return +d.value; });
    var exp = Math.LN2 / Math.log((x_max - x_min) / (x_mid - x_min));
    console.log('min, mid, max: ' + [x_min, x_mid, x_max] + ' gives exponent: ' + exp);
    pow_scale = d3.scale.pow().exponent(exp).domain([x_min, x_max]).range([0.0, Math.pow(1.0-.15,1/4.)]);

    var x_ave = d3.mean(data.links, function (d) { return +d.value; });
    var N_nodes = data.nodes.length;
    length = 100 * (width + height) * Math.pow(pow_scale(x_ave) / pow_scale(x_mid), 2) / Math.pow(N_edges, .75) / Math.pow(N_nodes, .25);

    console.log('scaled min, mid, mean, max: ' + [pow_scale(0), pow_scale(.5), pow_scale(x_ave), pow_scale(1)]);
    console.log("length: " + length + " for " + N_edges + ", " +  N_nodes + " edges and nodes");
    return [pow_scale, length];
}

function draw_force_directed_graph(graph, width, height, tag, process_group, process_name, friction, stiffness, charge, radius, opacity) {
    width = typeof width !== 'undefined' ? width : 1000;
    height = typeof height !== 'undefined' ? height : 600;
    tag = typeof tag !== 'undefined' ? tag : "div.content";
    groups = typeof groups !== 'undefined' ? groups : Array(11);
    process_group = typeof process_group !== 'undefined' ? process_group : function (d) { return '' + d; };
    process_name = typeof process_name !== 'undefined' ? process_name : function (d) { return '' + d; };
    radius = typeof radius !== 'undefined' ? radius : (width + height) / 200.0;
    friction = typeof friction !== 'undefined' ? friction : 0.5;
    stiffness = typeof stiffness !== 'undefined' ? stiffness : 0.5;
    opacity = typeof opacity !== 'undefined' ? opacity : 0.5;
    charge = typeof charge !== 'undefined' ? charge : -500;

    var stroke_width = radius / 4.0;

    pow_scale_and_length = autoscale_and_length(graph, width, height);
    var pow_scale = pow_scale_and_length[0], length = pow_scale_and_length[1] ;


    for(var indx in graph.nodes) { 
        graph.nodes[indx].r = radius; }

    var color = d3.scale.ordinal().domain(d3.range(10)).range(['#17becf', '#8c564b', '#1f77b4', '#d62728', '#2ca02c', '#ff7f0e', '#9467bd',  '#e377c2', '#7f7f7f', '#bcbd22']);

    var force = d3.layout.force()
        .friction(1.0 - friction)
        .charge(charge)
        .linkDistance(length)
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
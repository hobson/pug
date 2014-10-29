// requires functions from miner/js/plot-util.js

function mouseover(d) {
  // selector = ".bar.row-"+d.row + ".col"+d.col;
  // console.log('mouse over selctor: ' + selector);
  // console.log(d);
  // d3.select(selector).classed('hover', true);
}


function mouseout(d) {
  // FIXME: doesn't work
  // selector = ".row-"+d.row + ".col-"+d.col;
  // console.log('mouse out selector: ' + selector);
  // console.log(d);
  // d3.select().classed('hover', false);
}


function bar_plot(d3data, conf) {
    default_conf = {"plot_container_id": "plot_container", "margin": {top: 30, right: 80, bottom: 30, left: 50}}
    conf                   = typeof conf                   == "undefined" ? default_conf                   : conf;
    conf.plot_container_id = typeof conf.plot_container_id == "undefined" ? default_conf.plot_container_id : conf.plot_container_id;
    conf.margin            = typeof conf.margin            == "undefined" ? default_conf.margin            : conf.margin;
    conf.width  = 960 - conf.margin.left - conf.margin.right;
    conf.height = 500 - conf.margin.top  - conf.margin.bottom;
    // FIXME: add pixel_width as conf parameter (default=960);
    conf.width  = 960 - conf.margin.left - conf.margin.right;
    conf.height = 500 - conf.margin.top  - conf.margin.bottom;

    var num_layers = d3data.length - 1;
    xlabel = conf.xlabel.length ? conf.xlabel : d3data[0][0];
    ylabel = conf.ylabel.length ? conf.ylabel : d3data[0][1];
    var layers = split_d3_series(d3data);
    for (var i=0; i<layers.length; i++) {
        for (var j=0; j<layers[i].length; j++) {
            layers[i][j].series = layers[i]
            layers[i][j].col = i;
            layers[i][j].row = j;
            layers[i][j].heading = conf.header[i+1];
            layers[i][j].layer = layers[i];
        }
    }
    console.log('layers (d3data as arrays of objects with x,y properties)');
    console.log(layers);

    console.log('d3data unaltered');
    console.log(d3data);
    d3data = arrays_as_objects(d3data);
    console.log('d3data as array of objects');
    console.log(d3data);
    var num_stacks = d3data.length; // number of samples per layer

    conf.xscale = d3.scale.linear().range([0, conf.width]);
    conf.xlabel = "Horizontal Value (Time?)";
    conf.yscale = d3.scale.linear().range([conf.height, 0]);
    conf.ylabel = "Vertical Value";

    console.log("conf.plot_container_id");
    console.log(conf.plot_container_id);
    console.log(conf.margin);

    d3data.sort(function(a, b) { return a.x - b.x; });

    var yGroupMax = d3.max(layers, function(layer) { return d3.max(layer, function(d) { return d.y; }); }),
        yStackMax = d3.max(layers, function(layer) { return d3.max(layer, function(d) { return d.y0 + d.y; }); });

    conf.header = (conf.header === 'undefined' || conf.header.length != num_layers + 1) ? d3.range(num_layers) : conf.header;

    console.log('conf.header');
    console.log(conf.header);
    console.log(conf.header.length);


    // var x = d3.scale.ordinal()
    //     .domain(d3.range(num_stacks))
    //     .rangeRoundBands([0, conf.width], 0.08);

    var x = d3.scale.ordinal()
        .domain(d3data.map(function(d) { return d.x; }))
        .rangeRoundBands([0, conf.width], 0.08);


    var y = d3.scale.linear()
        .domain([0, yStackMax])
        .range([conf.height, 0]);


    // var y = d3.scale.linear()
    //     .range([height, 0]);

    var color = d3.scale.linear()
        .domain([0, num_layers - 1])
        .range(["#aad", "#556"]);

    // var xAxis = d3.svg.axis()
    //     .scale(x)
    //     .tickSize(0)
    //     .tickPadding(6)
    //     .orient("bottom");

    var xAxis = d3.svg.axis()
        .scale(x)
        .tickSize(0)
        .tickPadding(6)
        .orient("bottom");

    var yAxis = d3.svg.axis()
        .scale(y)
        .orient("left")
        .ticks(10, "%");

    // var yAxis = d3.svg.axis()
    //     .scale(y)
    //     .orient("left");

    // // need something like this here to append the series data to each rect
    // var series = svg.selectAll(".series")
    //     .data(all_series)
    //   .enter().append("g")
    //     .attr("class", "series");


    var svg = d3.select("#" + conf.plot_container_id).append("svg")
        .attr("width", conf.width + conf.margin.left + conf.margin.right)
        .attr("height", conf.height + conf.margin.top + conf.margin.bottom)
      .append("g")
        .attr("transform", "translate(" + conf.margin.left + "," + conf.margin.top + ")");

    var layer = svg.selectAll(".layer")
        .data(layers)
      .enter().append("g")
        .attr("class", "layer")
        .style("fill", function(d, i) { return color(i); });

      // chart.selectAll(".bar")
      //     .data(d3data)
      //   .enter().append("rect")
      //     .attr("class", "bar")
      //     .attr("x", function(d) { return x(d.name); })
      //     .attr("y", function(d) { return y(d.value); })
      //     .attr("height", function(d) { return conf.height - y(d.value); })
      //     .attr("width", x.rangeBand());
    var rect_element;

    var rect = layer.selectAll("rect")
        .data(function(d) { console.log(d); return d; })
      .enter().append("rect")
        .attr("x", function(d) { return x(d.x); })
        .attr("y", conf.height)
        .attr("width", x.rangeBand())
        .attr("class", function(d) { return "bar row-" + d.row + " col-" + d.col; })
        .attr("height", 0)
        .on("mouseover", mouseout)
        .on("mouseout", mouseout);
    //    .on("click", mouseclick);

    rect.transition()
        .delay(function(d, i) { return i * 10; })
        .attr("y", function(d) { return y(d.y0 + d.y); })
        .attr("height", function(d) { return y(d.y0) - y(d.y0 + d.y); });

    svg.append("g")
        .attr("class", "x axis")
        .attr("transform", "translate(0," + conf.height + ")")
        .call(xAxis);

    d3.selectAll("input").on("change", change);

    var timeout = setTimeout(function() {
      d3.select("input[value=\"grouped\"]").property("checked", true).each(change);
    }, 2000);

    function change() {
      clearTimeout(timeout);
      if (this.value === "grouped") transitionGrouped();
      else transitionStacked();
    }

    function transitionGrouped() {
      y.domain([0, yGroupMax]);

      rect.transition()
          .duration(500)
          .delay(function(d, i) { return i * 10; })
          .attr("x", function(d, i, j) { return x(d.x) + x.rangeBand() / num_layers * j; })
          .attr("width", x.rangeBand() / num_layers)
        .transition()
          .attr("y", function(d) { return y(d.y); })
          .attr("height", function(d) { return conf.height - y(d.y); });
    }

    function transitionStacked() {
      y.domain([0, yStackMax]);

      rect.transition()
          .duration(500)
          .delay(function(d, i) { return i * 10; })
          .attr("y", function(d) { return y(d.y0 + d.y); })
          .attr("height", function(d) { return y(d.y0) - y(d.y0 + d.y); })
        .transition()
          .attr("x", function(d) { return x(d.x); })
          .attr("width", x.rangeBand());
    }

} // function bar_plot(d3data)

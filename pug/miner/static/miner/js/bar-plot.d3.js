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
    default_conf         = {"plot_container_id": "plot_container", "container_width": 960, "container_height": 500, "margin": {top: 30, right: 80, bottom: 30, left: 50}};

    conf                   = typeof conf                   == "undefined" ? default_conf                                : conf;
    conf.plot_container_id = typeof conf.plot_container_id == "undefined" ? default_conf.plot_container_id              : conf.plot_container_id;
    conf.margin            = typeof conf.margin            == "undefined" ? default_conf.margin                         : conf.margin;
    conf.container_width   = typeof conf.container_width   == "undefined" ? default_conf.container_width                : conf.container_width;
    conf.container_height  = typeof conf.container_height  == "undefined" ? default_conf.container_height               : conf.container_height;
    conf.width             = typeof conf.width             == "undefined" ? conf.container_width - conf.margin.left - conf.margin.right  : conf.width;
    conf.height            = typeof conf.height            == "undefined" ? conf.container_height - conf.margin.top  - conf.margin.bottom : conf.height;

    xlabel  = typeof conf.xlabel == "undefined" ? d3data[0][0] : conf.xlabel;
    xfield  = typeof d3data[0][0] == "string" ? d3data[0][0] : conf.xlabel;
    ylabel  = typeof conf.ylabel == "undefined" ? d3data[1][0] : conf.ylabel;
    ylabels = ((typeof conf.ylabel == "object") && (d3data.length == (1 + conf.ylabel.length))) ? conf.ylabel : d3data.slice(1).map(function(d) {return d[0];});
    var num_layers = ylabels.length;

    console.log(ylabels);
    console.log(xfield);

    // TODO: standardize on the "series" data structure below which is also used in the line-plot
    var layers = split_d3_series(d3data);
    for (var i=0; i<layers.length; i++) {
        for (var j=0; j<layers[i].length; j++) {
            layers[i][j].series = layers[i];
            layers[i][j].layer  = layers[i];
            layers[i][j].col = i;
            layers[i][j].row = j;
            layers[i][j].heading = ylabels[i];
        }
    }
    console.log('layers (d3data as arrays of objects with x,y properties)');
    console.log(layers);

    d3data = arrays_as_objects(d3data);
    var num_stacks = d3data.length; // number of samples per layer

    conf.xscale = d3.scale.ordinal()
        .domain(d3data.map(function(d) { return d[xfield]; }))
        .rangeRoundBands([0, conf.width], 0.08);
    conf.xlabel = "Horizontal Value (Time?)";
    conf.yscale = d3.scale.linear().range([conf.height, 0]);
    conf.ylabel = "Vertical Value";


    d3data.sort(function(a, b) { return a[xfield] - b[xfield]; });

    var color = d3.scale.linear()
        .domain([0, num_layers - 1])
        .range(["#aad", "#556"]);

    console.log('all_series');
    var all_series = ylabels.map(function(name) {
      var series = { name: name, values: null };
      series.values = d3data.map(function(d) {
            return { series: series, x: d[xfield], y: +d[name] };
      }); // d3data.map(function(d) {
      return series;
    });
    console.log(all_series);

    var ymin = d3.min(all_series, function(series) { return d3.min(series.values, function(d) { console.log(d); return d.y; }); });
    var ymax = d3.max(all_series, function(series) { return d3.max(series.values, function(d) { console.log(d); return d.y; }); });

    console.log([ymin, ymax]);

    var yGroupMax = ymax;
    var yStackMax = d3.max(layers, function(layer) { return d3.max(layer, function(d) { return d.y0 + d.y; }); });


    // var x = d3.scale.ordinal()
    //     .domain(d3.range(num_stacks))
    //     .rangeRoundBands([0, conf.width], 0.08);

    var x = conf.xscale;


    var y = d3.scale.linear()
        .domain([0, yStackMax])
        .range([conf.height, 0]);


    // var y = d3.scale.linear()
    //     .range([height, 0]);



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
        .attr("x", function(d) { return x(d[xfield]); })
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
          .attr("x", function(d, i, j) { return x(d[xfield]) + x.rangeBand() / num_layers * j; })
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
          .attr("x", function(d) { return x(d[xfield]); })
          .attr("width", x.rangeBand());
    }

} // function bar_plot(d3data)

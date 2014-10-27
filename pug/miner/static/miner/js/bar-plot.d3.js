// requires functions from miner/js/plot-util.js

function mouseover(d) {
  console.log('bar hover');
  // displays tip at center of voronoi region instead of near point
  // tip.show(d);

  console.log('mouseover');
  console.log(d);
  // doesn't work
  // d.series.line.parentNode.appendChild(d.series.line);
  d3.select(d.series.line).classed("hover", true);
}

//   // tip.attr("transform", "translate(" + x_scale(d.x) + "," + y_scale(d.y) + ")");
//   console.log("transform", "translate(" + x_scale(d.x) + "," + y_scale(d.y) + ")");
//   focus.attr("transform", "translate(" + x_scale(d.x) + "," + y_scale(d.y) + ")");
//   series_name = d.series.name.length ? d.series.name : ylabel;
//   tt = (xlabel.length ? xlabel : "bin") + ": " + d.x + "\u00A0\u00A0\u00A0\u00A0" + series_name + ": " + d.y;
//   focus.select("text").text(tt);

//   query_obj.min_lag = d.x-5;
//   query_obj.max_lag = d.x+5;

//   // This generates the right link, but the SVG doesn't respond to clicks on the circle or anywhere nearby
//   focus.select("a").attr("xlink:href", "?"+obj2query(query_obj));
//   console.log(focus.select("a"));
//   console.log(focus.select("a").attr("xlink:href"));
//   // FIXME: for this link to be visible/clickable the mouseout function has to be triggered when the mouse enters the circle and leaves the voronoi region
// }


function mouseout(d) {
  console.log('bar mouse out');
  // tip.hide(d);
  console.log('mouseout')
  console.log(d);

  d3.select(d.series.line).classed("hover", false);
  focus.select("text").text("");
}


function bar_plot(d3data, conf) {
    conf = typeof conf == 'undefined' ? {"plot_container_id": "plot_container", 
            "margin": {top: 30, right: 80, bottom: 30, left: 50}} : conf;

    var ans = arrays_as_d3_series(d3data);
    xlabel = conf.xlabel.length ? conf.xlabel : ans.xlabel;
    var ylabels = [conf.ylabel];
    ylabel = conf.ylabel.length ? conf.ylabel : ans.ylabels[0];
    var data = ans.data;

    console.log("conf.plot_container_id");
    console.log(conf.plot_container_id);

    data.sort(function(a, b) { return a.x - b.x; });
    var n = d3data.length - 1, // number of stack layers or group members or data sequences or serieses
        m = data.length; // number of samples per layer
    var layers = split_d3_series(d3data);


    var yGroupMax = d3.max(layers, function(layer) { return d3.max(layer, function(d) { return d.y; }); }),
        yStackMax = d3.max(layers, function(layer) { return d3.max(layer, function(d) { return d.y0 + d.y; }); });

    console.log('conf.header');
    console.log(conf.header);
    console.log(conf.header.length);
    conf.header = (conf.header === 'undefined' || conf.header.length != n + 1) ? d3.range(n) : conf.header;
    
    for (var i=0; i<layers.length; i++) {
        for (var j=0; j<layers[i].length; j++) {
            layers[i][j].column = i; 
            layers[i][j].row = j; 
            layers[i][j].heading = conf.header[i+1];
        }
    }

    console.log('layers');
    console.log(layers);

    var margin = {top: 40, right: 10, bottom: 20, left: 10},
        width = 960 - margin.left - margin.right,
        height = 500 - margin.top - margin.bottom;

    var x = d3.scale.ordinal()
        .domain(d3.range(m))
        .rangeRoundBands([0, width], .08);

    var y = d3.scale.linear()
        .domain([0, yStackMax])
        .range([height, 0]);

    var color = d3.scale.linear()
        .domain([0, n - 1])
        .range(["#aad", "#556"]);

    var xAxis = d3.svg.axis()
        .scale(x)
        .tickSize(0)
        .tickPadding(6)
        .orient("bottom");


    var yAxis = d3.svg.axis()
        .scale(y)
        .orient("left")
        .ticks(10, "%");

    // // need something like this here to append the series data to each rect
    // var series = svg.selectAll(".series")
    //     .data(all_series)
    //   .enter().append("g")
    //     .attr("class", "series");


    var svg = d3.select("#" + conf.plot_container_id).append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
      .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    var layer = svg.selectAll(".layer")
        .data(layers)
      .enter().append("g")
        .attr("class", "layer")
        .style("fill", function(d, i) { return color(i); });

    var rect = layer.selectAll("rect")
        .data(function(d) { return d; })
      .enter().append("rect")
        .attr("x", function(d) { return x(d.x); })
        .attr("y", height)
        .attr("width", x.rangeBand())
        .attr("height", 0)
    //    .on("mouseover", mouseover)
    //    .on("click", mouseclick)
    //    .on("mouseout", mouseout);

    rect.transition()
        .delay(function(d, i) { return i * 10; })
        .attr("y", function(d) { return y(d.y0 + d.y); })
        .attr("height", function(d) { return y(d.y0) - y(d.y0 + d.y); });

    svg.append("g")
        .attr("class", "x axis")
        .attr("transform", "translate(0," + height + ")")
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
          .attr("x", function(d, i, j) { return x(d.x) + x.rangeBand() / n * j; })
          .attr("width", x.rangeBand() / n)
        .transition()
          .attr("y", function(d) { return y(d.y); })
          .attr("height", function(d) { return height - y(d.y); });
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


// var xAxis = d3.svg.axis()
//     .scale(x)
//     .orient("bottom");

// var yAxis = d3.svg.axis()
//     .scale(y)
//     .orient("left")
//     .ticks(10, "%");

// var svg = d3.select("body").append("svg")
//     .attr("width", width + margin.left + margin.right)
//     .attr("height", height + margin.top + margin.bottom)
//   .append("g")
//     .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

// d3.tsv("data.tsv", type, function(error, data) {
//   x.domain(data.map(function(d) { return d.letter; }));
//   y.domain([0, d3.max(data, function(d) { return d.frequency; })]);

//   svg.append("g")
//       .attr("class", "x axis")
//       .attr("transform", "translate(0," + height + ")")
//       .call(xAxis);

//   svg.append("g")
//       .attr("class", "y axis")
//       .call(yAxis)
//     .append("text")
//       .attr("transform", "rotate(-90)")
//       .attr("y", 6)
//       .attr("dy", ".71em")
//       .style("text-anchor", "end")
//       .text("Frequency");

//   svg.selectAll(".bar")
//       .data(data)
//     .enter().append("rect")
//       .attr("class", "bar")
//       .attr("x", function(d) { return x(d.letter); })
//       .attr("width", x.rangeBand())
//       .attr("y", function(d) { return y(d.frequency); })
//       .attr("height", function(d) { return height - y(d.frequency); });

// });

// function type(d) {
//   d.frequency = +d.frequency;
//   return d;
// }

// </script>
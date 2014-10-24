// FIXME: put all globals in a plot conf object/namespace
var conf = {"plot_container_id": "plot_container", 
            "margin": {top: 30, right: 80, bottom: 30, left: 50}};
conf.width = 960 - conf.margin.left - conf.margin.right;
conf.height = 500 - conf.margin.top - conf.margin.bottom;
conf.xscale = d3.scale.linear().range([0, conf.width]);
conf.xlabel = "Horizontal Value (Time?)";
conf.yscale = d3.scale.linear().range([conf.height, 0]);
conf.ylabel = "Vertical Value";

console.log("conf");
console.log(conf);
// tooltips
var svg = d3.select("#" + conf.plot_container_id).append("svg")
            .attr("width",  conf.width + conf.margin.left + conf.margin.right)
            .attr("height", conf.height + conf.margin.top + conf.margin.bottom)
      .append("g")
        .attr("transform", "translate(" + conf.margin.left + "," + conf.margin.top + ")");

console.log("svg");
console.log(svg);

console.log("focus");
console.log(focus);

var focus = svg.append("g")
    .attr("transform", "translate(-100,-100)")  // make sure initial tool-tip circle is located outside (upper left) of the plot (svg element)
    .attr("class", "focus");


function mouseover(d) {
  // displays tip at center of voronoi region instead of near point
  // tip.show(d);

  console.log('mouseover');
  console.log(d);
  // doesn't work
  d.series.line.parentNode.appendChild(d.series.line);
  d3.select(d.series.line).classed("series-hover", true);

  // tip.attr("transform", "translate(" + conf.xscale(d.x) + "," + conf.yscale(d.y) + ")");
  console.log("transform", "translate(" + conf.xscale(d.x) + "," + conf.yscale(d.y) + ")");
  focus.attr("transform", "translate(" + conf.xscale(d.x) + "," + conf.yscale(d.y) + ")");
  series_name = d.series.name.length ? d.series.name : conf.ylabel;
  tt = (conf.xlabel.length ? conf.xlabel : "bin") + ": " + d.x + "\u00A0\u00A0\u00A0\u00A0" + series_name + ": " + d.y;
  focus.select("text").text(tt);

  query_obj.min_lag = d.x-5;
  query_obj.max_lag = d.x+5;

  // This generates the right link, but the SVG doesn't respond to clicks on the circle or anywhere nearby
  focus.select("a").attr("xlink:href", "?"+obj2query(query_obj));
  console.log(focus.select("a"));
  console.log(focus.select("a").attr("xlink:href"));
  // FIXME: for this link to be visible/clickable the mouseout function has to be triggered when the mouse enters the circle and leaves the voronoi region
}

// // FIXME: Unused!
// function mouseclick(d) {
//   console.log('mouseclick')
//   console.log(d);
//   var url = document.URL + "&lag=" + d.x + "&series=" + d.series.name;
//   var hist_formats = ["", "-pmf", "-cmf", "-cfd"];
//   hist_formats.forEach(function(hf) { 
//     url = url.replace("/hist"+hf+"/", "/cases/");
//   });
//   var plot_types = ["linked", "link", "l", "zoomable", "zoom", "z"];
//   plot_types.forEach(function(pt) { 
//     url = url.replace("&plot="+pt, "&table=quick");
//   });
//   window.location = url;
// }


function mouseout(d) {
  // tip.hide(d);
  console.log('mouseout')
  console.log(d);
  d3.select(d.series.line).classed("series-hover", false);
  focus.select("text").text("");
}



// Line plot with clickable Voronoi regions and mouse-over tool tips showing the coordinate values
// 
// Arguments:
//   d3data (array): N*M 2-D array, where N is the number of data series to plot (typically 2)
//     d3data[0][0] (String or Null): x-axis label (horizontal, independent axis or domain)
//     d3data[1][0] (String or Null): y-axis label (vertical, dependent axis or range)
//     d3data[0][1..M] (Number or String): x-coordinate values, Strings are converted to dates in seconds since epoch
//     d3data[1][1..M] (Number): y-coordinate values
//   x-axis (String, optional): horizontal x-axis label (overrides d3data[0][0])
//   y-axis (String, optional): vertical y-axis label (overrides d3data[0][0])
function line_plot(d3data, new_xlabel, new_ylabel) {
    var ans = arrays_as_d3_series(d3data);
    console.log(ans);
    conf.xlabel = new_xlabel.length ? new_xlabel : ans.xlabel;
    var ylabels = [new_ylabel];  // FIXME
    conf.ylabel = new_ylabel.length ? new_ylabel : ans.ylabels[0]; // FIXME
    var data = ans.data;

    console.log('data');
    console.log(data);
    data.sort(function(a, b) { return a.x - b.x; });

    var color = d3.scale.category10().domain(ans.ylabels);

    // parse xdata as datetimes if the xlabel starts with the word "date" or "time" 
    if ((conf.xlabel.substring(0, 4).toUpperCase() == "DATE")
        // || (conf.xlabel.substring(0, 4).toUpperCase() == "TIME")
      ) {
      conf.xscale = d3.time.scale().range([0, conf.width]);
      
      data.forEach(function(d) {
        console.log(d);
        console.log(d.x);
        d.x = d3_parse_date(d.x); }
        );
    }

    var xAxis = d3.svg.axis().scale(conf.xscale).orient("bottom");

    var yAxis = d3.svg.axis().scale(conf.yscale).orient("left");

    var voronoi = d3.geom.voronoi()
        .x(function(d) { return conf.xscale(d.x); })
        .y(function(d) { return conf.yscale(d.y); })
        .clipExtent([[-conf.margin.left, -conf.margin.top], [conf.width + conf.margin.right, conf.height + conf.margin.bottom]]);

    var line = d3.svg.line()
        .x(function(d) { return conf.xscale(d.x); })
        .y(function(d) { return conf.yscale(d.y); });



    var all_series = color.domain().map(function(name) {
      var series = { 
        name: name,
        values: null 
      };
      series.values = data.map(function(d) {
            return {
              series: series,
              //name: name,  // unnecesary?
              x: d.x,
              y: +d[name]
            }; // return {
      }); // data.map(function(d) {
      return series;
    });


    conf.xscale.domain(d3.extent(data, function(d) { return d.x; }));

    conf.yscale.domain([
      d3.min(all_series, function(c) { return d3.min(c.values, function(v) { return v.y; }); }),
      d3.max(all_series, function(c) { return d3.max(c.values, function(v) { return v.y; }); })
    ]);

    svg.append("g")
        .attr("class", "y axis")
        .attr("transform", "translate(0," + conf.height + ")")
        .call(xAxis)
      .append("text")
        .attr("y", conf.yscale.range()[1])
        .style("text-anchor", "end")
        .attr("x", conf.xscale.range()[1])
        .attr("dy", "-.3em")

        .text(conf.xlabel);

    svg.append("g")
        .attr("class", "x axis")
        .call(yAxis)
      .append("text")
        .attr("transform", "rotate(-90)")
        .attr("y", 6)
        .attr("dy", ".7em")
        .style("text-anchor", "end")
        .text(conf.ylabel);

    var series = svg.selectAll(".series")
        .data(all_series)
      .enter().append("g")
        .attr("class", "series");

    series.append("path")
        .attr("class", "line")
        .attr("d", function(d) { d.line=this; return line(d.values); })
        .style("stroke", function(d) { return color(d.name); });


    // legend (series label at the end of each line)
    series.append("text")
        .datum(function(d) { return { name: d.name, value: d.values[d.values.length - 1]}; })
        .attr("transform", function(d) { return "translate(" + conf.xscale(d.value.x) + "," + conf.yscale(d.value.y) + ")"; })
        .attr("x", 3)
        .attr("dy", ".35em")
        .text(function(d) { return d.name; });

    var voronoiGroup = svg.append("g")
        .attr("class", "voronoi");

    voronoiGroup.selectAll("path")
        .data(voronoi(d3.nest()
            .key(function(d) { return conf.xscale(d.x) + "," + conf.yscale(d.y); })
            .rollup(function(v) { return v[0]; })
            .entries(d3.merge(all_series.map(function(d) { return d.values; })))
            .map(function(d) { return d.values; })))
      .enter().append("path")
        .attr("d", function(d) { return "M" + d.join("L") + "Z"; })
        .datum(function(d) { return d.point; })
        .on("mouseover", mouseover)
    // it seems like onclick is handled by an <a href>
    //    .on("click", mouseclick)
        .on("mouseout", mouseout);

    // reappend the svg with a focus circle and see if it'll mouse-out from the veronoi
    focus = svg.append("g")
        .attr("transform", "translate(-100,-100)")  // make sure initial tool-tip circle is located outside (upper left) of the plot (svg element)
        .attr("class", "focus");

    focus.append("text").attr("y", -12);

    focus.append("a").attr("xlink:href", "/")
      .append("circle").attr("r", 6.5).style("fill", "steelblue").style("fill-opacity", 0.3);
}




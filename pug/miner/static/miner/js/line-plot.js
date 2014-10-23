function d3_parse_date(date_or_time) {
  return d3.time.format("%Y%m%d").parse(date_or_time);
}

// Expects d3data to be an array of arrays (columns of data)
// The first element of each array is it's label (header/name)
// Returns a d3-compatible object with an xlabel, ylabels = header with xlabel removed
// and data which is an array of objects with elements x and y (y attribute is named by the header/ylabels)
function arrays_as_d3_series(d3data) {
    console.log('d3data before transpose');
    console.log(d3data);
    var ans = {};
    d3data = d3.transpose(d3data);
    // console.log(d3data);
    ans.data = [];
    ans.header = d3data[0];
    // console.log(header);
    for (var i=1; i < d3data.length; i++) {
        var obj = {};
        obj.x = d3data[i][0];
        for (var k=1; k < ans.header.length; k++) {
            obj[ans.header[k]] = d3data[i][k];
            }
        // console.log(i);
        // console.log(obj);
        ans.data.push(obj);
        }
    // console.log(data);

    ans.xlabel = ans.header[0];
    ans.header.shift();
    ans.ylabels = ans.header;
    return ans;
    }

function query2obj(query) {
  query = query ? query : location.search;
  // ignore the questionmark in the search (query) string part of the URI
  if (query[0] == '?') { query = query.substring(1); }
  // console.log(query);
  query = query.replace(/%2C/g,",").replace(/%2B/g," ");
  // console.log(query);
  return JSON.parse('{' + decodeURI(query).replace(/"/g, '\\"') + '}');
                    // .replace(/%2C/g,",")
                    // .replace(/%2B/g," ")
                    // .replace(/&/g, '","')
                    // .replace(/=/g,'":"') + '"}'
  }

function obj2query(obj, prefix) {
    var str = [];
    for(var p in obj) {
      var k = prefix ? prefix + "[" + p + "]" : p, v = obj[p];
      str.push(typeof v == "object" ?
        obj2query(v, k) :
        encodeURIComponent(k) + "=" + encodeURIComponent(v));
    }
    return str.join("&");
}

function query_param(name) {
    name = name.replace(/[\[]/, "\\[").replace(/[\]]/, "\\]");
    var regex = new RegExp("[\\?&]" + name + "=([^&#]*)"),
        results = regex.exec(location.search);
    return results === null ? "" : decodeURIComponent(results[1].replace(/\+/g, " "));
}

// globals used by mouseover and mouseout for tooltips, etc
var margin = {top: 30, right: 80, bottom: 30, left: 50};
var  width = 960 - margin.left - margin.right;
var height = 500 - margin.top - margin.bottom;
var x_scale = d3.scale.linear().range([0, 1]);
var y_scale = d3.scale.linear().range([1, 0]);
var ylabel = "Vertical Value";
var xlabel = "Horizontal Value (Time?)";

// FIXME: put all globals in a plot conf object/namespace
var conf = {margin: margin, width: width, height: height, x_scale: x_scale, xlabel: xlabel, y_scale: y_scale, ylabel: ylabel};

console.log("conf");
console.log(conf);
// tooltips
var svg = d3.select("#linegraph").append("svg")
            .attr("width",  width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)
      .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

console.log("svg");
console.log(svg);

console.log("focus");
console.log(focus);

var focus = svg.append("g")
    .attr("transform", "translate(-100,-100)")  // make sure initial tool-tip circle is located outside (upper left) of the plot (svg element)
    .attr("class", "focus");



// query object used to set the HTTP GET query for the URI when the user clicks on a region/circle
var query_obj = query2obj();
delete query_obj.plot;
query_obj.table = "fast";


function mouseover(d) {
  // displays tip at center of voronoi region instead of near point
  // tip.show(d);

  console.log('mouseover');
  console.log(d);
  // doesn't work
  d.series.line.parentNode.appendChild(d.series.line);
  d3.select(d.series.line).classed("series-hover", true);

  // tip.attr("transform", "translate(" + x_scale(d.x) + "," + y_scale(d.y) + ")");
  console.log("transform", "translate(" + x_scale(d.x) + "," + y_scale(d.y) + ")");
  focus.attr("transform", "translate(" + x_scale(d.x) + "," + y_scale(d.y) + ")");
  series_name = d.series.name.length ? d.series.name : ylabel;
  tt = (xlabel.length ? xlabel : "bin") + ": " + d.x + "\u00A0\u00A0\u00A0\u00A0" + series_name + ": " + d.y;
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




    // var d3data = {{ data.d3data|safe }};

    // var xlabel = "{{ data.xlabel|escapejs }}";
    // var ylabel = "{{ data.ylabel|escapejs }}";

    var ans = arrays_as_d3_series(d3data);
    xlabel = new_xlabel.length ? new_xlabel : ans.xlabel;
    var ylabels = [ylabel];
    ylabel = new_ylabel.length ? new_ylabel : ans.ylabels[0];
    var data = ans.data;
    data.sort(function(a, b) { return a.x - b.x; });

        console.log('data_obj that contains the data bit')
        console.log(ans)
        console.log('d3data after grabbing data bit')
        console.log(data)
        console.log(data)

    var color = d3.scale.category10().domain(ans.ylabels);

    x_scale = d3.scale.linear().range([0, width]);
    // parse xdata as datetimes if the xlabel starts with the word "date" or "time" 
    if ((xlabel.substring(0, 4).toUpperCase() == "DATE") 
        // || (xlabel.substring(0, 4).toUpperCase() == "TIME")
      ) {
      x_scale = d3.time.scale().range([0, width]);
      
      data.forEach(function(d) { 
        console.log(d);
        console.log(d.x);
        d.x = d3_parse_date(d.x); }
        );
    }

    y_scale = d3.scale.linear().range([height, 0]);

    var xAxis = d3.svg.axis().scale(x_scale).orient("bottom");

    var yAxis = d3.svg.axis().scale(y_scale).orient("left");

    var voronoi = d3.geom.voronoi()
        .x(function(d) { return x_scale(d.x); })
        .y(function(d) { return y_scale(d.y); })
        .clipExtent([[-margin.left, -margin.top], [width + margin.right, height + margin.bottom]]);

    var line = d3.svg.line()
        .x(function(d) { return x_scale(d.x); })
        .y(function(d) { return y_scale(d.y); });



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


    x_scale.domain(d3.extent(data, function(d) { return d.x; }));

    y_scale.domain([
      d3.min(all_series, function(c) { return d3.min(c.values, function(v) { return v.y; }); }),
      d3.max(all_series, function(c) { return d3.max(c.values, function(v) { return v.y; }); })
    ]);

    svg.append("g")
        .attr("class", "y axis")
        .attr("transform", "translate(0," + height + ")")
        .call(xAxis)
      .append("text")
        .attr("y", y_scale.range()[1])
        .style("text-anchor", "end")
        .attr("x", x_scale.range()[1])
        .attr("dy", "-.3em")

        .text(xlabel);

    svg.append("g")
        .attr("class", "x axis")
        .call(yAxis)
      .append("text")
        .attr("transform", "rotate(-90)")
        .attr("y", 6)
        .attr("dy", ".7em")
        .style("text-anchor", "end")
        .text(ylabel);

    var series = svg.selectAll(".series")
        .data(all_series)
      .enter().append("g")
        .attr("class", "series");

    series.append("path")
        .attr("class", "line")
        .attr("d", function(d) { d.line=this; return line(d.values); })
        .style("stroke", function(d) { return color(d.name); });


    // legend
    series.append("text")
        .datum(function(d) { return { name: d.name, value: d.values[d.values.length - 1]}; })
        .attr("transform", function(d) { return "translate(" + x_scale(d.value.x) + "," + y_scale(d.value.y) + ")"; })
        .attr("x", 3)
        .attr("dy", ".35em")
        .text(function(d) { return d.name; });

    var voronoiGroup = svg.append("g")
        .attr("class", "voronoi");

    voronoiGroup.selectAll("path")
        .data(voronoi(d3.nest()
            .key(function(d) { return x_scale(d.x) + "," + y_scale(d.y); })
            .rollup(function(v) { return v[0]; })
            .entries(d3.merge(all_series.map(function(d) { return d.values; })))
            .map(function(d) { return d.values; })))
      .enter().append("path")
        .attr("d", function(d) { return "M" + d.join("L") + "Z"; })
        .datum(function(d) { return d.point; })
        .on("mouseover", mouseover)
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




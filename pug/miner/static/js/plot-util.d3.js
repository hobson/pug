function mouseover(d) {
  // displays tip at center of voronoi region instead of near point
  // tip.show(d);

  console.log('default plot-util mouseover() callback');
  console.log(d);

//  d.series.line.parentNode.appendChild(d.series.line);
  //d3.select(d.series.line).classed("series-hover", true);
}


function mouseout(d) {
  // tip.hide(d);
  console.log('default plot-util mouseout() callback');
  console.log(d);

  //d3.select(d.series.line).classed("series-hover", false);
}


function d3_parse_datetime(date_or_time) {
  // If date_or_time is an approximately valid ISO 8601 date-time string 
  // return a javascript Date instance.
  // Otherwise return null.
  var acceptable_formats = [
    "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%Z", "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%SZ", "%Y-%m-%d %H:%M:%S%Z", "%Y-%m-%d %H:%M:%S"];
  for (index = 0; index < acceptable_formats.length; index++) {
    format = acceptable_formats[index];
    dt = d3.time.format(format).parse(date_or_time);
    // console.log('parsed datetime:');
    console.log(dt);
    if (dt !== null)
      return dt;
  }
  return null;
}


function d3_parse_date(date) {
  // ISO8601-like:
  return d3.time.format("%Y-%m-%d").parse(date);
  // if (dt !== null)
  //   return dt;
  // dt = d3.time.format("%y%m%d").parse(date);
  // if (dt !== null)
  //   return dt;
  // dt = d3.time.format("%m/%d/%Y").parse(date);
  // if (dt !== null)
  //   return dt;
  // dt = d3.time.format("%m/%d/%y").parse(date);
  // if (dt !== null)
  //   return dt;
  // dt = d3.time.format("%y-%m-%d").parse(date);
  // return dt;
  // return null;
  }


// Expects d3data to be an array of arrays (columns of data)
// The first element of each array is it's label (header/name)
// Returns a d3-compatible object with an xlabel, ylabels = header with xlabel removed
// and data which is an array of objects with elements x and y (y attribute is named by the header/ylabels)
function arrays_as_d3_series(d3data) {
    // console.log('line-plot.js:arrays_as_d3_series(): d3data before transpose');
    // console.log(d3data);
    var ans = {};
    var transposed_d3data = d3.transpose(d3data);
    ans.header = transposed_d3data.shift();
    var N = transposed_d3data.length;
    var M = ans.header.length;
    var data = new Array(N);
    console.log("header in arrays_as_d3_series() of length " + N);
    console.log(ans.header);
    console.log(transposed_d3data);
    for (var i=0; i<N; i++) {
        data[i] = {};
        data[i].x = transposed_d3data[i][0];
        for (var k=1; k<M; k++) {
            data[i][ans['header'][k]] = transposed_d3data[i][k];
            }
        console.log(i + ': ' + data[i][ans['header'][0]]);
        }
    ans.data = data;
    // for some reason the order of elements here is shuffled
    // the last element overwrites the second
    console.log(ans['data']);

    ans.xlabel = ans['header'].shift();
    ans.ylabels = ans['header'];
    return ans;
    }


function arrays_as_object(columns) {
    var obj = {};
    for (i=0; i<columns.length; i++) {
        var column = columns[i];
        var name = column[0];
        obj[name] = new Array(column.length - 1);
        for (j=1; j<column.length; j++) {
            obj[name][j-1] = column[i][j];
        }
    }
    return obj;
}


function normalize_conf(d3data, conf) {
    default_conf         = {"plot_container_id": "plot_container", "container_width": 960, "container_height": 500, "margin": {top: 30, right: 80, bottom: 30, left: 50}};

    conf                   = typeof conf                   == "undefined" ? default_conf                                : conf;
    conf.plot_container_id = typeof conf.plot_container_id == "undefined" ? default_conf.plot_container_id              : conf.plot_container_id;
    conf.margin            = typeof conf.margin            == "undefined" ? default_conf.margin                         : conf.margin;
    conf.container_width   = typeof conf.container_width   == "undefined" ? default_conf.container_width                : conf.container_width;
    conf.container_height  = typeof conf.container_height  == "undefined" ? default_conf.container_height               : conf.container_height;
    conf.width             = typeof conf.width             == "undefined" ? conf.container_width - conf.margin.left - conf.margin.right  : conf.width;
    conf.height            = typeof conf.height            == "undefined" ? conf.container_height - conf.margin.top  - conf.margin.bottom : conf.height;

    conf.x_is_date         = typeof conf.x_is_date         == "undefined" ? default_conf.x_is_date                      : conf.x_is_date;

    conf.xlabel = typeof conf.xlabel == "undefined" ? d3data[0][0] : conf.xlabel;
    conf.xfield  = typeof d3data[0][0] == "string" ? d3data[0][0] : conf.xlabel;
    conf.ylabel = typeof conf.ylabel == "undefined" ? d3data[1][0] : conf.ylabel;

    ylabels = ((typeof conf.ylabel == "object") && (d3data.length == (1 + conf.ylabel.length))) ? conf.ylabel : d3data.slice(1).map(function(d) {return d[0];});
    conf.ylabels = ylabels;
    conf.num_layers = conf.ylabels.length;
    conf.color = d3.scale.category10().domain(conf.ylabels);

    // TODO: check for other types of x-axis values (floats, ints, dates, times) and produce the appropriate x-scale in an autoscale function
    // parse xdata as datetimes if the conf.xlabel starts with the word "date" or "time" 
    if (!conf.x_is_date && (conf.xlabel.substring(0, 4).toUpperCase() == "DATE"))
        // || (conf.xlabel.substring(0, 4).toUpperCase() == "TIME")
      conf.x_is_date = true;

    return conf;
    }


function arrays_as_objects(columns) {
    var objects = Array();
    for (var i=0; i<columns.length; i++) {
        var column = columns[i];
        var name = column[0];
        // console.log(name);
        for (var j=1; j<column.length; j++) {
            // console.log(' ' + i + ', ' + j + ', ' + objects.length );
            if (i === 0) { objects.push({}); }
            // console.log(objects[j-1]);
            objects[j-1][name] = column[j];
            // console.log(objects[j-1]);
        }
    }
    return objects;
}


function d3_series_as_xy_series(d3data, ylabels) {
    var all_series = ylabels.map(function(name) {
        var series = {
            name: name,
            values: null };
        series.values = d3data.map(function(d) {
            return {
                "series": series,
                "x": d["x"],
                "y": +d[name] }; // return {
            }); // d3data.map(function(d) {
        return series;
        });
    return all_series; }


function properties(d) {
    props = Array();
    for (var property in d) {
            if (d.hasOwnProperty(property)) {
                props.push(property);
            }
        }
    return props;
    }

function split_objects(d3data) {
    // convert an array of objects n arrays of objects, each with attributes like x, y, name, uri
    var stack = d3.layout.stack();
    var props = properties(d3data[0]);
    var n = props.length;  // number of dimensions or columns (in addition to the x coordinate)
    var m = d3data.length; // number of records
    layers = stack(d3.range(n).map(function(j) {
        var l = [];
        for (var i=0; i < m; i++) {
            l.push({"x": i, "y": d3data[j][props[i]], "y0": 0});
            //console.log('layers['+i+']['+j+'] = ' + obj + ' = ' + '(' + obj.x + ',' + obj.y + ',' + obj.y0 + ')');
        } // for i
        return l;
    })); // .map(function(j)
    return layers;
}

function split_d3_series(d3data) {
    // convert an array of arrays into an array of objects, each with attributes like x, y, name, uri
    var stack = d3.layout.stack();
    var n = d3data.length - 1;  // number of dimensions or columns (in addition to the x coordinate)
    var m = d3data[0].length - 1; // number of records
    layers = stack(d3.range(n).map(function(j) {
        var l = [];
        for (var i=0; i < m; i++) {
            l.push({"x": d3data[0][i+1], "y": d3data[j+1][i+1], "y0": 0});
            //console.log('layers['+i+']['+j+'] = ' + obj + ' = ' + '(' + obj.x + ',' + obj.y + ',' + obj.y0 + ')');
        } // for i
        return l;
    })); // .map(function(j)
    return layers;
}

function query2obj(query) {
  query = query ? query : location.search;
  // console.log(query);
  // ignore the questionmark in the search (query) string part of the URI
  if (query[0] == '?') {
    query = query.substring(1); }
  // console.log(query);
  query = query.replace(/%2C/g,",").replace(/%2B/g," ");
  // console.log(query);
  query = '{"' + decodeURI(query).replace(/"/g, '\\"').replace(/%2C/g,",").replace(/%2B/g," ").replace(/&/g, '","').replace(/=/g,'":"') + '"}';
  // deal with a zero-length or malformed query without any GET keys
  if (query.length > 4 && query.indexOf(':') > 1) {
    return JSON5.parse(query); }
  else { return {}; }
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


function create_svg_element(conf) {
    return d3.select("#" + conf.plot_container_id).append("svg")
                .attr("width",  conf.width + conf.margin.left + conf.margin.right)
                .attr("height", conf.height + conf.margin.top + conf.margin.bottom)
          .append("g")
            .attr("transform", "translate(" + conf.margin.left + "," + conf.margin.top + ")");
    }


function create_yaxis(conf) {
    console.log('--------- create yaxis() ------------');
    return d3.svg.axis().scale(conf.yscale).orient("left"); }


function create_xaxis(conf) {
    console.log('---------- create xaxis ------------');
    console.log(conf.xscale);
    var axis = d3.svg.axis().scale(conf.xscale).orient("bottom");
    axis = axis.ticks(10);
    var N = conf.d3data.length;
    var midlength = Math.round(N/2);
    axis.tickValues([conf.xmin, conf.xmax]);
    if (conf.x_is_date) {
        console.log('set tickFormat for dates in x-axis');
        axis.tickFormat(d3.time.format("%y-%m-%d"));
        }
    // console.log('xAxis ticks:');
    // console.log(axis.tickValues());
    console.log(axis.ticks());
    return axis;
}


// d3 selection method to move it to the top of the graphics layer stack (so it displays on top)
// Example:
//   `svg.select("circle").moveToFront();`
d3.selection.prototype.moveToFront = function() {
  return this.each(function(){
    this.parentNode.appendChild(this);
  });
};


function insert_text_background(focus) {
    var textElm = focus.select("text").node();
    // console.log(textElm);
    var SVGRect = textElm.getBBox();

    var rect = focus.insert("rect", "text")
      .attr("x", SVGRect.x).attr("y", SVGRect.y)
      .attr("width", SVGRect.width).attr("height", SVGRect.height)
      .attr("rx", 4).attr("ry", 4);
    rect.attr("class", "tooltip-box");
    return focus;
}

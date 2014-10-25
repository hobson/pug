function mouseover(d) {
  // displays tip at center of voronoi region instead of near point
  // tip.show(d);

  console.log('mouseover');
  console.log(d);

//  d.series.line.parentNode.appendChild(d.series.line);
  //d3.select(d.series.line).classed("series-hover", true);
}


function mouseout(d) {
  // tip.hide(d);
  console.log('mouseout')
  console.log(d);

  //d3.select(d.series.line).classed("series-hover", false);
}


function d3_parse_date(date_or_time) {
  return d3.time.format("%Y%m%d").parse(date_or_time);
}

// Expects d3data to be an array of arrays (columns of data)
// The first element of each array is it's label (header/name)
// Returns a d3-compatible object with an xlabel, ylabels = header with xlabel removed
// and data which is an array of objects with elements x and y (y attribute is named by the header/ylabels)
function arrays_as_d3_series(d3data) {
    console.log('line-plot.js:arrays_as_d3_series(): d3data before transpose');
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


function arrays_as_objects(columns) {
    var objects = Array();
    for (var i=0; i<columns.length; i++) {
        var column = columns[i];
        var name = column[0];
        console.log(name);
        for (var j=1; j<column.length; j++) {
            console.log(' ' + i + ', ' + j + ', ' + objects.length );
            if (i === 0) { objects.push({}); }
            console.log(objects[j-1]);
            objects[j-1][name] = column[j];
            console.log(objects[j-1]);
        }
    }
    return objects;
}

// FIXME: implement this:
function split_d3_series(d3data) {
    var stack = d3.layout.stack();
    var n = d3data.length - 1;  // number of dimensions or columns (in addition to the x coordinate)
    var m = d3data[0].length - 1; // number of records
    layers = stack(d3.range(n).map(function(j) {
        var l = [];
        for (var i=0; i < m; i++) {
            l.push({"x": i, "y": d3data[j+1][i+1], "y0": 0});
            //console.log('layers['+i+']['+j+'] = ' + obj + ' = ' + '(' + obj.x + ',' + obj.y + ',' + obj.y0 + ')');
        } // for i
        return l;
    })); // .map(function(j)
    return layers;
}

function query2obj(query) {
  query = query ? query : location.search;
  console.log(query);
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


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


// FIXME: implement this:
function split_d3_series(d3data) {
    var stack = d3.layout.stack();
    var n = d3data.length - 1;  // number of dimensions or columns (in addition to the x coordinate)
    var m = d3data[0].length - 1; // number of records
    layers = stack(d3.range(n).map(function(j) {
        l = new Array();
        for (var i=0; i < m; i++) {
            l.push({"x": i, "y": d3data[j+1][i+1], "y0": 0});
            //console.log('layers['+i+']['+j+'] = ' + obj + ' = ' + '(' + obj.x + ',' + obj.y + ',' + obj.y0 + ')');
        } // for i
        return l;
    })); // .map(function(j)
    return layers;
}
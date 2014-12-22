
function line_plot(d3data, conf) {
    console.log('==================== LINE PLOT =======================');
    conf = normalize_conf(d3data, conf);

    // THIS IS TO ALLOW PLOT TO BE CLICAKBLE and SEND USER to a TABLE VIEW OF THE REGION CLICKED
    // // retrieve the GET query from the URI of this page:
    // conf.query = query2obj();
    // // Change the query to request a table view instead of the plot view that got us to this page/plot
    // delete conf.query.plot;
    // conf.query.table = "fast";


    conf.xscale = d3.scale.linear().range([0, conf.width]);
    conf.yscale = d3.scale.linear().range([conf.height, 0]);

    function mouseover(d) {
      // displays tip at center of voronoi region instead of near point
      // tip.show(d);
      var focus = d3.select("g.focus");
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

      // // conf.query is a global dictionary of the query parameters for this page, previously obtained using plot-util.query2obj();
      // // Need to set the Lag window for the table query to a range likely to capture the points near where the user clicked:
      // conf.query.min_lag = d.x-5;
      // conf.query.max_lag = d.x+5;

      // This generates the right link, but the SVG doesn't respond to clicks on the circle or anywhere nearby
      focus.select("a").attr("xlink:href", "?"+obj2query(conf.query));
      console.log(focus.select("a"));
      console.log(focus.select("a").attr("xlink:href"));
      // FIXME: for this link to be visible/clickable the mouseout function has to be triggered when the mouse enters the circle and leaves the voronoi region
    }


    function mouseout(d) {
      var focus = d3.select("g.focus");
      // tip.hide(d);
      console.log('mouseout');
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
    function draw_plot(d3data, conf) {
        d3data = arrays_as_d3_series(d3data).data;
        console.log("line plot d3data after conversion to d3_series ...");
        console.log(d3data);

        if (conf.x_is_date) {
          // FIXME: Check that ALL the elements of the array are valid datetimes before replacing the data
          d3data.forEach(function(d) {
            dt = d3_parse_datetime(d["x"]);
            if (dt === null) {
                dt = d["x"]; }
            d["x"] = dt;
            }
            );

          conf.xmin = d3.min(d3data, function(d) { return d["x"]; });
          conf.xmax = d3.max(d3data, function(d) { return d["x"]; });
          console.log('xmin,xmax = ' + conf.xmin + ' , ' + conf.xmax );
          conf.xscale = d3.time.scale()
            .domain([conf.xmin, conf.xmax])
            .range([0, conf.width]);
        }
        else {
          // needed elsewhere, even though xscale.range doesn't use them:
          conf.xmin = d3.min(d3data, function(d) { return d["x"]; });
          conf.xmax = d3.max(d3data, function(d) { return d["x"]; });
          conf.xscale = d3.scale.ordinal()
            .domain(d3data.map(function(d) { return d.x; }))
            .rangePoints([0, conf.width]);
        } // if conf.x_is_date
        
        // don't sort until after date-time strings have been parsed
        d3data.sort(function(a, b) { return a.x - b.x; });
        console.log("after sorting...");
        console.log(d3data);


        conf.d3data = d3data;
        // console.log('line plot all_series');
        all_series = d3_series_as_xy_series(d3data, conf.ylabels);
        // console.log(all_series);
        
        // console.log(d3data.map(function(d) { return d.x; }));


        // console.log('xscale domain and range');
        // console.log(conf.xscale.domain());
        // console.log(conf.xscale.range());

        var ymin = d3.min(all_series, function(series) { return d3.min(series.values, function(d) { return d.y; }); });
        var ymax = d3.max(all_series, function(series) { return d3.max(series.values, function(d) { return d.y; }); });


        conf.yscale = d3.scale.linear()
            .domain([ymin, ymax])
            .range([conf.height, 0]);

        // console.log('xscaled x values');
        // console.log(d3data.map(function(d) { return [d.x, conf.xscale(d.x)] }));
        // console.log('yscaled x values');
        // console.log(d3data.map(function(d) { return [d.y, conf.yscale(d.y)] }));


        // To display mouseover tooltips, we need an SVG element in the DOM with a g.focus element 
        // to move and add text to within the mouseover/mouseout callbacks
        // TODO: use the element ID (conf.plot_container_id) to select it locally within the mouseover and mouseout functions
        var svg = create_svg_element(conf);

        // FIXME: use autoscale function to find domain/ranges that are approximately 0-100 or 0-1 or 0 to -1 or 0 to -100 and make percentages of them
        var yAxis = create_yaxis(conf);  //.ticks(10, "%");
        // console.log(yAxis);

        var xAxis = create_xaxis(conf);
        // console.log(xAxis(new Date('2014-01-01T01:02:03Z')));

        var voronoi = d3.geom.voronoi()
            .x(function(d) {
              // console.log("voronoi x"); console.log(conf.xscale(d.x));
              return conf.xscale(d.x); })
            .y(function(d) {
              // console.log("voronoi y"); console.log(conf.yscale(d.y)); 
              return conf.yscale(d.y); })
            .clipExtent([[-conf.margin.left, -conf.margin.top], [conf.width + conf.margin.right, conf.height + conf.margin.bottom]]);

        var line = d3.svg.line()
            .x(function(d) {
              // console.log("line x"); console.log(d.x); console.log(conf.xscale(d.x)); 
              return conf.xscale(d.x); })
            .y(function(d) {
              // console.log("line y"); console.log(d.y); console.log(conf.yscale(d.y)); 
              return conf.yscale(d.y); });

        console.log('drawing x axis');

        svg.append("g")
            .attr("class", "y axis")
            .attr("transform", "translate(0," + conf.height + ")")
            .call(xAxis)
          .append("text")
            .attr("y", conf.yscale.range()[1])
            .style("text-anchor", "end")
            .attr("x", conf.xscale.range()[conf.xscale.range().length-1])
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


        console.log('adding g elements for each series');
        var series = svg.selectAll(".series")
            .data(all_series)
          .enter().append("g")
            .attr("class", "series");

        console.log('drawing paths (lines)');
        series.append("path")
            .attr("class", "line")
            .attr("d", function(d) { d.line=this; return line(d.values); })
            .style("stroke", function(d) { return conf.color(d.name); });


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

        var focus = svg.append("g").attr("class", "focus")
            .attr("transform", "translate(" + -100 + "," + -100 + ")");

        focus = svg.select("g.focus");

        focus.append("text").attr("y", -12);

        focus.append("a").attr("xlink:href", "/")
          .append("circle").attr("r", 6.5).style("fill", "steelblue").style("fill-opacity", 0.3);
} // function line_plot

draw_plot(d3data, conf);
}




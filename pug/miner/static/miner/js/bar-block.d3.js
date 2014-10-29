function bar_plot(d3data, conf) {
    default_conf = {"plot_container_id": "plot_container", "margin": {top: 30, right: 80, bottom: 30, left: 50}}
    // FIXME: put all globals in a plot conf object/namespace
    console.log(conf);
    conf                   = typeof conf                   == "undefined" ? default_conf                   : conf;
    conf.plot_container_id = typeof conf.plot_container_id == "undefined" ? default_conf.plot_container_id : conf.plot_container_id;
    conf.margin            = typeof conf.margin            == "undefined" ? default_conf.margin            : conf.margin;
    conf.width  = 960 - conf.margin.left - conf.margin.right;
    conf.height = 500 - conf.margin.top  - conf.margin.bottom;

    console.log(d3data);
    d3data[0][0] = "name";
    d3data[1][0] = "value";
    d3data = arrays_as_objects(d3data);
    console.log(d3data);
    
    // conf.xscale = d3.scale.linear().range([0, conf.width]);
    // conf.xlabel = "Horizontal Value (Time?)";
    // conf.yscale = d3.scale.linear().range([conf.height, 0]);
    // conf.ylabel = "Vertical Value";

    var x = d3.scale.ordinal()
        .rangeRoundBands([0, conf.width], 0.1);

    var y = d3.scale.linear()
        .range([conf.height, 0]);

    var xAxis = d3.svg.axis()
        .scale(x)
        .orient("bottom");

    var yAxis = d3.svg.axis()
        .scale(y)
        .orient("left");

    var chart = d3.select(".chart")
        .attr("width", conf.width + conf.margin.left + conf.margin.right)
        .attr("height", conf.height + conf.margin.top + conf.margin.bottom)
      .append("g")
        .attr("transform", "translate(" + conf.margin.left + "," + conf.margin.top + ")");

    // d3.tsv("/static/miner/data.tsv", type, function(error, data) {
      console.log('done reading tsv file');
      console.log(typeof d3data);
      console.log(d3data);
      x.domain(d3data.map(function(d) { return d.name; }));
      y.domain([0, d3.max(d3data, function(d) { return d.value; })]);

      chart.append("g")
          .attr("class", "x axis")
          .attr("transform", "translate(0," + conf.height + ")")
          .call(xAxis);

      chart.append("g")
          .attr("class", "y axis")
          .call(yAxis);

      chart.selectAll(".bar")
          .data(d3data)
        .enter().append("rect")
          .attr("class", "bar")
          .attr("x", function(d) { return x(d.name); })
          .attr("y", function(d) { return y(d.value); })
          .attr("height", function(d) { return conf.height - y(d.value); })
          .attr("width", x.rangeBand());
    // });

    function type(d) {
      d.value = +d.value; // coerce to number
      return d;
    }
}
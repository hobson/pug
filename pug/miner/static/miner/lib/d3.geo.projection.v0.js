(function() {
  d3.geo.project = function(object, projection) {
    var stream = projection.stream;
    if (!stream) throw new Error("not yet supported");
    return (object && d3_geo_projectObjectType.hasOwnProperty(object.type) ? d3_geo_projectObjectType[object.type] : d3_geo_projectGeometry)(object, stream);
  };
  function d3_geo_projectFeature(object, stream) {
    return {
      type: "Feature",
      id: object.id,
      properties: object.properties,
      geometry: d3_geo_projectGeometry(object.geometry, stream)
    };
  }
  function d3_geo_projectGeometry(geometry, stream) {
    if (!geometry) return null;
    if (geometry.type === "GeometryCollection") return {
      type: "GeometryCollection",
      geometries: object.geometries.map(function(geometry) {
        return d3_geo_projectGeometry(geometry, stream);
      })
    };
    if (!d3_geo_projectGeometryType.hasOwnProperty(geometry.type)) return null;
    var sink = d3_geo_projectGeometryType[geometry.type];
    d3.geo.stream(geometry, stream(sink));
    return sink.result();
  }
  var d3_geo_projectObjectType = {
    Feature: d3_geo_projectFeature,
    FeatureCollection: function(object, stream) {
      return {
        type: "FeatureCollection",
        features: object.features.map(function(feature) {
          return d3_geo_projectFeature(feature, stream);
        })
      };
    }
  };
  var d3_geo_projectPoints = [], d3_geo_projectLines = [];
  var d3_geo_projectPoint = {
    point: function(x, y) {
      d3_geo_projectPoints.push([ x, y ]);
    },
    result: function() {
      var result = !d3_geo_projectPoints.length ? null : d3_geo_projectPoints.length < 2 ? {
        type: "Point",
        coordinates: d3_geo_projectPoints[0]
      } : {
        type: "MultiPoint",
        coordinates: d3_geo_projectPoints
      };
      d3_geo_projectPoints = [];
      return result;
    }
  };
  var d3_geo_projectLine = {
    lineStart: d3_geo_projectNoop,
    point: function(x, y) {
      d3_geo_projectPoints.push([ x, y ]);
    },
    lineEnd: function() {
      if (d3_geo_projectPoints.length) d3_geo_projectLines.push(d3_geo_projectPoints), 
      d3_geo_projectPoints = [];
    },
    result: function() {
      var result = !d3_geo_projectLines.length ? null : d3_geo_projectLines.length < 2 ? {
        type: "LineString",
        coordinates: d3_geo_projectLines[0]
      } : {
        type: "MultiLineString",
        coordinates: d3_geo_projectLines
      };
      d3_geo_projectLines = [];
      return result;
    }
  };
  var d3_geo_projectPolygon = {
    polygonStart: d3_geo_projectNoop,
    lineStart: d3_geo_projectNoop,
    point: function(x, y) {
      d3_geo_projectPoints.push([ x, y ]);
    },
    lineEnd: function() {
      var n = d3_geo_projectPoints.length;
      if (n) {
        do d3_geo_projectPoints.push(d3_geo_projectPoints[0].slice()); while (++n < 4);
        d3_geo_projectLines.push(d3_geo_projectPoints), d3_geo_projectPoints = [];
      }
    },
    polygonEnd: d3_geo_projectNoop,
    result: function() {
      if (!d3_geo_projectLines.length) return null;
      var polygons = [], holes = [];
      d3_geo_projectLines.forEach(function(ring) {
        if (d3_geo_projectClockwise(ring)) polygons.push([ ring ]); else holes.push(ring);
      });
      holes.forEach(function(hole) {
        var point = hole[0];
        polygons.some(function(polygon) {
          if (d3_geo_projectContains(polygon[0], point)) {
            polygon.push(hole);
            return true;
          }
        }) || polygons.push([ hole ]);
      });
      d3_geo_projectLines = [];
      return !polygons.length ? null : polygons.length > 1 ? {
        type: "MultiPolygon",
        coordinates: polygons
      } : {
        type: "Polygon",
        coordinates: polygons[0]
      };
    }
  };
  var d3_geo_projectGeometryType = {
    Point: d3_geo_projectPoint,
    MultiPoint: d3_geo_projectPoint,
    LineString: d3_geo_projectLine,
    MultiLineString: d3_geo_projectLine,
    Polygon: d3_geo_projectPolygon,
    MultiPolygon: d3_geo_projectPolygon
  };
  function d3_geo_projectNoop() {}
  function d3_geo_projectClockwise(ring) {
    if ((n = ring.length) < 4) return false;
    var i = 0, n, area = ring[n - 1][1] * ring[0][0] - ring[n - 1][0] * ring[0][1];
    while (++i < n) area += ring[i - 1][1] * ring[i][0] - ring[i - 1][0] * ring[i][1];
    return area <= 0;
  }
  function d3_geo_projectContains(ring, point) {
    var x = point[0], y = point[1], contains = false;
    for (var i = 0, n = ring.length, j = n - 1; i < n; j = i++) {
      var pi = ring[i], xi = pi[0], yi = pi[1], pj = ring[j], xj = pj[0], yj = pj[1];
      if (yi > y ^ yj > y && x < (xj - xi) * (y - yi) / (yj - yi) + xi) contains = !contains;
    }
    return contains;
  }
  var Îµ = 1e-6, Îµ2 = Îµ * Îµ, Ï€ = Math.PI, halfÏ€ = Ï€ / 2, sqrtÏ€ = Math.sqrt(Ï€), radians = Ï€ / 180, degrees = 180 / Ï€;
  function sinci(x) {
    return x ? x / Math.sin(x) : 1;
  }
  function sgn(x) {
    return x > 0 ? 1 : x < 0 ? -1 : 0;
  }
  function asin(x) {
    return x > 1 ? halfÏ€ : x < -1 ? -halfÏ€ : Math.asin(x);
  }
  function acos(x) {
    return x > 1 ? 0 : x < -1 ? Ï€ : Math.acos(x);
  }
  function asqrt(x) {
    return x > 0 ? Math.sqrt(x) : 0;
  }
  var projection = d3.geo.projection, projectionMutator = d3.geo.projectionMutator;
  d3.geo.interrupt = function(project) {
    var lobes = [ [ [ [ -Ï€, 0 ], [ 0, halfÏ€ ], [ Ï€, 0 ] ] ], [ [ [ -Ï€, 0 ], [ 0, -halfÏ€ ], [ Ï€, 0 ] ] ] ];
    var bounds;
    function forward(Î», Ï†) {
      var sign = Ï† < 0 ? -1 : +1, hemilobes = lobes[+(Ï† < 0)];
      for (var i = 0, n = hemilobes.length - 1; i < n && Î» > hemilobes[i][2][0]; ++i) ;
      var coordinates = project(Î» - hemilobes[i][1][0], Ï†);
      coordinates[0] += project(hemilobes[i][1][0], sign * Ï† > sign * hemilobes[i][0][1] ? hemilobes[i][0][1] : Ï†)[0];
      return coordinates;
    }
    function reset() {
      bounds = lobes.map(function(hemilobes) {
        return hemilobes.map(function(lobe) {
          var x0 = project(lobe[0][0], lobe[0][1])[0], x1 = project(lobe[2][0], lobe[2][1])[0], y0 = project(lobe[1][0], lobe[0][1])[1], y1 = project(lobe[1][0], lobe[1][1])[1], t;
          if (y0 > y1) t = y0, y0 = y1, y1 = t;
          return [ [ x0, y0 ], [ x1, y1 ] ];
        });
      });
    }
    if (project.invert) forward.invert = function(x, y) {
      var hemibounds = bounds[+(y < 0)], hemilobes = lobes[+(y < 0)];
      for (var i = 0, n = hemibounds.length; i < n; ++i) {
        var b = hemibounds[i];
        if (b[0][0] <= x && x < b[1][0] && b[0][1] <= y && y < b[1][1]) {
          var coordinates = project.invert(x - project(hemilobes[i][1][0], 0)[0], y);
          coordinates[0] += hemilobes[i][1][0];
          return pointEqual(forward(coordinates[0], coordinates[1]), [ x, y ]) ? coordinates : null;
        }
      }
    };
    var projection = d3.geo.projection(forward), stream_ = projection.stream;
    projection.stream = function(stream) {
      var rotate = projection.rotate(), rotateStream = stream_(stream), sphereStream = (projection.rotate([ 0, 0 ]), 
      stream_(stream));
      projection.rotate(rotate);
      rotateStream.sphere = function() {
        d3.geo.stream(sphere(), sphereStream);
      };
      return rotateStream;
    };
    projection.lobes = function(_) {
      if (!arguments.length) return lobes.map(function(lobes) {
        return lobes.map(function(lobe) {
          return [ [ lobe[0][0] * 180 / Ï€, lobe[0][1] * 180 / Ï€ ], [ lobe[1][0] * 180 / Ï€, lobe[1][1] * 180 / Ï€ ], [ lobe[2][0] * 180 / Ï€, lobe[2][1] * 180 / Ï€ ] ];
        });
      });
      lobes = _.map(function(lobes) {
        return lobes.map(function(lobe) {
          return [ [ lobe[0][0] * Ï€ / 180, lobe[0][1] * Ï€ / 180 ], [ lobe[1][0] * Ï€ / 180, lobe[1][1] * Ï€ / 180 ], [ lobe[2][0] * Ï€ / 180, lobe[2][1] * Ï€ / 180 ] ];
        });
      });
      reset();
      return projection;
    };
    function sphere() {
      var Îµ = 1e-6, coordinates = [];
      for (var i = 0, n = lobes[0].length; i < n; ++i) {
        var lobe = lobes[0][i], Î»0 = lobe[0][0] * 180 / Ï€, Ï†0 = lobe[0][1] * 180 / Ï€, Ï†1 = lobe[1][1] * 180 / Ï€, Î»2 = lobe[2][0] * 180 / Ï€, Ï†2 = lobe[2][1] * 180 / Ï€;
        coordinates.push(resample([ [ Î»0 + Îµ, Ï†0 + Îµ ], [ Î»0 + Îµ, Ï†1 - Îµ ], [ Î»2 - Îµ, Ï†1 - Îµ ], [ Î»2 - Îµ, Ï†2 + Îµ ] ], 30));
      }
      for (var i = lobes[1].length - 1; i >= 0; --i) {
        var lobe = lobes[1][i], Î»0 = lobe[0][0] * 180 / Ï€, Ï†0 = lobe[0][1] * 180 / Ï€, Ï†1 = lobe[1][1] * 180 / Ï€, Î»2 = lobe[2][0] * 180 / Ï€, Ï†2 = lobe[2][1] * 180 / Ï€;
        coordinates.push(resample([ [ Î»2 - Îµ, Ï†2 - Îµ ], [ Î»2 - Îµ, Ï†1 + Îµ ], [ Î»0 + Îµ, Ï†1 + Îµ ], [ Î»0 + Îµ, Ï†0 - Îµ ] ], 30));
      }
      return {
        type: "Polygon",
        coordinates: [ d3.merge(coordinates) ]
      };
    }
    function resample(coordinates, m) {
      var i = -1, n = coordinates.length, p0 = coordinates[0], p1, dx, dy, resampled = [];
      while (++i < n) {
        p1 = coordinates[i];
        dx = (p1[0] - p0[0]) / m;
        dy = (p1[1] - p0[1]) / m;
        for (var j = 0; j < m; ++j) resampled.push([ p0[0] + j * dx, p0[1] + j * dy ]);
        p0 = p1;
      }
      resampled.push(p1);
      return resampled;
    }
    function pointEqual(a, b) {
      return Math.abs(a[0] - b[0]) < Îµ && Math.abs(a[1] - b[1]) < Îµ;
    }
    return projection;
  };
  function airy(Î²) {
    var tanÎ²_2 = Math.tan(.5 * Î²), B = 2 * Math.log(Math.cos(.5 * Î²)) / (tanÎ²_2 * tanÎ²_2);
    function forward(Î», Ï†) {
      var cosÎ» = Math.cos(Î»), cosÏ† = Math.cos(Ï†), sinÏ† = Math.sin(Ï†), cosz = cosÏ† * cosÎ», K = -((1 - cosz ? Math.log(.5 * (1 + cosz)) / (1 - cosz) : -.5) + B / (1 + cosz));
      return [ K * cosÏ† * Math.sin(Î»), K * sinÏ† ];
    }
    forward.invert = function(x, y) {
      var Ï = Math.sqrt(x * x + y * y), z = Î² * -.5, i = 50, Î´;
      if (!Ï) return [ 0, 0 ];
      do {
        var z_2 = .5 * z, cosz_2 = Math.cos(z_2), sinz_2 = Math.sin(z_2), tanz_2 = Math.tan(z_2), lnsecz_2 = Math.log(1 / cosz_2);
        z -= Î´ = (2 / tanz_2 * lnsecz_2 - B * tanz_2 - Ï) / (-lnsecz_2 / (sinz_2 * sinz_2) + 1 - B / (2 * cosz_2 * cosz_2));
      } while (Math.abs(Î´) > Îµ && --i > 0);
      var sinz = Math.sin(z);
      return [ Math.atan2(x * sinz, Ï * Math.cos(z)), asin(y * sinz / Ï) ];
    };
    return forward;
  }
  function airyProjection() {
    var Î² = halfÏ€, m = projectionMutator(airy), p = m(Î²);
    p.radius = function(_) {
      if (!arguments.length) return Î² / Ï€ * 180;
      return m(Î² = _ * Ï€ / 180);
    };
    return p;
  }
  (d3.geo.airy = airyProjection).raw = airy;
  function aitoff(Î», Ï†) {
    var cosÏ† = Math.cos(Ï†), sinciÎ± = sinci(acos(cosÏ† * Math.cos(Î» /= 2)));
    return [ 2 * cosÏ† * Math.sin(Î») * sinciÎ±, Math.sin(Ï†) * sinciÎ± ];
  }
  aitoff.invert = function(x, y) {
    if (x * x + 4 * y * y > Ï€ * Ï€ + Îµ) return;
    var Î» = x, Ï† = y, i = 25;
    do {
      var sinÎ» = Math.sin(Î»), sinÎ»_2 = Math.sin(Î» / 2), cosÎ»_2 = Math.cos(Î» / 2), sinÏ† = Math.sin(Ï†), cosÏ† = Math.cos(Ï†), sin_2Ï† = Math.sin(2 * Ï†), sin2Ï† = sinÏ† * sinÏ†, cos2Ï† = cosÏ† * cosÏ†, sin2Î»_2 = sinÎ»_2 * sinÎ»_2, C = 1 - cos2Ï† * cosÎ»_2 * cosÎ»_2, E = C ? acos(cosÏ† * cosÎ»_2) * Math.sqrt(F = 1 / C) : F = 0, F, fx = 2 * E * cosÏ† * sinÎ»_2 - x, fy = E * sinÏ† - y, Î´xÎ´Î» = F * (cos2Ï† * sin2Î»_2 + E * cosÏ† * cosÎ»_2 * sin2Ï†), Î´xÎ´Ï† = F * (.5 * sinÎ» * sin_2Ï† - E * 2 * sinÏ† * sinÎ»_2), Î´yÎ´Î» = F * .25 * (sin_2Ï† * sinÎ»_2 - E * sinÏ† * cos2Ï† * sinÎ»), Î´yÎ´Ï† = F * (sin2Ï† * cosÎ»_2 + E * sin2Î»_2 * cosÏ†), denominator = Î´xÎ´Ï† * Î´yÎ´Î» - Î´yÎ´Ï† * Î´xÎ´Î»;
      if (!denominator) break;
      var Î´Î» = (fy * Î´xÎ´Ï† - fx * Î´yÎ´Ï†) / denominator, Î´Ï† = (fx * Î´yÎ´Î» - fy * Î´xÎ´Î») / denominator;
      Î» -= Î´Î», Ï† -= Î´Ï†;
    } while ((Math.abs(Î´Î») > Îµ || Math.abs(Î´Ï†) > Îµ) && --i > 0);
    return [ Î», Ï† ];
  };
  (d3.geo.aitoff = function() {
    return projection(aitoff);
  }).raw = aitoff;
  function armadillo(Ï†0) {
    var sinÏ†0 = Math.sin(Ï†0), cosÏ†0 = Math.cos(Ï†0), sÏ†0 = Ï†0 > 0 ? 1 : -1, tanÏ†0 = Math.tan(sÏ†0 * Ï†0), k = (1 + sinÏ†0 - cosÏ†0) / 2;
    function forward(Î», Ï†) {
      var cosÏ† = Math.cos(Ï†), cosÎ» = Math.cos(Î» /= 2);
      return [ (1 + cosÏ†) * Math.sin(Î»), (sÏ†0 * Ï† > -Math.atan2(cosÎ», tanÏ†0) - .001 ? 0 : -sÏ†0 * 10) + k + Math.sin(Ï†) * cosÏ†0 - (1 + cosÏ†) * sinÏ†0 * cosÎ» ];
    }
    forward.invert = function(x, y) {
      var Î» = 0, Ï† = 0, i = 50;
      do {
        var cosÎ» = Math.cos(Î»), sinÎ» = Math.sin(Î»), cosÏ† = Math.cos(Ï†), sinÏ† = Math.sin(Ï†), A = 1 + cosÏ†, fx = A * sinÎ» - x, fy = k + sinÏ† * cosÏ†0 - A * sinÏ†0 * cosÎ» - y, Î´xÎ´Î» = .5 * A * cosÎ», Î´xÎ´Ï† = -sinÎ» * sinÏ†, Î´yÎ´Î» = .5 * sinÏ†0 * A * sinÎ», Î´yÎ´Ï† = cosÏ†0 * cosÏ† + sinÏ†0 * cosÎ» * sinÏ†, denominator = Î´xÎ´Ï† * Î´yÎ´Î» - Î´yÎ´Ï† * Î´xÎ´Î», Î´Î» = .5 * (fy * Î´xÎ´Ï† - fx * Î´yÎ´Ï†) / denominator, Î´Ï† = (fx * Î´yÎ´Î» - fy * Î´xÎ´Î») / denominator;
        Î» -= Î´Î», Ï† -= Î´Ï†;
      } while ((Math.abs(Î´Î») > Îµ || Math.abs(Î´Ï†) > Îµ) && --i > 0);
      return sÏ†0 * Ï† > -Math.atan2(Math.cos(Î»), tanÏ†0) - .001 ? [ Î» * 2, Ï† ] : null;
    };
    return forward;
  }
  function armadilloProjection() {
    var Ï†0 = Ï€ / 9, sÏ†0 = Ï†0 > 0 ? 1 : -1, tanÏ†0 = Math.tan(sÏ†0 * Ï†0), m = projectionMutator(armadillo), p = m(Ï†0), stream_ = p.stream;
    p.parallel = function(_) {
      if (!arguments.length) return Ï†0 / Ï€ * 180;
      tanÏ†0 = Math.tan((sÏ†0 = (Ï†0 = _ * Ï€ / 180) > 0 ? 1 : -1) * Ï†0);
      return m(Ï†0);
    };
    p.stream = function(stream) {
      var rotate = p.rotate(), rotateStream = stream_(stream), sphereStream = (p.rotate([ 0, 0 ]), 
      stream_(stream));
      p.rotate(rotate);
      rotateStream.sphere = function() {
        sphereStream.polygonStart(), sphereStream.lineStart();
        for (var Î» = sÏ†0 * -180; sÏ†0 * Î» < 180; Î» += sÏ†0 * 90) sphereStream.point(Î», sÏ†0 * 90);
        while (sÏ†0 * (Î» -= Ï†0) >= -180) {
          sphereStream.point(Î», sÏ†0 * -Math.atan2(Math.cos(Î» * radians / 2), tanÏ†0) * degrees);
        }
        sphereStream.lineEnd(), sphereStream.polygonEnd();
      };
      return rotateStream;
    };
    return p;
  }
  (d3.geo.armadillo = armadilloProjection).raw = armadillo;
  function tanh(x) {
    x = Math.exp(2 * x);
    return (x - 1) / (x + 1);
  }
  function sinh(x) {
    return .5 * (Math.exp(x) - Math.exp(-x));
  }
  function cosh(x) {
    return .5 * (Math.exp(x) + Math.exp(-x));
  }
  function arsinh(x) {
    return Math.log(x + asqrt(x * x + 1));
  }
  function arcosh(x) {
    return Math.log(x + asqrt(x * x - 1));
  }
  function august(Î», Ï†) {
    var tanÏ† = Math.tan(Ï† / 2), k = asqrt(1 - tanÏ† * tanÏ†), c = 1 + k * Math.cos(Î» /= 2), x = Math.sin(Î») * k / c, y = tanÏ† / c, x2 = x * x, y2 = y * y;
    return [ 4 / 3 * x * (3 + x2 - 3 * y2), 4 / 3 * y * (3 + 3 * x2 - y2) ];
  }
  august.invert = function(x, y) {
    x *= 3 / 8, y *= 3 / 8;
    if (!x && Math.abs(y) > 1) return null;
    var x2 = x * x, y2 = y * y, s = 1 + x2 + y2, sin3Î· = Math.sqrt(.5 * (s - Math.sqrt(s * s - 4 * y * y))), Î· = asin(sin3Î·) / 3, Î¾ = sin3Î· ? arcosh(Math.abs(y / sin3Î·)) / 3 : arsinh(Math.abs(x)) / 3, cosÎ· = Math.cos(Î·), coshÎ¾ = cosh(Î¾), d = coshÎ¾ * coshÎ¾ - cosÎ· * cosÎ·;
    return [ sgn(x) * 2 * Math.atan2(sinh(Î¾) * cosÎ·, .25 - d), sgn(y) * 2 * Math.atan2(coshÎ¾ * Math.sin(Î·), .25 + d) ];
  };
  (d3.geo.august = function() {
    return projection(august);
  }).raw = august;
  var bakerÏ† = Math.log(1 + Math.SQRT2);
  function baker(Î», Ï†) {
    var Ï†0 = Math.abs(Ï†);
    return Ï†0 < Ï€ / 4 ? [ Î», Math.log(Math.tan(Ï€ / 4 + Ï† / 2)) ] : [ Î» * Math.cos(Ï†0) * (2 * Math.SQRT2 - 1 / Math.sin(Ï†0)), sgn(Ï†) * (2 * Math.SQRT2 * (Ï†0 - Ï€ / 4) - Math.log(Math.tan(Ï†0 / 2))) ];
  }
  baker.invert = function(x, y) {
    if ((y0 = Math.abs(y)) < bakerÏ†) return [ x, 2 * Math.atan(Math.exp(y)) - halfÏ€ ];
    var sqrt8 = Math.sqrt(8), Ï† = Ï€ / 4, i = 25, Î´, y0;
    do {
      var cosÏ†_2 = Math.cos(Ï† / 2), tanÏ†_2 = Math.tan(Ï† / 2);
      Ï† -= Î´ = (sqrt8 * (Ï† - Ï€ / 4) - Math.log(tanÏ†_2) - y0) / (sqrt8 - .5 * cosÏ†_2 * cosÏ†_2 / tanÏ†_2);
    } while (Math.abs(Î´) > Îµ2 && --i > 0);
    return [ x / (Math.cos(Ï†) * (sqrt8 - 1 / Math.sin(Ï†))), sgn(y) * Ï† ];
  };
  (d3.geo.baker = function() {
    return projection(baker);
  }).raw = baker;
  var berghausAzimuthalEquidistant = d3.geo.azimuthalEquidistant.raw;
  function berghaus(n) {
    var k = 2 * Ï€ / n;
    function forward(Î», Ï†) {
      var p = berghausAzimuthalEquidistant(Î», Ï†);
      if (Math.abs(Î») > halfÏ€) {
        var Î¸ = Math.atan2(p[1], p[0]), r = Math.sqrt(p[0] * p[0] + p[1] * p[1]), Î¸0 = k * Math.round((Î¸ - halfÏ€) / k) + halfÏ€, Î± = Math.atan2(Math.sin(Î¸ -= Î¸0), 2 - Math.cos(Î¸));
        Î¸ = Î¸0 + asin(Ï€ / r * Math.sin(Î±)) - Î±;
        p[0] = r * Math.cos(Î¸);
        p[1] = r * Math.sin(Î¸);
      }
      return p;
    }
    forward.invert = function(x, y) {
      var r = Math.sqrt(x * x + y * y);
      if (r > halfÏ€) {
        var Î¸ = Math.atan2(y, x), Î¸0 = k * Math.round((Î¸ - halfÏ€) / k) + halfÏ€, s = Î¸ > Î¸0 ? -1 : 1, A = r * Math.cos(Î¸0 - Î¸), cotÎ± = 1 / Math.tan(s * Math.acos((A - Ï€) / Math.sqrt(Ï€ * (Ï€ - 2 * A) + r * r)));
        Î¸ = Î¸0 + 2 * Math.atan((cotÎ± + s * Math.sqrt(cotÎ± * cotÎ± - 3)) / 3);
        x = r * Math.cos(Î¸), y = r * Math.sin(Î¸);
      }
      return berghausAzimuthalEquidistant.invert(x, y);
    };
    return forward;
  }
  function berghausProjection() {
    var n = 5, m = projectionMutator(berghaus), p = m(n), stream_ = p.stream, Îµ = .01, cr = -Math.cos(Îµ * radians), sr = Math.sin(Îµ * radians);
    p.lobes = function(_) {
      if (!arguments.length) return n;
      return m(n = +_);
    };
    p.stream = function(stream) {
      var rotate = p.rotate(), rotateStream = stream_(stream), sphereStream = (p.rotate([ 0, 0 ]), 
      stream_(stream));
      p.rotate(rotate);
      rotateStream.sphere = function() {
        sphereStream.polygonStart(), sphereStream.lineStart();
        for (var i = 0, Î´ = 360 / n, Î´0 = 2 * Ï€ / n, Ï† = 90 - 180 / n, Ï†0 = halfÏ€; i < n; ++i, 
        Ï† -= Î´, Ï†0 -= Î´0) {
          sphereStream.point(Math.atan2(sr * Math.cos(Ï†0), cr) * degrees, asin(sr * Math.sin(Ï†0)) * degrees);
          if (Ï† < -90) {
            sphereStream.point(-90, -180 - Ï† - Îµ);
            sphereStream.point(-90, -180 - Ï† + Îµ);
          } else {
            sphereStream.point(90, Ï† + Îµ);
            sphereStream.point(90, Ï† - Îµ);
          }
        }
        sphereStream.lineEnd(), sphereStream.polygonEnd();
      };
      return rotateStream;
    };
    return p;
  }
  (d3.geo.berghaus = berghausProjection).raw = berghaus;
  function mollweideBromleyÎ¸(Cp) {
    return function(Î¸) {
      var CpsinÎ¸ = Cp * Math.sin(Î¸), i = 30, Î´;
      do Î¸ -= Î´ = (Î¸ + Math.sin(Î¸) - CpsinÎ¸) / (1 + Math.cos(Î¸)); while (Math.abs(Î´) > Îµ && --i > 0);
      return Î¸ / 2;
    };
  }
  function mollweideBromley(Cx, Cy, Cp) {
    var Î¸ = mollweideBromleyÎ¸(Cp);
    function forward(Î», Ï†) {
      return [ Cx * Î» * Math.cos(Ï† = Î¸(Ï†)), Cy * Math.sin(Ï†) ];
    }
    forward.invert = function(x, y) {
      var Î¸ = asin(y / Cy);
      return [ x / (Cx * Math.cos(Î¸)), asin((2 * Î¸ + Math.sin(2 * Î¸)) / Cp) ];
    };
    return forward;
  }
  var mollweideÎ¸ = mollweideBromleyÎ¸(Ï€), mollweide = mollweideBromley(Math.SQRT2 / halfÏ€, Math.SQRT2, Ï€);
  (d3.geo.mollweide = function() {
    return projection(mollweide);
  }).raw = mollweide;
  function boggs(Î», Ï†) {
    var k = 2.00276, Î¸ = mollweideÎ¸(Ï†);
    return [ k * Î» / (1 / Math.cos(Ï†) + 1.11072 / Math.cos(Î¸)), (Ï† + Math.SQRT2 * Math.sin(Î¸)) / k ];
  }
  boggs.invert = function(x, y) {
    var k = 2.00276, ky = k * y, Î¸ = y < 0 ? -Ï€ / 4 : Ï€ / 4, i = 25, Î´, Ï†;
    do {
      Ï† = ky - Math.SQRT2 * Math.sin(Î¸);
      Î¸ -= Î´ = (Math.sin(2 * Î¸) + 2 * Î¸ - Ï€ * Math.sin(Ï†)) / (2 * Math.cos(2 * Î¸) + 2 + Ï€ * Math.cos(Ï†) * Math.SQRT2 * Math.cos(Î¸));
    } while (Math.abs(Î´) > Îµ && --i > 0);
    Ï† = ky - Math.SQRT2 * Math.sin(Î¸);
    return [ x * (1 / Math.cos(Ï†) + 1.11072 / Math.cos(Î¸)) / k, Ï† ];
  };
  (d3.geo.boggs = function() {
    return projection(boggs);
  }).raw = boggs;
  function parallel1Projection(projectAt) {
    var Ï†0 = 0, m = projectionMutator(projectAt), p = m(Ï†0);
    p.parallel = function(_) {
      if (!arguments.length) return Ï†0 / Ï€ * 180;
      return m(Ï†0 = _ * Ï€ / 180);
    };
    return p;
  }
  function sinusoidal(Î», Ï†) {
    return [ Î» * Math.cos(Ï†), Ï† ];
  }
  sinusoidal.invert = function(x, y) {
    return [ x / Math.cos(y), y ];
  };
  (d3.geo.sinusoidal = function() {
    return projection(sinusoidal);
  }).raw = sinusoidal;
  function bonne(Ï†0) {
    if (!Ï†0) return sinusoidal;
    var cotÏ†0 = 1 / Math.tan(Ï†0);
    function forward(Î», Ï†) {
      var Ï = cotÏ†0 + Ï†0 - Ï†, E = Ï ? Î» * Math.cos(Ï†) / Ï : Ï;
      return [ Ï * Math.sin(E), cotÏ†0 - Ï * Math.cos(E) ];
    }
    forward.invert = function(x, y) {
      var Ï = Math.sqrt(x * x + (y = cotÏ†0 - y) * y), Ï† = cotÏ†0 + Ï†0 - Ï;
      return [ Ï / Math.cos(Ï†) * Math.atan2(x, y), Ï† ];
    };
    return forward;
  }
  (d3.geo.bonne = function() {
    return parallel1Projection(bonne).parallel(45);
  }).raw = bonne;
  var bromley = mollweideBromley(1, 4 / Ï€, Ï€);
  (d3.geo.bromley = function() {
    return projection(bromley);
  }).raw = bromley;
  function chamberlin(points) {
    points = points.map(function(p) {
      return [ p[0], p[1], Math.sin(p[1]), Math.cos(p[1]) ];
    });
    for (var a = points[2], b, i = 0; i < 3; ++i, a = b) {
      b = points[i];
      a.v = chamberlinDistanceAzimuth(b[1] - a[1], a[3], a[2], b[3], b[2], b[0] - a[0]);
      a.point = [ 0, 0 ];
    }
    var Î²0 = chamberlinAngle(points[0].v[0], points[2].v[0], points[1].v[0]), Î²1 = chamberlinAngle(points[0].v[0], points[1].v[0], points[2].v[0]), Î²2 = Ï€ - Î²0;
    points[2].point[1] = 0;
    points[0].point[0] = -(points[1].point[0] = .5 * points[0].v[0]);
    var mean = [ points[2].point[0] = points[0].point[0] + points[2].v[0] * Math.cos(Î²0), 2 * (points[0].point[1] = points[1].point[1] = points[2].v[0] * Math.sin(Î²0)) ];
    function forward(Î», Ï†) {
      var sinÏ† = Math.sin(Ï†), cosÏ† = Math.cos(Ï†), v = new Array(3);
      for (var i = 0; i < 3; ++i) {
        var p = points[i];
        v[i] = chamberlinDistanceAzimuth(Ï† - p[1], p[3], p[2], cosÏ†, sinÏ†, Î» - p[0]);
        if (!v[i][0]) return p.point;
        v[i][1] = chamberlinLongitude(v[i][1] - p.v[1]);
      }
      var point = mean.slice();
      for (var i = 0; i < 3; ++i) {
        var j = i == 2 ? 0 : i + 1;
        var a = chamberlinAngle(points[i].v[0], v[i][0], v[j][0]);
        if (v[i][1] < 0) a = -a;
        if (!i) {
          point[0] += v[i][0] * Math.cos(a);
          point[1] -= v[i][0] * Math.sin(a);
        } else if (i == 1) {
          a = Î²1 - a;
          point[0] -= v[i][0] * Math.cos(a);
          point[1] -= v[i][0] * Math.sin(a);
        } else {
          a = Î²2 - a;
          point[0] += v[i][0] * Math.cos(a);
          point[1] += v[i][0] * Math.sin(a);
        }
      }
      point[0] /= 3, point[1] /= 3;
      return point;
    }
    return forward;
  }
  function chamberlinProjection() {
    var points = [ [ 0, 0 ], [ 0, 0 ], [ 0, 0 ] ], m = projectionMutator(chamberlin), p = m(points), rotate = p.rotate;
    delete p.rotate;
    p.points = function(_) {
      if (!arguments.length) return points;
      points = _;
      var origin = d3.geo.centroid({
        type: "MultiPoint",
        coordinates: points
      }), r = [ -origin[0], -origin[1] ];
      rotate.call(p, r);
      return m(points.map(d3.geo.rotation(r)).map(chamberlinRadians));
    };
    return p.points([ [ -150, 55 ], [ -35, 55 ], [ -92.5, 10 ] ]);
  }
  function chamberlinDistanceAzimuth(dÏ†, c1, s1, c2, s2, dÎ») {
    var cosdÎ» = Math.cos(dÎ»), r;
    if (Math.abs(dÏ†) > 1 || Math.abs(dÎ») > 1) {
      r = acos(s1 * s2 + c1 * c2 * cosdÎ»);
    } else {
      var sindÏ† = Math.sin(.5 * dÏ†), sindÎ» = Math.sin(.5 * dÎ»);
      r = 2 * asin(Math.sqrt(sindÏ† * sindÏ† + c1 * c2 * sindÎ» * sindÎ»));
    }
    if (Math.abs(r) > Îµ) {
      return [ r, Math.atan2(c2 * Math.sin(dÎ»), c1 * s2 - s1 * c2 * cosdÎ») ];
    }
    return [ 0, 0 ];
  }
  function chamberlinAngle(b, c, a) {
    return acos(.5 * (b * b + c * c - a * a) / (b * c));
  }
  function chamberlinLongitude(Î») {
    return Î» - 2 * Ï€ * Math.floor((Î» + Ï€) / (2 * Ï€));
  }
  function chamberlinRadians(point) {
    return [ point[0] * radians, point[1] * radians ];
  }
  (d3.geo.chamberlin = chamberlinProjection).raw = chamberlin;
  function collignon(Î», Ï†) {
    var Î± = asqrt(1 - Math.sin(Ï†));
    return [ 2 / sqrtÏ€ * Î» * Î±, sqrtÏ€ * (1 - Î±) ];
  }
  collignon.invert = function(x, y) {
    var Î» = (Î» = y / sqrtÏ€ - 1) * Î»;
    return [ Î» > 0 ? x * Math.sqrt(Ï€ / Î») / 2 : 0, asin(1 - Î») ];
  };
  (d3.geo.collignon = function() {
    return projection(collignon);
  }).raw = collignon;
  function craig(Ï†0) {
    var tanÏ†0 = Math.tan(Ï†0);
    function forward(Î», Ï†) {
      return [ Î», (Î» ? Î» / Math.sin(Î») : 1) * (Math.sin(Ï†) * Math.cos(Î») - tanÏ†0 * Math.cos(Ï†)) ];
    }
    forward.invert = tanÏ†0 ? function(x, y) {
      if (x) y *= Math.sin(x) / x;
      var cosÎ» = Math.cos(x);
      return [ x, 2 * Math.atan2(Math.sqrt(cosÎ» * cosÎ» + tanÏ†0 * tanÏ†0 - y * y) - cosÎ», tanÏ†0 - y) ];
    } : function(x, y) {
      return [ x, asin(x ? y * Math.tan(x) / x : y) ];
    };
    return forward;
  }
  (d3.geo.craig = function() {
    return parallel1Projection(craig);
  }).raw = craig;
  function craster(Î», Ï†) {
    var sqrt3 = Math.sqrt(3);
    return [ sqrt3 * Î» * (2 * Math.cos(2 * Ï† / 3) - 1) / sqrtÏ€, sqrt3 * sqrtÏ€ * Math.sin(Ï† / 3) ];
  }
  craster.invert = function(x, y) {
    var sqrt3 = Math.sqrt(3), Ï† = 3 * asin(y / (sqrt3 * sqrtÏ€));
    return [ sqrtÏ€ * x / (sqrt3 * (2 * Math.cos(2 * Ï† / 3) - 1)), Ï† ];
  };
  (d3.geo.craster = function() {
    return projection(craster);
  }).raw = craster;
  function cylindricalEqualArea(Ï†0) {
    var cosÏ†0 = Math.cos(Ï†0);
    function forward(Î», Ï†) {
      return [ Î» * cosÏ†0, Math.sin(Ï†) / cosÏ†0 ];
    }
    forward.invert = function(x, y) {
      return [ x / cosÏ†0, asin(y * cosÏ†0) ];
    };
    return forward;
  }
  (d3.geo.cylindricalEqualArea = function() {
    return parallel1Projection(cylindricalEqualArea);
  }).raw = cylindricalEqualArea;
  function cylindricalStereographic(Ï†0) {
    var cosÏ†0 = Math.cos(Ï†0);
    function forward(Î», Ï†) {
      return [ Î» * cosÏ†0, (1 + cosÏ†0) * Math.tan(Ï† * .5) ];
    }
    forward.invert = function(x, y) {
      return [ x / cosÏ†0, Math.atan(y / (1 + cosÏ†0)) * 2 ];
    };
    return forward;
  }
  (d3.geo.cylindricalStereographic = function() {
    return parallel1Projection(cylindricalStereographic);
  }).raw = cylindricalStereographic;
  function eckert1(Î», Ï†) {
    var Î± = Math.sqrt(8 / (3 * Ï€));
    return [ Î± * Î» * (1 - Math.abs(Ï†) / Ï€), Î± * Ï† ];
  }
  eckert1.invert = function(x, y) {
    var Î± = Math.sqrt(8 / (3 * Ï€)), Ï† = y / Î±;
    return [ x / (Î± * (1 - Math.abs(Ï†) / Ï€)), Ï† ];
  };
  (d3.geo.eckert1 = function() {
    return projection(eckert1);
  }).raw = eckert1;
  function eckert2(Î», Ï†) {
    var Î± = Math.sqrt(4 - 3 * Math.sin(Math.abs(Ï†)));
    return [ 2 / Math.sqrt(6 * Ï€) * Î» * Î±, sgn(Ï†) * Math.sqrt(2 * Ï€ / 3) * (2 - Î±) ];
  }
  eckert2.invert = function(x, y) {
    var Î± = 2 - Math.abs(y) / Math.sqrt(2 * Ï€ / 3);
    return [ x * Math.sqrt(6 * Ï€) / (2 * Î±), sgn(y) * asin((4 - Î± * Î±) / 3) ];
  };
  (d3.geo.eckert2 = function() {
    return projection(eckert2);
  }).raw = eckert2;
  function eckert3(Î», Ï†) {
    var k = Math.sqrt(Ï€ * (4 + Ï€));
    return [ 2 / k * Î» * (1 + Math.sqrt(1 - 4 * Ï† * Ï† / (Ï€ * Ï€))), 4 / k * Ï† ];
  }
  eckert3.invert = function(x, y) {
    var k = Math.sqrt(Ï€ * (4 + Ï€)) / 2;
    return [ x * k / (1 + asqrt(1 - y * y * (4 + Ï€) / (4 * Ï€))), y * k / 2 ];
  };
  (d3.geo.eckert3 = function() {
    return projection(eckert3);
  }).raw = eckert3;
  function eckert4(Î», Ï†) {
    var k = (2 + halfÏ€) * Math.sin(Ï†);
    Ï† /= 2;
    for (var i = 0, Î´ = Infinity; i < 10 && Math.abs(Î´) > Îµ; i++) {
      var cosÏ† = Math.cos(Ï†);
      Ï† -= Î´ = (Ï† + Math.sin(Ï†) * (cosÏ† + 2) - k) / (2 * cosÏ† * (1 + cosÏ†));
    }
    return [ 2 / Math.sqrt(Ï€ * (4 + Ï€)) * Î» * (1 + Math.cos(Ï†)), 2 * Math.sqrt(Ï€ / (4 + Ï€)) * Math.sin(Ï†) ];
  }
  eckert4.invert = function(x, y) {
    var A = .5 * y * Math.sqrt((4 + Ï€) / Ï€), k = asin(A), c = Math.cos(k);
    return [ x / (2 / Math.sqrt(Ï€ * (4 + Ï€)) * (1 + c)), asin((k + A * (c + 2)) / (2 + halfÏ€)) ];
  };
  (d3.geo.eckert4 = function() {
    return projection(eckert4);
  }).raw = eckert4;
  function eckert5(Î», Ï†) {
    return [ Î» * (1 + Math.cos(Ï†)) / Math.sqrt(2 + Ï€), 2 * Ï† / Math.sqrt(2 + Ï€) ];
  }
  eckert5.invert = function(x, y) {
    var k = Math.sqrt(2 + Ï€), Ï† = y * k / 2;
    return [ k * x / (1 + Math.cos(Ï†)), Ï† ];
  };
  (d3.geo.eckert5 = function() {
    return projection(eckert5);
  }).raw = eckert5;
  function eckert6(Î», Ï†) {
    var k = (1 + halfÏ€) * Math.sin(Ï†);
    for (var i = 0, Î´ = Infinity; i < 10 && Math.abs(Î´) > Îµ; i++) {
      Ï† -= Î´ = (Ï† + Math.sin(Ï†) - k) / (1 + Math.cos(Ï†));
    }
    k = Math.sqrt(2 + Ï€);
    return [ Î» * (1 + Math.cos(Ï†)) / k, 2 * Ï† / k ];
  }
  eckert6.invert = function(x, y) {
    var j = 1 + halfÏ€, k = Math.sqrt(j / 2);
    return [ x * 2 * k / (1 + Math.cos(y *= k)), asin((y + Math.sin(y)) / j) ];
  };
  (d3.geo.eckert6 = function() {
    return projection(eckert6);
  }).raw = eckert6;
  function eisenlohr(Î», Ï†) {
    var s0 = Math.sin(Î» /= 2), c0 = Math.cos(Î»), k = Math.sqrt(Math.cos(Ï†)), c1 = Math.cos(Ï† /= 2), t = Math.sin(Ï†) / (c1 + Math.SQRT2 * c0 * k), c = Math.sqrt(2 / (1 + t * t)), v = Math.sqrt((Math.SQRT2 * c1 + (c0 + s0) * k) / (Math.SQRT2 * c1 + (c0 - s0) * k));
    return [ eisenlohrK * (c * (v - 1 / v) - 2 * Math.log(v)), eisenlohrK * (c * t * (v + 1 / v) - 2 * Math.atan(t)) ];
  }
  eisenlohr.invert = function(x, y) {
    var p = d3.geo.august.raw.invert(x / 1.2, y * 1.065);
    if (!p) return null;
    var Î» = p[0], Ï† = p[1], i = 20;
    x /= eisenlohrK, y /= eisenlohrK;
    do {
      var _0 = Î» / 2, _1 = Ï† / 2, s0 = Math.sin(_0), c0 = Math.cos(_0), s1 = Math.sin(_1), c1 = Math.cos(_1), cos1 = Math.cos(Ï†), k = Math.sqrt(cos1), t = s1 / (c1 + Math.SQRT2 * c0 * k), t2 = t * t, c = Math.sqrt(2 / (1 + t2)), v0 = Math.SQRT2 * c1 + (c0 + s0) * k, v1 = Math.SQRT2 * c1 + (c0 - s0) * k, v2 = v0 / v1, v = Math.sqrt(v2), vm1v = v - 1 / v, vp1v = v + 1 / v, fx = c * vm1v - 2 * Math.log(v) - x, fy = c * t * vp1v - 2 * Math.atan(t) - y, Î´tÎ´Î» = s1 && Math.SQRT1_2 * k * s0 * t2 / s1, Î´tÎ´Ï† = (Math.SQRT2 * c0 * c1 + k) / (2 * (c1 + Math.SQRT2 * c0 * k) * (c1 + Math.SQRT2 * c0 * k) * k), Î´cÎ´t = -.5 * t * c * c * c, Î´cÎ´Î» = Î´cÎ´t * Î´tÎ´Î», Î´cÎ´Ï† = Î´cÎ´t * Î´tÎ´Ï†, A = (A = 2 * c1 + Math.SQRT2 * k * (c0 - s0)) * A * v, Î´vÎ´Î» = (Math.SQRT2 * c0 * c1 * k + cos1) / A, Î´vÎ´Ï† = -(Math.SQRT2 * s0 * s1) / (k * A), Î´xÎ´Î» = vm1v * Î´cÎ´Î» - 2 * Î´vÎ´Î» / v + c * (Î´vÎ´Î» + Î´vÎ´Î» / v2), Î´xÎ´Ï† = vm1v * Î´cÎ´Ï† - 2 * Î´vÎ´Ï† / v + c * (Î´vÎ´Ï† + Î´vÎ´Ï† / v2), Î´yÎ´Î» = t * vp1v * Î´cÎ´Î» - 2 * Î´tÎ´Î» / (1 + t2) + c * vp1v * Î´tÎ´Î» + c * t * (Î´vÎ´Î» - Î´vÎ´Î» / v2), Î´yÎ´Ï† = t * vp1v * Î´cÎ´Ï† - 2 * Î´tÎ´Ï† / (1 + t2) + c * vp1v * Î´tÎ´Ï† + c * t * (Î´vÎ´Ï† - Î´vÎ´Ï† / v2), denominator = Î´xÎ´Ï† * Î´yÎ´Î» - Î´yÎ´Ï† * Î´xÎ´Î»;
      if (!denominator) break;
      var Î´Î» = (fy * Î´xÎ´Ï† - fx * Î´yÎ´Ï†) / denominator, Î´Ï† = (fx * Î´yÎ´Î» - fy * Î´xÎ´Î») / denominator;
      Î» -= Î´Î»;
      Ï† = Math.max(-halfÏ€, Math.min(halfÏ€, Ï† - Î´Ï†));
    } while ((Math.abs(Î´Î») > Îµ || Math.abs(Î´Ï†) > Îµ) && --i > 0);
    return Math.abs(Math.abs(Ï†) - halfÏ€) < Îµ ? [ 0, Ï† ] : i && [ Î», Ï† ];
  };
  var eisenlohrK = 3 + 2 * Math.SQRT2;
  (d3.geo.eisenlohr = function() {
    return projection(eisenlohr);
  }).raw = eisenlohr;
  function fahey(Î», Ï†) {
    var t = Math.tan(Ï† / 2);
    return [ Î» * faheyK * asqrt(1 - t * t), (1 + faheyK) * t ];
  }
  fahey.invert = function(x, y) {
    var t = y / (1 + faheyK);
    return [ x ? x / (faheyK * asqrt(1 - t * t)) : 0, 2 * Math.atan(t) ];
  };
  var faheyK = Math.cos(35 * radians);
  (d3.geo.fahey = function() {
    return projection(fahey);
  }).raw = fahey;
  function foucaut(Î», Ï†) {
    var k = Ï† / 2, cosk = Math.cos(k);
    return [ 2 * Î» / sqrtÏ€ * Math.cos(Ï†) * cosk * cosk, sqrtÏ€ * Math.tan(k) ];
  }
  foucaut.invert = function(x, y) {
    var k = Math.atan(y / sqrtÏ€), cosk = Math.cos(k), Ï† = 2 * k;
    return [ x * sqrtÏ€ * .5 / (Math.cos(Ï†) * cosk * cosk), Ï† ];
  };
  (d3.geo.foucaut = function() {
    return projection(foucaut);
  }).raw = foucaut;
  d3.geo.gilbert = function(projection) {
    var e = d3.geo.equirectangular().scale(degrees).translate([ 0, 0 ]);
    function gilbert(coordinates) {
      return projection([ coordinates[0] * .5, asin(Math.tan(coordinates[1] * .5 * radians)) * degrees ]);
    }
    if (projection.invert) gilbert.invert = function(coordinates) {
      coordinates = projection.invert(coordinates);
      coordinates[0] *= 2;
      coordinates[1] = 2 * Math.atan(Math.sin(coordinates[1] * radians)) * degrees;
      return coordinates;
    };
    gilbert.stream = function(stream) {
      stream = projection.stream(stream);
      var s = e.stream({
        point: function(Î», Ï†) {
          stream.point(Î» * .5, asin(Math.tan(-Ï† * .5 * radians)) * degrees);
        },
        lineStart: function() {
          stream.lineStart();
        },
        lineEnd: function() {
          stream.lineEnd();
        },
        polygonStart: function() {
          stream.polygonStart();
        },
        polygonEnd: function() {
          stream.polygonEnd();
        }
      });
      s.sphere = function() {
        stream.sphere();
      };
      s.valid = false;
      return s;
    };
    return gilbert;
  };
  function ginzburgPolyconic(a, b, c, d, e, f, g, h) {
    if (arguments.length < 8) h = 0;
    function forward(Î», Ï†) {
      if (!Ï†) return [ a * Î» / Ï€, 0 ];
      var Ï†2 = Ï† * Ï†, xB = a + Ï†2 * (b + Ï†2 * (c + Ï†2 * d)), yB = Ï† * (e - 1 + Ï†2 * (f - h + Ï†2 * g)), m = (xB * xB + yB * yB) / (2 * yB), Î± = Î» * Math.asin(xB / m) / Ï€;
      return [ m * Math.sin(Î±), Ï† * (1 + Ï†2 * h) + m * (1 - Math.cos(Î±)) ];
    }
    forward.invert = function(x, y) {
      var Î» = Ï€ * x / a, Ï† = y, Î´Î», Î´Ï†, i = 50;
      do {
        var Ï†2 = Ï† * Ï†, xB = a + Ï†2 * (b + Ï†2 * (c + Ï†2 * d)), yB = Ï† * (e - 1 + Ï†2 * (f - h + Ï†2 * g)), p = xB * xB + yB * yB, q = 2 * yB, m = p / q, m2 = m * m, dÎ±dÎ» = Math.asin(xB / m) / Ï€, Î± = Î» * dÎ±dÎ»;
        xB2 = xB * xB, dxBdÏ† = (2 * b + Ï†2 * (4 * c + Ï†2 * 6 * d)) * Ï†, dyBdÏ† = e + Ï†2 * (3 * f + Ï†2 * 5 * g), 
        dpdÏ† = 2 * (xB * dxBdÏ† + yB * (dyBdÏ† - 1)), dqdÏ† = 2 * (dyBdÏ† - 1), dmdÏ† = (dpdÏ† * q - p * dqdÏ†) / (q * q), 
        cosÎ± = Math.cos(Î±), sinÎ± = Math.sin(Î±), mcosÎ± = m * cosÎ±, msinÎ± = m * sinÎ±, dÎ±dÏ† = Î» / Ï€ * (1 / asqrt(1 - xB2 / m2)) * (dxBdÏ† * m - xB * dmdÏ†) / m2, 
        fx = msinÎ± - x, fy = Ï† * (1 + Ï†2 * h) + m - mcosÎ± - y, Î´xÎ´Ï† = dmdÏ† * sinÎ± + mcosÎ± * dÎ±dÏ†, 
        Î´xÎ´Î» = mcosÎ± * dÎ±dÎ», Î´yÎ´Ï† = 1 + dmdÏ† - (dmdÏ† * cosÎ± - msinÎ± * dÎ±dÏ†), Î´yÎ´Î» = msinÎ± * dÎ±dÎ», 
        denominator = Î´xÎ´Ï† * Î´yÎ´Î» - Î´yÎ´Ï† * Î´xÎ´Î»;
        if (!denominator) break;
        Î» -= Î´Î» = (fy * Î´xÎ´Ï† - fx * Î´yÎ´Ï†) / denominator;
        Ï† -= Î´Ï† = (fx * Î´yÎ´Î» - fy * Î´xÎ´Î») / denominator;
      } while ((Math.abs(Î´Î») > Îµ || Math.abs(Î´Ï†) > Îµ) && --i > 0);
      return [ Î», Ï† ];
    };
    return forward;
  }
  var ginzburg4 = ginzburgPolyconic(2.8284, -1.6988, .75432, -.18071, 1.76003, -.38914, .042555);
  (d3.geo.ginzburg4 = function() {
    return projection(ginzburg4);
  }).raw = ginzburg4;
  var ginzburg5 = ginzburgPolyconic(2.583819, -.835827, .170354, -.038094, 1.543313, -.411435, .082742);
  (d3.geo.ginzburg5 = function() {
    return projection(ginzburg5);
  }).raw = ginzburg5;
  var ginzburg6 = ginzburgPolyconic(5 / 6 * Ï€, -.62636, -.0344, 0, 1.3493, -.05524, 0, .045);
  (d3.geo.ginzburg6 = function() {
    return projection(ginzburg6);
  }).raw = ginzburg6;
  function ginzburg8(Î», Ï†) {
    var Î»2 = Î» * Î», Ï†2 = Ï† * Ï†;
    return [ Î» * (1 - .162388 * Ï†2) * (.87 - 952426e-9 * Î»2 * Î»2), Ï† * (1 + Ï†2 / 12) ];
  }
  ginzburg8.invert = function(x, y) {
    var Î» = x, Ï† = y, i = 50, Î´;
    do {
      var Ï†2 = Ï† * Ï†;
      Ï† -= Î´ = (Ï† * (1 + Ï†2 / 12) - y) / (1 + Ï†2 / 4);
    } while (Math.abs(Î´) > Îµ && --i > 0);
    i = 50;
    x /= 1 - .162388 * Ï†2;
    do {
      var Î»4 = (Î»4 = Î» * Î») * Î»4;
      Î» -= Î´ = (Î» * (.87 - 952426e-9 * Î»4) - x) / (.87 - .00476213 * Î»4);
    } while (Math.abs(Î´) > Îµ && --i > 0);
    return [ Î», Ï† ];
  };
  (d3.geo.ginzburg8 = function() {
    return projection(ginzburg8);
  }).raw = ginzburg8;
  var ginzburg9 = ginzburgPolyconic(2.6516, -.76534, .19123, -.047094, 1.36289, -.13965, .031762);
  (d3.geo.ginzburg9 = function() {
    return projection(ginzburg9);
  }).raw = ginzburg9;
  function quincuncialProjection(projectHemisphere) {
    var dx = projectHemisphere(halfÏ€, 0)[0] - projectHemisphere(-halfÏ€, 0)[0];
    function projection() {
      var quincuncial = false, m = projectionMutator(projectAt), p = m(quincuncial);
      p.quincuncial = function(_) {
        if (!arguments.length) return quincuncial;
        return m(quincuncial = !!_);
      };
      return p;
    }
    function projectAt(quincuncial) {
      var forward = quincuncial ? function(Î», Ï†) {
        var t = Math.abs(Î») < halfÏ€, p = projectHemisphere(t ? Î» : Î» > 0 ? Î» - Ï€ : Î» + Ï€, Ï†);
        var x = (p[0] - p[1]) * Math.SQRT1_2, y = (p[0] + p[1]) * Math.SQRT1_2;
        if (t) return [ x, y ];
        var d = dx * Math.SQRT1_2, s = x > 0 ^ y > 0 ? -1 : 1;
        return [ s * x - sgn(y) * d, s * y - sgn(x) * d ];
      } : function(Î», Ï†) {
        var s = Î» > 0 ? -.5 : .5, point = projectHemisphere(Î» + s * Ï€, Ï†);
        point[0] -= s * dx;
        return point;
      };
      if (projectHemisphere.invert) forward.invert = quincuncial ? function(x0, y0) {
        var x = (x0 + y0) * Math.SQRT1_2, y = (y0 - x0) * Math.SQRT1_2, t = Math.abs(x) < .5 * dx && Math.abs(y) < .5 * dx;
        if (!t) {
          var d = dx * Math.SQRT1_2, s = x > 0 ^ y > 0 ? -1 : 1, x1 = -s * (x0 + (y > 0 ? 1 : -1) * d), y1 = -s * (y0 + (x > 0 ? 1 : -1) * d);
          x = (-x1 - y1) * Math.SQRT1_2;
          y = (x1 - y1) * Math.SQRT1_2;
        }
        var p = projectHemisphere.invert(x, y);
        if (!t) p[0] += x > 0 ? Ï€ : -Ï€;
        return p;
      } : function(x, y) {
        var s = x > 0 ? -.5 : .5, location = projectHemisphere.invert(x + s * dx, y), Î» = location[0] - s * Ï€;
        if (Î» < -Ï€) Î» += 2 * Ï€; else if (Î» > Ï€) Î» -= 2 * Ï€;
        location[0] = Î»;
        return location;
      };
      return forward;
    }
    projection.raw = projectAt;
    return projection;
  }
  function gringorten(Î», Ï†) {
    var sÎ» = sgn(Î»), sÏ† = sgn(Ï†), cosÏ† = Math.cos(Ï†), x = Math.cos(Î») * cosÏ†, y = Math.sin(Î») * cosÏ†, z = Math.sin(sÏ† * Ï†);
    Î» = Math.abs(Math.atan2(y, z));
    Ï† = asin(x);
    if (Math.abs(Î» - halfÏ€) > Îµ) Î» %= halfÏ€;
    var point = gringortenHexadecant(Î» > Ï€ / 4 ? halfÏ€ - Î» : Î», Ï†);
    if (Î» > Ï€ / 4) z = point[0], point[0] = -point[1], point[1] = -z;
    return point[0] *= sÎ», point[1] *= -sÏ†, point;
  }
  gringorten.invert = function(x, y) {
    var sx = sgn(x), sy = sgn(y), x0 = -sx * x, y0 = -sy * y, t = y0 / x0 < 1, p = gringortenHexadecantInvert(t ? y0 : x0, t ? x0 : y0), Î» = p[0], Ï† = p[1];
    if (t) Î» = -halfÏ€ - Î»;
    var cosÏ† = Math.cos(Ï†), x = Math.cos(Î») * cosÏ†, y = Math.sin(Î») * cosÏ†, z = Math.sin(Ï†);
    return [ sx * (Math.atan2(y, -z) + Ï€), sy * asin(x) ];
  };
  function gringortenHexadecant(Î», Ï†) {
    if (Ï† === halfÏ€) return [ 0, 0 ];
    var sinÏ† = Math.sin(Ï†), r = sinÏ† * sinÏ†, r2 = r * r, j = 1 + r2, k = 1 + 3 * r2, q = 1 - r2, z = asin(1 / Math.sqrt(j)), v = q + r * j * z, p2 = (1 - sinÏ†) / v, p = Math.sqrt(p2), a2 = p2 * j, a = Math.sqrt(a2), h = p * q;
    if (Î» === 0) return [ 0, -(h + r * a) ];
    var cosÏ† = Math.cos(Ï†), secÏ† = 1 / cosÏ†, drdÏ† = 2 * sinÏ† * cosÏ†, dvdÏ† = (-3 * r + z * k) * drdÏ†, dp2dÏ† = (-v * cosÏ† - (1 - sinÏ†) * dvdÏ†) / (v * v), dpdÏ† = .5 * dp2dÏ† / p, dhdÏ† = q * dpdÏ† - 2 * r * p * drdÏ†, dra2dÏ† = r * j * dp2dÏ† + p2 * k * drdÏ†, Î¼ = -secÏ† * drdÏ†, Î½ = -secÏ† * dra2dÏ†, Î¶ = -2 * secÏ† * dhdÏ†, Î› = 4 * Î» / Ï€;
    if (Î» > .222 * Ï€ || Ï† < Ï€ / 4 && Î» > .175 * Ï€) {
      var x = (h + r * asqrt(a2 * (1 + r2) - h * h)) / (1 + r2);
      if (Î» > Ï€ / 4) return [ x, x ];
      var x1 = x, x0 = .5 * x, i = 50;
      x = .5 * (x0 + x1);
      do {
        var g = Math.sqrt(a2 - x * x), f = x * (Î¶ + Î¼ * g) + Î½ * asin(x / a) - Î›;
        if (!f) break;
        if (f < 0) x0 = x; else x1 = x;
        x = .5 * (x0 + x1);
      } while (Math.abs(x1 - x0) > Îµ && --i > 0);
    } else {
      var x = Îµ, i = 25, Î´;
      do {
        var x2 = x * x, g = asqrt(a2 - x2), Î¶Î¼g = Î¶ + Î¼ * g, f = x * Î¶Î¼g + Î½ * asin(x / a) - Î›, df = Î¶Î¼g + (Î½ - Î¼ * x2) / g;
        x -= Î´ = g ? f / df : 0;
      } while (Math.abs(Î´) > Îµ && --i > 0);
    }
    return [ x, -h - r * asqrt(a2 - x * x) ];
  }
  function gringortenHexadecantInvert(x, y) {
    var x0 = 0, x1 = 1, r = .5, i = 50;
    while (true) {
      var r2 = r * r, sinÏ† = Math.sqrt(r), z = Math.asin(1 / Math.sqrt(1 + r2)), v = 1 - r2 + r * (1 + r2) * z, p2 = (1 - sinÏ†) / v, p = Math.sqrt(p2), a2 = p2 * (1 + r2), h = p * (1 - r2), g2 = a2 - x * x, g = Math.sqrt(g2), y0 = y + h + r * g;
      if (Math.abs(x1 - x0) < Îµ2 || --i === 0 || y0 === 0) break;
      if (y0 > 0) x0 = r; else x1 = r;
      r = .5 * (x0 + x1);
    }
    if (!i) return null;
    var Ï† = Math.asin(sinÏ†), cosÏ† = Math.cos(Ï†), secÏ† = 1 / cosÏ†, drdÏ† = 2 * sinÏ† * cosÏ†, dvdÏ† = (-3 * r + z * (1 + 3 * r2)) * drdÏ†, dp2dÏ† = (-v * cosÏ† - (1 - sinÏ†) * dvdÏ†) / (v * v), dpdÏ† = .5 * dp2dÏ† / p, dhdÏ† = (1 - r2) * dpdÏ† - 2 * r * p * drdÏ†, Î¶ = -2 * secÏ† * dhdÏ†, Î¼ = -secÏ† * drdÏ†, Î½ = -secÏ† * (r * (1 + r2) * dp2dÏ† + p2 * (1 + 3 * r2) * drdÏ†);
    return [ Ï€ / 4 * (x * (Î¶ + Î¼ * g) + Î½ * Math.asin(x / Math.sqrt(a2))), Ï† ];
  }
  d3.geo.gringorten = quincuncialProjection(gringorten);
  function ellipticJi(u, v, m) {
    if (!u) {
      var b = ellipticJ(v, 1 - m);
      return [ [ 0, b[0] / b[1] ], [ 1 / b[1], 0 ], [ b[2] / b[1], 0 ] ];
    }
    var a = ellipticJ(u, m);
    if (!v) return [ [ a[0], 0 ], [ a[1], 0 ], [ a[2], 0 ] ];
    var b = ellipticJ(v, 1 - m), denominator = b[1] * b[1] + m * a[0] * a[0] * b[0] * b[0];
    return [ [ a[0] * b[2] / denominator, a[1] * a[2] * b[0] * b[1] / denominator ], [ a[1] * b[1] / denominator, -a[0] * a[2] * b[0] * b[2] / denominator ], [ a[2] * b[1] * b[2] / denominator, -m * a[0] * a[1] * b[0] / denominator ] ];
  }
  function ellipticJ(u, m) {
    var ai, b, Ï†, t, twon;
    if (m < Îµ) {
      t = Math.sin(u);
      b = Math.cos(u);
      ai = .25 * m * (u - t * b);
      return [ t - ai * b, b + ai * t, 1 - .5 * m * t * t, u - ai ];
    }
    if (m >= 1 - Îµ) {
      ai = .25 * (1 - m);
      b = cosh(u);
      t = tanh(u);
      Ï† = 1 / b;
      twon = b * sinh(u);
      return [ t + ai * (twon - u) / (b * b), Ï† - ai * t * Ï† * (twon - u), Ï† + ai * t * Ï† * (twon + u), 2 * Math.atan(Math.exp(u)) - halfÏ€ + ai * (twon - u) / b ];
    }
    var a = [ 1, 0, 0, 0, 0, 0, 0, 0, 0 ], c = [ Math.sqrt(m), 0, 0, 0, 0, 0, 0, 0, 0 ], i = 0;
    b = Math.sqrt(1 - m);
    twon = 1;
    while (Math.abs(c[i] / a[i]) > Îµ && i < 8) {
      ai = a[i++];
      c[i] = .5 * (ai - b);
      a[i] = .5 * (ai + b);
      b = asqrt(ai * b);
      twon *= 2;
    }
    Ï† = twon * a[i] * u;
    do {
      t = c[i] * Math.sin(b = Ï†) / a[i];
      Ï† = .5 * (asin(t) + Ï†);
    } while (--i);
    return [ Math.sin(Ï†), t = Math.cos(Ï†), t / Math.cos(Ï† - b), Ï† ];
  }
  function ellipticFi(Ï†, Ïˆ, m) {
    var r = Math.abs(Ï†), i = Math.abs(Ïˆ), sinhÏˆ = sinh(i);
    if (r) {
      var cscÏ† = 1 / Math.sin(r), cotÏ†2 = 1 / (Math.tan(r) * Math.tan(r)), b = -(cotÏ†2 + m * sinhÏˆ * sinhÏˆ * cscÏ† * cscÏ† - 1 + m), c = (m - 1) * cotÏ†2, cotÎ»2 = .5 * (-b + Math.sqrt(b * b - 4 * c));
      return [ ellipticF(Math.atan(1 / Math.sqrt(cotÎ»2)), m) * sgn(Ï†), ellipticF(Math.atan(asqrt((cotÎ»2 / cotÏ†2 - 1) / m)), 1 - m) * sgn(Ïˆ) ];
    }
    return [ 0, ellipticF(Math.atan(sinhÏˆ), 1 - m) * sgn(Ïˆ) ];
  }
  function ellipticF(Ï†, m) {
    if (!m) return Ï†;
    if (m === 1) return Math.log(Math.tan(Ï† / 2 + Ï€ / 4));
    var a = 1, b = Math.sqrt(1 - m), c = Math.sqrt(m);
    for (var i = 0; Math.abs(c) > Îµ; i++) {
      if (Ï† % Ï€) {
        var dÏ† = Math.atan(b * Math.tan(Ï†) / a);
        if (dÏ† < 0) dÏ† += Ï€;
        Ï† += dÏ† + ~~(Ï† / Ï€) * Ï€;
      } else Ï† += Ï†;
      c = (a + b) / 2;
      b = Math.sqrt(a * b);
      c = ((a = c) - b) / 2;
    }
    return Ï† / (Math.pow(2, i) * a);
  }
  function guyou(Î», Ï†) {
    var k_ = (Math.SQRT2 - 1) / (Math.SQRT2 + 1), k = Math.sqrt(1 - k_ * k_), K = ellipticF(halfÏ€, k * k), f = -1;
    var Ïˆ = Math.log(Math.tan(Ï€ / 4 + Math.abs(Ï†) / 2)), r = Math.exp(f * Ïˆ) / Math.sqrt(k_), at = guyouComplexAtan(r * Math.cos(f * Î»), r * Math.sin(f * Î»)), t = ellipticFi(at[0], at[1], k * k);
    return [ -t[1], sgn(Ï†) * (.5 * K - t[0]) ];
  }
  function guyouComplexAtan(x, y) {
    var x2 = x * x, y_1 = y + 1, t = 1 - x2 - y * y;
    return [ sgn(x) * Ï€ / 4 - .5 * Math.atan2(t, 2 * x), -.25 * Math.log(t * t + 4 * x2) + .5 * Math.log(y_1 * y_1 + x2) ];
  }
  function guyouComplexDivide(a, b) {
    var denominator = b[0] * b[0] + b[1] * b[1];
    return [ (a[0] * b[0] + a[1] * b[1]) / denominator, (a[1] * b[0] - a[0] * b[1]) / denominator ];
  }
  guyou.invert = function(x, y) {
    var k_ = (Math.SQRT2 - 1) / (Math.SQRT2 + 1), k = Math.sqrt(1 - k_ * k_), K = ellipticF(halfÏ€, k * k), f = -1;
    var j = ellipticJi(.5 * K - y, -x, k * k), tn = guyouComplexDivide(j[0], j[1]), Î» = Math.atan2(tn[1], tn[0]) / f;
    return [ Î», 2 * Math.atan(Math.exp(.5 / f * Math.log(k_ * tn[0] * tn[0] + k_ * tn[1] * tn[1]))) - halfÏ€ ];
  };
  d3.geo.guyou = quincuncialProjection(guyou);
  function hammerRetroazimuthal(Ï†0) {
    var sinÏ†0 = Math.sin(Ï†0), cosÏ†0 = Math.cos(Ï†0), rotate = hammerRetroazimuthalRotation(Ï†0);
    rotate.invert = hammerRetroazimuthalRotation(-Ï†0);
    function forward(Î», Ï†) {
      var p = rotate(Î», Ï†);
      Î» = p[0], Ï† = p[1];
      var sinÏ† = Math.sin(Ï†), cosÏ† = Math.cos(Ï†), cosÎ» = Math.cos(Î»), z = acos(sinÏ†0 * sinÏ† + cosÏ†0 * cosÏ† * cosÎ»), sinz = Math.sin(z), K = Math.abs(sinz) > Îµ ? z / sinz : 1;
      return [ K * cosÏ†0 * Math.sin(Î»), (Math.abs(Î») > halfÏ€ ? K : -K) * (sinÏ†0 * cosÏ† - cosÏ†0 * sinÏ† * cosÎ») ];
    }
    forward.invert = function(x, y) {
      var Ï = Math.sqrt(x * x + y * y), sinz = -Math.sin(Ï), cosz = Math.cos(Ï), a = Ï * cosz, b = -y * sinz, c = Ï * sinÏ†0, d = asqrt(a * a + b * b - c * c), Ï† = Math.atan2(a * c + b * d, b * c - a * d), Î» = (Ï > halfÏ€ ? -1 : 1) * Math.atan2(x * sinz, Ï * Math.cos(Ï†) * cosz + y * Math.sin(Ï†) * sinz);
      return rotate.invert(Î», Ï†);
    };
    return forward;
  }
  function hammerRetroazimuthalRotation(Ï†0) {
    var sinÏ†0 = Math.sin(Ï†0), cosÏ†0 = Math.cos(Ï†0);
    return function(Î», Ï†) {
      var cosÏ† = Math.cos(Ï†), x = Math.cos(Î») * cosÏ†, y = Math.sin(Î») * cosÏ†, z = Math.sin(Ï†);
      return [ Math.atan2(y, x * cosÏ†0 - z * sinÏ†0), asin(z * cosÏ†0 + x * sinÏ†0) ];
    };
  }
  function hammerRetroazimuthalProjection() {
    var Ï†0 = 0, m = projectionMutator(hammerRetroazimuthal), p = m(Ï†0), rotate_ = p.rotate, stream_ = p.stream, circle = d3.geo.circle();
    p.parallel = function(_) {
      if (!arguments.length) return Ï†0 / Ï€ * 180;
      var r = p.rotate();
      return m(Ï†0 = _ * Ï€ / 180).rotate(r);
    };
    p.rotate = function(_) {
      if (!arguments.length) return _ = rotate_.call(p), _[1] += Ï†0 / Ï€ * 180, _;
      rotate_.call(p, [ _[0], _[1] - Ï†0 / Ï€ * 180 ]);
      circle.origin([ -_[0], -_[1] ]);
      return p;
    };
    p.stream = function(stream) {
      stream = stream_(stream);
      stream.sphere = function() {
        stream.polygonStart();
        var Îµ = .01, ring = circle.angle(90 - Îµ)().coordinates[0], n = ring.length - 1, i = -1, p;
        stream.lineStart();
        while (++i < n) stream.point((p = ring[i])[0], p[1]);
        stream.lineEnd();
        ring = circle.angle(90 + Îµ)().coordinates[0];
        n = ring.length - 1;
        stream.lineStart();
        while (--i >= 0) stream.point((p = ring[i])[0], p[1]);
        stream.lineEnd();
        stream.polygonEnd();
      };
      return stream;
    };
    return p;
  }
  (d3.geo.hammerRetroazimuthal = hammerRetroazimuthalProjection).raw = hammerRetroazimuthal;
  var hammerAzimuthalEqualArea = d3.geo.azimuthalEqualArea.raw;
  function hammer(A, B) {
    if (arguments.length < 2) B = A;
    if (B === 1) return hammerAzimuthalEqualArea;
    if (B === Infinity) return hammerQuarticAuthalic;
    function forward(Î», Ï†) {
      var coordinates = hammerAzimuthalEqualArea(Î» / B, Ï†);
      coordinates[0] *= A;
      return coordinates;
    }
    forward.invert = function(x, y) {
      var coordinates = hammerAzimuthalEqualArea.invert(x / A, y);
      coordinates[0] *= B;
      return coordinates;
    };
    return forward;
  }
  function hammerProjection() {
    var B = 2, m = projectionMutator(hammer), p = m(B);
    p.coefficient = function(_) {
      if (!arguments.length) return B;
      return m(B = +_);
    };
    return p;
  }
  function hammerQuarticAuthalic(Î», Ï†) {
    return [ Î» * Math.cos(Ï†) / Math.cos(Ï† /= 2), 2 * Math.sin(Ï†) ];
  }
  hammerQuarticAuthalic.invert = function(x, y) {
    var Ï† = 2 * asin(y / 2);
    return [ x * Math.cos(Ï† / 2) / Math.cos(Ï†), Ï† ];
  };
  (d3.geo.hammer = hammerProjection).raw = hammer;
  function hatano(Î», Ï†) {
    var c = Math.sin(Ï†) * (Ï† < 0 ? 2.43763 : 2.67595);
    for (var i = 0, Î´; i < 20; i++) {
      Ï† -= Î´ = (Ï† + Math.sin(Ï†) - c) / (1 + Math.cos(Ï†));
      if (Math.abs(Î´) < Îµ) break;
    }
    return [ .85 * Î» * Math.cos(Ï† *= .5), Math.sin(Ï†) * (Ï† < 0 ? 1.93052 : 1.75859) ];
  }
  hatano.invert = function(x, y) {
    var Î¸ = Math.abs(Î¸ = y * (y < 0 ? .5179951515653813 : .5686373742600607)) > 1 - Îµ ? Î¸ > 0 ? halfÏ€ : -halfÏ€ : asin(Î¸);
    return [ 1.1764705882352942 * x / Math.cos(Î¸), Math.abs(Î¸ = ((Î¸ += Î¸) + Math.sin(Î¸)) * (y < 0 ? .4102345310814193 : .3736990601468637)) > 1 - Îµ ? Î¸ > 0 ? halfÏ€ : -halfÏ€ : asin(Î¸) ];
  };
  (d3.geo.hatano = function() {
    return projection(hatano);
  }).raw = hatano;
  var healpixParallel = 41 + 48 / 36 + 37 / 3600;
  function healpix(h) {
    var lambert = d3.geo.cylindricalEqualArea.raw(0), Ï†0 = healpixParallel * Ï€ / 180, dx0 = 2 * Ï€, dx1 = d3.geo.collignon.raw(Ï€, Ï†0)[0] - d3.geo.collignon.raw(-Ï€, Ï†0)[0], y0 = lambert(0, Ï†0)[1], y1 = d3.geo.collignon.raw(0, Ï†0)[1], dy1 = d3.geo.collignon.raw(0, halfÏ€)[1] - y1, k = 2 * Ï€ / h;
    function forward(Î», Ï†) {
      var point, Ï†2 = Math.abs(Ï†);
      if (Ï†2 > Ï†0) {
        var i = Math.min(h - 1, Math.max(0, Math.floor((Î» + Ï€) / k)));
        Î» += Ï€ * (h - 1) / h - i * k;
        point = d3.geo.collignon.raw(Î», Ï†2);
        point[0] = point[0] * dx0 / dx1 - dx0 * (h - 1) / (2 * h) + i * dx0 / h;
        point[1] = y0 + (point[1] - y1) * 4 * dy1 / dx0;
        if (Ï† < 0) point[1] = -point[1];
      } else {
        point = lambert(Î», Ï†);
      }
      point[0] /= 2;
      return point;
    }
    forward.invert = function(x, y) {
      x *= 2;
      var y2 = Math.abs(y);
      if (y2 > y0) {
        var i = Math.min(h - 1, Math.max(0, Math.floor((x + Ï€) / k)));
        x = (x + Ï€ * (h - 1) / h - i * k) * dx1 / dx0;
        var point = d3.geo.collignon.raw.invert(x, .25 * (y2 - y0) * dx0 / dy1 + y1);
        point[0] -= Ï€ * (h - 1) / h - i * k;
        if (y < 0) point[1] = -point[1];
        return point;
      }
      return lambert.invert(x, y);
    };
    return forward;
  }
  function healpixProjection() {
    var n = 2, m = projectionMutator(healpix), p = m(n), stream_ = p.stream;
    p.lobes = function(_) {
      if (!arguments.length) return n;
      return m(n = +_);
    };
    p.stream = function(stream) {
      var rotate = p.rotate(), rotateStream = stream_(stream), sphereStream = (p.rotate([ 0, 0 ]), 
      stream_(stream));
      p.rotate(rotate);
      rotateStream.sphere = function() {
        d3.geo.stream(sphere(), sphereStream);
      };
      return rotateStream;
    };
    function sphere() {
      var step = 180 / n;
      return {
        type: "Polygon",
        coordinates: [ d3.range(-180, 180 + step / 2, step).map(function(x, i) {
          return [ x, i & 1 ? 90 - 1e-6 : healpixParallel ];
        }).concat(d3.range(180, -180 - step / 2, -step).map(function(x, i) {
          return [ x, i & 1 ? -90 + 1e-6 : -healpixParallel ];
        })) ]
      };
    }
    return p;
  }
  (d3.geo.healpix = healpixProjection).raw = healpix;
  function hill(K) {
    var L = 1 + K, sinÎ² = Math.sin(1 / L), Î² = asin(sinÎ²), A = 2 * Math.sqrt(Ï€ / (B = Ï€ + 4 * Î² * L)), B, Ï0 = .5 * A * (L + Math.sqrt(K * (2 + K))), K2 = K * K, L2 = L * L;
    function forward(Î», Ï†) {
      var t = 1 - Math.sin(Ï†), Ï, Ï‰;
      if (t && t < 2) {
        var Î¸ = halfÏ€ - Ï†, i = 25, Î´;
        do {
          var sinÎ¸ = Math.sin(Î¸), cosÎ¸ = Math.cos(Î¸), Î²_Î²1 = Î² + Math.atan2(sinÎ¸, L - cosÎ¸), C = 1 + L2 - 2 * L * cosÎ¸;
          Î¸ -= Î´ = (Î¸ - K2 * Î² - L * sinÎ¸ + C * Î²_Î²1 - .5 * t * B) / (2 * L * sinÎ¸ * Î²_Î²1);
        } while (Math.abs(Î´) > Îµ2 && --i > 0);
        Ï = A * Math.sqrt(C);
        Ï‰ = Î» * Î²_Î²1 / Ï€;
      } else {
        Ï = A * (K + t);
        Ï‰ = Î» * Î² / Ï€;
      }
      return [ Ï * Math.sin(Ï‰), Ï0 - Ï * Math.cos(Ï‰) ];
    }
    forward.invert = function(x, y) {
      var Ï2 = x * x + (y -= Ï0) * y, cosÎ¸ = (1 + L2 - Ï2 / (A * A)) / (2 * L), Î¸ = acos(cosÎ¸), sinÎ¸ = Math.sin(Î¸), Î²_Î²1 = Î² + Math.atan2(sinÎ¸, L - cosÎ¸);
      return [ asin(x / Math.sqrt(Ï2)) * Ï€ / Î²_Î²1, asin(1 - 2 * (Î¸ - K2 * Î² - L * sinÎ¸ + (1 + L2 - 2 * L * cosÎ¸) * Î²_Î²1) / B) ];
    };
    return forward;
  }
  function hillProjection() {
    var K = 1, m = projectionMutator(hill), p = m(K);
    p.ratio = function(_) {
      if (!arguments.length) return K;
      return m(K = +_);
    };
    return p;
  }
  (d3.geo.hill = hillProjection).raw = hill;
  var sinuMollweideÏ† = .7109889596207567, sinuMollweideY = .0528035274542;
  function sinuMollweide(Î», Ï†) {
    return Ï† > -sinuMollweideÏ† ? (Î» = mollweide(Î», Ï†), Î»[1] += sinuMollweideY, Î») : sinusoidal(Î», Ï†);
  }
  sinuMollweide.invert = function(x, y) {
    return y > -sinuMollweideÏ† ? mollweide.invert(x, y - sinuMollweideY) : sinusoidal.invert(x, y);
  };
  (d3.geo.sinuMollweide = function() {
    return projection(sinuMollweide).rotate([ -20, -55 ]);
  }).raw = sinuMollweide;
  function homolosine(Î», Ï†) {
    return Math.abs(Ï†) > sinuMollweideÏ† ? (Î» = mollweide(Î», Ï†), Î»[1] -= Ï† > 0 ? sinuMollweideY : -sinuMollweideY, 
    Î») : sinusoidal(Î», Ï†);
  }
  homolosine.invert = function(x, y) {
    return Math.abs(y) > sinuMollweideÏ† ? mollweide.invert(x, y + (y > 0 ? sinuMollweideY : -sinuMollweideY)) : sinusoidal.invert(x, y);
  };
  (d3.geo.homolosine = function() {
    return projection(homolosine);
  }).raw = homolosine;
  function kavrayskiy7(Î», Ï†) {
    return [ 3 * Î» / (2 * Ï€) * Math.sqrt(Ï€ * Ï€ / 3 - Ï† * Ï†), Ï† ];
  }
  kavrayskiy7.invert = function(x, y) {
    return [ 2 / 3 * Ï€ * x / Math.sqrt(Ï€ * Ï€ / 3 - y * y), y ];
  };
  (d3.geo.kavrayskiy7 = function() {
    return projection(kavrayskiy7);
  }).raw = kavrayskiy7;
  function lagrange(n) {
    function forward(Î», Ï†) {
      if (Math.abs(Math.abs(Ï†) - halfÏ€) < Îµ) return [ 0, Ï† < 0 ? -2 : 2 ];
      var sinÏ† = Math.sin(Ï†), v = Math.pow((1 + sinÏ†) / (1 - sinÏ†), n / 2), c = .5 * (v + 1 / v) + Math.cos(Î» *= n);
      return [ 2 * Math.sin(Î») / c, (v - 1 / v) / c ];
    }
    forward.invert = function(x, y) {
      var y0 = Math.abs(y);
      if (Math.abs(y0 - 2) < Îµ) return x ? null : [ 0, sgn(y) * halfÏ€ ];
      if (y0 > 2) return null;
      x /= 2, y /= 2;
      var x2 = x * x, y2 = y * y, t = 2 * y / (1 + x2 + y2);
      t = Math.pow((1 + t) / (1 - t), 1 / n);
      return [ Math.atan2(2 * x, 1 - x2 - y2) / n, asin((t - 1) / (t + 1)) ];
    };
    return forward;
  }
  function lagrangeProjection() {
    var n = .5, m = projectionMutator(lagrange), p = m(n);
    p.spacing = function(_) {
      if (!arguments.length) return n;
      return m(n = +_);
    };
    return p;
  }
  (d3.geo.lagrange = lagrangeProjection).raw = lagrange;
  function larrivee(Î», Ï†) {
    return [ Î» * (1 + Math.sqrt(Math.cos(Ï†))) / 2, Ï† / (Math.cos(Ï† / 2) * Math.cos(Î» / 6)) ];
  }
  larrivee.invert = function(x, y) {
    var x0 = Math.abs(x), y0 = Math.abs(y), Ï€_sqrt2 = Ï€ / Math.SQRT2, Î» = Îµ, Ï† = halfÏ€;
    if (y0 < Ï€_sqrt2) Ï† *= y0 / Ï€_sqrt2; else Î» += 6 * acos(Ï€_sqrt2 / y0);
    for (var i = 0; i < 25; i++) {
      var sinÏ† = Math.sin(Ï†), sqrtcosÏ† = asqrt(Math.cos(Ï†)), sinÏ†_2 = Math.sin(Ï† / 2), cosÏ†_2 = Math.cos(Ï† / 2), sinÎ»_6 = Math.sin(Î» / 6), cosÎ»_6 = Math.cos(Î» / 6), f0 = .5 * Î» * (1 + sqrtcosÏ†) - x0, f1 = Ï† / (cosÏ†_2 * cosÎ»_6) - y0, df0dÏ† = sqrtcosÏ† ? -.25 * Î» * sinÏ† / sqrtcosÏ† : 0, df0dÎ» = .5 * (1 + sqrtcosÏ†), df1dÏ† = (1 + .5 * Ï† * sinÏ†_2 / cosÏ†_2) / (cosÏ†_2 * cosÎ»_6), df1dÎ» = Ï† / cosÏ†_2 * (sinÎ»_6 / 6) / (cosÎ»_6 * cosÎ»_6), denom = df0dÏ† * df1dÎ» - df1dÏ† * df0dÎ», dÏ† = (f0 * df1dÎ» - f1 * df0dÎ») / denom, dÎ» = (f1 * df0dÏ† - f0 * df1dÏ†) / denom;
      Ï† -= dÏ†;
      Î» -= dÎ»;
      if (Math.abs(dÏ†) < Îµ && Math.abs(dÎ») < Îµ) break;
    }
    return [ x < 0 ? -Î» : Î», y < 0 ? -Ï† : Ï† ];
  };
  (d3.geo.larrivee = function() {
    return projection(larrivee);
  }).raw = larrivee;
  function laskowski(Î», Ï†) {
    var Î»2 = Î» * Î», Ï†2 = Ï† * Ï†;
    return [ Î» * (.975534 + Ï†2 * (-.119161 + Î»2 * -.0143059 + Ï†2 * -.0547009)), Ï† * (1.00384 + Î»2 * (.0802894 + Ï†2 * -.02855 + Î»2 * 199025e-9) + Ï†2 * (.0998909 + Ï†2 * -.0491032)) ];
  }
  laskowski.invert = function(x, y) {
    var Î» = sgn(x) * Ï€, Ï† = y / 2, i = 50;
    do {
      var Î»2 = Î» * Î», Ï†2 = Ï† * Ï†, Î»Ï† = Î» * Ï†, fx = Î» * (.975534 + Ï†2 * (-.119161 + Î»2 * -.0143059 + Ï†2 * -.0547009)) - x, fy = Ï† * (1.00384 + Î»2 * (.0802894 + Ï†2 * -.02855 + Î»2 * 199025e-9) + Ï†2 * (.0998909 + Ï†2 * -.0491032)) - y, Î´xÎ´Î» = .975534 - Ï†2 * (.119161 + 3 * Î»2 * .0143059 + Ï†2 * .0547009), Î´xÎ´Ï† = -Î»Ï† * (2 * .119161 + 4 * .0547009 * Ï†2 + 2 * .0143059 * Î»2), Î´yÎ´Î» = Î»Ï† * (2 * .0802894 + 4 * 199025e-9 * Î»2 + 2 * -.02855 * Ï†2), Î´yÎ´Ï† = 1.00384 + Î»2 * (.0802894 + 199025e-9 * Î»2) + Ï†2 * (3 * (.0998909 - .02855 * Î»2) - 5 * .0491032 * Ï†2), denominator = Î´xÎ´Ï† * Î´yÎ´Î» - Î´yÎ´Ï† * Î´xÎ´Î», Î´Î» = (fy * Î´xÎ´Ï† - fx * Î´yÎ´Ï†) / denominator, Î´Ï† = (fx * Î´yÎ´Î» - fy * Î´xÎ´Î») / denominator;
      Î» -= Î´Î», Ï† -= Î´Ï†;
    } while ((Math.abs(Î´Î») > Îµ || Math.abs(Î´Ï†) > Îµ) && --i > 0);
    return i && [ Î», Ï† ];
  };
  (d3.geo.laskowski = function() {
    return projection(laskowski);
  }).raw = laskowski;
  function littrow(Î», Ï†) {
    return [ Math.sin(Î») / Math.cos(Ï†), Math.tan(Ï†) * Math.cos(Î») ];
  }
  littrow.invert = function(x, y) {
    var x2 = x * x, y2 = y * y, y2_1 = y2 + 1, cosÏ† = x ? Math.SQRT1_2 * Math.sqrt((y2_1 - Math.sqrt(x2 * x2 + 2 * x2 * (y2 - 1) + y2_1 * y2_1)) / x2 + 1) : 1 / Math.sqrt(y2_1);
    return [ asin(x * cosÏ†), sgn(y) * acos(cosÏ†) ];
  };
  (d3.geo.littrow = function() {
    return projection(littrow);
  }).raw = littrow;
  function loximuthal(Ï†0) {
    var cosÏ†0 = Math.cos(Ï†0), tanÏ†0 = Math.tan(Ï€ / 4 + Ï†0 / 2);
    function forward(Î», Ï†) {
      var y = Ï† - Ï†0, x = Math.abs(y) < Îµ ? Î» * cosÏ†0 : Math.abs(x = Ï€ / 4 + Ï† / 2) < Îµ || Math.abs(Math.abs(x) - halfÏ€) < Îµ ? 0 : Î» * y / Math.log(Math.tan(x) / tanÏ†0);
      return [ x, y ];
    }
    forward.invert = function(x, y) {
      var Î», Ï† = y + Ï†0;
      return [ Math.abs(y) < Îµ ? x / cosÏ†0 : Math.abs(Î» = Ï€ / 4 + Ï† / 2) < Îµ || Math.abs(Math.abs(Î») - halfÏ€) < Îµ ? 0 : x * Math.log(Math.tan(Î») / tanÏ†0) / y, Ï† ];
    };
    return forward;
  }
  (d3.geo.loximuthal = function() {
    return parallel1Projection(loximuthal).parallel(40);
  }).raw = loximuthal;
  function miller(Î», Ï†) {
    return [ Î», 1.25 * Math.log(Math.tan(Ï€ / 4 + .4 * Ï†)) ];
  }
  miller.invert = function(x, y) {
    return [ x, 2.5 * Math.atan(Math.exp(.8 * y)) - .625 * Ï€ ];
  };
  (d3.geo.miller = function() {
    return projection(miller);
  }).raw = miller;
  function modifiedStereographic(C) {
    var m = C.length - 1;
    function forward(Î», Ï†) {
      var cosÏ† = Math.cos(Ï†), k = 2 / (1 + cosÏ† * Math.cos(Î»)), zr = k * cosÏ† * Math.sin(Î»), zi = k * Math.sin(Ï†), i = m, w = C[i], ar = w[0], ai = w[1], t;
      while (--i >= 0) {
        w = C[i];
        ar = w[0] + zr * (t = ar) - zi * ai;
        ai = w[1] + zr * ai + zi * t;
      }
      ar = zr * (t = ar) - zi * ai;
      ai = zr * ai + zi * t;
      return [ ar, ai ];
    }
    forward.invert = function(x, y) {
      var i = 20, zr = x, zi = y;
      do {
        var j = m, w = C[j], ar = w[0], ai = w[1], br = 0, bi = 0, t;
        while (--j >= 0) {
          w = C[j];
          br = ar + zr * (t = br) - zi * bi;
          bi = ai + zr * bi + zi * t;
          ar = w[0] + zr * (t = ar) - zi * ai;
          ai = w[1] + zr * ai + zi * t;
        }
        br = ar + zr * (t = br) - zi * bi;
        bi = ai + zr * bi + zi * t;
        ar = zr * (t = ar) - zi * ai - x;
        ai = zr * ai + zi * t - y;
        var denominator = br * br + bi * bi, Î´r, Î´i;
        zr -= Î´r = (ar * br + ai * bi) / denominator;
        zi -= Î´i = (ai * br - ar * bi) / denominator;
      } while (Math.abs(Î´r) + Math.abs(Î´i) > Îµ * Îµ && --i > 0);
      if (i) {
        var Ï = Math.sqrt(zr * zr + zi * zi), c = 2 * Math.atan(Ï * .5), sinc = Math.sin(c);
        return [ Math.atan2(zr * sinc, Ï * Math.cos(c)), Ï ? asin(zi * sinc / Ï) : 0 ];
      }
    };
    return forward;
  }
  var modifiedStereographicCoefficients = {
    alaska: [ [ .9972523, 0 ], [ .0052513, -.0041175 ], [ .0074606, .0048125 ], [ -.0153783, -.1968253 ], [ .0636871, -.1408027 ], [ .3660976, -.2937382 ] ],
    gs48: [ [ .98879, 0 ], [ 0, 0 ], [ -.050909, 0 ], [ 0, 0 ], [ .075528, 0 ] ],
    gs50: [ [ .984299, 0 ], [ .0211642, .0037608 ], [ -.1036018, -.0575102 ], [ -.0329095, -.0320119 ], [ .0499471, .1223335 ], [ .026046, .0899805 ], [ 7388e-7, -.1435792 ], [ .0075848, -.1334108 ], [ -.0216473, .0776645 ], [ -.0225161, .0853673 ] ],
    miller: [ [ .9245, 0 ], [ 0, 0 ], [ .01943, 0 ] ],
    lee: [ [ .721316, 0 ], [ 0, 0 ], [ -.00881625, -.00617325 ] ]
  };
  function modifiedStereographicProjection() {
    var coefficients = modifiedStereographicCoefficients.miller, m = projectionMutator(modifiedStereographic), p = m(coefficients);
    p.coefficients = function(_) {
      if (!arguments.length) return coefficients;
      return m(coefficients = typeof _ === "string" ? modifiedStereographicCoefficients[_] : _);
    };
    return p;
  }
  (d3.geo.modifiedStereographic = modifiedStereographicProjection).raw = modifiedStereographic;
  function mtFlatPolarParabolic(Î», Ï†) {
    var sqrt6 = Math.sqrt(6), sqrt7 = Math.sqrt(7), Î¸ = Math.asin(7 * Math.sin(Ï†) / (3 * sqrt6));
    return [ sqrt6 * Î» * (2 * Math.cos(2 * Î¸ / 3) - 1) / sqrt7, 9 * Math.sin(Î¸ / 3) / sqrt7 ];
  }
  mtFlatPolarParabolic.invert = function(x, y) {
    var sqrt6 = Math.sqrt(6), sqrt7 = Math.sqrt(7), Î¸ = 3 * asin(y * sqrt7 / 9);
    return [ x * sqrt7 / (sqrt6 * (2 * Math.cos(2 * Î¸ / 3) - 1)), asin(Math.sin(Î¸) * 3 * sqrt6 / 7) ];
  };
  (d3.geo.mtFlatPolarParabolic = function() {
    return projection(mtFlatPolarParabolic);
  }).raw = mtFlatPolarParabolic;
  function mtFlatPolarQuartic(Î», Ï†) {
    var k = (1 + Math.SQRT1_2) * Math.sin(Ï†), Î¸ = Ï†;
    for (var i = 0, Î´; i < 25; i++) {
      Î¸ -= Î´ = (Math.sin(Î¸ / 2) + Math.sin(Î¸) - k) / (.5 * Math.cos(Î¸ / 2) + Math.cos(Î¸));
      if (Math.abs(Î´) < Îµ) break;
    }
    return [ Î» * (1 + 2 * Math.cos(Î¸) / Math.cos(Î¸ / 2)) / (3 * Math.SQRT2), 2 * Math.sqrt(3) * Math.sin(Î¸ / 2) / Math.sqrt(2 + Math.SQRT2) ];
  }
  mtFlatPolarQuartic.invert = function(x, y) {
    var sinÎ¸_2 = y * Math.sqrt(2 + Math.SQRT2) / (2 * Math.sqrt(3)), Î¸ = 2 * asin(sinÎ¸_2);
    return [ 3 * Math.SQRT2 * x / (1 + 2 * Math.cos(Î¸) / Math.cos(Î¸ / 2)), asin((sinÎ¸_2 + Math.sin(Î¸)) / (1 + Math.SQRT1_2)) ];
  };
  (d3.geo.mtFlatPolarQuartic = function() {
    return projection(mtFlatPolarQuartic);
  }).raw = mtFlatPolarQuartic;
  function mtFlatPolarSinusoidal(Î», Ï†) {
    var A = Math.sqrt(6 / (4 + Ï€)), k = (1 + Ï€ / 4) * Math.sin(Ï†), Î¸ = Ï† / 2;
    for (var i = 0, Î´; i < 25; i++) {
      Î¸ -= Î´ = (Î¸ / 2 + Math.sin(Î¸) - k) / (.5 + Math.cos(Î¸));
      if (Math.abs(Î´) < Îµ) break;
    }
    return [ A * (.5 + Math.cos(Î¸)) * Î» / 1.5, A * Î¸ ];
  }
  mtFlatPolarSinusoidal.invert = function(x, y) {
    var A = Math.sqrt(6 / (4 + Ï€)), Î¸ = y / A;
    if (Math.abs(Math.abs(Î¸) - halfÏ€) < Îµ) Î¸ = Î¸ < 0 ? -halfÏ€ : halfÏ€;
    return [ 1.5 * x / (A * (.5 + Math.cos(Î¸))), asin((Î¸ / 2 + Math.sin(Î¸)) / (1 + Ï€ / 4)) ];
  };
  (d3.geo.mtFlatPolarSinusoidal = function() {
    return projection(mtFlatPolarSinusoidal);
  }).raw = mtFlatPolarSinusoidal;
  function naturalEarth(Î», Ï†) {
    var Ï†2 = Ï† * Ï†, Ï†4 = Ï†2 * Ï†2;
    return [ Î» * (.8707 - .131979 * Ï†2 + Ï†4 * (-.013791 + Ï†4 * (.003971 * Ï†2 - .001529 * Ï†4))), Ï† * (1.007226 + Ï†2 * (.015085 + Ï†4 * (-.044475 + .028874 * Ï†2 - .005916 * Ï†4))) ];
  }
  naturalEarth.invert = function(x, y) {
    var Ï† = y, i = 25, Î´;
    do {
      var Ï†2 = Ï† * Ï†, Ï†4 = Ï†2 * Ï†2;
      Ï† -= Î´ = (Ï† * (1.007226 + Ï†2 * (.015085 + Ï†4 * (-.044475 + .028874 * Ï†2 - .005916 * Ï†4))) - y) / (1.007226 + Ï†2 * (.015085 * 3 + Ï†4 * (-.044475 * 7 + .028874 * 9 * Ï†2 - .005916 * 11 * Ï†4)));
    } while (Math.abs(Î´) > Îµ && --i > 0);
    return [ x / (.8707 + (Ï†2 = Ï† * Ï†) * (-.131979 + Ï†2 * (-.013791 + Ï†2 * Ï†2 * Ï†2 * (.003971 - .001529 * Ï†2)))), Ï† ];
  };
  (d3.geo.naturalEarth = function() {
    return projection(naturalEarth);
  }).raw = naturalEarth;
  function nellHammer(Î», Ï†) {
    return [ Î» * (1 + Math.cos(Ï†)) / 2, 2 * (Ï† - Math.tan(Ï† / 2)) ];
  }
  nellHammer.invert = function(x, y) {
    var p = y / 2;
    for (var i = 0, Î´ = Infinity; i < 10 && Math.abs(Î´) > Îµ; i++) {
      var c = Math.cos(y / 2);
      y -= Î´ = (y - Math.tan(y / 2) - p) / (1 - .5 / (c * c));
    }
    return [ 2 * x / (1 + Math.cos(y)), y ];
  };
  (d3.geo.nellHammer = function() {
    return projection(nellHammer);
  }).raw = nellHammer;
  var peirceQuincuncialProjection = quincuncialProjection(guyou);
  (d3.geo.peirceQuincuncial = function() {
    return peirceQuincuncialProjection().quincuncial(true).rotate([ -90, -90, 45 ]).clipAngle(180 - 1e-6);
  }).raw = peirceQuincuncialProjection.raw;
  function polyconic(Î», Ï†) {
    if (Math.abs(Ï†) < Îµ) return [ Î», 0 ];
    var tanÏ† = Math.tan(Ï†), k = Î» * Math.sin(Ï†);
    return [ Math.sin(k) / tanÏ†, Ï† + (1 - Math.cos(k)) / tanÏ† ];
  }
  polyconic.invert = function(x, y) {
    if (Math.abs(y) < Îµ) return [ x, 0 ];
    var k = x * x + y * y, Ï† = y * .5, i = 10, Î´;
    do {
      var tanÏ† = Math.tan(Ï†), secÏ† = 1 / Math.cos(Ï†), j = k - 2 * y * Ï† + Ï† * Ï†;
      Ï† -= Î´ = (tanÏ† * j + 2 * (Ï† - y)) / (2 + j * secÏ† * secÏ† + 2 * (Ï† - y) * tanÏ†);
    } while (Math.abs(Î´) > Îµ && --i > 0);
    tanÏ† = Math.tan(Ï†);
    return [ (Math.abs(y) < Math.abs(Ï† + 1 / tanÏ†) ? asin(x * tanÏ†) : sgn(x) * (acos(Math.abs(x * tanÏ†)) + halfÏ€)) / Math.sin(Ï†), Ï† ];
  };
  (d3.geo.polyconic = function() {
    return projection(polyconic);
  }).raw = polyconic;
  function rectangularPolyconic(Ï†0) {
    var sinÏ†0 = Math.sin(Ï†0);
    function forward(Î», Ï†) {
      var A = sinÏ†0 ? Math.tan(Î» * sinÏ†0 / 2) / sinÏ†0 : Î» / 2;
      if (!Ï†) return [ 2 * A, -Ï†0 ];
      var E = 2 * Math.atan(A * Math.sin(Ï†)), cotÏ† = 1 / Math.tan(Ï†);
      return [ Math.sin(E) * cotÏ†, Ï† + (1 - Math.cos(E)) * cotÏ† - Ï†0 ];
    }
    forward.invert = function(x, y) {
      if (Math.abs(y += Ï†0) < Îµ) return [ sinÏ†0 ? 2 * Math.atan(sinÏ†0 * x / 2) / sinÏ†0 : x, 0 ];
      var k = x * x + y * y, Ï† = 0, i = 10, Î´;
      do {
        var tanÏ† = Math.tan(Ï†), secÏ† = 1 / Math.cos(Ï†), j = k - 2 * y * Ï† + Ï† * Ï†;
        Ï† -= Î´ = (tanÏ† * j + 2 * (Ï† - y)) / (2 + j * secÏ† * secÏ† + 2 * (Ï† - y) * tanÏ†);
      } while (Math.abs(Î´) > Îµ && --i > 0);
      var E = x * (tanÏ† = Math.tan(Ï†)), A = Math.tan(Math.abs(y) < Math.abs(Ï† + 1 / tanÏ†) ? asin(E) * .5 : acos(E) * .5 + Ï€ / 4) / Math.sin(Ï†);
      return [ sinÏ†0 ? 2 * Math.atan(sinÏ†0 * A) / sinÏ†0 : 2 * A, Ï† ];
    };
    return forward;
  }
  (d3.geo.rectangularPolyconic = function() {
    return parallel1Projection(rectangularPolyconic);
  }).raw = rectangularPolyconic;
  var robinsonConstants = [ [ .9986, -.062 ], [ 1, 0 ], [ .9986, .062 ], [ .9954, .124 ], [ .99, .186 ], [ .9822, .248 ], [ .973, .31 ], [ .96, .372 ], [ .9427, .434 ], [ .9216, .4958 ], [ .8962, .5571 ], [ .8679, .6176 ], [ .835, .6769 ], [ .7986, .7346 ], [ .7597, .7903 ], [ .7186, .8435 ], [ .6732, .8936 ], [ .6213, .9394 ], [ .5722, .9761 ], [ .5322, 1 ] ];
  robinsonConstants.forEach(function(d) {
    d[1] *= 1.0144;
  });
  function robinson(Î», Ï†) {
    var i = Math.min(18, Math.abs(Ï†) * 36 / Ï€), i0 = Math.floor(i), di = i - i0, ax = (k = robinsonConstants[i0])[0], ay = k[1], bx = (k = robinsonConstants[++i0])[0], by = k[1], cx = (k = robinsonConstants[Math.min(19, ++i0)])[0], cy = k[1], k;
    return [ Î» * (bx + di * (cx - ax) / 2 + di * di * (cx - 2 * bx + ax) / 2), (Ï† > 0 ? halfÏ€ : -halfÏ€) * (by + di * (cy - ay) / 2 + di * di * (cy - 2 * by + ay) / 2) ];
  }
  robinson.invert = function(x, y) {
    var yy = y / halfÏ€, Ï† = yy * 90, i = Math.min(18, Math.abs(Ï† / 5)), i0 = Math.max(0, Math.floor(i));
    do {
      var ay = robinsonConstants[i0][1], by = robinsonConstants[i0 + 1][1], cy = robinsonConstants[Math.min(19, i0 + 2)][1], u = cy - ay, v = cy - 2 * by + ay, t = 2 * (Math.abs(yy) - by) / u, c = v / u, di = t * (1 - c * t * (1 - 2 * c * t));
      if (di >= 0 || i0 === 1) {
        Ï† = (y >= 0 ? 5 : -5) * (di + i);
        var j = 50, Î´;
        do {
          i = Math.min(18, Math.abs(Ï†) / 5);
          i0 = Math.floor(i);
          di = i - i0;
          ay = robinsonConstants[i0][1];
          by = robinsonConstants[i0 + 1][1];
          cy = robinsonConstants[Math.min(19, i0 + 2)][1];
          Ï† -= (Î´ = (y >= 0 ? halfÏ€ : -halfÏ€) * (by + di * (cy - ay) / 2 + di * di * (cy - 2 * by + ay) / 2) - y) * degrees;
        } while (Math.abs(Î´) > Îµ2 && --j > 0);
        break;
      }
    } while (--i0 >= 0);
    var ax = robinsonConstants[i0][0], bx = robinsonConstants[i0 + 1][0], cx = robinsonConstants[Math.min(19, i0 + 2)][0];
    return [ x / (bx + di * (cx - ax) / 2 + di * di * (cx - 2 * bx + ax) / 2), Ï† * radians ];
  };
  (d3.geo.robinson = function() {
    return projection(robinson);
  }).raw = robinson;
  function satelliteVertical(P) {
    function forward(Î», Ï†) {
      var cosÏ† = Math.cos(Ï†), k = (P - 1) / (P - cosÏ† * Math.cos(Î»));
      return [ k * cosÏ† * Math.sin(Î»), k * Math.sin(Ï†) ];
    }
    forward.invert = function(x, y) {
      var Ï2 = x * x + y * y, Ï = Math.sqrt(Ï2), sinc = (P - Math.sqrt(1 - Ï2 * (P + 1) / (P - 1))) / ((P - 1) / Ï + Ï / (P - 1));
      return [ Math.atan2(x * sinc, Ï * Math.sqrt(1 - sinc * sinc)), Ï ? asin(y * sinc / Ï) : 0 ];
    };
    return forward;
  }
  function satellite(P, Ï‰) {
    var vertical = satelliteVertical(P);
    if (!Ï‰) return vertical;
    var cosÏ‰ = Math.cos(Ï‰), sinÏ‰ = Math.sin(Ï‰);
    function forward(Î», Ï†) {
      var coordinates = vertical(Î», Ï†), y = coordinates[1], A = y * sinÏ‰ / (P - 1) + cosÏ‰;
      return [ coordinates[0] * cosÏ‰ / A, y / A ];
    }
    forward.invert = function(x, y) {
      var k = (P - 1) / (P - 1 - y * sinÏ‰);
      return vertical.invert(k * x, k * y * cosÏ‰);
    };
    return forward;
  }
  function satelliteProjection() {
    var P = 1.4, Ï‰ = 0, m = projectionMutator(satellite), p = m(P, Ï‰);
    p.distance = function(_) {
      if (!arguments.length) return P;
      return m(P = +_, Ï‰);
    };
    p.tilt = function(_) {
      if (!arguments.length) return Ï‰ * 180 / Ï€;
      return m(P, Ï‰ = _ * Ï€ / 180);
    };
    return p;
  }
  (d3.geo.satellite = satelliteProjection).raw = satellite;
  function times(Î», Ï†) {
    var t = Math.tan(Ï† / 2), s = Math.sin(Ï€ / 4 * t);
    return [ Î» * (.74482 - .34588 * s * s), 1.70711 * t ];
  }
  times.invert = function(x, y) {
    var t = y / 1.70711, s = Math.sin(Ï€ / 4 * t);
    return [ x / (.74482 - .34588 * s * s), 2 * Math.atan(t) ];
  };
  (d3.geo.times = function() {
    return projection(times);
  }).raw = times;
  function twoPointEquidistant(z0) {
    if (!z0) return d3.geo.azimuthalEquidistant.raw;
    var Î»a = -z0 / 2, Î»b = -Î»a, z02 = z0 * z0, tanÎ»0 = Math.tan(Î»b), S = .5 / Math.sin(Î»b);
    function forward(Î», Ï†) {
      var za = acos(Math.cos(Ï†) * Math.cos(Î» - Î»a)), zb = acos(Math.cos(Ï†) * Math.cos(Î» - Î»b)), ys = Ï† < 0 ? -1 : 1;
      za *= za, zb *= zb;
      return [ (za - zb) / (2 * z0), ys * asqrt(4 * z02 * zb - (z02 - za + zb) * (z02 - za + zb)) / (2 * z0) ];
    }
    forward.invert = function(x, y) {
      var y2 = y * y, cosza = Math.cos(Math.sqrt(y2 + (t = x + Î»a) * t)), coszb = Math.cos(Math.sqrt(y2 + (t = x + Î»b) * t)), t, d;
      return [ Math.atan2(d = cosza - coszb, t = (cosza + coszb) * tanÎ»0), (y < 0 ? -1 : 1) * acos(Math.sqrt(t * t + d * d) * S) ];
    };
    return forward;
  }
  function twoPointEquidistantProjection() {
    var points = [ [ 0, 0 ], [ 0, 0 ] ], m = projectionMutator(twoPointEquidistant), p = m(0), rotate = p.rotate;
    delete p.rotate;
    p.points = function(_) {
      if (!arguments.length) return points;
      points = _;
      var interpolate = d3.geo.interpolate(_[0], _[1]), origin = interpolate(.5), p = d3.geo.rotation([ -origin[0], -origin[1] ])(_[0]), b = interpolate.distance * .5, c = (p[0] < 0 ? -1 : +1) * p[1] * radians, Î³ = asin(Math.sin(c) / Math.sin(b));
      rotate.call(p, [ -origin[0], -origin[1], -Î³ * degrees ]);
      return m(b * 2);
    };
    return p;
  }
  (d3.geo.twoPointEquidistant = twoPointEquidistantProjection).raw = twoPointEquidistant;
  function twoPointAzimuthal(d) {
    var cosd = Math.cos(d);
    function forward(Î», Ï†) {
      var coordinates = d3.geo.gnomonic.raw(Î», Ï†);
      coordinates[0] *= cosd;
      return coordinates;
    }
    forward.invert = function(x, y) {
      return d3.geo.gnomonic.raw.invert(x / cosd, y);
    };
    return forward;
  }
  function twoPointAzimuthalProjection() {
    var points = [ [ 0, 0 ], [ 0, 0 ] ], m = projectionMutator(twoPointAzimuthal), p = m(0), rotate = p.rotate;
    delete p.rotate;
    p.points = function(_) {
      if (!arguments.length) return points;
      points = _;
      var interpolate = d3.geo.interpolate(_[0], _[1]), origin = interpolate(.5), p = d3.geo.rotation([ -origin[0], -origin[1] ])(_[0]), b = interpolate.distance * .5, c = (p[0] < 0 ? -1 : +1) * p[1] * radians, Î³ = asin(Math.sin(c) / Math.sin(b));
      rotate.call(p, [ -origin[0], -origin[1], -Î³ * degrees ]);
      return m(b);
    };
    return p;
  }
  (d3.geo.twoPointAzimuthal = twoPointAzimuthalProjection).raw = twoPointAzimuthal;
  function vanDerGrinten(Î», Ï†) {
    if (Math.abs(Ï†) < Îµ) return [ Î», 0 ];
    var sinÎ¸ = Math.abs(Ï† / halfÏ€), Î¸ = asin(sinÎ¸);
    if (Math.abs(Î») < Îµ || Math.abs(Math.abs(Ï†) - halfÏ€) < Îµ) return [ 0, sgn(Ï†) * Ï€ * Math.tan(Î¸ / 2) ];
    var cosÎ¸ = Math.cos(Î¸), A = Math.abs(Ï€ / Î» - Î» / Ï€) / 2, A2 = A * A, G = cosÎ¸ / (sinÎ¸ + cosÎ¸ - 1), P = G * (2 / sinÎ¸ - 1), P2 = P * P, P2_A2 = P2 + A2, G_P2 = G - P2, Q = A2 + G;
    return [ sgn(Î») * Ï€ * (A * G_P2 + Math.sqrt(A2 * G_P2 * G_P2 - P2_A2 * (G * G - P2))) / P2_A2, sgn(Ï†) * Ï€ * (P * Q - A * Math.sqrt((A2 + 1) * P2_A2 - Q * Q)) / P2_A2 ];
  }
  vanDerGrinten.invert = function(x, y) {
    if (Math.abs(y) < Îµ) return [ x, 0 ];
    if (Math.abs(x) < Îµ) return [ 0, halfÏ€ * Math.sin(2 * Math.atan(y / Ï€)) ];
    var x2 = (x /= Ï€) * x, y2 = (y /= Ï€) * y, x2_y2 = x2 + y2, z = x2_y2 * x2_y2, c1 = -Math.abs(y) * (1 + x2_y2), c2 = c1 - 2 * y2 + x2, c3 = -2 * c1 + 1 + 2 * y2 + z, d = y2 / c3 + (2 * c2 * c2 * c2 / (c3 * c3 * c3) - 9 * c1 * c2 / (c3 * c3)) / 27, a1 = (c1 - c2 * c2 / (3 * c3)) / c3, m1 = 2 * Math.sqrt(-a1 / 3), Î¸1 = acos(3 * d / (a1 * m1)) / 3;
    return [ Ï€ * (x2_y2 - 1 + Math.sqrt(1 + 2 * (x2 - y2) + z)) / (2 * x), sgn(y) * Ï€ * (-m1 * Math.cos(Î¸1 + Ï€ / 3) - c2 / (3 * c3)) ];
  };
  (d3.geo.vanDerGrinten = function() {
    return projection(vanDerGrinten);
  }).raw = vanDerGrinten;
  function vanDerGrinten2(Î», Ï†) {
    if (Math.abs(Ï†) < Îµ) return [ Î», 0 ];
    var sinÎ¸ = Math.abs(Ï† / halfÏ€), Î¸ = asin(sinÎ¸);
    if (Math.abs(Î») < Îµ || Math.abs(Math.abs(Ï†) - halfÏ€) < Îµ) return [ 0, sgn(Ï†) * Ï€ * Math.tan(Î¸ / 2) ];
    var cosÎ¸ = Math.cos(Î¸), A = Math.abs(Ï€ / Î» - Î» / Ï€) / 2, A2 = A * A, x1 = cosÎ¸ * (Math.sqrt(1 + A2) - A * cosÎ¸) / (1 + A2 * sinÎ¸ * sinÎ¸);
    return [ sgn(Î») * Ï€ * x1, sgn(Ï†) * Ï€ * asqrt(1 - x1 * (2 * A + x1)) ];
  }
  vanDerGrinten2.invert = function(x, y) {
    if (!x) return [ 0, halfÏ€ * Math.sin(2 * Math.atan(y / Ï€)) ];
    var x1 = Math.abs(x / Ï€), A = (1 - x1 * x1 - (y /= Ï€) * y) / (2 * x1), A2 = A * A, B = Math.sqrt(A2 + 1);
    return [ sgn(x) * Ï€ * (B - A), sgn(y) * halfÏ€ * Math.sin(2 * Math.atan2(Math.sqrt((1 - 2 * A * x1) * (A + B) - x1), Math.sqrt(B + A + x1))) ];
  };
  (d3.geo.vanDerGrinten2 = function() {
    return projection(vanDerGrinten2);
  }).raw = vanDerGrinten2;
  function vanDerGrinten3(Î», Ï†) {
    if (Math.abs(Ï†) < Îµ) return [ Î», 0 ];
    var sinÎ¸ = Ï† / halfÏ€, Î¸ = asin(sinÎ¸);
    if (Math.abs(Î») < Îµ || Math.abs(Math.abs(Ï†) - halfÏ€) < Îµ) return [ 0, Ï€ * Math.tan(Î¸ / 2) ];
    var A = (Ï€ / Î» - Î» / Ï€) / 2, y1 = sinÎ¸ / (1 + Math.cos(Î¸));
    return [ Ï€ * (sgn(Î») * asqrt(A * A + 1 - y1 * y1) - A), Ï€ * y1 ];
  }
  vanDerGrinten3.invert = function(x, y) {
    if (!y) return [ x, 0 ];
    var y1 = y / Ï€, A = (Ï€ * Ï€ * (1 - y1 * y1) - x * x) / (2 * Ï€ * x);
    return [ x ? Ï€ * (sgn(x) * Math.sqrt(A * A + 1) - A) : 0, halfÏ€ * Math.sin(2 * Math.atan(y1)) ];
  };
  (d3.geo.vanDerGrinten3 = function() {
    return projection(vanDerGrinten3);
  }).raw = vanDerGrinten3;
  function vanDerGrinten4(Î», Ï†) {
    if (!Ï†) return [ Î», 0 ];
    var Ï†0 = Math.abs(Ï†);
    if (!Î» || Ï†0 === halfÏ€) return [ 0, Ï† ];
    var B = Ï†0 / halfÏ€, B2 = B * B, C = (8 * B - B2 * (B2 + 2) - 5) / (2 * B2 * (B - 1)), C2 = C * C, BC = B * C, B_C2 = B2 + C2 + 2 * BC, B_3C = B + 3 * C, Î»0 = Î» / halfÏ€, Î»1 = Î»0 + 1 / Î»0, D = sgn(Math.abs(Î») - halfÏ€) * Math.sqrt(Î»1 * Î»1 - 4), D2 = D * D, F = B_C2 * (B2 + C2 * D2 - 1) + (1 - B2) * (B2 * (B_3C * B_3C + 4 * C2) + 12 * BC * C2 + 4 * C2 * C2), x1 = (D * (B_C2 + C2 - 1) + 2 * asqrt(F)) / (4 * B_C2 + D2);
    return [ sgn(Î») * halfÏ€ * x1, sgn(Ï†) * halfÏ€ * asqrt(1 + D * Math.abs(x1) - x1 * x1) ];
  }
  vanDerGrinten4.invert = function(x, y) {
    if (!x || !y) return [ x, y ];
    y /= Ï€;
    var x1 = sgn(x) * x / halfÏ€, D = (x1 * x1 - 1 + 4 * y * y) / Math.abs(x1), D2 = D * D, B = 2 * y, i = 50;
    do {
      var B2 = B * B, C = (8 * B - B2 * (B2 + 2) - 5) / (2 * B2 * (B - 1)), C_ = (3 * B - B2 * B - 10) / (2 * B2 * B), C2 = C * C, BC = B * C, B_C = B + C, B_C2 = B_C * B_C, B_3C = B + 3 * C, F = B_C2 * (B2 + C2 * D2 - 1) + (1 - B2) * (B2 * (B_3C * B_3C + 4 * C2) + C2 * (12 * BC + 4 * C2)), F_ = -2 * B_C * (4 * BC * C2 + (1 - 4 * B2 + 3 * B2 * B2) * (1 + C_) + C2 * (-6 + 14 * B2 - D2 + (-8 + 8 * B2 - 2 * D2) * C_) + BC * (-8 + 12 * B2 + (-10 + 10 * B2 - D2) * C_)), sqrtF = Math.sqrt(F), f = D * (B_C2 + C2 - 1) + 2 * sqrtF - x1 * (4 * B_C2 + D2), f_ = D * (2 * C * C_ + 2 * B_C * (1 + C_)) + F_ / sqrtF - 8 * B_C * (D * (-1 + C2 + B_C2) + 2 * sqrtF) * (1 + C_) / (D2 + 4 * B_C2);
      B -= Î´ = f / f_;
    } while (Î´ > Îµ && --i > 0);
    return [ sgn(x) * (Math.sqrt(D * D + 4) + D) * Ï€ / 4, halfÏ€ * B ];
  };
  (d3.geo.vanDerGrinten4 = function() {
    return projection(vanDerGrinten4);
  }).raw = vanDerGrinten4;
  var wagner4 = function() {
    var A = 4 * Ï€ + 3 * Math.sqrt(3), B = 2 * Math.sqrt(2 * Ï€ * Math.sqrt(3) / A);
    return mollweideBromley(B * Math.sqrt(3) / Ï€, B, A / 6);
  }();
  (d3.geo.wagner4 = function() {
    return projection(wagner4);
  }).raw = wagner4;
  function wagner6(Î», Ï†) {
    return [ Î» * Math.sqrt(1 - 3 * Ï† * Ï† / (Ï€ * Ï€)), Ï† ];
  }
  wagner6.invert = function(x, y) {
    return [ x / Math.sqrt(1 - 3 * y * y / (Ï€ * Ï€)), y ];
  };
  (d3.geo.wagner6 = function() {
    return projection(wagner6);
  }).raw = wagner6;
  function wagner7(Î», Ï†) {
    var s = .90631 * Math.sin(Ï†), c0 = Math.sqrt(1 - s * s), c1 = Math.sqrt(2 / (1 + c0 * Math.cos(Î» /= 3)));
    return [ 2.66723 * c0 * c1 * Math.sin(Î»), 1.24104 * s * c1 ];
  }
  wagner7.invert = function(x, y) {
    var t1 = x / 2.66723, t2 = y / 1.24104, p = Math.sqrt(t1 * t1 + t2 * t2), c = 2 * asin(p / 2);
    return [ 3 * Math.atan2(x * Math.tan(c), 2.66723 * p), p && asin(y * Math.sin(c) / (1.24104 * .90631 * p)) ];
  };
  (d3.geo.wagner7 = function() {
    return projection(wagner7);
  }).raw = wagner7;
  function wiechel(Î», Ï†) {
    var cosÏ† = Math.cos(Ï†), sinÏ† = Math.cos(Î») * cosÏ†, sin1_Ï† = 1 - sinÏ†, cosÎ» = Math.cos(Î» = Math.atan2(Math.sin(Î») * cosÏ†, -Math.sin(Ï†))), sinÎ» = Math.sin(Î»);
    cosÏ† = asqrt(1 - sinÏ† * sinÏ†);
    return [ sinÎ» * cosÏ† - cosÎ» * sin1_Ï†, -cosÎ» * cosÏ† - sinÎ» * sin1_Ï† ];
  }
  wiechel.invert = function(x, y) {
    var w = -.5 * (x * x + y * y), k = Math.sqrt(-w * (2 + w)), b = y * w + x * k, a = x * w - y * k, D = Math.sqrt(a * a + b * b);
    return [ Math.atan2(k * b, D * (1 + w)), D ? -asin(k * a / D) : 0 ];
  };
  (d3.geo.wiechel = function() {
    return projection(wiechel);
  }).raw = wiechel;
  function winkel3(Î», Ï†) {
    var coordinates = aitoff(Î», Ï†);
    return [ (coordinates[0] + Î» / halfÏ€) / 2, (coordinates[1] + Ï†) / 2 ];
  }
  winkel3.invert = function(x, y) {
    var Î» = x, Ï† = y, i = 25;
    do {
      var cosÏ† = Math.cos(Ï†), sinÏ† = Math.sin(Ï†), sin_2Ï† = Math.sin(2 * Ï†), sin2Ï† = sinÏ† * sinÏ†, cos2Ï† = cosÏ† * cosÏ†, sinÎ» = Math.sin(Î»), cosÎ»_2 = Math.cos(Î» / 2), sinÎ»_2 = Math.sin(Î» / 2), sin2Î»_2 = sinÎ»_2 * sinÎ»_2, C = 1 - cos2Ï† * cosÎ»_2 * cosÎ»_2, E = C ? acos(cosÏ† * cosÎ»_2) * Math.sqrt(F = 1 / C) : F = 0, F, fx = .5 * (2 * E * cosÏ† * sinÎ»_2 + Î» / halfÏ€) - x, fy = .5 * (E * sinÏ† + Ï†) - y, Î´xÎ´Î» = .5 * F * (cos2Ï† * sin2Î»_2 + E * cosÏ† * cosÎ»_2 * sin2Ï†) + .5 / halfÏ€, Î´xÎ´Ï† = F * (sinÎ» * sin_2Ï† / 4 - E * sinÏ† * sinÎ»_2), Î´yÎ´Î» = .125 * F * (sin_2Ï† * sinÎ»_2 - E * sinÏ† * cos2Ï† * sinÎ»), Î´yÎ´Ï† = .5 * F * (sin2Ï† * cosÎ»_2 + E * sin2Î»_2 * cosÏ†) + .5, denominator = Î´xÎ´Ï† * Î´yÎ´Î» - Î´yÎ´Ï† * Î´xÎ´Î», Î´Î» = (fy * Î´xÎ´Ï† - fx * Î´yÎ´Ï†) / denominator, Î´Ï† = (fx * Î´yÎ´Î» - fy * Î´xÎ´Î») / denominator;
      Î» -= Î´Î», Ï† -= Î´Ï†;
    } while ((Math.abs(Î´Î») > Îµ || Math.abs(Î´Ï†) > Îµ) && --i > 0);
    return [ Î», Ï† ];
  };
  (d3.geo.winkel3 = function() {
    return projection(winkel3);
  }).raw = winkel3;
})();
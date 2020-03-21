<html>
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="initial-scale=1, maximum-scale=1, user-scalable=no">
    <link rel="icon" type="image/png" href="https://upload.wikimedia.org/wikipedia/commons/thumb/6/68/Ambulance_font_awesome.svg/200px-Ambulance_font_awesome.svg.png">
    <title>COVID-19 Dashboard</title>
    <style>
      html, body {
        padding: 0;
        margin: 0;
        height: 100%;
        width: 100%;
        font-family: "Lato", sans-serif;
        color: #EEEEEE;
        overflow: hidden;
      }
      #viewDiv {
        margin:0;
        padding:0;
        width:100%;
        height:100%;
      }
      .plot-container {
        top: 0;
        left: 0;
        z-index:98;
        background-color: #393e46;
        overflow: hidden;
        position: absolute;
        height: 100%;
      }

      .counties {
        top: 0;
        right: 0;
        width: 0;
        transition: 0.3s;
        z-index:97;
        background-color: #393e46;
        overflow-y: scroll;
        position: absolute;
        height: 100%;
      }

      .popup {
        top: 0;
        left: 0;
        z-index:50;
        background-color: #393e46;
        overflow: hidden;
        position: absolute;
        transition: 0.5s;
        opacity: 0.8;
        border-radius: 5px;
        border: 1px solid black;
      }
      .tools-btn {
        font-size: 18px;
        cursor: pointer;
        z-index: 99;
        position: absolute;
        right: 2%;
        top: 2%;
        color: #EEEEEE;
      }
      
      .tools-btn:hover {
        color: #4ecca3;
      }
      
      .tools-btn:active {
        color: #4d6dcb;
      }

      .plt-ctn {
        margin: 0;
        position: absolute;
        width:100%;
        height:65%;
        padding: 1px;
        top: 0;
      }

      .disable {
        top: 0;
        left: 0;
        z-index:80;
        opacity: 0.2;
        background-color: #393e46;
        overflow: hidden;
        position: absolute;
      }

      .control {
        overflow: hidden;
        position: absolute;
      }

      .warning {
        position: absolute;
        overflow: hidden;
        z-index: 99;
        top: 0;
        left: 0;
        opacity: 0.5;
        background-color: #FF0000;
        transition: 0.5s;
        width: 100%;
        height: 0;
      }

      #sliderDiv {
        position: absolute;
        z-index: 1;
        bottom: 0;
        border: 1px solid black;
        background-color: #FEFEFE;
        height: 50px;
        width: 100%;
      }

      table, td, tr, th {
        border: 1px solid #EEEEEE;
        border-collapse: collapse;
        padding 1px;
        font-size: 12px;
      }

      #county_table {
        margin-right: 20px;
        margin-left: auto;
        margin-top: 20px;
      }

      #county_table td {
        font-size: 16px;
      }

      .tab {
        overflow: hidden;
        background-color: inherit;
        padding: 5px;
      }

      .tab button {
        background-color: inherit;
        color: #eeeeee;
        float: left;
        border: 1px solid #eeeeee;
        outline: none;
        cursor: pointer;
        padding: 14px 16px;
        transition: 0.3s;
      }

      .tab button:hover {
        background-color: #444444;
      }
      
      .tab button.active {
        background-color: #333333;
      }

      .equation {
        font-size: 11px;
      }
    </style>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">
    <link rel="stylesheet" href="https://js.arcgis.com/4.14/esri/themes/light/main.css">
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script src="https://js.arcgis.com/4.14/"></script>
    <script type="text/javascript" async
      src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.7/MathJax.js?config=TeX-MML-AM_CHTML">
    </script>
    <script>
      var selected_data = null;
      var LOG_SCALE = false;
      var ENABLE_EXP = false;
      var ENABLE_LOG = false;
      var SLIDER_POS = {{ days - 1 }};
      var PLOT_TYPE = "TRACE";
      var all_data = {{ points_dict }};
      function logisticProjection(terms, n) {
        var y = [];
        var max = terms[0];
        var r = terms[1];
        var c = terms[2];
        var o = terms[3];
        for(var i = 0; i < n; ++i) {
          y.push(max/(1+Math.exp(-r*(i-c))) + o);
        }
        return y;
      }
      function exponentialProjection(terms, n) {
        var y = [];
        var p0 = terms[0];
        var r = terms[1];
        var a = terms[2];
        for(var i = 0; i < n; ++i) {
          y.push(p0 *Math.pow((1 + r), (i-a)))
        }
        return y;
      }
      function log_x(base, val) {
        return Math.log(val) / Math.log(base);
      }
      function daysToDouble(terms, c) {
        var curr = log_x(1+terms[1], c/terms[0]) + terms[2];
        var doub = log_x(1+terms[1], (c*2)/terms[0]) + terms[2];
        return doub - curr;
      }

      function openWarningGeneric(msg) {
        var elem = document.getElementById("warningDiv");
        var text = document.getElementById("warning-text");
        var style = elem.style;
        style.height = "20px";
        text.innerHTML = msg;
      }
      function setTab(evt, type) {
        PLOT_TYPE = type;
        tablinks = document.getElementsByClassName("tablink");
        for (i = 0; i < tablinks.length; i++) {
          tablinks[i].className = tablinks[i].className.replace(" active", "");
        }
        evt.currentTarget.className += " active";
        update();
      }
      function getBubbleSize(cases) {
        return Math.log(Math.max(...cases.slice(0,SLIDER_POS - 1))+1) * 10;
      }
      function updateBubbles(graphics) {
        graphics.graphics.forEach(function(item, i) {
          var size = getBubbleSize(item.attributes.confirmed);
          item.symbol.size = size;
        });
      }
      function closeDiv(id, x=true, y=true) {
        var elem = document.getElementById(id);
        var style = elem.style;
        style.border = 0;
        style.padding = 0;
        if(x) {
          style.width = 0;
        }
        if(y) {
          style.height = 0;
        }
      }
      function openDisable() {
        var elem = document.getElementById("disableMap");
        var style = elem.style;
        style.width = "100%";
        style.height = "100%";
      }

      function getDates(series) {
        dates = [];
        for(i = 0; i < series.length; i++) {
           // Start date.
           var d = new Date("2020-01-22");
           d.setDate(d.getDate() + i);
           var m = d.getMonth() + 1;
           var d = d.getDate();
           var mm = m < 10 ? '0' + m : m;
           var dd = d < 10 ? '0' + d : d;
           var date_str = ''+mm+'/'+dd;
           dates.push(date_str);
        }
        return dates;
      }
      
      require([
          "esri/Map",
          "esri/views/MapView",
          "esri/Graphic",
          "esri/layers/GraphicsLayer",
          "esri/widgets/Slider",
      ], function(Map, MapView, Graphic, GraphicsLayer, Slider) {
      var slider = new Slider({
        container: "sliderDiv",
        min: 0,
        max: {{ days - 1 }},
        values: [{{ days }}],
        steps: 1,
        snapOnClickEnabled: true,
        labelsVisible: true,
        rangeLabelsVisible: true
      });
      var map = new Map({
        basemap: "gray-vector",
      });
      var graphics = new GraphicsLayer();
      map.add(graphics);
      for(var [k,v] of Object.entries(all_data)) {
        var point = v;
        var color = (point['old'] == 0 ? [255,0,0,0.5] : [120,0,0,.5]);
        var visible = (point['old'] > 0 ? false : true)
        graphics.add(new Graphic({
          geometry: {
            type:"point",
            longitude: point['lon'], 
            latitude: point['lat'], 
          },
          visible: visible,
          symbol: {
            type: "simple-marker",
            color: color,  // red
            size: point['size'],
            outline: {
              color: [30, 0, 0 ,0.5], // white
              width: 1
            }
          },
          attributes: {
            name: point['name'],
            total_confirmed: point['confirmed'][point['confirmed'].length - 1],
            total_deaths: point['deaths'][point['deaths'].length - 1],
            total_recovered: point['recovered'][point['recovered'].length - 1],
            confirmed: point['confirmed'],
            deaths: point['deaths'],
            recovered: point['recovered'],
            lat: point['lat'],
            lon: point['lon'],
            old: point['old'],
            ages: point['ages'],
            ages_died: point['ages_died'],
            exp_terms: point['exp_terms'],
            log_terms: point['log_terms'],
            growth_factor: point['growth'],
            counties: point['counties'],
            population: point['population'],
          },
        }));
      }
      var view = new MapView({
        container: "viewDiv",
        map: map,
        center: [-98.5795, 39.828],
        zoom: 4,
      });
      view.on("click", function(evt) {
        var pt = evt.screenPoint;
        view.hitTest(pt)
          .then(getGraphic);
      });
      view.on("drag", function(evt) {
          closeDiv('popupDiv');
      });
      slider.on("thumb-change", function(evt) {
          SLIDER_POS = evt.value;
          updateBubbles(graphics);
      });
      slider.on("thumb-drag", function(evt) {
          SLIDER_POS = evt.value;
          updateBubbles(graphics);
      });
      function getGraphic(r) {
        var graphic = r.results[0].graphic;
        if(graphic.attributes.name !== undefined) {
          openPopup(r.screenPoint,graphic.attributes);
        } else {
          closeDiv('popupDiv');
        }
      }
      function openPopup(pt, data) {
        var elem = document.getElementById("popupDiv");
        var name = document.getElementById("popup-name");
        var confirmed = document.getElementById("popup-confirmed");
        var deaths = document.getElementById("popup-deaths");
        var recovered = document.getElementById("popup-recovered");
        var population = document.getElementById("popup-population");
        var updated = document.getElementById("popup-updated");
        var dates = getDates(data.confirmed)
        var style = elem.style;
        style.left = pt.x;
        style.top = pt.y;
        style.padding="15px";
        style.width = "auto";
        style.height = "auto";
        style.border = "1px solid black";
        name.innerHTML = data.name;
        confirmed.innerHTML = "Confirmed: " + data.total_confirmed;
        deaths.innerHTML = "Deaths: " + data.total_deaths;
        recovered.innerHTML = "Recovered: " + data.total_recovered;
        population.innerHTML = "Pop: " + data.population;
        updated.innerHTML = "Last updated: " + dates[dates.length - 1];
        selected_data = data;
        if(data.old > 0) {
          openWarning(data.name, data.old);
        } else {
          closeDiv("warningDiv",false, true);
        }
      }
      function openWarning(name, old) {
        var msg = "WARNING! Data for " + name + " has not been updated for " + old + " days. Numbers for this province/state are likely incorrect.";
        openWarningGeneric(msg);
      }
    });
    function getPlotData(data) {
      var conf = {
        x: getDates(data.confirmed),
        y: data.confirmed,
        mode: 'lines+markers',
        name: 'Confirmed',
        marker: {
          color: '#ffd373',
        }
      };
      var rec = {
        x: getDates(data.recovered),
        y: data.recovered,
        mode: 'lines+markers',
        name: 'Recovered',
        marker: {
          color: '#7cff70',
        }
      };
      var dead = {
        x: getDates(data.deaths),
        y: data.deaths,
        mode: 'lines+markers',
        name: 'Deaths',
        marker: {
          color: '#fa6964',
        }
      };
      var traces = [conf, rec, dead];
      if (ENABLE_EXP) {
        var project = parseInt(document.getElementById('projection').value)
        if(data.exp_terms.length == 3) {
          console.log(data.exp_terms);
          var y = exponentialProjection(data.exp_terms,data.confirmed.length + project);
          var x = getDates(y);
          var exp = {
            x: x,
            y: y,
            mode: 'lines',
            name: 'Exponential Trend',
            marker: {
              color: '#8efaf3',
            },
            line: {
              dash: 'dot',
            },
          };
          traces.push(exp);
        }
      }
      if (ENABLE_LOG) {
        var project = parseInt(document.getElementById('projection').value)
        if(data.log_terms.length == 4) {
          var y = logisticProjection(data.log_terms,data.confirmed.length + project);
          var x = getDates(y);
          var log = {
            x: x,
            y: y,
            mode: 'lines',
            name: 'Logistic Trend',
            marker: {
              color: '#bd91ed',
            },
            line: {
              dash: 'dot',
            },
          };
          traces.push(log);
        }
      }
      return traces;
    }
    function firstCase(data, thresh = 0) {
      for(i = 0; i < data.length; i++) {
        if(data[i] > thresh) {
          return i;
        }
      }
      return 0;
    }
    function hideControls() {
      var controls = document.getElementsByClassName("control");
      for(var i = 0; i < controls.length; ++i) {
        controls[i].style.visibility = "hidden";
      }
    }
    function showControls(div) {
      var control = document.getElementById(div);
      control.style.visibility = "visible";
    }
    function updateTable() {
      var confirmed = selected_data.confirmed;
      var data_end = confirmed.length - 1;
      var growth = document.getElementById('growth_factor');
      var new_cases = document.getElementById('new_cases');
      new_cases.innerHTML = confirmed[data_end] - confirmed[data_end-1]
      var g_factor = selected_data.growth_factor;
      var end = g_factor.length - 1;
      var today = g_factor[end];
      var yesterday = g_factor[end-1];
      var diff = today - yesterday
      var pct = (diff/yesterday) * 100;
      growth.innerHTML = `${today.toFixed(3)} - (${pct.toFixed(2)}%)`;
      // Set color if improved.
      if (today < 1) {
        growth.style.color = '#00ff00'
      } else {
        growth.style.color = '#ff0000'
      }
      if (diff < 0) {
        growth.innerHTML += '&#9660;'
      } else {
        growth.innerHTML += '&#9650;'
      }
      var exp_terms = selected_data['exp_terms'];
      var exp_td = document.getElementById('exp_terms');
      var p0 = exp_terms[0].toFixed(2);
      var r = exp_terms[1].toFixed(2);
      var x0 = exp_terms[2].toFixed(2);
      exp_td.innerHTML=`P0=${p0}, r=${r}, x0=${x0}`;
      var log_terms = selected_data['log_terms'];
      var log_td = document.getElementById('log_terms');
      var l = log_terms[0].toFixed(2);
      var r = log_terms[1].toFixed(2);
      var xi = log_terms[2].toFixed(2);
      var b = log_terms[3].toFixed(2);
      log_td.innerHTML=`L=${l}, r=${r}, xi=${xi}, b=${b}`;
      var d2d = document.getElementById('d2d');
      d2d.innerHTML = daysToDouble(exp_terms, selected_data.confirmed[selected_data.confirmed.length-1]).toFixed(3);
    }
    function updatePlot() {
      showControls('trace-control')
      var data = getPlotData(selected_data);
      var margin = (data.length > 3 ? data[3].x.length : data[0].x.length);
      var scale = (LOG_SCALE ? 'log' : 'linear');
      var plot_layout = {
title: "Growth rate for: " + selected_data.name + " - (Population: " + selected_data.population + ")",
        yaxis: {
          type: scale,
          title: "Cases",
          automargin: true,
        },
        xaxis: {
          title: "Days",
          automargin: true,
          range:[firstCase(data[0].y), margin],
        },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: {
          family: 'Times New Roman, Times, serif',
          size: 12,
          color: '#EEEEEE'
        },
      };
      Plotly.newPlot('graph', data, plot_layout, {displaylogo:false});
    }
    function updateCounties() {
      var elem = document.getElementById("countyDiv");
      var counties = selected_data.counties;
      if(counties.length > 0) {
        var style = elem.style;
        style.padding="0px";
        style.width = "25%";
        style.height = "100%";
        var tbl = document.getElementById("county_table");
        tbl.innerHTML = "";
        // Fill table data.
        for (var i = 0; i < counties.length; ++i) {
          var idx = counties.length - 1 - i;
          var county = counties[idx];
          var row = tbl.insertRow(0);
          var n = row.insertCell(0);
          var c = row.insertCell(1);
          var d = row.insertCell(2);
          n.innerHTML = county.name;
          c.innerHTML = county.c;
          d.innerHTML = county.d;
        }
        var header = tbl.createTHead();
        var row = header.insertRow(0);
        var n = row.insertCell(0);
        var c = row.insertCell(1);
        var d = row.insertCell(2);
        n.innerHTML = "<b>County</b>";
        c.innerHTML = "<b>Confirmed</b>";
        d.innerHTML = "<b>Death</b>";
      } else {
        closeDiv("countyDiv", true, false);
      }
    }
    function updateHistogram() {
      var conf = {
        x: selected_data.ages,
        type: 'histogram',
        name: 'Confirmed',
        xbins: {
          size: 10,
        },
      };
      var died = {
        x: selected_data.ages_died,
        type: 'histogram',
        name: 'Died',
        xbins: {
          size: 10,
        },
      };
      console.log(selected_data.ages_died);
      var plot_layout = {
        title: "Age distribution for: " + selected_data.name,
        yaxis: {
          title: "Cases",
          automargin: true,
        },
        xaxis: {
          title: "Days",
          automargin: true,
        },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: {
          family: 'Times New Roman, Times, serif',
          size: 12,
          color: '#EEEEEE'
        },
      };
      Plotly.newPlot('graph', [conf,died], plot_layout, {displaylogo:false});
      openWarningGeneric("Age data is severely limited and is likely biased.");
    }
    function updateCompare() {
      showControls('compare-control')
      var data = []
      {% for i in range(2) %}
        var e = document.getElementById('country-select{{ i }}')
        var thresh = parseInt(document.getElementById('case_thresh').value)
        var name = e[e.selectedIndex].text;
        var country = all_data[name];
        var f = firstCase(country.confirmed, thresh);
        var l = country.confirmed.length - 1;
        var y = country.confirmed.slice(f,l);
        var d = {
          y: y,
          mode: 'lines+markers',
          name: name,
        };
        data.push(d);
      {% endfor %}
      var scale = (LOG_SCALE ? 'log' : 'linear');
      var plot_layout = {
        title: "Growth Comparison",
        yaxis: {
          type: scale,
          title: "Cases",
          automargin: true,
        },
        xaxis: {
          title: "Days",
          automargin: true,
        },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: {
          family: 'Times New Roman, Times, serif',
          size: 12,
          color: '#EEEEEE'
        },
      };
      Plotly.newPlot('graph', data, plot_layout, {displaylogo:false});
    }
    function update() {
      hideControls();
      updateCounties();
      if(PLOT_TYPE == "TRACE") {
        updatePlot();
      } else if(PLOT_TYPE == "COMPARE") {
        updateCompare();
      } else if(PLOT_TYPE == "HIST") {
        updateHistogram();
      }
      updateTable();
    }
    function openPlot() {
      var elem = document.getElementById("plotDiv");
      var style = elem.style;
      style.padding="15px";
      style.width = "75%";
      style.height = "100%";
      update();
    }
    function toggleLog() {
      LOG_SCALE = !LOG_SCALE;
      update();
    }
    function setSelectValues(value) {
      {% for i in range(2) %}
        var el = document.getElementById("country-select{{ i }}");
        for (var i = 0; i < el.options.length; i++) {
          if (el.options[i].text === value) {
            el.selectedIndex = i;
            break;
          }
        }
      {% endfor %}
    }
</script>
</head>
<body>
  <div id="viewDiv"></div>
  <div id="sliderDiv"></div>
  <div class="plot-container" id="plotDiv">
    <div>
      <a class='tools-btn' onclick="closeDiv('plotDiv',true, false); closeDiv('disableMap'); closeDiv('countyDiv', true, false)" style="right:5px;top:5px"><i class="fa fa-window-close"></i></a>
    </div>
    <div class="plt-ctn">
      <div id="graph" style="width:100%; height:100%;"></div>
      <div class="tab">
        <button class="tablink" id='default-tab' onclick="setTab(event, 'TRACE')">Trends</button>
        <button class="tablink" onclick="setTab(event, 'HIST')">Ages</button>
        <button class="tablink" onclick="setSelectValues(selected_data.name);setTab(event, 'COMPARE')">Compare</button>
      </div>
      <div class="control" id="trace-control">
        <button onclick="toggleLog()">Toggle Log Scale</button>
        <input type="number" id="projection" min="0" max="30" value="0" onchange="update()">
        <input type="checkbox" id="enable_exp" onchange ="ENABLE_EXP=this.checked; update()")>
        <label for="enable_exp">Enable Exponential Trend</label>
        <input type="checkbox" id="enable_log" onchange ="ENABLE_LOG=this.checked; update()")>
        <label for="enable_log">Enable Logistic Trend</label>
      </div>
      <div class="control" id="compare-control">
        <button onclick="toggleLog()">Toggle Log Scale</button>
        {% for i in range(2) %}
          <select id="country-select{{ i }}" onchange="update()">
            {% for k,v in points_dict.items() %}
              <option value="{{ k }}">{{ k }}</option>
            {% endfor %}
          </select>
        {% endfor %}
        <span>Starting number of cases:</span>
        <input type="number" id="case_thresh" min="0" max="500" value="100" onchange="update()">
      </div>
      <br>
      <br>
      <center>
      <table>
        <tr>
          <th>New Cases</th>
          <th>Growth Factor<span class="equation">$${\frac{\Delta N_d}{\Delta N_{d-1}}}$$</span></th>
          <th>Exponential Growth<span class="equation">$${f(x)=P_0(1+r)^{x-x_0}}$$</span></th>
          <th>Logistic Growth<span class="equation">$${f(x)=\frac{L}{1+e^{-r(x-x_i)}}+b}$$</span></th>
          <th>Days to Double</th>
        </tr>
        <tr>
          <td align="center"><span id="new_cases"></span></td>
          <td align="center"><span id="growth_factor"></span></td>
          <td align="center"><span id="exp_terms"></span></td>
          <td align="center"><span id="log_terms"></span></td>
          <td align="center"><span id="d2d"></span></td>
        </tr>
      </table>
      </center>
    </div>
  </div>
  <div class="popup" id="popupDiv">
    <div>
      <a class='tools-btn' onclick="closeDiv('popupDiv')" style="right:5px;top:5px"><i class="fa fa-window-close"></i></a>
    </div>
    <div id='plt-btn'>
      <a class='tools-btn' onclick="openPlot(); openDisable()" style="right:25px;top:5px"><i class="fa fa-bar-chart"></i></a>
    </div>
    <span style="font-weight:bold" id="popup-name"></span>
    <br>
    <span id="popup-confirmed"></span>
    <br>
    <span id="popup-deaths"></span>
    <br>
    <span id="popup-recovered"></span>
    <br>
    <span id="popup-population"></span>
    <br>
    <span id="popup-updated"></span>
  </div>
  <div class="warning" id="warningDiv">
    <center><span style="font-weight:bold" id="warning-text"></span></center>
    <div>
      <a class='tools-btn' onclick="closeDiv('warningDiv',false,true)" style="right:5px;top:5px"><i class="fa fa-window-close"></i></a>
    </div>
  </div>
  <div class="counties" id="countyDiv">
    <table id="county_table">
    </table>
  </div>
  <div class="disable" id="disableMap"></div>
  <script>
    // Set default active tab.
    var default_tab = document.getElementById("default-tab");
    default_tab.className += " active";
  </script>
</body>
</html>

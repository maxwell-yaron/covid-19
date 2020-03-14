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
        z-index:99;
        background-color: #393e46;
        overflow: hidden;
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
        font-size: 16px;
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
        height:70%;
        padding: 5px;
        top: 50%;
        transform: translateY(-50%);
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
        z-index: 1;
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
    </style>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">
    <link rel="stylesheet" href="https://js.arcgis.com/4.14/esri/themes/light/main.css">
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script src="https://js.arcgis.com/4.14/"></script>
    <script>
      var selected_data = null;
      var LOG_SCALE = false;
      var SLIDER_POS = {{ days - 1 }};
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
        basemap: "national-geographic",
      });
      var graphics = new GraphicsLayer();
      map.add(graphics);
      {% for point in points %}
      var color = ({{ point['old'] }} == 0 ? [255,0,0,0.5] : [120,0,0,.5]);
      graphics.add(new Graphic({
        geometry: {
          type:"point",
          longitude: {{ point['lon'] }}, 
          latitude: {{ point['lat'] }}, 
        },
        symbol: {
          type: "simple-marker",
          color: color,  // red
          size: {{ point['size'] }},
          outline: {
            color: [30, 0, 0 ,0.5], // white
            width: 1
          }
        },
        attributes: {
          name: "{{ point['name'] }}",
          total_confirmed: {{ point['confirmed'][-1] }},
          total_deaths: {{ point['deaths'][-1] }},
          total_recovered: {{ point['recovered'][-1] }},
          confirmed: {{ point['confirmed'] }},
          deaths: {{ point['deaths'] }},
          recovered: {{ point['recovered'] }},
          lat: {{ point['lat'] }},
          lon: {{ point['lon'] }},
          old: {{ point['old'] }},
        },
      }));
      {% endfor %}
      var view = new MapView({
        container: "viewDiv",
        map: map,
        center: [-98.5795, 39.828],
        zoom: 5,
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
          console.log(evt.value);
          updateBubbles(graphics);
      });
      slider.on("thumb-drag", function(evt) {
          SLIDER_POS = evt.value;
          updateBubbles(graphics);
      });
      function getGraphic(r) {
        var graphic = r.results[0].graphic;
        openPopup(r.screenPoint,graphic.attributes);
      }
      function openPopup(pt, data) {
        var elem = document.getElementById("popupDiv");
        var name = document.getElementById("popup-name");
        var confirmed = document.getElementById("popup-confirmed");
        var deaths = document.getElementById("popup-deaths");
        var recovered = document.getElementById("popup-recovered");
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
        selected_data = data;
        if(data.old > 0) {
          openWarning(data.name, data.old);
        } else {
          closeDiv("warningDiv",false, true);
        }
      }
      function openWarning(name, old) {
        var elem = document.getElementById("warningDiv");
        var text = document.getElementById("warning-text");
        var style = elem.style;
        style.height = "20px";
        text.innerHTML = "WARNING! Data for " + name + " has not been updated for " + old + " days. Numbers for this province/state are likely incorrect."
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
      return traces;
    }
    function firstCase(data) {
      for(i = 0; i < data.length; i++) {
        if(data[i] > 0) {
          return i;
        }
      }
      return 0;
    }
    function updatePlot() {
      var data = getPlotData(selected_data);
      var scale = (LOG_SCALE ? 'log' : 'linear');
      var plot_layout = {
        title: "Growth rate for: " + selected_data.name,
        yaxis: {
          type: scale,
          title: "Cases",
          automargin: true,
        },
        xaxis: {
          title: "Days",
          automargin: true,
          range:[firstCase(data[0].y), data[0].x.length],
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
    function openPlot() {
      var elem = document.getElementById("plotDiv");
      var style = elem.style;
      style.padding="15px";
      style.width = "75%";
      style.height = "100%";
      updatePlot();
    }
    function toggleLog() {
      LOG_SCALE = !LOG_SCALE;
      updatePlot();
    }
</script>
</head>
<body>
  <div id="viewDiv"></div>
  <div id="sliderDiv"></div>
  <div class="plot-container" id="plotDiv">
    <div>
      <a class='tools-btn' onclick="closeDiv('plotDiv',true, false); closeDiv('disableMap')" style="right:5px;top:5px"><i class="fa fa-window-close"></i></a>
    </div>
    <div class="plt-ctn">
      <div id="graph" style="width:100%; height:100%;"></div>
    </div>
    <div class="control">
      <button onclick="toggleLog()">Toggle Log Scale</button>
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
  </div>
  <div class="warning" id="warningDiv">
    <center><span style="font-weight:bold" id="warning-text"></span></center>
    <div>
      <a class='tools-btn' onclick="closeDiv('warningDiv',false,true)" style="right:5px;top:5px"><i class="fa fa-window-close"></i></a>
    </div>
  </div>
  <div class="disable" id="disableMap"></div>
</body>
</html>

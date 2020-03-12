<html>
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="initial-scale=1, maximum-scale=1, user-scalable=no">
    <title>COVID-19 Dashboard</title>
    <style>
      html, body {
        padding: 0;
        margin: 0;
        height: 100%;
        width: 100%;
      }

      #viewDiv {
        margin:0;
        padding:0;
        width:100%;
        height:100%;
      }
    </style>
    <link rel="stylesheet" href="https://js.arcgis.com/4.14/esri/themes/light/main.css">
    <script src="https://js.arcgis.com/4.14/"></script>
    <script>
      require([
          "esri/Map",
          "esri/views/MapView",
          "esri/Graphic",
          "esri/layers/GraphicsLayer",
      ], function(Map, MapView, Graphic, GraphicsLayer) {
      var map = new Map({
        basemap: "national-geographic",
      });
      var graphics = new GraphicsLayer();
      map.add(graphics);
      var tpl = {
        title: "{name}",
        content: "Confirmed: {total_confirmed}<br>Recovered: {total_recovered}<br>Deaths: {total_deaths}<br>coordinates: Lat:{lat},Lon:{lon}",
      };
      {% for point in points %}
      graphics.add(new Graphic({
        geometry: {
          type:"point",
          longitude: {{ point['lon'] }}, 
          latitude: {{ point['lat'] }}, 
        },
        symbol: {
          type: "simple-marker",
          color: [225, 0, 0, 0.5],  // orange
          size: "{{ point['size'] }}px",
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
        },
        popupTemplate: tpl,
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
        view.hitTest(pt).then(getGraphic);
      });
      function getGraphic(r) {
        var graphic = r.results[0].graphic;
        console.log(graphic.attributes);
      }
    });
</script>
</head>
<body>
<div id="viewDiv"></div>
</body>
</html>

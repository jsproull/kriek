function RaspBrew() {
	var _this = this;
	
	// This is constantly called to update the data via ajax.
	this.updateStatus = function() {
		
		$.ajax({
			url: '/status/50',
			type: 'GET',
			dataType: 'json',
			success: function(data){ 
				_this.updateFromData(data);
				
				setTimeout(_this.updateStatus, 1000);
			},
			error: function(data) {
				//alert('woops!'); //or whatever
				setTimeout(_this.updateStatus, 1000);
			}
		});
	};
	
	// Updates the UI as needed
	this.updateFromData = function(data) {
		var latest = data[0];
		for (var probeid in latest.probes) {
			var probe = latest.probes[probeid];
			$('#probe' + probeid + '_temp').html(probe.temp);
			var tt = (probe.target_temp ? probe.target_temp : '--');
			$('#probe' + probeid + '_target').html(tt);
		}
		
		for (var ssrid in latest.ssrs) {
			var ssr = latest.ssrs[ssrid];
			$('#ssr' + ssrid).html(ssr.state ? "On" : "Off");
		}
		
		
		_this.updateChart(data);
	}
	
	// Updates the chart with the current data set
	this.updateChart = function(data) {
		  
		  var dd = {};
		  var values = [];
		  
		  for (var i = 0; i < data.length; i++) {
		  	var d = data[i];
			for (var probeid in d.probes) {
				var probe = d.probes[probeid];
				if (!dd[probeid]) {
					dd[probeid] = []
				}
				
				dd[probeid].push({x: d.date, y: probe.temp});
			}
		  }
		
		  var colours=["#ff7f0e","#2ca02c","#2222ff","#667711"];
		  var datum=[];
		  var d = data[0];
		  var count=0;
		  for (var probeid in dd) {
		  	datum.push({ area:false, values: dd[probeid], key: d.probes[probeid].name, color:colours[count++] });
		  }
		
		//update the chart
		d3.select('#tempChart svg')
		.datum(datum)
		.transition().duration(500)
		.call(this.chart);
	
	}
	
	//create the chart
	this.createChart = function() {
		var _this = this;
		
		nv.addGraph(function() {
		  _this.chart = nv.models.lineChart()
		  .options({
			margin: {left: 100, bottom: 100},
			x: function(d,i) { return i},
			showXAxis: true,
			showYAxis: true,
			transitionDuration: 250
		  })
		  ;

		  // chart sub-models (ie. xAxis, yAxis, etc) when accessed directly, return themselves, not the parent chart, so need to chain separately
		  _this.chart.xAxis
			.axisLabel("Time (s)")
			.tickFormat(d3.format(',.2f'));

		  _this.chart.yAxis
			.axisLabel('Temperature (c)')
			.tickFormat(d3.format(',.2f'))
			;

		  //TODO: Figure out a good way to do this automatically
		  nv.utils.windowResize(_this.chart.update);
		  //nv.utils.windowResize(function() { d3.select('#chart1 svg').call(chart) });

		  _this.chart.dispatch.on('stateChange', function(e) { nv.log('New State:', JSON.stringify(e)); });

		  return _this.chart;
		});
	}

	this.createChart();
	
	this.updateStatus();
	
	return this;
};

var raspbrew = new RaspBrew();


// Wrapping in nv.addGraph allows for '0 timeout render', stores rendered charts in nv.graphs, and may do more in the future... it's NOT required

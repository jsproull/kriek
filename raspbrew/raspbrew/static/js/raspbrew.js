function RaspBrew() {
	var _this = this;
	
	var lastData = null;
	
	// This is constantly called to update the data via ajax.
	this.updateStatus = function() {
		
		var url = '/status/50';
		
		var startDate = $("#startDate").attr('disabled');
		var endDate = $("#endDate").attr('disabled')
		
		if (startDate == undefined || endDate == undefined) {
			var sd = null;
			var ed = (new Date).getTime();
			
			startDate = $("#startDate").val();
			if (startDate) {
				sd = new Date($("#startDate").datetimepicker('getDate'));
				url = url + '/' + parseInt(sd.getTime()/1000);
				
				endDate = $("#endDate").val();
				if (endDate) {
					ed = new Date($("#endDate").datetimepicker('getDate'));
					url = url + '/' + parseInt(ed.getTime()/1000);
				}
			}
		}
		
		$.ajax({
			url: url,
			type: 'GET',
			dataType: 'json',
			success: function(data){ 
				if (data) {
					_this.updateFromData(data);
				}
				
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
	
		if (!data || data.length==0) {
			$('.raspbrew_updateable').html('--');
			this.emptyChart();
			return;
		}
		
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
		
		//update the chart
		_this.updateChart(data);
	}
	
	// Clears out the chart if there's no data
	this.emptyChart = function() {
		if (this.chart) {
			var datum = this.lastData;
			if (datum) {
				for (var i=0;i<datum.length;i++) {
					datum[i].values = [{x:0,y:0}];
				}
			} else {
				datum = [ 
					{ 
					  "key" : "" , 
					  "values" : []
					}

				]
			}
			//update the chart
			d3.select('#tempChart svg')
			.datum(datum)
			.transition().duration(500)
			.call(this.chart);
		}
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
				var date = new Date(parseInt(d.date)*1000)
	
				dd[probeid].push({x: date, y: probe.temp});
			}
		}

		var colours=["#ff7f0e","#2ca02c","#2222ff","#667711"];
		var datum=[];
		var d = data[0];
		var count=0;
		for (var probeid in dd) {
			datum.push({ values: dd[probeid], key: d.probes[probeid].name, color:colours[count++] });
		}
		
		this.lastData = datum;
		
		if (this.chart) {
			//update the chart
			d3.select('#tempChart svg')
			.datum(datum)
			.transition().duration(500)
			.call(this.chart);
		}
	
	}
	
	//create the chart
	this.createChart = function() {
		var _this = this;
		  
		nv.addGraph(function() {
		  _this.chart = nv.models.lineChart()
		  .options({
			//margin: {left: 100, bottom: 100},
			showXAxis: true,
			showYAxis: true,
			//transitionDuration: 250
		  })
		  ;

		  // chart sub-models (ie. xAxis, yAxis, etc) when accessed directly, return themselves, not the parent chart, so need to chain separately
		  _this.chart.xAxis
			.axisLabel("Time (s)")
			.tickFormat(function(d) {
				//why do i have to do this??
				return d3.time.format("%H:%M:%S")(new Date(d));
			})
			
		  _this.chart.yAxis
			.axisLabel('Temperature (c)')
			.tickFormat(d3.format(',.2f'));

		  nv.utils.windowResize(_this.chart.update);

		  _this.chart.dispatch.on('stateChange', function(e) { nv.log('New State:', JSON.stringify(e)); });

		  return _this.chart;
		});
	}
	
	//sets the time - starttime and endtime are both moment objects
	this.quickTime = function(startTime, endTime) {
		$('#startDateCheckbox').prop('checked', true);
		$('#endDateCheckbox').prop('checked', true);
		$("#startDate").datetimepicker('setDate', startTime.toDate() );
		$("#endDate").datetimepicker('setDate', endTime.toDate() );
	}


	$( document ).ready(function() {
		_this.createChart();
		_this.updateStatus();
		
		$("#startDate").datetimepicker();
		$("#endDate").datetimepicker();
	});
	
	return this;
};

var raspbrew = new RaspBrew();


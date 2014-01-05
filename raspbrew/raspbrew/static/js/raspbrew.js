//                      _                       
//                     | |                      
//  _ __ __ _ ___ _ __ | |__  _ __ _____      __
// | '__/ _` / __| '_ \| '_ \| '__/ _ \ \ /\ / /
// | | | (_| \__ \ |_) | |_) | | |  __/\ V  V / 
// |_|  \__,_|___/ .__/|_.__/|_|  \___| \_/\_/  
//               | |                            
//               |_|                            
//
//  RaspBrew v3.0
//

function RaspBrew() {
	var _this = this;
	
	this.lastChartData = null;
	this.lastLoadedData = null;
	this._systemStatus = null;
	
	this.updateTime = 2000;
	this.updateSystemSettingsTime = 20000;
	this.chartPoints = 50;
	
	this.colourList = ['#DD6E2F','#DD992F','#285890','#1F9171','#7A320A','#7A4F0A','#082950','#06503C'];
	this._chartUpdatesEnabled = true;

	this.baseURL = $('#brew').length > 0 ? '/status/brew' : '/status/ferm';
	this.confId = 1;
	
	//converts to fahrenheit if necessary
	//all temps are stored in C on the server and converted here to imperial.
	this.getTemperature = function(temp) {
	    temp = parseFloat(temp);
        if (isNaN(temp)) {
            return 0.0
        }

		if (_this._systemStatus && _this._systemStatus.units != 'metric') {
			return (9.0/5.0)*temp + 32;
		} else {
			return temp;
		}
	}
	
	// This is constantly called to update the data via ajax.
	this.updateStatus = function() {

		var url =  _this.baseURL + '/' + _this.confId + '/' + _this.chartPoints;
		
		if ($("#startDate").is(":focus") || $("#endDate").is(":focus")) {
			setTimeout(_this.updateStatus, _this.updateTime);
			return;
		}
		
		var startDateEnabled = $("#startDate").attr('disabled') === undefined;
		var endDateEnabled = $("#endDate").attr('disabled') === undefined;
	
		if (startDateEnabled || endDateEnabled) {
			var sd = null;
			var ed = (new Date).getTime();
		
			startDateValue = $("#startDate").val();
			if (startDateValue) {
				sd = new Date($("#startDate").datetimepicker('getDate'));
				url = url + '/' + parseFloat(sd.getTime());
			
				endDateValue = $("#endDate").val();
				if (endDateEnabled && endDateValue) {
					ed = new Date($("#endDate").datetimepicker('getDate'));
					url = url + '/' + parseFloat(ed.getTime());
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

					//update the chart
					if (this._chartUpdatesEnabled) {
						_this.updateChart(data);
					}

					//set this after the update so we know what we currently have loaded
					_this.lastLoadedData=data[0];
				}
				
				setTimeout(_this.updateStatus, _this.updateTime);
			},
			error: function(data) {
				//alert('woops!'); //or whatever
				setTimeout(_this.updateStatus, 5000);
			}
		});
	};
	
	// This is called to update the system status.
	this.updateSystemStatus = function() {
		$.ajax({
			url: "/status/system",
			type: 'GET',
			dataType: 'json',
			success: function(data){ 
				_this._systemStatus = data;
				if (data) {
					if (data.serverrunning) {
						$('#serverstatus').addClass('hidden');
					} else {
						$('#serverstatus').removeClass('hidden');
					}
				}
				
				if (data.units) {
					//update all the temp labels
					$('.templabel').each(function(index, item) { 
						var h = $(item).html();
						var fc = data.units == "metric" ? "c" : "f";
						xh = h.replace(/\(.*\)/g, "(" + fc + ")");
						$(item).html(xh);
					});
				}
				
				setTimeout(_this.updateSystemStatus, _this.updateSystemSettingsTime);
			},
			error: function(data) {
				//alert('woops!'); //or whatever
				setTimeout(_this.updateSystemStatus, 5000);
			}
		});
	};
	
	// Updates the UI as needed
	this.updateFromData = function(data, force) {

		if (!force) {
			force = false;
		}

		//we are waiting for the server to update the data
		if (this._writingData && !force) {
			return;
		}
	
		if (!data || data.length==0) {
			$('.raspbrew-updateable').html('--');
			this.emptyChart();
			return;
		}
		
		var latest = data[0];
		if (!force && latest && _this.lastLoadedData && (latest.date == _this.lastLoadedData.date)) {
			//no need to update
			return;
		}
		
		for (var probeid in latest.probes) {
			var probe = latest.probes[probeid];
			
			var tempInput = $('#probe' + probeid + '_temp');
			var ttempInput = $('#probe' + probeid + '_target');
			
			var temp = _this.getTemperature(probe.temp);
			var targetTemp = NaN;
			if (probe.target_temp) {
				targetTemp = parseFloat(probe.target_temp);
			}
			
			if (! tempInput.is(":focus"))
				tempInput.html(temp.toFixed(2));
			if (! ttempInput.is(":focus") && ! ttempInput.parent().hasClass('has-success')) {
				if (probe.target_temp) {
					ttempInput.val(targetTemp.toFixed(2));
				} else {
					ttempInput.val("");
				}
			}
			
			//how close are we to the target temp?
			if (!isNaN(temp) && !isNaN(targetTemp)) {
				var percent = Math.min(temp, targetTemp)/Math.max(temp, targetTemp);
				var color=jQuery.Color().hsla(120, 1, percent/2, 1);
				tempInput.animate({
				  color: color
			  	}, 1500 );
			}
			
		}
		
		for (var ssrid in latest.ssrs) {
			var ssr = latest.ssrs[ssrid];
			
			//only update if something has changed in this ssr
			//if (_this.lastLoadedData && _this.lastLoadedData.ssrs && _this.lastLoadedData.ssrs[ssrid].state == ssr.state && _this.lastLoadedData.ssrs[ssrid].enabled == ssr.enabled) {
			//	continue;
			//}
			
				
			$('#ssr' + ssrid + "_icon").removeClass("fa-check-square-o");
			$('#ssr' + ssrid + "_icon").removeClass("fa-square-o");
			$('#ssr' + ssrid).removeClass("powerOff");
			$('#ssr' + ssrid).removeClass("power");
			
			if (ssr.state) {
				$('#ssr' + ssrid + "_icon").addClass("fa-check-square-o");
				$('#ssr' + ssrid).addClass("power");
			} else {
				$('#ssr' + ssrid + "_icon").addClass("fa-square-o");
				$('#ssr' + ssrid).addClass("powerOff");
			}
			
			//state
			$('#ssr' + ssrid + "_state").removeClass("label-on");
			$('#ssr' + ssrid + "_state").removeClass("label-off");
			
			if (ssr.state) {
				$('#ssr' + ssrid + "_state").addClass("label-on");
				$('#ssr' + ssrid + "_state").html("On");
			} else {
				$('#ssr' + ssrid + "_state").addClass("label-off");
				$('#ssr' + ssrid + "_state").html("Off");
			}

			//set the eta and degrees per hour
			if (ssr.eta) {
				var eta=ssr.eta;
				var eta=new Date(eta);
				eta=moment(eta).fromNow(true);
				$('#ssr' + ssrid + '_eta').html(eta);
			} else {
				$('#ssr' + ssrid + '_eta').html('--');
			}
			
			if (ssr.dpm) {
				var dpm = parseFloat(ssr.dpm).toFixed(3);
				//$('#probe' + probeid + '_dpm').parent().removeClass("hidden");
				$('#ssr' + ssrid + '_dpm').html(dpm);
			} else {
				//$('#probe' + probeid + '_dpm').parent().addClass("hidden");
				$('#ssr' + ssrid + '_dpm').html('--');
			}


			//enabled -- only used in ferm.html
			$('#ssr' + ssrid + "_panel").removeClass("disabled");
			$('#ssr' + ssrid + "_enabled").removeClass("label-enabled");
			$('#ssr' + ssrid + "_enabled").removeClass("label-disabled");

			if (ssr.enabled) {
				$('#ssr' + ssrid + "_panel").addClass("disabled");
				$('#ssr' + ssrid + "_enabled").addClass("label-enabled");
				$('#ssr' + ssrid + "_enabled").html("Yes");
			} else {
				$('#ssr' + ssrid + "_panel").addClass("disabled");
				$('#ssr' + ssrid + "_enabled").addClass("label-disabled");
				$('#ssr' + ssrid + "_enabled").html("No");
			}


			//button
			if (ssr.enabled) {
				$('#ssr' + ssrid + '_setCurrent').removeClass('btn-primary');
				$('#ssr' + ssrid + '_setCurrent').addClass('btn-warning');
				$('#ssr' + ssrid + '_setCurrent').addClass('enabled');
				$('#ssr' + ssrid + '_setCurrent').html("On")
			} else {
				$('#ssr' + ssrid + '_setCurrent').addClass('btn-primary');
				$('#ssr' + ssrid + '_setCurrent').removeClass('btn-warning');
				$('#ssr' + ssrid + '_setCurrent').removeClass('enabled');
				$('#ssr' + ssrid + '_setCurrent').html("Off")
			}

			//power
			if (ssr.pid && ssr.pid.power) {
				$('#ssr' + ssrid + '_power').html(ssr.pid.power + "%");
			} else {
				$('#ssr' + ssrid + '_power').html('--');
			}
		}

	}
	
	// Clears out the chart if there's no data
	this.emptyChart = function() {
		
		if (this.chart) {
			var datum = _this.lastLoadedData;
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
				var date = new Date(parseFloat(d.date));
				var temp = probe.temp;
				if (temp) {
					temp=_this.getTemperature(probe.temp)
					dd[probeid].push({x: date, y: temp});
				}
			}
		}

		var datum=[];
		var d = data[0];
		var count=0;
		for (var probeid in dd) {
			if (d.probes && d.probes[probeid]) {
				datum.push({ values: dd[probeid], key: d.probes[probeid].name, color:this.colourList[count++] });
			}
		}
		
		this.lastChartData = datum;
		
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
		$('#startDate').prop('disabled', false);
		$('#endDate').prop('disabled', false);
		$("#startDate").datetimepicker('setDate', startTime.toDate() );
		$("#endDate").datetimepicker('setDate', endTime.toDate() );
	}

	//sets the ssr as 'current'
	this.toggleSSR = function(ssrid) {
		if (ssrid) {
			var enabled = !$('#ssr' + ssrid + '_setCurrent').hasClass('enabled')

			//update the local data and refresh
			if (_this.lastLoadedData && _this.lastLoadedData['ssrs'] && _this.lastLoadedData['ssrs'][ssrid]) {
				_this.lastLoadedData['ssrs'][ssrid].enabled = enabled;
				this.updateFromData([_this.lastLoadedData], true);
			}

			var post = { ssrs: [ { pk: ssrid, enabled:enabled } ] };
			_this.sendUpdate(post);
		}
	}
	
	//updates the target temperature of the given probe id
	this.updateTargetTemp = function(input, probeid) {
	
		//if we don't have the probeid, get it from the input
		if (!probeid) {
			probeid = parseInt(input.replace(/[^\d]/g,""));
		}
		
		input=$('#'+input)
		$(input).parent().removeClass('has-success');
		
		//validate the input
		var val=input.val();
		if (val == "") {
			val = null;
		} else {
			var val=parseFloat(val);
			if (isNaN(val) || val > 999) {
				input.parent().addClass('has-error');
				return;
			} 
			input.val(val.toFixed(2));
		}		

		var post = { probes: [ { pk: probeid, target_temperature: val } ]  };

		_this.sendUpdate(post);
	}

	this.sendUpdate = function(post) {
		this._writingData = true;

		$('.raspbrew-updateable').attr('disabled', true);
		$.ajax({
			url: "/update",
			type: 'POST',
			dataType: 'json',
			data: JSON.stringify(post),
			success: function(data){
				$('.raspbrew-updateable').attr('disabled', false);
				setTimeout(function(){_this._writingData = false;}, 1000);
			},
			error: function() {
				$('.raspbrew-updateable').attr('disabled', false);
				_this._writingData = false;
			}
		});
	}
	
	//this sets wether or not we should be updating the char
	this.setChartUpdatesEnabled = function(enabled) {
		this._chartUpdatesEnabled = enabled;
		if (enabled) {
			$('#chartUpdates').html('Chart Updates Enabled');
		} else {
			$('#chartUpdates').html('Chart Updates Disabled');
		}
	}
	
	//shows a configuration dialog for a given ssr
	this.configureSSR = function(ssrid, ssrname) {
		
		var data = _this.lastLoadedData;
		
		if (data && data.ssrs && data.ssrs[ssrid]) {
			_this._editingSSR = data.ssrs[ssrid];
			_this._editingSSR.id = ssrid;
			
			$('#ssrEnabled').prop('checked')
			$('#ssrEnabled').prop('checked', this._editingSSR.enabled)
			$('#ssrPower').val(this._editingSSR.pid.power)
			$('#ssrModalTitle').html(_this._editingSSR.name);
			$('#ssrModal').modal({});
		}
	}

	//saves the ssr from the modal dialog
	this.saveSSRConfig = function() {
		if (!_this._editingSSR) {
			return;
		}
		
		var enabled = $('#ssrEnabled').prop('checked') ? 1 : 0 ;
		var power = $('#ssrPower').val();
		
		pid={};
		
		if (!isNaN(parseInt(power))) {
			pid.power = power;
		}
		
		var post = { ssrs: [ { pk: _this._editingSSR.id, enabled: enabled, pid: pid } ] };
		
		_this.sendUpdate(post);
		
		$('#ssrModal').modal('hide');
	}

	$( document ).ready(function() {
		_this.createChart();
		_this.updateStatus();
		_this.updateSystemStatus();
		$("#startDate").datetimepicker({timeFormat: "HH:mm:ss"});
		$("#endDate").datetimepicker({timeFormat: "HH:mm:ss"});
		
		//set up our enter key submit
		$('.target-temp').on("keypress", function(e) {
			if (e.keyCode == 13) {
				_this.updateTargetTemp(this.id);
				return false; // prevent the button click from happening
			}
		});
	});
	
	return this;
};

var raspbrew = new RaspBrew();


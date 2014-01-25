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
	this.latestData = null; 	// an array of results from the server
	this._systemStatus = null;
	
	this.updateTime = 2000;
	this.updateSystemSettingsTime = 20000;
	this.chartPoints = 20;
	
	this.colourList = ['#DD6E2F','#DD992F','#285890','#1F9171','#7A320A','#7A4F0A','#082950','#06503C'];
	this._chartUpdatesEnabled = true;

	this.baseURL = '/status/?type=' + ($('#brew').length > 0 ? 'brew' : 'ferm');
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

		var url =  _this.baseURL + '&confId=' + _this.confId + '&numberToReturn=' + _this.chartPoints;

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
				url = url + '&startDate=' + parseFloat(sd.getTime());
			
				endDateValue = $("#endDate").val();
				if (endDateEnabled && endDateValue) {
					ed = new Date($("#endDate").datetimepicker('getDate'));
					url = url + '&endDate=' + parseFloat(ed.getTime());
				}
			}
		}
		
		$.ajax({
			url: url,
			type: 'GET',
			dataType: 'json',
			success: function(data){ 
				if (data) {
					if (data && data.results) {
						_this.latestData = data.results;

						//to make it easier, we recreate the probes array here
						if (data.results.length > 0) {
							for (var j=0;j<data.results.length;j++){
								var newProbes = []

								for (var i=0;i<data.results[j].probes.length;i++) {
									var p=data.results[j].probes[i];
									newProbes.push(p.probe);
								}

								data.results[j].probes = newProbes;
							}

							_this.updateFromData(data.results[0]);

							//set this after the update so we know what we currently have loaded
							_this.lastLoadedData=data.results[0];
						} else {
							_this.lastLoadedData=null;
						}


						//update the chart
						if (_this._chartUpdatesEnabled) {
							_this.updateChart(data.results);
						}


						//console.log('_this.lastLoadedData', _this.lastLoadedData, data);
					}
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
			url: "/system/status/",
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
	
		if (!data) {
			$('.raspbrew-updateable').html('--');
			this.emptyChart();
			return;
		}
		
		var latest = data;
		if (!latest || (!force && latest && _this.lastLoadedData && (latest.date == _this.lastLoadedData.date))) {
			//no need to update
			return;
		}
		
		for (var index in latest.probes) {
			var probe = latest.probes[index];
			var probeid = probe.id;

			var tempInput = $('#probe' + probeid + '_temp');
			var ttempInput = $('#probe' + probeid + '_target');
			
			var temp = _this.getTemperature(probe.temperature);
			var targetTemp = NaN;
			if (probe.target_temperature) {
				targetTemp = parseFloat(probe.target_temperature);
			}
			
			if (! tempInput.is(":focus"))
				tempInput.html(temp.toFixed(2));
			if (! ttempInput.is(":focus") && ! ttempInput.parent().hasClass('has-success')) {
				if (probe.target_temperature) {
					ttempInput.val(targetTemp.toFixed(2));
				} else {
					ttempInput.val("");
				}
			}
			
			//disable the targettemp if this probe has no ssrs
			/*if (!probe.ssrs || probe.ssrs.length == 0) {
				ttempInput.attr('disabled', true);
			} else {
				ttempInput.attr('disabled', false);
			}*/
			
			//how close are we to the target temp?
			if (!isNaN(temp) && !isNaN(targetTemp)) {
				var percent = Math.min(temp, targetTemp)/Math.max(temp, targetTemp);
				var color=jQuery.Color().hsla(120, 1, percent/2, 1);
				tempInput.animate({
				  color: color
			  	}, 1500 );
			}

			for (var index in probe.ssrs) {
				var ssr = probe.ssrs[index];
				var ssrid = ssr.id;

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
	}
	
	// Clears out the chart if there's no data
	this.emptyChart = function() {
		
		if (this.chart) {
			var datum = _this.lastChartData;
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

		var dd = [];
		var values = [];

		var startDate, endDate;

		var datum=[];

		var states = [];
		
		for (var i = 0; i < data.length; i++) {
			var d = data[i];
			if (!d.probes) {
				continue;
			}
			//console.log('d.probes', d.probes);

			for (var index in d.probes) {
				var probe = d.probes[index];
				var probeid = probe.id;
				if (!states[index]) {
					states[index]=[];
				}

				if (!dd[index]) {
					dd[index] = []
				}
				var date = new Date(moment(d.date));
				var temp = probe.temperature;
				if (temp) {
					if (startDate == null) {
						startDate=date;
					}
					if (startDate) {
						endDate=date;
					}
					//console.log(temp);
					temp=_this.getTemperature(probe.temperature)
					dd[index].push({x: date, y: temp});
				}

				//we only have to push each dd object once and the dd[index] array will get updated
				datum[index] = ({ values: dd[index], key: probe.name, color:this.colourList[index] });
				
				//set this if it's true or false
				if (probe.ssrs) {
					for (var ssri in probe.ssrs) {
						ssr = probe.ssrs[ssri]
						if (ssr && ssr.state == true) {
							states[index][i] = true;
						}
					}
				}

				//console.log(index, dd[index])
			}
		}

		//udpate the time axis
		var diffInHours = moment(startDate).diff(moment(endDate),'hours');
		if (diffInHours > 24) {
				_this.chart.xAxis.axisLabel('Time (s)').tickFormat(function(d) {
					//why do i have to do this??
					return d3.time.format("%x %H:%M")(new Date(d));
				});
		} else {
				_this.chart.xAxis.axisLabel('Time (s)').tickFormat(function(d) {
					//why do i have to do this??
					return d3.time.format("%H:%M:%S")(new Date(d));
				});
		}


		//console.log('chart data', datum);

		this.lastChartData = datum;
		
		if (this.chart) {
			//update the chart
			d3.select('#tempChart svg')
			.datum(datum)
			.transition().duration(500)
			.call(this.chart);
			
			setTimeout(function() { 
				for (var probeid in states) {
					if (states[probeid] && states[probeid].length>0) {
						//console.log( states[probeid] );
						for (var index in states[probeid]) {
									$(".nv-series-" + 1 + " .nv-point-" + index).attr('r', 5);//.attr('fill','blue')
							}
					}
				}
			}, 1000);
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
				this.updateFromData(_this.lastLoadedData, true);
			}

			var post = { pk: ssrid, enabled:enabled };
			_this.sendUpdate("/ssrs/" + _this._editingSSR + "/", post);
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

		//update the actual data
		var probe = _this.findProbe(probeid);
		probe.target_temperature = val;

		var post = { pk: probeid, target_temperature: probe.target_temperature  };

		_this.sendUpdate("/probes/" + probeid + "/", post);
	}

	this.sendUpdate = function(url, post, callback, errcallback) {
		this._writingData = true;

		$('.raspbrew-updateable').attr('disabled', true);
		$.ajax({
			url: url,
			type: 'PATCH',
			dataType: 'json',
			data: JSON.stringify(post),
			contentType:"application/json",
			success: function(data){
				$('.raspbrew-updateable').attr('disabled', false);
				setTimeout(function(){_this._writingData = false;}, 1000);
				if (callback) { callback(data); }
			},
			error: function() {
				$('.raspbrew-updateable').attr('disabled', false);
				_this._writingData = false;
				if (errcallback) { errcallback(data); }
			}
		});

		this.updateFromData(_this.lastLoadedData, true);
	}
	
	//this sets wether or not we should be updating the char
	this.toggleChartUpdatesEnabled = function(enabled) {
		this._chartUpdatesEnabled = !this._chartUpdatesEnabled;
		enabled = $('#chartEnabledCheckbox').prop('checked', this._chartUpdatesEnabled);
	}

	//finds the requested probe by id from the latest loaded data
	this.findProbe = function(probeid) {
		var data = _this.lastLoadedData;

		if (data && data.probes) {
			for (var i=0;i<data.probes.length;i++) {
				var probe = data.probes[i];
				if (probe.id == probeid) {
					return probe;
				}
			}
		}
	}

	//finds the requested ssr by id from the latest loaded data
	this.findSSR = function(ssrid) {
		var data = _this.lastLoadedData;

		if (data && data.probes) {
			for (var i=0;i<data.probes.length;i++) {
				var probe = data.probes[i];

				for (var j=0;j<probe.ssrs.length;j++) {
					var ssr = probe.ssrs[j];
					if (ssr.id == ssrid) {
						return ssr;
					}
				}
			}
		}
	}
	
	//shows a configuration dialog for a given ssr
	this.configureSSR = function(ssrid) {
		debugger;
		_this._editingSSR = ssrid;

		var ssr = _this.findSSR(ssrid);

		$('#ssrEnabled').prop('checked', ssr.enabled)
		$('#ssrPower').val(ssr.pid.power)
		$('#ssrModalTitle').html(ssr.name);
		$('#ssrModal').modal({});
	}

	//saves the ssr from the modal dialog
	this.saveSSRConfig = function() {
		if (!_this._editingSSR) {
			return;
		}
		
		var enabled = $('#ssrEnabled').prop('checked') ? 1 : 0 ;
		var power = $('#ssrPower').val();
		var ssr = _this.findSSR(_this._editingSSR);

		//update our values
		var pid=ssr.pid;
		ssr.enabled = enabled;
		
		if (!isNaN(parseInt(power))) {
			pid.power = power;
		}

		var post = { pk: ssr.id, enabled: enabled, pid: pid };

		//call back function
		var cb = function(data) {
			_this._editingSSR = null;
		}

		_this.sendUpdate("/ssrs/" + ssr.id + "/", post, cb, cb);

		$('#ssrModal').modal('hide');
	}

	//this method will try to calibrate the heater pid
	this.calibratePID = function() {
		if (!_this.latestData || _this.latestData.length == 0) {
			return;
		}

		/*
		  	Dead-Time (TD): the dead-time of the system is the time delay between the initial response and a 10 % increase in the process variable
			(which is the HLT temperature in our case). Unity is given in seconds.
		*/

		//go through all of our data points and figure out when we've gone up 10% from the first data point
		var start = _this.latestData[0];
		var end = null;
		for (var i=0;i<_this.latestData.length;i++) {
			var data = _this.latestData[i];
			if (data.temperature > start.temperature*1.1) {
				break;
			}
			end = data;
		}

		if (!end) {
			alert('something wrongo');
			return;
		}

		var deadtime = moment(end.date) - moment(start.date);

		if (datetime <= 0) {
			alert('something wrongo2');
			return;
		}
		console.log('deadtime', deadtime);

		//Normalized slope (a): the normalized slope of the step response is the increase in temperature per second per percentage of the PID controller output.
			// Stated in a formula: a = change in temperature divided by time-interval divided by PID controller output.
		//Gain (K): the gain of the HLT system. We can model our HLT system as having one input (the PID controller output in %)
			// and one output (the HLT temperature). The Gain of this HLT system is then defined as output divided by input and has a unity of °C / %.
		//Time-constant (tau): the time-constant of the system is another important parameter of the system. It describes how quick the
			// temperature will increase, given a particular output of the PID controller. Unity is given in seconds.
	}

	//on ready
	$( document ).ready(function() {
		_this.createChart();

		$("#startDate").datetimepicker({timeFormat: "HH:mm:ss"});
		//default to start of today
		var d=new Date();
		d.setHours(0,0,0,0);
		$("#startDate").datetimepicker('setDate', d);
		$('#startDateCheckbox').prop('checked', true);
		$('#startDate').prop('disabled', false);

		$("#endDate").datetimepicker({timeFormat: "HH:mm:ss"});
		
		//set up our enter key submit
		$('.target-temp').on("keypress", function(e) {
			if (e.keyCode == 13) {
				_this.updateTargetTemp(this.id);
				return false; // prevent the button click from happening
			}
		});

		//ensure we have a confId
		if ($('.raspbrew-tab').length > 0) {
			_this.confId = $('.raspbrew-tab').attr('data-confid');
		} else {
			_this.confId = $('#confid').attr('data-confid');
		}

		//set up tabs on click
		$('a[data-toggle="tab"]').on('shown.bs.tab', function (e) {
			_this.confId = $(e.target).attr('data-confid');
			_this.updateStatus();
		  //e.relatedTarget // previous tab
		})

		//start our updates
		_this.updateStatus();
		_this.updateSystemStatus();
	});
	
	return this;
};

var raspbrew = new RaspBrew();


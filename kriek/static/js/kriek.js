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
	this.latestChartData = null; 	// an array of results from the server
	this._systemStatus = null;
	
	this.updateTime = 1000;
	this.updateSystemSettingsTime = 20000;
	this.chartPoints = 50;
	
	this.colourList = ['#DD6E2F','#DD992F','#285890','#1F9171','#7A320A','#7A4F0A','#082950','#06503C'];

	this._chartUpdatesEnabled = true;
	this._updatesEnabled = true;

	this.baseURL = '/status/?type=' + ($('#brew').length > 0 ? 'brew' : 'ferm');
	this.confId = 1;

	this.probes = {}; //cached probes by id

	this.currentSchedule = null; //the currently enabled step schedule

	this.enabledSSR = null; //the currently enabled ssr
	this.enabledProbe = null; //the currently enabled probe (that is, the probe that the enabled ssr is reading)

	//converts to fahrenheit if necessary
	//all temps are stored in C on the server and converted here to imperial.
	this.getTemperature = function(temp) {
	    temp = parseFloat(temp);
        if (isNaN(temp)) {
            return 0.0
        }

		if (_this._systemStatus && _this._systemStatus.units != 'metric') {
			temp = (9.0/5.0)*temp + 32;
			return temp.toFixed(1);
		} else {
			temp = temp;
			return temp.toFixed(2);
		}
	}

	//converts to celsius if needed
	this.convertToCelsiusIfNeeded = function(temp) {
		temp = parseFloat(temp);
        if (isNaN(temp)) {
            return 0.0;
        }

		if (_this._systemStatus && _this._systemStatus.units != 'metric') {
			temp = (temp - 32) * 5/9;
			return temp.toFixed(1);
		} else {
			return temp.toFixed(2);
		}
	}

	//gets the temperature as a string format
	this.getTemperatureFormatted = function(temp) {
		var temp = parseFloat(_this.getTemperature(temp));

		if (_this._systemStatus && _this._systemStatus.units != 'metric') {
			return temp.toFixed(1) + "f";
		} else {
			return temp.toFixed(2) + "c";
		}
	}

	//loads all the probes and caches them in this.probes
	this.loadProbes = function() {
	
		//wait for when we have a system status or if we're writing data
		if (_this._systemStatus == null || _this._writingData) {
			setTimeout(_this.loadProbes, _this.updateTime);
			return;
		}

		var url = "/probes/";
		$.ajax({
			url: url,
			type: 'GET',
			dataType: 'json',
			success: function(data){
				if (data && data.results) {
					for (var i=0;i<data.results.length;i++){
						var probe = data.results[i];
						_this.probes[probe.id] = probe;
					}
					_this.updateFromData(data.results);
				}
				setTimeout(_this.loadProbes, _this.updateTime);
			},
			error: function(data) {
				setTimeout(_this.loadProbes, _this.updateTime);
			}
		});
	}

	// This is constantly called to update the data via ajax.
	this.updateStatus = function() {

		if (!_this.confId || _this._writingData) {
			return;
		}

		var url =  _this.baseURL + '&confId=' + _this.confId + '&numberToReturn=' + _this.chartPoints;

		if (! _this._chartUpdatesEnabled || $("#startDate").is(":focus") || $("#endDate").is(":focus")) {
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
						_this.latestChartData = data.results;
						
						//update the chart
						if (_this._chartUpdatesEnabled) {
							_this.updateChart(data.results);
						}
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

					//update the global settings
					_this._updatesEnabled = data.updatesenabled;
					$('#updatesEnabledCheckbox').prop('checked', _this._updatesEnabled);

					if (!_this._updatesEnabled) {
						$('#updatesEnabled').show();
					} else {
						$('#updatesEnabled').hide();
					}
					
				}
				
				if (data.units) {
					
					if (data.units == 'metric') {
						$('#metric').prop('checked', true);
					} else {
						$('#imperial').prop('checked', true);
					}

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

		//set these as null
		_this.enabledSSR = null;
		_this.enabledProbe = null;

		if (!force) {
			force = false;
		}

		if (!data) {
			$('.kriek-updateable').html('--');
			this.emptyChart();
			return;
		}
		
		var latest = data;
		//if (!latest || (!force && latest && _this.lastLoadedData && (latest.date == _this.lastLoadedData.date))) {
			//no need to update
		//	return;
		//}

		//set this after the update so we know what we currently have loaded
		_this.lastLoadedData=latest;

		for (var index in latest) {
			var probe = latest[index];

			if (!probe) {
				continue;
			}

			var probeid = probe.id;

			var tempInput = $('#probe' + probeid + '_temp');
			var ttempInput = $('#probe' + probeid + '_target');

			var temp = _this.getTemperature(probe.temperature);
			
			var targetTemp = NaN;
			if (probe.target_temperature) {
				targetTemp = _this.getTemperature(probe.target_temperature);
			}

			if (! tempInput.is(":focus")) {
				tempInput.html(temp);
			}

			if (! ttempInput.is(":focus") && ! ttempInput.parent().hasClass('has-success')) {
				if (targetTemp) {
					ttempInput.val(targetTemp);
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

			//update the ssrs
			for (var index in probe.ssrs) {
				var ssr = probe.ssrs[index];
				var ssrid = ssr.id;
				if (!ssr) {
					continue;
				}

				if (ssr.enabled) {
					_this.enabledSSR = ssr;
					_this.enabledProbe = probe;

					var title = document.title.match(/.* - \w+/);
					title = title + " (" + _this.getTemperatureFormatted(probe.temperature) + ")";
					document.title = title;
				}

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

				if (ssr.degrees_per_minute) {
					var dpm = parseFloat(ssr.degrees_per_minute).toFixed(3);
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

			//update schedules if any
			if (probe.schedules) {
				var len = probe.schedules.length;
				if (len == 0) {
					$("#probe" + probe.id + "_nosched").show();
					$("#probe" + probe.id + "_schedContainer").hide();
					continue;
				}

				$("#probe" + probe.id + "_nosched").hide();
				$("#probe" + probe.id + "_schedContainer").show();

				var s = $("#probe" + probe.id + "_schedselect");
				//set up the select
				if ($("#probe" + probe.id + "_schedselect option").size() != len+1) {
					s.empty();

					//set up our select
					$("<option />", {value: null, text: "-- Disabled --"}).appendTo(s);
					for (var i=0;i<len;i++) {
						var sched = probe.schedules[i];

						$("<option />", {value: sched.id, text: sched.name}).appendTo(s);

					}
				}


				for (var i=0;i<len;i++) {
					var sched = probe.schedules[i];
					if (sched.enabled) {
						//if we have an active schedule set up the ui

						var sched = probe.schedules[i];

						//pick the currently enabled one
						_this.currentSchedule = sched;
						$("#probe" + probe.id + "_schedselect").val(i+1);
						var stepsDiv = $("#probe" + probe.id + "_schedSteps");

						if (sched.scheduleSteps) {

							//sort by step index
							var steps = sched.scheduleSteps.sort(function(a,b)
							{
							   return a.step_index > b.step_index;
							});

							if ($("#probe" + probe.id + "_schedSteps a").size() != sched.scheduleSteps.length) {
								stepsDiv.empty();
							}

							for (var j=0;j<steps.length;j++) {
								var step = steps[j];
								var a = $('#step_' + step.id)
								if (!a.length) {
									a = $("<a onclick='kriek.enableStep(this); return false;' href='#' id='step_" + step.id + "' class='list-group-item'/>");
									a.appendTo(stepsDiv);
								}

								//update the active steps
								if (step.active) {
										a.addClass("active");
										var start=new Date(moment(step.active_time))
										var end=moment(start).add('seconds', step.hold_seconds);
										eta=end.fromNow(true);
										a.html("Holding at: <b>" + _this.getTemperatureFormatted(step.start_temperature) + "</b> For: <b>" + eta + "</b>" );

								} else {
										end=moment(new Date()).add('seconds', step.hold_seconds)
										a.html("Hold at: <b>" + _this.getTemperatureFormatted(step.start_temperature) + "</b> For: <b>" + end.from(moment(new Date()), true) + "</b>" );
										a.removeClass("active");
								}

							}
						} else if (sched.scheduleTimes) {
							//TODO
						}

					}
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

			for (var index=0;index<d.probes.length;index++) {
				var probe = d.probes[index];
				var probeid = probe.probe;
				var probeIndex = _this.findProbeIndex(probeid);
				
				if (!states[probeIndex]) {
					states[probeIndex]=[];
				}

				if (!dd[probeIndex]) {
					dd[probeIndex] = []
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
					temp=parseFloat(_this.getTemperature(probe.temperature));
					dd[probeIndex].push({x: date, y: temp});
				}

				//we only have to push each dd object once and the dd[index] array will get updated
				datum[probeIndex] = ({ values: dd[probeIndex], key: probe.name, color:this.colourList[probeIndex] });
				
				//set this if it's true or false
				if (probe.ssrs) {
					for (var ssri in probe.ssrs) {
						ssr = probe.ssrs[ssri]
						if (ssr && ssr.state == true) {
							states[probeIndex][i] = true;
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
		// remove all undefined array objects
		datum = datum.filter(function(n){return n});

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
			//var enabled = !$('#ssr' + ssrid + '_setCurrent').hasClass('enabled')
			var enabled = $('#ssr' + ssrid + '_enabled').hasClass('label-enabled')
			var ssr = _this.findSSR(ssrid);
			if (!ssr) {
				return;
			}

			//disable all other ssrs locally
			for (var probeid in _this.probes){
				var probe = _this.probes[probeid];
				for (var j=0;j<probe.ssrs.length;j++){
					var _ssr = probe.ssrs[j];
					if (_ssr.id != ssr.id) {
						_ssr.enabled=false;
					}
				}
			}

			ssr.enabled = !enabled;

			//update the local data and refresh
			if (_this.lastLoadedData) {
				_this.updateFromData(_this.lastLoadedData, true);
			}

			var post = { pk: ssrid, enabled:ssr.enabled };
			_this.sendUpdate("/ssrs/" + ssr.id + "/", post);
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
			input.val(val.toFixed( _this._systemStatus.units == "metric" ? 2 : 1 ));
		}

		//update the actual data
		var probe = _this.probes[probeid];
		if (probe) {
			probe.target_temperature = this.convertToCelsiusIfNeeded(val);
		}

		var post = { pk: probeid, target_temperature: probe.target_temperature  };

		_this.sendUpdate("/probes/" + probeid + "/", post);
	}

	//sends a generic patch update
	this.sendUpdate = function(url, post, callback, errcallback) {
		_this._writingData = true;

		$('.kriek-updateable').attr('disabled', true);
		$.ajax({
			url: url,
			type: 'PATCH',
			dataType: 'json',
			data: JSON.stringify(post),
			contentType:"application/json",
			success: function(data){
				$('.kriek-updateable').attr('disabled', false);
				setTimeout(function(){_this._writingData = false;}, 2000);
				if (callback) { callback(data); }
			},
			error: function(data) {
				$('.kriek-updateable').attr('disabled', false);
				//_this._writingData = false;
				if (errcallback) { errcallback(data); }
			}
		});

		_this.updateFromData(_this.lastLoadedData, true);
	}

	//update global setting with a key/value
	this.updateGlobalSetting = function(key, value, callback, errcallback) {
		url = '/update_global_setting'
		_this._writingData = true;

		$.ajax({
			url: url,
			type: 'POST',
			data: { key: key, value: value },
			success: function(data){
				setTimeout(function(){_this._writingData = false;}, 1000);
				if (callback) { callback(data); }
			},
			error: function(data) {
				_this._writingData = false;
				if (errcallback) { errcallback(data); }
			}
		});
	}

	//purge all data
	this.purgeAllData = function() {
		if (confirm("Delete All Data (this cannot be undone)")) {
			$('#pleaseWaitDialog').modal();

			$.ajax({
				url: "/purgeAllData",
				type: 'POST',
				data: { confirm: true },
				success: function(data){
					$('#pleaseWaitDialog').modal('hide');
					alert("data purge successful.");
				},
				error: function(data) {
					$('#pleaseWaitDialog').modal('hide');
					alert("data purge was NOT successful.");
				}
			});
		}
	}
	
	//this sets whether or not we should be updating the chart
	this.toggleChartUpdatesEnabled = function(enabled) {
		this._chartUpdatesEnabled = !this._chartUpdatesEnabled;
		$('#chartEnabledCheckbox').prop('checked', this._chartUpdatesEnabled);
	}

	//this sets whether or not we should be updating the char
	this.toggleUpdatesEnabled = function(enabled) {
		if (enabled !== undefined) {
			_this._updatesEnabled = enabled;
		} else {
			_this._updatesEnabled = !_this._updatesEnabled;
		}

		if (!_this._updatesEnabled) {
			$('#updatesEnabled').show();
		} else {
			$('#updatesEnabled').hide();
		}

		_this.updateGlobalSetting('UPDATES_ENABLED', _this._updatesEnabled ? "True" : "False");
		$('#updatesEnabledCheckbox').prop('checked', _this._updatesEnabled);
	}

	//udpates the units imperia/metic
	this.toggleUnits = function(units) {
		var u = $('input', $(units));
		u.prop('checked',true);
		_this.updateGlobalSetting('UNITS', u.prop('id'));
		_this._systemStatus.units = u.prop('id');
	}

	//finds the requested probe by id from the latest loaded data
	this.findProbe = function(probeid) {
		var data = _this.lastLoadedData;

		if (data && data) {
			for (var i=0;i<data.length;i++) {
				var probe = data[i];
				if (probe.id == probeid) {
					return probe;
				}
			}
		}

		return null;
	}

	//returns the index of the probe so we can match the colour
	this.findProbeIndex = function(probeid) {
		var data = _this.lastLoadedData;

		if (data && data) {
			for (var i=0;i<data.length;i++) {
				var probe = data[i];
				if (probe.id == probeid) {
					return i;
				}
			}
		}

		return -1;
	}

	//finds the requested ssr by id from the latest loaded data
	this.findSSR = function(ssrid) {
		var data = _this.lastLoadedData;

		if (data) {
			for (var i=0;i<data.length;i++) {
				var probe = data[i];

				for (var j=0;j<probe.ssrs.length;j++) {
					var ssr = probe.ssrs[j];
					if (ssr.id == ssrid) {
						return ssr;
					}
				}
			}
		}
	}

	//called when the user enables/disables pids
	this.onPidCheckboxChanged = function() {
		var pidenabled = $('#ssrPIDEnabled').prop('checked');
		//if the pid is not enabled, disable the inputs
		$("input.pid").prop('disabled', ! pidenabled);
	}
	
	//shows a configuration dialog for a given ssr
	this.configureSSR = function(ssrid,manual_mode) {
		
		if (manual_mode) {
			$("#advancedPID").hide();
		} else {
			$("#advancedPID").show();
		}

		_this._editingSSR = ssrid;

		var ssr = _this.findSSR(ssrid);

		$('#ssrEnabled').prop('checked', ssr.enabled);
		$('#ssrPower').val(ssr.pid.power);
		$('#ssrK').val(ssr.pid.k_param);
		$('#ssrI').val(ssr.pid.i_param);
		$('#ssrD').val(ssr.pid.d_param);
		$('#ssrCycleTime').val(ssr.pid.cycle_time);
		$('#ssrPIDEnabled').prop('checked', ssr.pid.enabled)

		$('#ssrModalTitle').html(ssr.name);
		$('#ssrModal').modal({});
	}

	//saves the ssr from the modal dialog
	this.saveSSRConfig = function() {
		if (!_this._editingSSR) {
			return;
		}
		
		var enabled = $('#ssrEnabled').prop('checked') ? 1 : 0 ;
		var pidenabled = $('#ssrPIDEnabled').prop('checked') ? 1 : 0 ;
		var power = $('#ssrPower').val();
		var k = $('#ssrK').val();
		var i = $('#ssrI').val();
		var d = $('#ssrD').val();
		var cycleTime = $('#ssrCycleTime').val();

		var ssr = _this.findSSR(_this._editingSSR);

		//update our values
		var pid=ssr.pid;
		pid.enabled = pidenabled;
		ssr.enabled = enabled;
		
		if (!isNaN(parseInt(power))) {
			pid.power = power;
		}
		if (!isNaN(parseFloat(k))) {
			pid.k_param = k;
		}
		if (!isNaN(parseFloat(i))) {
			pid.i_param = i;
		}
		if (!isNaN(parseFloat(d))) {
			pid.d_param = d;
		}
		if (!isNaN(parseFloat(cycleTime))) {
			pid.cycle_time = cycleTime;
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
		if (!_this.latestChartData || _this.latestChartData.length == 0 || _this.enabledProbe == null) {
			return;
		}

		/*
		  	Dead-Time (TD): the dead-time of the system is the time delay between the initial response and a 10 % increase in the process variable
			(which is the HLT temperature in our case). Unity is given in seconds.
		*/

		//go through all of our data points and figure out when we've gone up 10% from the first data point
		var start = _this.latestChartData[_this.latestChartData.length-1];
		var end = null;

		var startTemp = null;
		var endTemp = null;
		var enabledProbeIndex = 0;

		for (var i=_this.latestChartData.length-1;i>=0;i--) {
			var data = _this.latestChartData[i];
			//find the probe
			for (var j=0;j<data.probes.length;j++) {
				var probe = data.probes[j];
				if (probe.probe == _this.enabledProbe.id) {
					enabledProbeIndex = j;
					if (startTemp == null) {
						startTemp = probe.temperature;
					} else if (probe.temperature != startTemp && probe.temperature > startTemp*1.1) {
						endTemp = probe.temperature;
						end = data;
						break;
					}
				}
			}

			if (endTemp != null) {
				break;
			}
		}

		if (!end) {
			alert('something wrongo');
			return;
		}

		//go through and find when we hit the provided temperature t
		var findDataAtTemp = function(t) {
			for (var i=_this.latestChartData.length-1;i>=0;i--) {
				var data = _this.latestChartData[i];
				if (data.probes[enabledProbeIndex].temperature > t) {
					return data;
				}
			}
		}


		var t0 = start.date;
		var T1 = parseFloat(startTemp);
		var T2 = parseFloat(_this.latestChartData[0].probes[enabledProbeIndex].temperature);

		var K = T2 - T1 / _this.enabledSSR.pid.power;
		var d = findDataAtTemp(T1 + .283 * (T2 - T1));
		tau3 = moment(d.date) - moment(t0);

		var d = findDataAtTemp(T1 + 0.632 * (T2 - T1));
		tau = moment(d.date) - moment(t0);

		var TD = moment(end.date) - moment(start.date);

		if (TD <= 0) {
			alert('something wrongo2');
			return;
		}

		//Integral of Time weighted Absolute Error (ITAE-Load)
		var kc = (1.357 / K) * Math.pow((TD / tau),-0.947);
		var ti = (tau / 0.842) * Math.pow((TD / tau), 0.738);
		var td = (0.381 * tau) * Math.pow((TD / tau), 0.995);

		console.log('deadtime', TD, tau3, tau);
		console.log(kc, ti, td);


		//Normalized slope (a): the normalized slope of the step response is the increase in temperature per second per percentage of the PID controller output.
			// Stated in a formula: a = change in temperature divided by time-interval divided by PID controller output.
		//Gain (K): the gain of the HLT system. We can model our HLT system as having one input (the PID controller output in %)
			// and one output (the HLT temperature). The Gain of this HLT system is then defined as output divided by input and has a unity of °C / %.
		//Time-constant (tau): the time-constant of the system is another important parameter of the system. It describes how quick the
			// temperature will increase, given a particular output of the PID controller. Unity is given in seconds.
	}

	//called when the user wants to use a schedule
	this.scheduleSelected = function(select) {

		//active this schedule
		scheduleid = $(select).val()
		var enabled = true;

		//disabled
		if (!scheduleid && _this.currentSchedule) {
			scheduleid = _this.currentSchedule.id;
			enabled = false;
		}

		var post = { pk: scheduleid, enabled: enabled };

		$(".schedSteps").empty();

		_this.sendUpdate("/schedules/" + scheduleid + "/", post);
	}

	//enables a specific step of a schedule
	this.enableStep = function(step) {

		var stepid = parseInt(step.id.replace(/[^\d]/g,""));
		var post = { pk: stepid, active: true };
		_this.sendUpdate("/scheduleSteps/" + stepid + "/", post);
		console.log($("#step_" + stepid));

		$(".schedSteps a").removeClass("active");
		$("#step_" + stepid).addClass("active");
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
		if ($('.kriek-tab').length > 0) {
			_this.confId = $('.kriek-tab').attr('data-confid');
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
		_this.loadProbes();
		_this.updateSystemStatus();
	});
	
	return this;
};

var kriek = new RaspBrew();


import Chart from 'chartjs';
import $ from 'jquery';
window.jQuery = $;
window.$ = $;

class Charts {
  constructor() {
  
    this.firstInit = true;
    this.colors = {
      primary: 'rgb(23, 150, 243)',
      success: 'rgb(76, 175, 80)',
      warning: 'rgb(255, 193, 7)',
      danger: 'rgb(255, 23, 68)',
      grayLight: 'rgb(238, 238, 238)',
      grayDark: 'rgb(158, 158, 158)'
    };

    $('#idStart').text($.datepicker.formatDate( "mm/dd/yy", new Date( )));
    $('#idEnd').text($.datepicker.formatDate( "mm/dd/yy", new Date( )));
  }

  setGlobalOptions() {
    // setting the responsive mode to true by default
    Chart.defaults.global.responsive = true;

    // setting the axes color and padding
    Chart.defaults.line.scales.xAxes[0].gridLines =
      Chart.defaults.line.scales.yAxes[0].gridLines =
      Chart.defaults.bar.scales.xAxes[0].gridLines =
      Chart.defaults.bar.scales.yAxes[0].gridLines =
      Chart.defaults.horizontalBar.scales.xAxes[0].gridLines =
      Chart.defaults.horizontalBar.scales.yAxes[0].gridLines = {
        tickMarkLength: 20,
        color: this.colors.grayLight,
        zeroLineColor: 'transparent'
      };

    // setting the padding and label color for the yAxes (these don't have a tickMarkLength)
    Chart.defaults.line.scales.yAxes[0].ticks =
      Chart.defaults.bar.scales.yAxes[0].ticks = {
        padding: 16,
        fontColor: this.colors.grayDark
      };

    // setting the padding and label color for the xAxes (these don't have a tickMarkLength)
    Chart.defaults.line.scales.xAxes[0].ticks =
      Chart.defaults.bar.scales.xAxes[0].ticks = {
        padding: 8,
        fontColor: this.colors.grayDark
      };

    // hover settings for the line charts
    Chart.defaults.line.hover.mode = 'nearest';
    Chart.defaults.line.hover.intersect = true;

    // tooltips settings for the line charts
    Chart.defaults.line.tooltips = {
      mode: 'index',
      intersect: false
    };

    // setting the color of the polar area's grid lines to be the same as the x and y axes of the line and bar charts
    Chart.defaults.polarArea.scale.gridLines.color = this.colors.grayLight;
    Chart.defaults.polarArea.scale.angleLines.color = this.colors.grayLight;

    /**
     * setting the color of the radar's grid and angle lines to be the same as the x and y axes of the line
     * and bar charts
     */
    Chart.defaults.radar.scale.gridLines =
      Chart.defaults.radar.scale.angleLines = {
        color: this.colors.grayLight
      };

    // setting the legend label's color
    Chart.defaults.global.legend.labels.fontColor = this.colors.grayDark;
  }

  createChart(canvas, options) {
    if (!canvas) {
      throw new Error('The chart\'s canvas couldn\'t be found in the DOM.');
    }

    if (this.firstInit) {
      this.setGlobalOptions();
      this.firstInit = false;
    }

    return new Chart(canvas.getContext('2d'), options);
  }

  clearCharts(chart)
  {
    const pieChartCanvas = document.getElementById('pieChart');
    if (pieChartCanvas) {
      pieChartCanvas.destroy();

      chart.createChart(pieChartCanvas, {
        type: 'pie',
        data: [],
        options: {
          maintainAspectRatio: false
        }
      });


     const barChartCanvas = document.getElementById('barChart');
    if (barChartCanvas) {

      barChartCanvas.destroy();

      chart.createChart(barChartCanvas, {
        type: 'bar',
        data: [],
        options: {
          legend: {
            display: true
          },
          scales: {
            xAxes: [{
              barPercentage: 0.7
            }]
          }
        }
      });
    }
    }
  }

  init(api) {
    this.service = api;
    // init bar chart
    const barChartCanvas = document.getElementById('barChart');
    if (barChartCanvas) {
      var chartData = api.GetHighFivePie();

      this.createChart(barChartCanvas, {
        type: 'bar',
        data: chartData,
        options: {
          legend: {
            display: true
          },
          scales: {
            xAxes: [{
              barPercentage: 0.7
            }]
          }
        }
      });
    }

    // init pie chart
    const pieChartCanvas = document.getElementById('pieChart');
    if (pieChartCanvas) {

      this.createChart(pieChartCanvas, {
        type: 'pie',
        data: chartData,
        options: {
          maintainAspectRatio: false
        }
      });
    }

    $('#idTotalKBUp').text(api.GetTotalUpload());
    $('#idTotalKBDown').text(api.GetTotalDownload());
    $('#idStart').datepicker();
    $('#idEnd').datepicker();

    var clearCharts = this.clearCharts;
    var self = this;

    $("#idSearch").click(function(){
      var start = $('#idStart').val();
      var end = $('#idEnd').val();

      clearCharts(self);
      $('#idTotalKBUp').text("(0 MB)");
      $('#idTotalKBDown').text("(0 MB)");
      $('#idTotal').text("(0)");
      $("#idRecordsBody tr").remove();

      api.SetDates(start,end);
    });

    var records = api.GetRecords();

    if(records != null)
    {
        $('#idTotal').text("(" + records.length + ")");
        $.each(records, function(index,item) {
          var tr = $('<tr>').append(
              $('<td>').text(item[0]),          
              $('<td>').text(String(item[2]).substring(0,15)),
              $('<td>').text(Math.round(item[4]/1024,2)),
              $('<td>').text(Math.round(item[5]/1024,2)),
              $('<td>').text(String(item[6]).substring(0,10)),
              $('<td>').text(item[3]),         
              $('<td>').text(item[1])
          ); 
          
          tr.appendTo('#idRecordsBody');
      });

      $('#idRecords').tablesorter({
        widgets: ["zebra", "filter"],
        widgetOptions : {
          // filter_anyMatch replaced! Instead use the filter_external option
          // Set to use a jQuery selector (or jQuery object) pointing to the
          // external filter (column specific or any match)
          filter_external : '.search',
          // add a default type search to the first name column
          filter_defaultFilter: { 1 : '~{query}' },
          // include column filters
          filter_columnFilters: true,
          filter_placeholder: { search : 'Search...' },
          filter_saveFilters : true,
          filter_reset: '.reset'
        }
      });

      var resort = true;
      $("#idRecords").trigger("update", [resort]);
    }
  }
}

export default Charts;

import $ from 'jquery';
window.jQuery = $;
window.$ = $;

class WhiteStatApi 
{
  init (chart) 
  {
    this.chart = chart;
    //this.url = "/images/whitestatdata.json";
    //this.url="http://192.168.1.5:888/json";
    this.url="/json";

    //this.historyUrl = "/images/whitestatdata.json";
    //this.historyUrl = "http://192.168.1.5:888/json/history";
    this.historyUrl = "/json/history";

    //this.lanUrl = "/images/whitestatnetdata.json";
    //this.lanUrl = "http://192.168.1.5:888/json/lansegments";
    this.lanUrl = "/json/lansegments";

    var start = $('#idStart').val();
    if(start == undefined || start == "")
    {
      $('#idStart').val($.datepicker.formatDate("mm/dd/yy",new Date()));
    }
    
    var end = $('#idEnd').val();
    if(end == undefined || end == "")
    {
      $('#idEnd').val($.datepicker.formatDate("mm/dd/yy",new Date()));
    }

    jQuery.ajaxSetup({async:true});  
    
    this.chart.init(this);
    this.refresh(this.chart);
  }

  refresh (chart) 
  {
    var self = this;

    var jqxhr = $.getJSON(self.url, function(data) {
        var dataRecords = data;
        self.records = dataRecords;    
        jqxhr = $.getJSON(self.lanUrl, function(data) {
            var lanRecord = data;
            self.lanRecord = lanRecord;    
            self.CalculateTotal();
            self.chart.refresh(self);
          }); 
      });
  }

  CalculateTotal()
  {
    this.topFive = [];
    this.downloadTotal = 0;
    this.uploadTotal = 0;

    if( this.records == null ||  this.records.data == null || this.records.data.length <= 0)
    {
      return;
    }

    var downloadTotal = 0;
    var uploadTotal = 0;

    var hostDownloads = {};
    var hostNames = {};

    var lanRecord = this.lanRecord;

    this.records.data.forEach(function(rec, index){
      var flag = false;
        
      lanRecord.forEach(function(subnet,index){ flag |= String(rec[0]).startsWith(subnet); });

      if(flag)
      {
        var ip = rec[0];
        var mac = rec[1];
        var host = rec[2];
        var kbIn = Math.round((parseFloat(rec[4]) || 0),2);
        var kbOut = Math.round((parseFloat(rec[5]) || 0),2);

        downloadTotal += kbIn;        
        uploadTotal += kbOut;

        if(host != "(none)")
        {
          hostNames[mac] = host;
        }
        else
        {
          hostNames[mac] = ip;
        }

        if(isNaN(hostDownloads[mac]) || hostDownloads[mac] == null) hostDownloads[mac] = 0;
        hostDownloads[mac]+= kbIn;
      }
    });  
    
    this.downloadTotal = downloadTotal;
    this.uploadTotal = uploadTotal;

    // Create items array
    var items = Object.keys(hostDownloads).map(function(key) {
      return [key, hostDownloads[key]];
    });

    // Sort the array based on the second element
    items.sort(function(first, second) {
      return second[1] - first[1];
    });

    var topFive = [];
    var topFiveKB = 0.0;
    // Create a new array with only the first 5 items
    items.slice(0, 5).forEach(function(rec, index){
      topFiveKB += rec[1];
      topFive.push([hostNames[rec[0]],rec[1]]);
    });

    topFive.push(["Others", this.downloadTotal - topFiveKB]);
    this.topFive = topFive;    
  }

  isValidDate(d) {
    return true;
  }

  SetDates(start, end)
  {
      if(start != "")
      {
        start=$.datepicker.formatDate("yy-mm-dd 00:00:00",new Date(start));
      }
      if(end != "")
      {
        end=$.datepicker.formatDate("yy-mm-dd 00:00:00",new Date(end));
      }
            
      var self = this;
      var url = self.historyUrl+"?start=" + start + "&end=" + end;
      var jqxhr = $.getJSON(url, function(data) {
          var dataRecords = data;
          self.records = dataRecords;
          self.highFive = null;
          self.CalculateTotal();   
          self.chart.refresh(self);
        });
  }

  GetTotalDownload()
  {
    return Math.round(this.downloadTotal / 1024,2);
  }

  GetTotalUpload()
  {
    return Math.round(this.uploadTotal / 1024,2);
  }

  GetRecords()
  {
    if(this.records == null) return [];
    return this.records.data;
  }

  GetHighFivePie()
  {
    if(this.highFive == null)
    {
      this.highFive = this.topFive;
    }

    if(this.highFive != null)
    {
      var pieLabels = [];
      var pieData = [];

      var highFive = this.highFive;

      highFive.forEach(function(rec, index)
      {
        var host = rec[0];
        var KB = Math.round(rec[1]/1024,2);

        pieLabels.push(host);
        pieData.push(KB);
      });

      var pieFrame = {};
      pieFrame.labels = pieLabels;
      var pieDataSet = {};
      pieDataSet.label = "Top Download(MB/Hosts)";
      pieDataSet.data = pieData;
      pieDataSet.backgroundColor = [
           "rgb(23, 150, 243)",
           "rgb(76, 175, 80)",
           "rgb(255, 193, 7)",
           "rgb(238, 238, 238)",
           "rgb(158, 158, 158)",
           "rgb(255, 23, 68)"
      ];

      pieFrame.datasets = [pieDataSet];

      return pieFrame;
    }
  }
}
  
export default WhiteStatApi;
  
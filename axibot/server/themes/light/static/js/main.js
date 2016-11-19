require([
  'vue',
  'utils'
], function (Vue, utils) {

  var sock = new WebSocket(utils.qualifyWebsocketURL("/api"));

  sock.onerror = function (error) {
    alert("websocket error: " + error);
  }

  sock.onmessage = function (e) {
    var msg = JSON.parse(e.data);
    if (msg.type === 'state') {
      vm.state = msg.state;
      vm.numActions = msg.num_actions;
      vm.actionIndex = msg.action_index;
    }
  }

  function sendMessage(msg) {
    sock.send(JSON.stringify(msg));
  }

  function uploadFile(file) {
      var uploadPath = "/upload";

      // Upload the file via ajax, get back an ID reference to it
      var formData = new FormData();
      formData.append("file", file);

      // XXX set the contents of the preview image to this doc

      var xhr = new XMLHttpRequest();
      xhr.open('POST', uploadPath, true);
      xhr.upload.onprogress = function (e) {
        if (e.lengthComputable) {
          if (e.loaded === e.total) {
            // Complete
          } else{
            var progress = (e.loaded / e.total * 100).toFixed(0);
          }
        }
      };

      console.log("uploading");
      xhr.send(formData);
      // Note: we could use onreadystatechange here to get notified of the completion.
  }

  var vm = new Vue({
    el: '#app',
    data: {
      'state': 'error',
      'actionIndex': 0,
      'numActions': 0
    },
    computed: {
      disableManualMove: function () {
        return (this.state != 'idle') && (this.state != 'paused');
      },
      disableResumePlotting: function () {
        return (this.state != 'idle') && (this.state != 'paused');
      },
      disablePausePlotting: function () {
        return (this.state != 'plotting');
      },
      disableCancelPlotting: function () {
        return (this.state != 'plotting') && (this.state != 'paused');
      }
    },
    methods: {
      penUp: function () {
        sendMessage({type: "manual-pen-up"});
      },
      penDown: function () {
        sendMessage({type: "manual-pen-down"});
      },
      resumePlotting: function () {
        sendMessage({type: "resume-plotting"});
      },
      pausePlotting: function () {
        sendMessage({type: "pause-plotting"});
      },
      cancelPlotting: function () {
        sendMessage({type: "cancel-plotting"});
      },
      fileSelected: function (e) {
        if (e.target.files.length > 0) {
          console.log("file selected", e.target.files[0]);
          uploadFile(e.target.files[0]);
        }
      }
    }
  });

});


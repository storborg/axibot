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
      vm.numPaths = msg.num_paths;
      vm.pathIndex = msg.path_index;

    } else if (msg.type == 'new-document') {
      var preview = document.getElementById('preview');
      preview.innerHTML = msg.document;

    } else if (msg.type == 'error') {
      alert("Server Error: " + msg.text);

    }
  }

  function sendMessage(msg) {
    sock.send(JSON.stringify(msg));
  }

  function sendFile(doc) {
    var msg = {
      type: 'set-document',
      document: doc
    };
    sendMessage(msg);
  }

  function handleFile(file) {
      // Set the contents of the preview image to this doc and send msg
      var reader = new FileReader();
      var preview = document.getElementById('preview');
      reader.onload = function (e) {
        preview.innerHTML = e.target.result;
        sendFile(e.target.result);
      }
      reader.readAsText(file);
  }

  var vm = new Vue({
    el: '#app',
    data: {
      'state': 'error',
      'pathIndex': 0,
      'numPaths': 0
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
          handleFile(e.target.files[0]);
        }
      }
    }
  });

});


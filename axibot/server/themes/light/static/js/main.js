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
      vm.penX = msg.x;
      vm.penY = msg.y;
      // XXX This should be done with bound attributes and scaled properly
      setPen(vm.penX / 20, vm.penY / 20);

    } else if (msg.type == 'new-document') {
      var doc = document.getElementById('document');
      doc.innerHTML = msg.document;

    } else if (msg.type == 'error') {
      alert("Server Error: " + msg.text);

    }
  }

  function setPen(x, y) {
    console.log("setpen", x, y);
    var pen = document.getElementById('pen');
    pen.style.left = x + 'px';
    pen.style.top = y + 'px';
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
      var doc = document.getElementById('document');
      reader.onload = function (e) {
        doc.innerHTML = e.target.result;
        sendFile(e.target.result);
      }
      reader.readAsText(file);
  }

  var vm = new Vue({
    el: '#app',
    data: {
      'state': 'error',
      'penX': 0,
      'penY': 0,
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
          handleFile(e.target.files[0]);
        }
      }
    }
  });

});


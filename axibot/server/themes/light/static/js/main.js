require([
  'vue',
  'utils'
], function (Vue, utils) {

  var sock = new WebSocket(utils.qualifyWebsocketURL("/api"));

  sock.onerror = function (error) {
    console.log("websocket: error", error);
    alert("websocket error: " + error);
  }

  sock.onmessage = function (e) {
    var msg = JSON.parse(e.data);
    console.log("websocket: message", msg);
    handleMessage(msg);
  }

  function sendMessage(msg) {
    sock.send(JSON.stringify(msg));
  }

  function handleMessage(msg) {
    if (msg.type === 'state') {
      vm.state = msg.state;
      vm.numActions = msg.num_actions;
      vm.actionIndex = msg.action_index;
    }
  }

  var vm = new Vue({
    el: '#app',
    data: {
      'state': 'error',
      'actionIndex': 0,
      'numActions': 0
    },
    methods: {
      penUp: function () {
        console.log("pen up pressed");
        sendMessage({type: "manual-pen-up"});
      },
      penDown: function () {
        console.log("pen down pressed");
        sendMessage({type: "manual-pen-down"});
      },
      resumePlotting: function () {
        console.log("resume plotting");
        sendMessage({type: "resume-plotting"});
      },
      pausePlotting: function () {
        console.log("pause plotting");
        sendMessage({type: "pause-plotting"});
      },
      cancelPlotting: function () {
        console.log("cancel plotting");
        sendMessage({type: "cancel-plotting"});
      }
    }
  });

});


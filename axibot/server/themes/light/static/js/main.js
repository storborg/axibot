require([
  'vue',
  'utils'
], function (Vue, utils) {

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
      },
      penDown: function () {
        console.log("pen down pressed");
      },
      startPlotting: function () {
        console.log("start plotting");
      },
      pausePlotting: function () {
        console.log("pause plotting");
      },
      cancelPlotting: function () {
        console.log("cancel plotting");
      }
    }
  });

  var sock = new WebSocket(utils.qualifyWebsocketURL("/api"));
  sock.onopen = function () {
    console.log("websocket: opened");
  }

  sock.onerror = function (error) {
    console.log("websocket: error", error);
  }

  sock.onmessage = function (e) {
    var msg = JSON.parse(e.data);
    console.log("websocket: message", msg);

    if (msg.type === 'state') {
      vm.state = msg.state;
      vm.numActions = msg.num_actions;
      vm.actionIndex = msg.action_index;
    }
  }
});


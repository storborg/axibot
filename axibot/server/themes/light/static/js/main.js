require([
  'vue',
  'utils'
], function (Vue, utils) {

  var vm = new Vue({
    el: '#app',
    data: {
      'state': 'error',
      'penX': 0,
      'penY': 0,
      'penUp': true,
      'consumedTime': 0,
      'estimatedTime': 0,
      'actionIndex': 0,
      'numActions': 0
    },
    computed: {
      previewX: function () {
        return this.penX / 2032;
      },
      previewY: function () {
        return this.penY / 2032;
      },
      progress: function () {
        return 100 * this.consumedTime / this.estimatedTime;
      },
      timeRemaining: function () {
        var d = new Date((this.estimatedTime - this.consumedTime) * 1000);
        return d.toISOString().substr(11, 8);
      }
    },
    methods: {
      manualPenUp: function () {
        this.sendMessage({type: "manual-pen-up"});
      },
      manualPenDown: function () {
        this.sendMessage({type: "manual-pen-down"});
      },
      resumePlotting: function () {
        this.sendMessage({type: "resume-plotting"});
      },
      cancelPlotting: function () {
        this.sendMessage({type: "cancel-plotting"});
      },
      fileSelected: function (e) {
        if (e.target.files.length > 0) {
          this.handleFile(e.target.files[0]);
        }
      },
      sendMessage: function (msg) {
        this.sock.send(JSON.stringify(msg));
      },
      handleFile: function (file) {
          // Set the contents of the preview image to this doc and send msg
          var reader = new FileReader();
          var doc = document.getElementById('document');
          var that = this;
          reader.onload = function (e) {
            doc.innerHTML = e.target.result;
            that.sendMessage({
              type: 'set-document',
              document: e.target.result
            });
          }
          reader.readAsText(file);
      }
    },
    created: function () {
      this.sock = new WebSocket(utils.qualifyWebsocketURL("/api"));
      this.sock.onerror = function (error) {
        alert("websocket error: " + error);
      }
      this.sock.onmessage = function (e) {
        var msg = JSON.parse(e.data);

        if (msg.type === 'state') {
          vm.state = msg.state;
          vm.numActions = msg.num_actions;
          vm.actionIndex = msg.action_index;
          vm.penX = msg.x;
          vm.penY = msg.y;
          vm.penUp = msg.pen_up;
          vm.consumedTime = msg.consumed_time;
          vm.estimatedTime = msg.estimated_time;

        } else if (msg.type == 'new-document') {
          var doc = document.getElementById('document');
          doc.innerHTML = msg.document;

        } else if (msg.type == 'error') {
          alert("Server Error: " + msg.text);

        }
      }
    }
  });

});


require([
  'jquery',
  'utils'
], function ($, utils) {

  $(function () {
    console.log('Loaded light: main.');

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
        $('#state').text(msg.state);
        $('#num_actions').text(msg.num_actions);
        $('#action_index').text(msg.action_index);
      }

    }

  });
});


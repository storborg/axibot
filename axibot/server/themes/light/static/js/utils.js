define(function () {
  "use strict";

  var exports = {};

  exports.qualifyWebsocketURL = function(path) {
    var protocol;
    if (window.location.protocol === "http:") {
      protocol = "ws:";
    } else {
      protocol = "wss:";
    }
    return protocol + window.location.host + path;
  };

  exports.secondsToString = function(secs) {
    var d = new Date(secs * 1000);
    return d.toISOString().substr(11, 8);
  };

  return exports;
});

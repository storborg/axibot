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

  return exports;
});

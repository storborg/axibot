export function qualifyWebsocketURL(path) {
  var protocol;
  if (window.location.protocol === "http:") {
    protocol = "ws:";
  } else {
    protocol = "wss:";
  }
  return protocol + window.location.host + path;
}


export function secondsToString(secs) {
  var d = new Date(secs * 1000);
  return d.toISOString().substr(11, 8);
}

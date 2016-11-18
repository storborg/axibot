require([
  'jquery',
  'dropzone',
  'utils'
], function ($, Dropzone, utils) {

    // Extended disable function
    jQuery.fn.extend({
        disable: function(state) {
            return this.each(function() {
                var $this = $(this);
                if($this.is('input, button, textarea, select'))
                    this.disabled = state;
                else
                    $this.toggleClass('disabled', state);
            });
        }
    });

    function initDropZone() {
      Dropzone.options.dropper = {
          init: function() {
              this.on("thumbnail", function () {
                  // XXX: is there a better way to do this?
                  var width = $(".dz-image img").width();
                  $("#dropper").width(width);
              });
          },
          paramName: "file", // The name that will be used to transfer the file
          autoProcessQueue: false, // Don't auto upload files
          autoDiscover: "false",
          accept: function(file, done) {
              console.log("dropzone accepted file");
              console.log(file);
              done();
          }
      };

      var dropper = new Dropzone("div#dropper",
          { url: "/upload", // Set url to something random to avoid auto uploads
            addRemoveLinks: true} // Show remove button
      );
      // Make the dropper green when a file is over it
      dropper.on("dragover", function () {
          console.log("setting hover class");
          this.className = 'hover'; return false;
      });
      dropper.on("dragleave",  function () {
          console.log("removing hover");
          this.className = ''; return false;
      });
      dropper.on("addedfile", function() {
          console.log("Enabling start");
          $("#start").disable(false);
      });
      dropper.on("removedfile", function() {
          console.log("Disabling start");
          $("#start").disable(true);
      });
      return dropper;
  }

  function bindButtons(dropper) {
      $("#start").on("click", function() {
          dropper.processQueue();
      })
  }

  $(function () {
    console.log('Loaded light: main.');

    var dropper = initDropZone();
    bindButtons(dropper);

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
      }

    }

  });
});


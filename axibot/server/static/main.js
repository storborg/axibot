
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
        accept: function(file, done) {
            console.log(file);
            done();
        }
    };

    var dropper = $("div#dropper");
    // Set the url to something random to avoid dropzone doing stupid things
    dropper.dropzone({ url: "blahblah" });
    // Make the dropper green when a file is over it
    dropper.on("dragover", function () {
        console.log("setting hover class");
        this.className = 'hover'; return false;
    });
    dropper.on("dragleave",  function () {
        console.log("removing hover");
        this.className = ''; return false;
    });
}

function bindButtons() {
    var buttons = ["up", "down", "left", "right"];
    for(const dir of buttons) {
        $(`button#${dir}`).on("click", function() {
            $.post(`move/${dir}`, function(data) {
            });
        });
    }
}

$(document).ready(function() {
    console.log("onReady");
    initDropZone();
    bindButtons();
});

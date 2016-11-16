// Common RequireJS config
// Used only in development and for optimization
var require = {
  shim: {
    underscore: {
      exports: '_',
      init: function () {
         this._.templateSettings = {
          evaluate    : /\{\{(.+?)\}\}/g,
          interpolate : /\{\{=(.+?)\}\}/g,
          escape      : /\{\{-(.+?)\}\}/g,
        };
      }
    },

    'bootstrap4/alert': ['jquery'],
    'bootstrap4/button': ['jquery'],
    'bootstrap4/carousel': ['jquery'],
    'bootstrap4/collapse': ['jquery'],
    'bootstrap4/dropdown': ['jquery'],
    'bootstrap4/modal': ['jquery'],
    'bootstrap4/popover': ['jquery', 'bootstrap4/tooltip'],
    'bootstrap4/scrollspy': ['jquery'],
    'bootstrap4/tab': ['jquery'],
    'bootstrap4/tooltip': ['jquery', 'tether'],
    'bootstrap4/util': ['jquery'],
  }
};

ckan.module('search_option_popover', function ($, _) {
  return {
    initialize: function () {
      this.el.on('click', this._onClick);
    },

    _onClick: function(event) {

        if($(this).hasClass('icon-minus-sign')){
            $('#search_option_panel').hide(500);
            $(this).removeClass('icon-minus-sign').addClass('icon-plus-sign');
        }else{
            $('#search_option_panel').show(500);
            $(this).removeClass('icon-plus-sign').addClass('icon-minus-sign');
        }
    }
  };
});

ckan.module('generatePDF', function ($, _) {
  return {

    initialize: function () {
        this.el.on('click', this._onClick);    
    },

    _onClick: function(event) {
        var action = $(this).attr('data-module-action');
        var id = $(this).attr('data-module-id');
        var action_url = '/stats/' + action + '_pdf';
        if (id.length){
            action_url = action_url + '/' + id;
        }
        window.open(action_url, '_bkank');
    }
  };
});



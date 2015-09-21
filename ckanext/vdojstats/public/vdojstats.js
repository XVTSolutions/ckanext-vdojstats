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
        var username = $(this).attr('data-module-username');
        var action_url = '/stats/' + action + '_pdf';
        if (username.length){
            action_url = action_url + '/' + username;
        }
        $('#search_form').attr('action', action_url).attr('target', '_blank').submit();
    }
  };
});

ckan.module('generateCSV', function ($, _) {
  return {

    initialize: function () {
        this.el.on('click', this._onClick);    
    },

    _onClick: function(event) {
        var action = $(this).attr('data-module-action');
        var username = $(this).attr('data-module-username');
        var action_url = '/stats/' + action + '_csv';
        if (username.length){
            action_url = action_url + '/' + username;
        }
        $('#search_form').attr('action', action_url).attr('target', '_blank').submit();
    }
  };
});

ckan.module('generateXML', function ($, _) {
  return {

    initialize: function () {
        this.el.on('click', this._onClick);    
    },

    _onClick: function(event) {
        var action = $(this).attr('data-module-action');
        var username = $(this).attr('data-module-username');
        var action_url = '/stats/' + action + '_xml';
        if (username.length){
            action_url = action_url + '/' + username;
        }
        $('#search_form').attr('action', action_url).attr('target', '_blank').submit();
    }
  };
});


ckan.module('vdojstats_select_organisation', function ($, _) {
    var properties = {
      opendata_organisation : ''
    };

    return {
    /* An object of module options */

    initialize: function () {
      properties.opendata_organisation = this.options.opendata_organisation;
      this.el.on('change', this._onChange);
      this.el.trigger('change');
    },

    _onChange: function(event) {
        var display = false;
        $('#open_dataset_div').hide(500);
        $(event.target).find('option:selected').each(function (){
            if($(this).val()==properties.opendata_organisation){
                display = true;
            }
        });
        if (display)
            $('#open_dataset_div').show(500);
        else{
            $('#open_dataset_div').hide(500);
            //clear all selected
            $('#open_dataset_div select option:selected').removeAttr('selected');
        }

    }
  };
});

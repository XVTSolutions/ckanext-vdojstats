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
        var specialElementHandlers = {
            '#editor': function (element,renderer) {
                return true;
            }
        };

        var doc = new jsPDF();
        doc.fromHTML($('#content h2').html(), 15, 15, {
            'width': 170,'elementHandlers': specialElementHandlers
        });
          var string = doc.output('datauristring');
          var x = window.open();
          x.document.open();
          x.document.location=string;
    }
  };
});



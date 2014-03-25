
  $(document).ready(function(){ 
/*
        var specialElementHandlers = {
            '#editor': function (element,renderer) {
                return true;
            }
        };
        $('#generatePDF').click(function () {
            var doc = new jsPDF();
            doc.fromHTML($('#target').html(), 15, 15, {
                'width': 170,'elementHandlers': specialElementHandlers
            });
            doc.save('sample-file.pdf');
        });
    var doc = new jsPDF();
    doc.text(20, 20, 'Hello world.');
    doc.save('Test.pdf');
*/

        $('#search_option_trigger').on('click', function(event){
            if($(this).hasClass('icon-minus-sign')){
                $('#search_option_panel').hide(500);
                $(this).removeClass('icon-minus-sign').addClass('icon-plus-sign');
            }else{
                $('#search_option_panel').show(500);
                $(this).removeClass('icon-plus-sign').addClass('icon-minus-sign');
            }
        });


    });


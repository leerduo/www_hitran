$(document).ready(function(){
    //get the height and width of the page
    var window_width = $(window).width();
    var window_height = $(window).height();

    //vertical and horizontal centering of modal window(s)
    /* use each(function()) so if we have more then one 
       modal window we center them all */
    $('.modal_window').each(function(){
        //get the height and width of the modal
        var modal_height = $(this).outerHeight();
        var modal_width = $(this).outerWidth();
        //calculate top and left offset needed for centering
        var top = (window_height-modal_height)/2;
        var left = (window_width-modal_width)/2;
        //apply new top and left css values
        $(this).css({'top' : top , 'left' : left});
    });

    $('.activate_modal').click(function(){  
        /* get the id of the modal window stored in the name of the
           activating element */
        var modal_id = $(this).attr('name');
        show_modal(modal_id);
    });

    $('.close_modal').click(function(){
        close_modal();
        });
    });
 
function close_modal() {
    //hide the mask  
    $('#mask').fadeOut(250);  
    //hide modal window(s)  
    $('.modal_window').fadeOut(250);  
}

function show_modal(modal_id) {
    // set display to block and opacity to 0 so we can use fadeTo  
    $('#mask').css({ 'display' : 'block', opacity : 0});  
    // fade in the mask to opacity 0.6  
    $('#mask').fadeTo(250,0.8);  
    // show the modal window  
    $('#'+modal_id).fadeIn(250);  

}

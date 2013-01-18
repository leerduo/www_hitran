// the ID of the molecule whose modal isotopologues window is open is called
// this_molecule, and it needs to be a global variable
var this_molecule = 0;
// the ID of the modal window for the selected molecule
var modal_id = 0;

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
        modal_id = $(this).attr('name');
        show_modal(modal_id);
    });

    $('.close_modal').click(function(){
        close_modal();
        });
    });
 
function close_modal() {
    //alert("isos window for molecule "+this_molecule+" is about to close");
    /*var s = '';
    for (isoID in isoIDs[this_molecule]) {
        s += ','+isoID;
    }
    alert("isos:"+s);*/
    /* select_molecule is to be:
        0 if no isotopologues have been ticked,
        1 if some but not all isotopologues have been ticked, or
        2 if all isotopologues have been ticked
    */
    select_molecule = 0;
    all_isos_checked = true;
    for (var i in isoIDs[this_molecule]) {
        isoID = isoIDs[this_molecule][i];
        var cbx = $('#'+modal_id).find('.isocheckbox_'+isoID);
        //alert("cbx for modal_id="+modal_id+", isoID="+isoID+" is "+ cbx);
        if (cbx.attr('checked')) {
            select_molecule = 1;
        } else {
            all_isos_checked = false;
        }
    }
    if (all_isos_checked) {
        select_molecule = 2;
    }
    //alert("select the molecule? "+select_molecule);
    var molec_cbx = $('#molec'+this_molecule);
    //alert("molec_cbx.checked = " + molec_cbx.attr('checked','checked'));
    if (select_molecule == 0) {
        // no isotopologues have been selected: untick the molecule's checkbox
        molec_cbx.removeAttr('checked');
        // and remove any grey-colouring
        molec_cbx.removeAttr('class');
    } else {
        // at least one isotopologue has been selected: tick the molecule's box
        molec_cbx.attr('checked','checked');
        if (select_molecule == 1) {
            // only some of the isotopologues have been selected: leave the
            // molecule's checkbox ticked, but set it to a grey colour
            molec_cbx.attr({'class': 'some_selected'});
        } else {
            // if all isotopologues are selected, remove grey colouring
            molec_cbx.removeAttr('class');
        }
    }
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
    this_molecule = $('#'+modal_id).attr('name');
}

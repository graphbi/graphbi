$(document).ready(function(){
    $("#button-query").click(function(){
	var query = $.trim($("#query").val());
		if(query != ""){
                  // Show alert dialog if value is not blank
                  var queryStatement = $('#query').val();
		  $.get( "query", {query:queryStatement}).done(function( data ) {
  			$( "#table" ).html( data );
		  });
		}
		else{
                alert("Empty query!");
            }

        });

    //define individual event for enter key
    $('#input-filter,#input-group').keyup(function(e){
    if(e.keyCode == 13){
      $(this).trigger("enterKey");
    }
    });

    //bind the event to the input fields
    $("#input-filter,#input-group").bind("enterKey",function(e){
      filter_group();
    });

    //function to filter or group the dataframe
    function filter_group(){
    var filter = $("#input-filter").val();
    var group = $("#input-group").val();
    $.get( "filter_group", {filter: filter,group: group }).done(function( data ){
        $( "#table" ).html( data );
    });
   };

   //function for first, previews, next and last buttons to load previews or next data
   $('#table').on('click','#button-first, #button-previous, #button-next, #button-last', function(){
     clicked_button = $(this).attr('id');
     $.get( "paging", {button:clicked_button}).done(function( data ) {
       $("#table").html( data );});
   });
});

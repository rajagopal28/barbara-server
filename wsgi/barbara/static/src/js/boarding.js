$(function(){
    $('#routeSelectInput')
        .change(function(event){
           var form = $('#boardForm');
            $(form).find('input[name="routeId"]').val($('#routeSelectInput').val());
            form.submit();
    });
    $('#startSelectInput')
        .change(function(event){
           var form = $('#boardForm');
            console.log($(form).find('input[name="startRoute"]'));
            $(form).find('input[name="startRoute"]').val($('#startSelectInput').val());
            form.submit();
    });
    $('#endSelectInput')
        .change(function(event){
           var form = $('#boardForm');
            console.log($(form).find('input[name="endRoute"]'));
            $(form).find('input[name="endRoute"]').val($('#endSelectInput').val());
            form.submit();
    });
});
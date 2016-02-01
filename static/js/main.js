$(function() {
  $('.sub').click(function() {
    $(this).fadeIn(100).fadeOut(100).fadeIn(100);

    if($(this).html().indexOf('+') > -1){
      $(this).html($(this).text().replace("+", "-"));
    }else{
      $(this).html($(this).text().replace("-", "+"));
    }

    $(this).parent().toggleClass('active');

    $.ajax({
      type: 'POST',
      data: 'name='+$(this).data('name'),
      url: '/sub',
      cache:false
    });
  });
});
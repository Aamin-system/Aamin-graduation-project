preventDefault = function(){
    var btn = $('.btn');
    var btnText = $(this).find(".btn-text")       
    var badge = $(".like-badge");
    var count = parseInt(badge.text());
    console.log(count);
 
    if (btn.hasClass('active')) {
       btnText.text("Like");
       badge.text(2);
       btn.removeClass('active');
    }else {
       btnText.text("Liked");
       badge.text(count + 1);
       btn.addClass('active');
    }
 }
 
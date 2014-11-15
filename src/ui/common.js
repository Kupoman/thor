function setupNav(nav) {
    $('.nav.current').empty();
    nav.forEach(function(i) {
        $('.nav.current').append('<li><a href="#">' + i + '</a></li>');
    });

    $('.nav.current li').first().addClass('active');
}

function navUp() {
    var el = $('.nav.current li.active').prev();
    if (!el.length)
        el = $('.nav.current li').last();

    $('.nav.current li').removeClass('active');
    el.addClass('active');
}

function navDown() {
    var el = $('.nav.current li.active').next();
    if (!el.length)
        el = $('.nav.current li').first();

    $('.nav.current li').removeClass('active');
    el.addClass('active');
}

function navEnter() {
    do_nav($('.tab-pane.active').attr('id'), $(".nav.current li.active a").html());
}

function switchToTab(id) {
    if ($('#tabs .active > a').attr('href') != '#' + id) {
        $('#tabs a[href=#' + id + ']').tab('show');
        $('.nav').removeClass('current');
        $('#' + id + ' .nav').addClass('current');
        $('.nav.current li').removeClass('active');
        $('.nav.current li').first().addClass('active');
    }
}
var block_nav = false;
var blocked_nav_enter_cb = undefined;

function setupNav(nav) {
    $('.nav.current').empty();
    nav.forEach(function(i) {
        $('.nav.current').append('<li><a href="#">' + i + '</a></li>');
    });

    $('.nav.current li').first().addClass('active');
}

function navUp() {
    if (!block_nav) {
        var el = $('.nav.current li.active').prev();
        if (!el.length)
            el = $('.nav.current li').last();

        $('.nav.current li').removeClass('active');
        el.addClass('active');
    }
}

function navDown() {
    if (!block_nav) {
        var el = $('.nav.current li.active').next();
        if (!el.length)
            el = $('.nav.current li').first();

        $('.nav.current li').removeClass('active');
        el.addClass('active');
    }
}

function navEnter() {
    if (!block_nav) {
        do_nav($('.tab-pane.active').attr('id'), $(".nav.current li.active a").html());
    }
    else if (blocked_nav_enter_cb !== undefined) {
        blocked_nav_enter_cb();
    }
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
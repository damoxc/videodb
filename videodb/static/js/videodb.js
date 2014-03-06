const KEY_ENTER = 13;
const KEY_SPACE = 32;
const KEY_LEFT  = 37;
const KEY_UP    = 38;
const KEY_RIGHT = 39;
const KEY_DOWN  = 40;
const KEY_F     = 70;
const KEY_R     = 82;

// Formatters
function fduration(seconds) {
    if (!seconds)
        seconds = 0

    if (seconds == 0)
        return "00:00"

    if (seconds < 60) {
        seconds = ("0"+seconds).slice(-2)
        return "00:" + seconds
    }

    minutes = Math.floor(seconds / 60)
    seconds = ("0" + (seconds % 60)).slice(-2)
    if (minutes < 60) {
        minutes = ("0" + minutes).slice(-2)
        return minutes + ":" + seconds
    }

    hours = ("0" + (Math.floor(minutes / 60))).slice(-2)
    minutes = ("0"+ (minutes % 60)).slice(-2)
    return hours + ":" + minutes + ":" + seconds
}

function fsize(bytes, showZero) {
    if (!bytes && !showZero) return '';
    bytes = bytes / 1024.0;

    if (bytes < 1024) { return bytes.toFixed(1)  + ' KiB'; }
    else { bytes = bytes / 1024; }

    if (bytes < 1024) { return bytes.toFixed(1)  + ' MiB'; }
    else { bytes = bytes / 1024; }

    return bytes.toFixed(1) + ' GiB'
}

function pad(n, width, z) {
  z = z || '0';
  n = n + '';
  return n.length >= width ? n : new Array(width - n.length + 1).join(z) + n;
}

function addTag(elem, tag) {
    elem = $(elem)
    var li = elem.parent();

    li.before("<li class='tag' data-tag='" + tag + "'>" + tag + "<a href='#' class='tag-remove'>x</a></li>");
    $.ajax('/video/' + elem.data('id') + '/add-tag/' + tag, {
        error: function() {

        }
    })
}

function addThumbScroll(img) {
    var img = $(img),
        src = img.attr('src'),
        act = null;

    img.mouseenter(function() {
        var baseSrc = src.substring(0, src.lastIndexOf('/')),
            thumb   = 1;

        var loopFunc = function() {
            img.attr('src', baseSrc + '/' + pad(thumb++, 8, 0) + '.jpg');
        };
        loopFunc();
        looping = window.setInterval(loopFunc, 1000);
    });

    img.mouseleave(function() {
        window.clearInterval(looping);
        img.attr('src', src);
    });
}

$(document).ready(function() {
    $('.thumb img').each(function() {
        addThumbScroll(this);
    });

    $('#tag-input').typeahead({
        minLength: 2,
        source: function(query, process) {
            $.ajax('/tags.json?q=' + query, {
                success: function(data) {
                    process(data.tags);
                }
            });
        }
    });

    $('#tag-input').change(function(e) {
        var tag = $(this).val();
        if (tag == '')
            return;

        $(this).val('');
        addTag(this, tag);
    })

    $('#tag-input').keydown(function(e) {
        if (e.keyCode != KEY_ENTER && e.keyCode != KEY_SPACE)
            return;

        if (e.keyCode ==  KEY_ENTER) {
            e.stopPropagation()
            e.preventDefault();
        }

        if ($(this).data('typeahead').shown) {
            return false;
        }

        var tag = $(this).val();
        if (tag == '')
            return false;

        $(this).val('');
        addTag(this, tag);
        return false;
    });

    $(window).keydown(function(e) {
        switch (e.keyCode) {
            case KEY_UP:
            case KEY_DOWN:
                var vol = videojs('video').volume();
                if (e.keyCode == KEY_UP) {
                    if (vol == 1.0)
                        return;
                    vol += 0.1;
                } else {
                    if (vol == 0.0)
                        return;
                    vol -= 0.1;
                }
                videojs('video').volume(vol);
                break;

            case KEY_LEFT:
            case KEY_RIGHT:
                var time = videojs('video').currentTime();
                var shift = (e.ctrlKey) ? 60 : 10;
                if (e.keyCode == KEY_RIGHT)
                    time += shift
                else
                    time -= shift
                videojs('video').currentTime(time);
                break;

            case KEY_SPACE:
                if (videojs('video').paused())
                    videojs('video').play();
                else
                    videojs('video').pause();
                break;

            case KEY_F:
                videojs('video').requestFullScreen();
                break;

            case KEY_R:
                if (e.altKey)
                    window.location = '/random';
                break;
        }
    });

    if ($('video')[0]) {
    videojs('video').ready(function() {
        var video = this;
        var ts = 0, watched = 0, viewed = false;

        $(video.controlBar.progressControl.b).on('mousemove', function(e) {
            var d = video.duration();
        })

        video.on('timeupdate', function(e) {
            if (ts && !viewed && !video.paused()) {
                watched += e.timeStamp - ts;
                if (watched >= 60000) {
                    var videoId = $(video.N).data('id');
                    viewed = true;
                    $.ajax('/video/' + videoId + '/add-view', {
                        success: function() {
                            $('dd.views').text(Number($('dd.views').text()) + 1)
                        }
                    });
                }
            }
            ts = e.timeStamp;
        })
        //myPlayer.play();
    });
    }

    if ($('#videos-table')[0]) {
        var page = 2;
        $(window).scroll(function() {
            var height = $(document).height() - $(window).height(),
                scroll = $(window).scrollTop();

            if (height == scroll) {
                $.ajax(location.pathname + '?page=' + page, {
                    success: function(data) {
                        page++;
                        data.videos.forEach(function(v) {
                            var thumb = pad(v.thumb, 8, 0);
                            var newRow = $('<tr>' +
                                '<td class="thumb">' +
                                    '<a href="/player/'+v.id +'">' +
                                        '<img src="/thumbs/' + v.id + '/' + thumb +'.jpg">' +
                                    '</a>' +
                                '</td>' +
                                '<td>' +
                                    '<a href="/player/'+v.id +'">' + v.name + '</a>' +
                                '</td>' +
                                '<td>' + fduration(v.length) + '</td>' +
                                '<td>' + v.views + ' views</td>' +
                                '<td>' + fsize(v.size) + '</td>' +
                            '</tr>')
                            addThumbScroll(newRow.find('.thumb img')[0]);
                            $('#videos-table').append(newRow)
                        })
                    }
                })
            }
        })
    }
/*
    $('word-cloud').jQCloud(wordArray,{
        width: 800,
        height: 600,
        delayedMode: false
    });*/
});

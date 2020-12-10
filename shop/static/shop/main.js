function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function round(value, precision) {
    var multiplier = Math.pow(10, precision || 0);
    return Math.round(value * multiplier) / multiplier;
}

function getRatingStars(ratingValue, size){
    var starMarkup = '<i class="fas fa-star"></i>',
        rounded_rating,
        display_rating,
        htmlString = '';

    if (ratingValue && ratingValue != "0"){
        display_rating = round(ratingValue,1);
        rounded_rating = Math.ceil(ratingValue);
        htmlString = '<span class="stars stars-' + (size ? size : 'none') + '" title="' + display_rating + ' stars">';
        for(var i = 1; i <= rounded_rating; i++){
            htmlString += starMarkup;
        }
        htmlString += display_rating + '</span>';
    } else {
        htmlString += '<small class="text-muted">Be the first to rate this item!</small>';
    }

    return htmlString;
}

function rate(itemId){
    console.log('about to rate item via ajax.');
    $.ajax({
        url: 'rate/',
        method: 'POST',
        data: $('.ratings-form').serialize(),
    })
    .done(function(data){
        console.log('Successfully rated item.');
        $('div.ratings-info').html(data);
        //alert($('.rating-number').attr('data-rating'), $('.rating-number').attr('data-rating-size'))
        $('.rating-number').html(
            getRatingStars($('.rating-number').attr('data-rating'), $('.rating-number').attr('data-rating-size'))
        );
    })
    .fail(function(error){
        console.log("Error submitting rating.");
        console.log(error);
    });
}

function favorite(itemId, url){
    console.log('about to favorite item via ajax.');
    $.ajax({
        url: url,
        method: 'POST',
        data: {
            'csrfmiddlewaretoken' : getCookie('csrftoken'),
        },
    })
    .done(function(data){
        console.log('Successfully favorited item.');
        $('div#' + itemId + ' .favorite').html(data);
    })
    .fail(function(error){
        console.log("Error submitting favorite.");
        console.log(error);
    });
}

function productQuestion(itemId){
    console.log('about to comment on dish via ajax.');
    $.ajax({
        url: 'question/', //$('.comment-form').attr('action'),
        method: 'POST',
        data: $('.comment-form').serialize(),
    })
    .done(function(data){
        console.log('Successfully posed question.');
        $('#usersComments').append(data);
    })
    .fail(function(error){
        console.log("Error submitting comment.");
        console.log(error);
    });
}

$('.ratings-form input[type="submit"]').on('click', function(e){
    e.preventDefault();
    var itemId = $(this).closest('.container').attr('data-id');
    rate(itemId);
});

$('[data-rating]').html(function(index,oldHTML){
    var rating = $(this).attr('data-rating');
    var size = $(this).attr('data-rating-size') || null;
    return getRatingStars(rating, size);
})

$('.newDish').click(function(e){
    // toggle new rating button
    if($(this).find('small').text() == ' New Rating') {
        $(this).find('small').html('<i class="fas fa-minus-circle"></i> Hide');
        $('#newRating').show();
    } else {
        $(this).find('small').html('<i class="fas fa-plus-circle"></i> New Rating');
        $('#newRating').hide();
    }
});

$('.help-text').html(function(index,oldHtml){
    return '<span class="help-icon" data-toggle="tooltip" data-html="true" data-placement="right" style="color:#009EC3" title="' + oldHtml + '"><i class="fas fa-info-circle"></i></span>';
});

$('.newComment').click(function(e){
    $('#newComment').toggle()
})

$('.comment-form input[type="submit"]').on('click', function(e){
    e.preventDefault();
    var itemId = $(this).closest('.container').attr('data-id');
    productQuestion(itemId);
    $(this).parent().trigger('reset')
    $('#newComment').hide();
});

$('.existing-images').on('click', '.existing-image .action-button', function(e){
    e.preventDefault();
    console.log('about to update image.');

    if ($(this).hasClass('is-default')) {
        return false;
    }

    $.ajax({
        url: $(this).attr('data-href'),
        method: 'POST',
        data: {
            'csrfmiddlewaretoken' : $('input[name="csrfmiddlewaretoken"]').val(),
        }
    })
    .done(function(data){
        console.log('Successfully updated photo.');
        $('div.existing-images').html(data);
    })
    .fail(function(error){
        console.log("Error updating photo.");
        console.log(error);
    });
});

$('div.thumbnails').on('click', '.thumbnail', function(e){
    // console.log('Clicked image');
    var thumbnail_image = $(this).find('img');
    $(this).siblings().removeClass('selected'); // .css('border', 'none');
    $(this).addClass('selected'); // css('border', '1px solid red');
    $('.main-image img').attr('src', thumbnail_image.attr('src'));
    // $('div.description').append(thumbnail_image.attr('src'));
});

$(function () {
    $('[data-toggle="tooltip"]').tooltip()
    // add bootstrap form-control class to signup and usercreation forms
    $('div.container.signup,div.container.login').find('input,textarea,select').addClass('form-control');
});



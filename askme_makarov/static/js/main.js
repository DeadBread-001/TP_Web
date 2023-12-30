function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();

            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

$(document).ready(function () {
    $('.checkbox-section input[type="checkbox"]').each(function () {
        var commentId = $(this).data('id');
        var checkbox = this;

        const formData = new FormData();
        formData.append('comment_id', commentId);

        const checkAuthorRequest = new Request('/check_author/', {
            method: 'POST', body: formData, headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        });

        fetch(checkAuthorRequest)
            .then((response) => response.json())
            .then((data) => {
                checkbox.disabled = data.author !== data.user;
            });
    });

    $('#comments-section').on('click', '.comment-like-btn', function () {
        var commentId = $(this).data('id');
        var $comment = $(this).closest('.comment');

        $.ajax({
            type: 'POST', url: '/like/', data: {
                comment_id: commentId, csrfmiddlewaretoken: getCookie('csrftoken')
            }, success: function (response) {
                var likeCount = response.count;
                $comment.find('.comment-like-section .mx-1').text(likeCount);
            }, error: function (error) {
                console.log('Like error:', error);
            }
        });
    });

    $('#comments-section').on('change', '.comment-correct-checkbox', function () {
        var commentId = $(this).data('id');
        var $comment = $(this).closest('.comment');

        $.ajax({
            type: 'POST', url: '/toggle_correct/', data: {
                comment_id: commentId, csrfmiddlewaretoken: getCookie('csrftoken')
            }, success: function (response) {
                var isCorrect = response.is_correct;
                if (isCorrect) {
                    $comment.addClass('bold');
                } else {
                    $comment.removeClass('bold');
                }
            }, error: function (error) {
                console.log('Toggle correct error:', error);
            }
        });
    });

    $('#comment-form').submit(function (event) {
        event.preventDefault();

        var url = $(this).data('url');

        $.ajax({
            type: 'POST',
            url: url,
            data: $(this).serialize() + '&csrfmiddlewaretoken=' + getCookie('csrftoken'),
            success: function (response) {
                $('#comments-section').append(response.html);
                $('#comment-form')[0].reset();
            },
            error: function (error) {
                console.log(error);
            }
        });
    });
});
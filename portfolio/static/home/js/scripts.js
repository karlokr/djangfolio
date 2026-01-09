jQuery(function ($) {

    'use strict';

    // --------------------------------------------------------------------
    // PreLoader
    // --------------------------------------------------------------------

    (function () {
        $('#right-container').removeClass('loading');
        $('#profile-image').removeClass('loading');
        $('#content-loading').removeClass('loading');
        $('#preloader').delay(700).fadeOut(700);
        $('.resume-button').addClass('selected');
        ajaxGetRepos();
        assignModals();
        $(window).resize(function () {
            fixHeights();
        });
        $("#ecovid").on("loadstart", function () {
            fixHeights();
        });
        $(window).scroll(function () {
            fixHeights();
        });
    }());



    // --------------------------------------------------------------------
    // Sticky Sidebar
    // --------------------------------------------------------------------

    // Only initialize sticky sidebar on visible elements (resume is shown by default)
    $('.left-col-block, #resume').theiaStickySidebar();

    $(".projects-button").on("click", function (event) {
        $(".projects-button").focus();
        $(".projects-button").addClass("active")
        $('#preloader').css("background", "");
        $('#preloader').css("opacity", "1.0");
        $('#preloader').css("display", "block");
        $('#preloader').delay(500).fadeOut('slow');
        $('#resume').fadeOut('slow');
        $('#projects').delay(500).fadeIn('slow', function() {
            // Initialize sticky sidebar on portfolio now that it's visible
            $('#projects').theiaStickySidebar();
        });
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
        $('.resume-button').removeClass('selected');
        $('.projects-button').addClass('selected');
    });
    $(".resume-button").on("click", function (event) {
        $(".resume-button").focus();
        $('#preloader').css("background", "");
        $('#preloader').css("opacity", "1.0");
        $('#preloader').css("display", "block");
        $('#preloader').delay(500).fadeOut('slow');
        $('#projects').fadeOut('slow');
        $('#resume').delay(500).fadeIn('slow');
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
        $('.projects-button').removeClass('selected');
        $('.resume-button').addClass('selected');
    });

    function ajaxGetRepos() {

        let all_data;
        
        // Get GitHub username from site configuration
        const githubUsername = window.SITE_CONFIG?.githubUsername || 'yourusername';

        $.ajax({
            url: `https://api.github.com/users/${githubUsername}/repos`,
            dataType: "json",
            type: "GET",
            data: {
                sort: "pushed"
            },
            success: function (data) {
                console.log("SUCCESS JSON:", data);
                all_data = data;
                let html = "";
                for (let i = 0; i < 9; i++) {
                    html += "<div class=\"col-md-4\">";
                    html += "<div class=\"github-item\" name=\"" + data[i]['name'] + "\" >";
                    html += "<h3 style='margin-bottom: 5px'><svg height=\"20\" class=\"octicon octicon-repo mr-1 v-align-middle\" fill=\"#586069\" aria-label=\"repo\" viewBox=\"0 0 12 16\" version=\"1.1\" width=\"15\" role=\"img\"><path fill-rule=\"evenodd\" d=\"M4 9H3V8h1v1zm0-3H3v1h1V6zm0-2H3v1h1V4zm0-2H3v1h1V2zm8-1v12c0 .55-.45 1-1 1H6v2l-1.5-1.5L3 16v-2H1c-.55 0-1-.45-1-1V1c0-.55.45-1 1-1h10c.55 0 1 .45 1 1zm-1 10H1v2h2v-1h3v1h5v-2zm0-10H2v9h9V1z\"></path></svg>"
                    html += "<a href=\"" + data[i]['html_url'] + "\">";
                    if (data[i]['name'].length > 25) {
                        html += "  " + data[i]['name'].substring(0, 20) + "...</h3>";
                    } else {
                        html += "  " + data[i]['name'] + "</h3>";
                    }
                    html += "</a>";
                    if (data[i]['description'].length > 60) {
                        html += "<small>" + data[i]['description'].substring(0, 60) + " [...]</small>";
                    } else {
                        html += "<small>" + data[i]['description'] + "</small>";
                    }
                    html += "</div>";
                    html += "</div>";
                };
                $("#github-items").append(html);

                let seeMore = `<div class="see-all col-md-12"><h3><a target="_blank" href="https://github.com/${githubUsername}?tab=repositories">See more...</a></h3></div>`;

                $("#github-items").append(seeMore);
            },
            complete: function () {
                for (let i = 0; i < 9; i++) {
                    $.ajax({
                        url: all_data[i]['languages_url'],
                        dataType: "json",
                        type: "GET",
                        success: function (data) {
                            let color = "";
                            let html = "";

                            switch (Object.keys(data)[0]) {
                                case "HTML":
                                    color = "#e34c26";
                                    break;
                                case "JavaScript":
                                    color = "#f1e05a";
                                    break;
                                case "C":
                                    color = "#555555";
                                    break;
                                case "C#":
                                    color = "#178600";
                                    break;
                                case "Java":
                                    color = "#b07219";
                                    break;
                                case "MATLAB":
                                    color = "#e16737";
                                    break;
                                case "Python":
                                    color = "#3572A5";
                                    break;
                            }

                            html += "<div style='margin-bottom: 0px; margin-top: 10px;'>";
                            html += "<span class='repo-language-color' style='background-color: " + color + "'></span>";
                            html += "<small>  " + Object.keys(data)[0] + "</small>";
                            html += `<a target='_blank' style='float:right' href='https://github.com/${githubUsername}/${all_data[i]['name']}/network/members'>`;
                            html += '  <svg class="v-align-middle octicon octicon-git-branch mr-1" viewBox="0 0 10 16" version="1.1" width="10" height="16" aria-hidden="true"><path fill-rule="evenodd" d="M10 5c0-1.11-.89-2-2-2a1.993 1.993 0 0 0-1 3.72v.3c-.02.52-.23.98-.63 1.38-.4.4-.86.61-1.38.63-.83.02-1.48.16-2 .45V4.72a1.993 1.993 0 0 0-1-3.72C.88 1 0 1.89 0 3a2 2 0 0 0 1 1.72v6.56c-.59.35-1 .99-1 1.72 0 1.11.89 2 2 2 1.11 0 2-.89 2-2 0-.53-.2-1-.53-1.36.09-.06.48-.41.59-.47.25-.11.56-.17.94-.17 1.05-.05 1.95-.45 2.75-1.25S8.95 7.77 9 6.73h-.02C9.59 6.37 10 5.73 10 5zM2 1.8c.66 0 1.2.55 1.2 1.2 0 .65-.55 1.2-1.2 1.2C1.35 4.2.8 3.65.8 3c0-.65.55-1.2 1.2-1.2zm0 12.41c-.66 0-1.2-.55-1.2-1.2 0-.65.55-1.2 1.2-1.2.65 0 1.2.55 1.2 1.2 0 .65-.55 1.2-1.2 1.2zm6-8c-.66 0-1.2-.55-1.2-1.2 0-.65.55-1.2 1.2-1.2.65 0 1.2.55 1.2 1.2 0 .65-.55 1.2-1.2 1.2z"></path></svg>';
                            html += "<small>  " + all_data[i]['forks_count'] + "</small></a>";
                            html += `<a style='float: right; margin-right: 12px;' target='_blank' href='https://github.com/${githubUsername}/${all_data[i]['name']}/stargazers'>`;
                            html += "  <svg class=\"octicon octicon-star v-align-middle mr-1\" viewBox=\"0 0 14 16\" version=\"1.1\" width=\"14\" height=\"16\" aria-hidden=\"true\"><path fill-rule=\"evenodd\" d=\"M14 6l-4.9-.64L7 1 4.9 5.36 0 6l3.6 3.26L2.67 14 7 11.67 11.33 14l-.93-4.74L14 6z\"></path></svg>";
                            html += "<small>  " + all_data[i]['stargazers_count'] + "</small></a>";
                            html += "</div>";

                            $('div[name=' + all_data[i]['name'] + ']').append(html);
                        },
                        error: function (jqXHR, textStatus, errorThrown) {
                            console.log("ERROR:", jqXHR, textStatus, errorThrown);
                        }
                    });
                }
            },

            error: function (jqXHR, textStatus, errorThrown) {
                console.log("ERROR:", jqXHR, textStatus, errorThrown);
            }
        });
    };

    function fixHeights() {
        $("#ecoimg").height($("#ecovid").height());
        $("#ecoimg").css("display: none");
        $("#ecoimg").css("display: block");
    }

    $("#projects-mail-button").on("click", function () {
        var form = $("#contactFormProjects");
        var messageContainer = $("#contactFormProjectsMessage");
        
        // Clear previous error states
        form.find('.form-control').removeClass('error success');
        messageContainer.empty();
        
        // Validate required fields
        var isValid = true;
        var errorFields = [];
        
        form.find('.form-control[required]').each(function() {
            if (!$(this).val().trim()) {
                $(this).addClass('error');
                isValid = false;
                errorFields.push($(this).attr('name'));
            }
        });
        
        if (!isValid) {
            var errorMsg = $('<div class="form-message error show">Please fill in all required fields.</div>');
            messageContainer.html(errorMsg);
            return;
        }
        
        var fromData = form.serialize();
        
        $.ajax({
                type: "POST",
                url: "/send-email/",
                data: fromData,
                dataType: "json",
                success: function(response) {
                    if (response.status === 'success') {
                        // Show success message
                        var successMsg = $('<div class="form-message success show">' + 
                            response.message.replace(/<[^>]*>/g, '') + '</div>');
                        messageContainer.html(successMsg);
                        
                        // Mark fields as success
                        form.find('.form-control').addClass('success');
                        
                        // Clear form after delay
                        setTimeout(function() {
                            form.find("input, textarea").val('').removeClass('success');
                            successMsg.fadeOut(300, function() { $(this).remove(); });
                        }, 3000);
                    } else {
                        // Show error message
                        var errorMsg = $('<div class="form-message error show">' + 
                            response.message.replace(/<[^>]*>/g, '') + '</div>');
                        messageContainer.html(errorMsg);
                        
                        // Mark fields as error
                        form.find('.form-control').filter(function() {
                            return !$(this).val();
                        }).addClass('error');
                    }
                },
                error: function(xhr, status, error) {
                    var errorMsg = "Sorry, there was an error sending your message.";
                    if (xhr.responseJSON && xhr.responseJSON.message) {
                        errorMsg = xhr.responseJSON.message.replace(/<[^>]*>/g, '');
                    }
                    
                    // Show error message
                    var errorMsgDiv = $('<div class="form-message error show">' + errorMsg + '</div>');
                    messageContainer.html(errorMsgDiv);
                    
                    // Mark all required fields as error
                    form.find('.form-control[required]').addClass('error');
                }
        })
    });

    $("#resume-mail-button").on("click", function () {
        var form = $("#contactFormResume");
        var messageContainer = $("#contactFormResumeMessage");
        
        // Clear previous error states
        form.find('.form-control').removeClass('error success');
        messageContainer.empty();
        
        // Validate required fields
        var isValid = true;
        var errorFields = [];
        
        form.find('.form-control[required]').each(function() {
            if (!$(this).val().trim()) {
                $(this).addClass('error');
                isValid = false;
                errorFields.push($(this).attr('name'));
            }
        });
        
        if (!isValid) {
            var errorMsg = $('<div class="form-message error show">Please fill in all required fields.</div>');
            messageContainer.html(errorMsg);
            return;
        }
        
        var fromData = form.serialize();
        
        $.ajax({
                type: "POST",
                url: "/send-email/",
                data: fromData,
                dataType: "json",
                success: function(response) {
                    if (response.status === 'success') {
                        // Show success message
                        var successMsg = $('<div class="form-message success show">' + 
                            response.message.replace(/<[^>]*>/g, '') + '</div>');
                        messageContainer.html(successMsg);
                        
                        // Mark fields as success
                        form.find('.form-control').addClass('success');
                        
                        // Clear form after delay
                        setTimeout(function() {
                            form.find("input, textarea").val('').removeClass('success');
                            successMsg.fadeOut(300, function() { $(this).remove(); });
                        }, 3000);
                    } else {
                        // Show error message
                        var errorMsg = $('<div class="form-message error show">' + 
                            response.message.replace(/<[^>]*>/g, '') + '</div>');
                        messageContainer.html(errorMsg);
                        
                        // Mark fields as error
                        form.find('.form-control').filter(function() {
                            return !$(this).val();
                        }).addClass('error');
                    }
                },
                error: function(xhr, status, error) {
                    var errorMsg = "Sorry, there was an error sending your message.";
                    if (xhr.responseJSON && xhr.responseJSON.message) {
                        errorMsg = xhr.responseJSON.message.replace(/<[^>]*>/g, '');
                    }
                    
                    // Show error message
                    var errorMsgDiv = $('<div class="form-message error show">' + errorMsg + '</div>');
                    messageContainer.html(errorMsgDiv);
                    
                    // Mark all required fields as error
                    form.find('.form-control[required]').addClass('error');
                }
         })
    });

    // Clear error state when user starts typing
    $('body').on('input', '.form-control.error', function() {
        $(this).removeClass('error');
    });

    function assignModals() {
        // Get the modal
        let modal = document.getElementById("myModal");
        let pdfmodal = document.getElementById("pdfModal");

        // Get the image and insert it inside the modal - use its "alt" text as a caption
        $('.portfolio-img').each(function (i, obj) {
            let modalImg = document.getElementById("img01");
            let modalVid = document.getElementById("vid01");
            let modalPdf = document.getElementById("pdf01");
            let captionText = document.getElementById("caption");
            obj.onclick = function () {
                captionText.innerHTML = this.alt;
                if (this.alt=="Kraken App") {
                    modalImg.style.width = "20%";
                } else {
                    modalImg.style.width = "80%";
                }
                modal.style.display = "block";
                modalVid.style.display = "none";
                modalPdf.style.display = "none";
                modalImg.style.display = "block";
                modalImg.src = this.src;
                modalVid.style.display = "none"; 
            }
        });



        // Get the video and insert it inside the modal - use its name as a caption
        $('.portfolio-vid').each(function (i, obj) {
            let modalImg = document.getElementById("img01");
            let modalVid = document.getElementById("vid01");
            let modalPdf = document.getElementById("pdf01");
            let captionText = document.getElementById("caption");
            obj.onclick = function () {
                let videos = document.getElementsByClassName('portfolio-vid');
                for (let i = 0; i < videos.length; i++) {
                    videos[i].pause();
                }
                captionText.innerHTML = $(this).children(".alt").first().html();
                modal.style.display = "block";
                modalImg.style.display = "none";
                modalPdf.style.display = "none";
                modalVid.style.display = "block";
                modalVid.src = this.src;

            }
        });

        $('.portfolio-pdf').each(function (i, obj) {
            let modalImg = document.getElementById("img01");
            let modalVid = document.getElementById("vid01");
            let modalPdf = document.getElementById("pdf01");
            let captionText = document.getElementById("caption");
            obj.onclick = function () {
                let videos = document.getElementsByClassName('portfolio-vid');
                for (let i = 0; i < videos.length; i++) {
                    videos[i].pause();
                }
                captionText.innerHTML = this.alt;
                pdfmodal.style.display = "block";
                modalImg.style.display = "none";
                modalVid.style.display = "none";
                modalPdf.style.display = "block";
                modalPdf.src = this.src + ".pdf";
            }
        });



        // When the user clicks on <span> (x), close the modal
        document.getElementsByClassName("close")[0].onclick = function () {
            modal.style.display = "none";
            pdfmodal.style.display = "none";
            let videos = document.getElementsByClassName('portfolio-vid');
            for (let i = 0; i < videos.length; i++) {
                videos[i].play();
            }
        }

        // When the user clicks on the background, close the modal
        document.getElementById("myModal").onclick = function () {
            modal.style.display = "none";
            let videos = document.getElementsByClassName('portfolio-vid');
            for (let i = 0; i < videos.length; i++) {
                videos[i].play();
            }
        }

        // When the user clicks on the background, close the modal
        document.getElementById("pdfModal").onclick = function () {
            pdfmodal.style.display = "none";
            let videos = document.getElementsByClassName('portfolio-vid');
            for (let i = 0; i < videos.length; i++) {
                videos[i].play();
            }
        }

        // Do nothing when the user clicks on the video
        document.getElementById("vid01").onclick = function (e) {
            e.stopPropagation();
        };

        // Do nothing when the user clicks on the image
        document.getElementById("img01").onclick = function (e) {
            e.stopPropagation();
        };

        function playVideo(video) {
            var playPromise = video.play();

            if (playPromise !== undefined) {
                playPromise.then(_ => {
                        // Automatic playback started!
                        // Show playing UI.
                    })
                    .catch(error => {
                        // Auto-play was prevented
                        // Show paused UI.
                    });
            }
        }

        $(window).on("scroll", function () {
            $('video').each(function () {
                if ($(this).is(":in-viewport")) {
                    playVideo($(this)[0]);
                } else {
                    $(this)[0].pause();
                }
            });
        });

        var resizeTimeout, sortedReverse = false;
        $(window).resize(function () {
            // window.resize fires too rapidly for our liking
            // use clear-set timeout approach
            if (resizeTimeout) {
                window.clearTimeout(resizeTimeout);
            }
            resizeTimeout = window.setTimeout(function () {
                var windowWidth = $(window).width();
                // sortedReverse flag is used to ensure that
                // we do not reverse the list unnecessarily
                if ((windowWidth < 992 && !sortedReverse) || (windowWidth >= 992 && sortedReverse)) {
                    $(".reverse").append(function () {
                        return $(this).children().detach().toArray().reverse();
                    });
                    sortedReverse = !sortedReverse;
                    $(".reverse div").css("text-align", "left");
                } else {
                    $(".reverse div").css("text-align", "right");
                }
            }, 100);
        }).trigger("resize");
    }


}); // JQuery end

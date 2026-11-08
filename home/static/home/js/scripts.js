jQuery(function ($) {

    'use strict';

    // Safe text sanitization function using DOMPurify
    function sanitizeText(text) {
        // Use DOMPurify to remove all HTML tags and return only text
        return DOMPurify.sanitize(text, { ALLOWED_TAGS: [], KEEP_CONTENT: true });
    }

    // --------------------------------------------------------------------
    // PreLoader
    // --------------------------------------------------------------------

    (function () {
        $('#right-container').removeClass('loading');
        $('#profile-image').removeClass('loading');
        $('#content-loading').removeClass('loading');
        $('#preloader').delay(700).fadeOut(700);
        $('.resume-button').addClass('selected');
        // Only fetch GitHub repos on the home page
        if ($('#github-items').length) {
            ajaxGetRepos();
        }
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
    // Layout
    // --------------------------------------------------------------------

    // On desktop the home page sits in a fixed frame (see #right-container in
    // style.css, which uses the same media query): the page scrolls as usual,
    // the left column is sticky, and only the right column moves. On narrow
    // screens the columns stack (see .columns-block).
    var fixedFrame = window.matchMedia('(min-width: 992px) and (min-height: 600px)');
    var stackedLayout = window.matchMedia('(max-width: 768px)');

    // Side by side, the Resume/Portfolio switch scrolls to the top, where the
    // new view starts. Stacked the buttons sit just above the view, so the
    // visitor stays where they are. The page's height is held while one view
    // fades out and the other in: with neither shown the page is much
    // shorter, and the browser would clamp the scroll position up to it.
    var viewSwitchTimer = null;

    function beginViewSwitch() {
        if (!stackedLayout.matches) {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
            return;
        }
        var $container = $('#right-container');
        clearTimeout(viewSwitchTimer);
        $container.css('min-height', $container.outerHeight());
        // Both fades take 200ms; release a little after the new view is in.
        viewSwitchTimer = setTimeout(function () {
            $container.css('min-height', '');
        }, 500);
    }

    // Show the Portfolio view with the usual fade.
    function showPortfolio() {
        $(".projects-button").focus();
        $(".projects-button").addClass("active")
        beginViewSwitch();
        // Fade the Resume out, then the Portfolio in, so the two are never
        // on the page at once (no loading overlay hides the switch anymore).
        // The videos now on screen start by themselves (see the video
        // observer in assignModals).
        $('#resume').stop(true, true).fadeOut(200, function () {
            $('#projects').stop(true, true).fadeIn(200);
        });
        $('.resume-button').removeClass('selected');
        $('.projects-button').addClass('selected');
    }

    $(".projects-button").on("click", function (event) {
        event.preventDefault();
        showPortfolio();
    });

    // A link like /#coaching-platform (the Back link on a project page when
    // the Projects page is hidden) opens the Portfolio at that project.
    (function () {
        if (!window.location.hash) {
            return;
        }
        let $target = $();
        try {
            $target = $('#projects').find(window.location.hash);
        } catch (e) {
            // Hash is not a valid selector.
        }
        if (!$target.length) {
            // Not a project: undo the early Portfolio styling from
            // home/index.html and let the page load as normal.
            document.documentElement.classList.remove('portfolio-jump');
            return;
        }
        // Run after every page-load ready handler (including the one in
        // base_layout.html that starts the preloader) so it can be undone.
        setTimeout(function () {
            showPortfolioInstantly($target.first());
        }, 0);
    }());

    // Open the Portfolio at a project with no preloader, fades or smooth
    // scrolling, for visitors coming back from that project's page.
    function showPortfolioInstantly($target) {
        $('#preloader').stop(true, true).hide();
        $('#right-container, #profile-image, #content-loading').removeClass('loading');
        $('#resume').stop(true, true).hide();
        $('#projects').stop(true, true).show();
        // The views now carry their own inline display, so drop the early
        // !important styling; otherwise the Resume/Portfolio buttons can't
        // switch views later.
        document.documentElement.classList.remove('portfolio-jump');
        $('.resume-button').removeClass('selected');
        $('.projects-button').addClass('selected');

        // Leave room for the fixed top navbar; in the fixed frame, put the
        // project 16px inside the frame's top line (at 76px).
        function pin() {
            window.scrollTo(0, $target.offset().top - (fixedFrame.matches ? 93 : 80));
        }
        pin();

        // Content above the project (images, the GitHub repo list) is still
        // loading and pushes it down. Keep it pinned until the visitor
        // scrolls or a few seconds have passed: re-pin when the page resizes,
        // when all images have loaded, and when the GitHub request finishes.
        let pinned = true;
        const observer = window.ResizeObserver ? new ResizeObserver(pin) : null;
        if (observer) {
            observer.observe(document.body);
        }
        function repin() {
            if (pinned) {
                pin();
            }
        }
        $(window).on('load', repin);
        $(document).on('ajaxStop', repin);
        const events = 'wheel touchstart keydown mousedown';
        function release() {
            pinned = false;
            if (observer) {
                observer.disconnect();
            }
            $(window).off('load', repin).off(events, release);
            $(document).off('ajaxStop', repin);
        }
        $(window).on(events, release);
        setTimeout(release, 8000);
    }
    $(".resume-button").on("click", function (event) {
        event.preventDefault();
        $(".resume-button").focus();
        beginViewSwitch();
        // Fade the Portfolio out, then the Resume in (see showPortfolio).
        $('#projects').stop(true, true).fadeOut(200, function () {
            $('#resume').stop(true, true).fadeIn(200);
        });
        $('.projects-button').removeClass('selected');
        $('.resume-button').addClass('selected');
    });

    // GitHub language colours for the repo cards.
    const languageColors = {
                        "HTML": "#e34c26",
                        "CSS": "#563d7c",
                        "JavaScript": "#f1e05a",
                        "TypeScript": "#3178c6",
                        "Python": "#3572A5",
                        "Java": "#b07219",
                        "C": "#555555",
                        "C++": "#f34b7d",
                        "C#": "#178600",
                        "Go": "#00ADD8",
                        "Rust": "#dea584",
                        "Ruby": "#701516",
                        "PHP": "#4F5D95",
                        "Swift": "#F05138",
                        "Kotlin": "#A97BFF",
                        "Dart": "#00B4AB",
                        "Scala": "#c22d40",
                        "R": "#198CE7",
                        "MATLAB": "#e16737",
                        "Shell": "#89e051",
                        "Bash": "#89e051",
                        "PowerShell": "#012456",
                        "Perl": "#0298c3",
                        "Lua": "#000080",
                        "Haskell": "#5e5086",
                        "Elixir": "#6e4a7e",
                        "Clojure": "#db5855",
                        "F#": "#b845fc",
                        "Objective-C": "#438eff",
                        "Vue": "#41b883",
                        "Svelte": "#ff3e00",
                        "SCSS": "#c6538c",
                        "Sass": "#a53b70",
                        "Less": "#1d365d",
                        "CoffeeScript": "#244776",
                        "Jupyter Notebook": "#DA5B0B",
                        "Dockerfile": "#384d54",
                        "Makefile": "#427819",
                        "CMake": "#DA3434",
                        "Groovy": "#4298b8",
                        "Assembly": "#6E4C13",
                        "Vim Script": "#199f4b",
                        "Emacs Lisp": "#c065db",
                        "TeX": "#3D6117",
                        "Julia": "#a270ba"
                    };

    function escapeHtml(text) {
        return $('<div>').text(text == null ? '' : String(text)).html();
    }

    // Repo list for the Portfolio's "GitHub Repos" section. It comes from this
    // site's /github-repos/ endpoint, which caches GitHub's answer server-side
    // (see home/github.py), so visitors never hit GitHub's rate limit.
    function ajaxGetRepos() {
        $.ajax({
            url: '/github-repos/',
            dataType: 'json',
            type: 'GET',
            success: function (data) {
                const username = data.username || '';
                const userPath = encodeURIComponent(username);
                let html = '';
                (data.repos || []).forEach(function (repo) {
                    const name = repo.name || '';
                    const shownName = name.length > 25 ? name.substring(0, 20) + '...' : name;
                    let description = repo.description || 'No description';
                    if (description.length > 60) {
                        description = description.substring(0, 60) + ' [...]';
                    }
                    const language = repo.language || 'Unknown';
                    const color = languageColors[repo.language] || '#586069';
                    const repoPath = userPath + '/' + encodeURIComponent(name);

                    html += '<div class="col-md-4"><div class="github-item">';
                    html += "<h3 style='margin-bottom: 5px'><svg height=\"20\" class=\"octicon octicon-repo mr-1 v-align-middle\" fill=\"#586069\" aria-label=\"repo\" viewBox=\"0 0 12 16\" version=\"1.1\" width=\"15\" role=\"img\"><path fill-rule=\"evenodd\" d=\"M4 9H3V8h1v1zm0-3H3v1h1V6zm0-2H3v1h1V4zm0-2H3v1h1V2zm8-1v12c0 .55-.45 1-1 1H6v2l-1.5-1.5L3 16v-2H1c-.55 0-1-.45-1-1V1c0-.55.45-1 1-1h10c.55 0 1 .45 1 1zm-1 10H1v2h2v-1h3v1h5v-2zm0-10H2v9h9V1z\"></path></svg>";
                    html += '<a href="' + escapeHtml(repo.html_url) + '">  ' + escapeHtml(shownName) + '</a></h3>';
                    html += '<small>' + escapeHtml(description) + '</small>';
                    html += "<div style='margin-bottom: 0px; margin-top: 10px;'>";
                    html += "<span class='repo-language-color' style='background-color: " + color + "'></span>";
                    html += '<small>   ' + escapeHtml(language) + '</small>';
                    html += "<a target='_blank' style='float:right' href='https://github.com/" + repoPath + "/network/members'>";
                    html += '  <svg class="v-align-middle octicon octicon-git-branch mr-1" viewBox="0 0 10 16" version="1.1" width="10" height="16" aria-hidden="true"><path fill-rule="evenodd" d="M10 5c0-1.11-.89-2-2-2a1.993 1.993 0 0 0-1 3.72v.3c-.02.52-.23.98-.63 1.38-.4.4-.86.61-1.38.63-.83.02-1.48.16-2 .45V4.72a1.993 1.993 0 0 0-1-3.72C.88 1 0 1.89 0 3a2 2 0 0 0 1 1.72v6.56c-.59.35-1 .99-1 1.72 0 1.11.89 2 2 2 1.11 0 2-.89 2-2 0-.53-.2-1-.53-1.36.09-.06.48-.41.59-.47.25-.11.56-.17.94-.17 1.05-.05 1.95-.45 2.75-1.25S8.95 7.77 9 6.73h-.02C9.59 6.37 10 5.73 10 5zM2 1.8c.66 0 1.2.55 1.2 1.2 0 .65-.55 1.2-1.2 1.2C1.35 4.2.8 3.65.8 3c0-.65.55-1.2 1.2-1.2zm0 12.41c-.66 0-1.2-.55-1.2-1.2 0-.65.55-1.2 1.2-1.2.65 0 1.2.55 1.2 1.2 0 .65-.55 1.2-1.2 1.2zm6-8c-.66 0-1.2-.55-1.2-1.2 0-.65.55-1.2 1.2-1.2.65 0 1.2.55 1.2 1.2 0 .65-.55 1.2-1.2 1.2z"></path></svg>';
                    html += '<small>  ' + Number(repo.forks_count || 0) + '</small></a>';
                    html += "<a style='float: right; margin-right: 12px;' target='_blank' href='https://github.com/" + repoPath + "/stargazers'>";
                    html += '  <svg class="octicon octicon-star v-align-middle mr-1" viewBox="0 0 14 16" version="1.1" width="14" height="16" aria-hidden="true"><path fill-rule="evenodd" d="M14 6l-4.9-.64L7 1 4.9 5.36 0 6l3.6 3.26L2.67 14 7 11.67 11.33 14l-.93-4.74L14 6z"></path></svg>';
                    html += '<small>  ' + Number(repo.stargazers_count || 0) + '</small></a>';
                    html += '</div></div></div>';
                });
                if (html) {
                    html += '<div class="see-all col-md-12"><h3><a target="_blank" href="https://github.com/' +
                        userPath + '?tab=repositories">See more...</a></h3></div>';
                }
                // Replace, not append: going Back restores a snapshot that
                // already holds the list, and this script runs again.
                $('#github-items').html(html);
            },
            error: function () {
                // No cached repo list yet and GitHub unavailable: leave the
                // section empty rather than showing an error.
            }
        });
    }

    function fixHeights() {
        $("#ecoimg").height($("#ecovid").height());
        $("#ecoimg").css("display: none");
        $("#ecoimg").css("display: block");
    }

    // --------------------------------------------------------------------
    // Cloudflare Turnstile (contact forms, only when a site key is set;
    // checked server-side in home/turnstile.py)
    // --------------------------------------------------------------------
    // Rendered explicitly: this script runs again on every htmx visit to the
    // home page, where Turnstile's automatic render never runs. Live widgets
    // are tracked by element, because going Back restores a snapshot of the
    // page whose widget markup is dead and has to be rendered afresh.
    window.turnstileWidgets = window.turnstileWidgets || new WeakMap();

    function turnstileTheme() {
        // The site's own toggle sets data-theme; otherwise follow the system.
        return document.documentElement.getAttribute('data-theme') || 'auto';
    }

    function renderTurnstile() {
        $('.turnstile-slot').each(function () {
            if (window.turnstileWidgets.has(this)) {
                return;
            }
            $(this).empty();
            window.turnstileWidgets.set(this, window.turnstile.render(this, {
                sitekey: this.dataset.sitekey,
                action: 'contact',
                theme: turnstileTheme(),
                // Fills its slot: 300px beside Submit, the column's width on
                // phones (see .form-actions in style.css).
                size: 'flexible'
            }));
        });
    }

    function loadTurnstile() {
        if (!$('.turnstile-slot').length) {
            return;
        }
        if (window.turnstile) {
            renderTurnstile();
            return;
        }
        window.onTurnstileLoad = renderTurnstile;
        if (!document.getElementById('turnstile-api')) {
            var script = document.createElement('script');
            script.id = 'turnstile-api';
            script.src = 'https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit&onload=onTurnstileLoad';
            script.async = true;
            document.head.appendChild(script);
        }
    }

    // Toggling the site theme re-renders the widgets to match.
    if (!window.turnstileThemeListener) {
        window.turnstileThemeListener = true;
        document.addEventListener('themechange', function () {
            if (!window.turnstile) {
                return;
            }
            $('.turnstile-slot').each(function () {
                if (window.turnstileWidgets.has(this)) {
                    window.turnstile.remove(window.turnstileWidgets.get(this));
                    window.turnstileWidgets.delete(this);
                }
            });
            renderTurnstile();
        });
    }

    // The form's widget id, or null when Turnstile is off for this form.
    function turnstileWidget(form) {
        var slot = form.find('.turnstile-slot').get(0);
        return slot ? (window.turnstileWidgets.get(slot) || '') : null;
    }

    // Tokens are single-use: after each submission the widget gets a new one.
    function resetTurnstile(form) {
        var widget = turnstileWidget(form);
        if (widget && window.turnstile) {
            window.turnstile.reset(widget);
        }
    }

    loadTurnstile();

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
        
        var widget = turnstileWidget(form);
        if (widget !== null && !(widget && window.turnstile && window.turnstile.getResponse(widget))) {
            var waitMsg = $('<div class="form-message error show">Please wait for the verification below the message box to finish, then send again.</div>');
            messageContainer.html(waitMsg);
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
                            sanitizeText(response.message) + '</div>');
                        messageContainer.html(successMsg);
                        
                        // Mark fields as success
                        form.find('.form-control').addClass('success');
                        
                        // Clear form after delay
                        setTimeout(function() {
                            // Only the visible fields: the hidden CSRF, honeypot and
                            // Turnstile inputs must survive for the next message.
                            form.find('.form-control').val('').removeClass('success');
                            successMsg.fadeOut(300, function() { $(this).remove(); });
                        }, 3000);
                    } else {
                        // Show error message
                        var errorMsg = $('<div class="form-message error show">' + 
                            sanitizeText(response.message) + '</div>');
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
                        errorMsg = sanitizeText(xhr.responseJSON.message);
                    }
                    
                    // Show error message
                    var errorMsgDiv = $('<div class="form-message error show">' + errorMsg + '</div>');
                    messageContainer.html(errorMsgDiv);
                    
                    // Mark all required fields as error
                    form.find('.form-control[required]').addClass('error');
                },
                complete: function() {
                    resetTurnstile(form);
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
        
        var widget = turnstileWidget(form);
        if (widget !== null && !(widget && window.turnstile && window.turnstile.getResponse(widget))) {
            var waitMsg = $('<div class="form-message error show">Please wait for the verification below the message box to finish, then send again.</div>');
            messageContainer.html(waitMsg);
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
                            sanitizeText(response.message) + '</div>');
                        messageContainer.html(successMsg);
                        
                        // Mark fields as success
                        form.find('.form-control').addClass('success');
                        
                        // Clear form after delay
                        setTimeout(function() {
                            // Only the visible fields: the hidden CSRF, honeypot and
                            // Turnstile inputs must survive for the next message.
                            form.find('.form-control').val('').removeClass('success');
                            successMsg.fadeOut(300, function() { $(this).remove(); });
                        }, 3000);
                    } else {
                        // Show error message
                        var errorMsg = $('<div class="form-message error show">' + 
                            sanitizeText(response.message) + '</div>');
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
                        errorMsg = sanitizeText(xhr.responseJSON.message);
                    }
                    
                    // Show error message
                    var errorMsgDiv = $('<div class="form-message error show">' + errorMsg + '</div>');
                    messageContainer.html(errorMsgDiv);
                    
                    // Mark all required fields as error
                    form.find('.form-control[required]').addClass('error');
                },
                complete: function() {
                    resetTurnstile(form);
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
                document.body.dataset.scrollY = window.scrollY;
                document.body.style.top = '-' + window.scrollY + 'px';
                document.body.classList.add('modal-open');
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
                document.body.dataset.scrollY = window.scrollY;
                document.body.style.top = '-' + window.scrollY + 'px';
                document.body.classList.add('modal-open');
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
                document.body.dataset.scrollY = window.scrollY;
                document.body.style.top = '-' + window.scrollY + 'px';
                document.body.classList.add('modal-open');
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
            var scrollY = document.body.dataset.scrollY || '0';
            document.body.classList.remove('modal-open');
            document.body.style.top = '';
            window.scrollTo(0, parseInt(scrollY));
            videosOnScreen.forEach(playVideo);
        }

        // When the user clicks on the background, close the modal
        document.getElementById("myModal").onclick = function () {
            modal.style.display = "none";
            var scrollY = document.body.dataset.scrollY || '0';
            document.body.classList.remove('modal-open');
            document.body.style.top = '';
            window.scrollTo(0, parseInt(scrollY));
            videosOnScreen.forEach(playVideo);
        }

        // When the user clicks on the background, close the modal
        document.getElementById("pdfModal").onclick = function () {
            pdfmodal.style.display = "none";
            var scrollY = document.body.dataset.scrollY || '0';
            document.body.classList.remove('modal-open');
            document.body.style.top = '';
            window.scrollTo(0, parseInt(scrollY));
            videosOnScreen.forEach(playVideo);
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

        // Play the Portfolio's videos while they're on screen and pause the
        // rest. Videos use preload="none", so they only download once played;
        // hidden ones (the Portfolio while it's closed) are never on screen,
        // so they don't load until it's opened.
        var videosOnScreen = new Set();
        if (window.IntersectionObserver) {
            var videoObserver = new IntersectionObserver(function (entries) {
                entries.forEach(function (entry) {
                    if (entry.isIntersecting) {
                        videosOnScreen.add(entry.target);
                        playVideo(entry.target);
                    } else {
                        videosOnScreen.delete(entry.target);
                        entry.target.pause();
                    }
                });
            });
            $('.portfolio-vid').each(function () {
                videoObserver.observe(this);
            });
        }

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

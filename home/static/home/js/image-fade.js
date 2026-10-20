/*
 * Fade images in instead of letting them pop in after an htmx page swap.
 *
 * htmx:afterSwap runs right after new content is inserted and before the
 * browser paints it. Any image in that content that hasn't finished loading
 * is hidden (its space is already reserved by its width/height attributes)
 * and fades in once it has loaded. Images that are already loaded are left
 * alone, so cached images still appear instantly.
 *
 * Full page loads don't need this: the preloader overlay covers the page
 * while images load. Without JavaScript, images simply show as normal.
 */
(function () {
    'use strict';

    // Never leave an image hidden for longer than this, whatever happens.
    var FAIL_SAFE_MS = 3000;

    function reveal(img) {
        // Turn the transition on only now, so hiding was instant and only the
        // reveal animates.
        img.classList.add('img-fade');
        img.classList.remove('img-pending');
    }

    function fadeInWhenLoaded(img) {
        if (img.complete && img.naturalWidth > 0) {
            return; // Already loaded: show immediately.
        }
        img.classList.add('img-pending');
        img.addEventListener('load', function () { reveal(img); }, { once: true });
        img.addEventListener('error', function () { reveal(img); }, { once: true });
        setTimeout(function () { reveal(img); }, FAIL_SAFE_MS);
    }

    document.addEventListener('htmx:afterSwap', function (event) {
        var target = event.detail && event.detail.target;
        if (!target || !target.querySelectorAll) {
            return;
        }
        target.querySelectorAll('img[src]').forEach(fadeInWhenLoaded);
    });
}());

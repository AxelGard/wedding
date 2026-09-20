/* Juandré & Axel — 4 September 2027
   Small, dependency-free enhancements. The page works fine without any of it. */

(function () {
    "use strict";

    /* ------------------------------------------------------- the big date --
       Change this one line if the time or date moves.
       Month is 0-indexed: 8 = September. Local time.                        */
    var WEDDING = new Date(2027, 8, 4, 15, 0, 0);

    /* --------------------------------------------------------- countdown -- */
    var board = document.getElementById("countdown");
    if (board) {
        var slots = {};
        ["days", "hours", "minutes", "seconds"].forEach(function (unit) {
            slots[unit] = board.querySelector('[data-unit="' + unit + '"]');
        });

        var tick = function () {
            var left = WEDDING - new Date();

            if (left <= 0) {
                board.innerHTML = '<li class="countdown__done"><b>Today</b>' +
                                  "<small>At last</small></li>";
                clearInterval(timer);
                return;
            }

            var s = Math.floor(left / 1000);
            var pad = function (n) { return n < 10 ? "0" + n : String(n); };

            slots.days.textContent    = Math.floor(s / 86400);
            slots.hours.textContent   = pad(Math.floor(s / 3600) % 24);
            slots.minutes.textContent = pad(Math.floor(s / 60) % 60);
            slots.seconds.textContent = pad(s % 60);
        };

        tick();
        var timer = setInterval(tick, 1000);
    }

    /* -------------------------------------------------------- mobile nav -- */
    var nav = document.getElementById("nav");
    var toggle = document.getElementById("navToggle");
    var links = document.getElementById("navLinks");

    if (toggle && links) {
        var setOpen = function (open) {
            toggle.setAttribute("aria-expanded", String(open));
            links.classList.toggle("is-open", open);
        };

        toggle.addEventListener("click", function () {
            setOpen(toggle.getAttribute("aria-expanded") !== "true");
        });

        links.addEventListener("click", function (e) {
            if (e.target.closest("a")) { setOpen(false); }
        });

        document.addEventListener("keydown", function (e) {
            if (e.key === "Escape") { setOpen(false); }
        });
    }

    /* Hairline under the bar once the page has moved */
    if (nav) {
        var shadow = function () {
            nav.classList.toggle("is-stuck", window.scrollY > 12);
        };
        shadow();
        window.addEventListener("scroll", shadow, { passive: true });
    }

    /* ----------------------------------------------- highlight the section -- */
    var sections = Array.prototype.slice.call(
        document.querySelectorAll("section[id], header[id]")
    );
    var navAnchors = links
        ? Array.prototype.slice.call(links.querySelectorAll('a[href^="#"]'))
        : [];

    if ("IntersectionObserver" in window && navAnchors.length) {
        var spy = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (!entry.isIntersecting) { return; }
                navAnchors.forEach(function (a) {
                    var on = a.getAttribute("href") === "#" + entry.target.id;
                    if (on) { a.setAttribute("aria-current", "true"); }
                    else { a.removeAttribute("aria-current"); }
                });
            });
        }, { rootMargin: "-45% 0px -50% 0px" });

        sections.forEach(function (el) { spy.observe(el); });
    }

    /* ------------------------------------------------------- fade-in bits -- */
    var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    var reveals = document.querySelectorAll(".reveal");

    if (reduced || !("IntersectionObserver" in window)) {
        Array.prototype.forEach.call(reveals, function (el) {
            el.classList.add("is-visible");
        });
    } else {
        var shower = new IntersectionObserver(function (entries, obs) {
            entries.forEach(function (entry, i) {
                if (!entry.isIntersecting) { return; }
                entry.target.style.transitionDelay = (i * 90) + "ms";
                entry.target.classList.add("is-visible");
                obs.unobserve(entry.target);
            });
        }, { rootMargin: "0px 0px -12% 0px", threshold: 0.12 });

        Array.prototype.forEach.call(reveals, function (el) { shower.observe(el); });
    }

    /* ----------------------------------------------------- add to calendar --
       Builds the .ics in the browser, so there's no extra file to keep in sync. */
    var cal = document.getElementById("addToCalendar");
    if (cal) {
        var stamp = function (d) {
            return d.getUTCFullYear() +
                   String(d.getUTCMonth() + 1).padStart(2, "0") +
                   String(d.getUTCDate()).padStart(2, "0") + "T" +
                   String(d.getUTCHours()).padStart(2, "0") +
                   String(d.getUTCMinutes()).padStart(2, "0") + "00Z";
        };

        var end = new Date(WEDDING.getTime() + 10 * 3600 * 1000);

        var ics = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Juandre and Axel//Wedding//EN",
            "BEGIN:VEVENT",
            "UID:wedding-2027-09-04@juandre-and-axel",
            "DTSTAMP:" + stamp(new Date()),
            "DTSTART:" + stamp(WEDDING),
            "DTEND:" + stamp(end),
            "SUMMARY:Juandré & Axel are getting married",
            "DESCRIPTION:Ceremony at 15:00\\, then dinner and dancing. Details at " +
                window.location.href,
            "LOCATION:Kanalmagasinet\\, Mem Kanalmagasinet 1\\, 614 92 Söderköping",
            "END:VEVENT",
            "END:VCALENDAR"
        ].join("\r\n");

        cal.setAttribute(
            "href",
            "data:text/calendar;charset=utf-8," + encodeURIComponent(ics)
        );
    }
})();

from pathlib import Path
import re

base_path = Path(r"products\templates\base.html")
html = base_path.read_text(encoding="utf-8-sig")

contact_bar = """
<div class="business-contact-bar">
    <div class="business-contact-inner">
        <a class="business-contact-item"
           href="tel:+14137316700"
           aria-label="Call The Label Group LLC at plus one 413 731 6700">
            <span class="business-contact-icon" aria-hidden="true">&#9742;</span>
            <span>+1 413-731-6700</span>
        </a>

        <a class="business-contact-item"
           href="mailto:labelgroup@comcast.net"
           aria-label="Email The Label Group LLC">
            <span class="business-contact-icon" aria-hidden="true">&#9993;</span>
            <span>labelgroup@comcast.net</span>
        </a>

        <span class="business-contact-item business-contact-address">
            <span class="business-contact-icon" aria-hidden="true">&#9906;</span>
            <span>580 St. James Avenue, Springfield, MA 01109, USA</span>
        </span>
    </div>
</div>
"""

css = r"""
/* The Label Group LLC: official U.S. business contact bar */
.business-contact-bar {
    width: 100%;
    background: #06152a;
    color: #ffffff;
    border-bottom: 1px solid rgba(255, 255, 255, 0.12);
    position: relative;
    z-index: 1001;
}

.business-contact-inner {
    width: min(1400px, 94%);
    margin: 0 auto;
    min-height: 42px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 8px 24px;
    padding: 9px 0;
    box-sizing: border-box;
}

.business-contact-item {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    color: #ffffff;
    font-size: 13px;
    line-height: 1.5;
    text-decoration: none;
    overflow-wrap: anywhere;
}

a.business-contact-item:hover,
a.business-contact-item:focus-visible {
    color: #f47b20;
    text-decoration: underline;
}

.business-contact-icon {
    color: #f47b20;
    font-size: 16px;
    flex: 0 0 auto;
}

.business-contact-address {
    margin-left: auto;
}

@media (max-width: 760px) {
    .business-contact-inner {
        justify-content: flex-start;
        gap: 7px 16px;
    }

    .business-contact-address {
        margin-left: 0;
        flex-basis: 100%;
    }
}

@media (max-width: 420px) {
    .business-contact-inner {
        width: 92%;
    }

    .business-contact-item {
        font-size: 12px;
    }
}
"""

# Add the contact bar once, replacing the existing promotional top line.
if 'class="business-contact-bar"' not in html:
    topline_pattern = re.compile(
        r"Free\s+quote\s+consultation\s*"
        r"(?:•|·|&bull;|&#8226;|&#x2022;)\s*"
        r"Durable\s+custom\s+printing\s*"
        r"(?:•|·|&bull;|&#8226;|&#x2022;)\s*"
        r"Built\s+for\s+business",
        re.IGNORECASE,
    )

    html, count = topline_pattern.subn(
        lambda match: contact_bar,
        html,
        count=1,
    )

    if count != 1:
        raise RuntimeError(
            "Could not find the existing promotional top line. "
            "No template changes were saved. Inspect base.html first."
        )

# Add the styling only once.
if "The Label Group LLC: official U.S. business contact bar" not in html:
    style_end = re.search(r"</style\s*>", html, re.IGNORECASE)

    if not style_end:
        raise RuntimeError(
            "Could not find a closing </style> tag in base.html. "
            "No template changes were saved."
        )

    html = (
        html[:style_end.start()]
        + "\n"
        + css
        + "\n"
        + html[style_end.start():]
    )

base_path.write_text(html, encoding="utf-8")
print("U.S. business contact bar added to the shared header.")

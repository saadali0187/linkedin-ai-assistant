"""Pool of pre-written LinkedIn posts for a frontend developer (JS/HTML/CSS).

Written in a senior-engineer voice: a crisp opinion or insight, no filler,
no "look how experienced I am" framing -- the authority comes from the take
itself. Posts rotate in order (see post_to_linkedin.py); add more any time,
the index just keeps advancing and wraps around when it runs out.

Each published post gets FOLLOW_CTA appended to the LinkedIn caption only --
the image card (generate_image.py) stays clean and renders just the insight
plus a small "Follow Saad Ali" signature line, not the full caption text.
"""

POSTS = [
    "CSS specificity fights are rarely a specificity problem -- they're a sign the selector architecture needs rethinking. Reach for a clearer structure before reaching for !important.",
    "The highest-leverage debugging skill isn't knowing every DevTools shortcut -- it's reading the error message fully before touching a single line of code. Most bugs tell you exactly where to look.",
    "Flexbox vs Grid stops being a debate once you split the job correctly: Grid owns the page-level layout, Flexbox owns the components inside it. Using one to force the other's job is where the pain comes from.",
    "Small, working commits beat one giant 'finished feature' commit every time. A clean history isn't bureaucracy -- it's the fastest way to find a regression six months from now.",
    "Semantic HTML is a force multiplier, not a nice-to-have. Structure the markup with <button>, <nav>, and <main> instead of div-soup and you get styling, accessibility, and readability for free.",
    ".map, .filter, and .reduce read cleaner than loops once the pattern clicks -- but readability wins over cleverness. If a plain for-loop communicates intent faster, use the for-loop.",
    "Before touching the code, write one sentence: what I expected vs what actually happened. Half the bugs I've fixed revealed themselves the moment I wrote that sentence down.",
    "CSS custom properties are one of the highest-ROI upgrades to plain CSS: one place to manage theme, spacing, and color instead of magic numbers scattered across a dozen files.",
    "Tutorials teach syntax. Projects teach engineering. Nothing builds real frontend judgment like being stuck on a bug you created yourself at 11pm with no tutorial to follow.",
    "Accessibility baked in from the first commit costs almost nothing. Accessibility retrofitted after launch costs a rewrite. Alt text, labels, and keyboard navigation are cheapest on day one.",
    "If a function needs a comment to explain what it does, it usually needs a better name instead. Comments should explain why a decision was made -- never what the code is already saying.",
    "Design mobile-first, not as a constraint but as a forcing function -- it makes you prioritize content ruthlessly. Scaling up to desktop is almost always easier than compressing a desktop layout down.",
    "Frameworks come and go. The engineers who stay valuable are the ones comfortable enough in plain HTML/CSS/JS to debug what the framework is actually doing underneath it.",
    "Branch names and commit messages are documentation. 'fix stuff' tells the next engineer -- often future you -- absolutely nothing about what broke or why.",
    "The CSS Grid `fr` unit is deceptively simple and genuinely changes how you think about layout. Once it clicks, hardcoded pixel widths start to feel like a workaround.",
    "The frontend work I'm proudest of was never the flashiest. It's the UI that just quietly works -- fast, stable, boring in the best way -- for real users who never think about it.",
    "A good README is a frontend skill, not a documentation afterthought. If a teammate can't run your project in five minutes, that's a UX problem -- the user just happens to be another developer.",
    "`const` and `let` over `var` isn't a style preference, it's a bug-prevention strategy. Block scoping quietly eliminates an entire category of bugs that used to be routine with `var`.",
    "Keep a running log of every non-trivial bug you've solved and how. Six months later, that log is a better reference than most Stack Overflow threads -- because it's indexed to your own codebase.",
    "Test layouts with real, ugly content -- long names, missing images, empty states -- not the clean placeholder text from the design file. Design files lie; production data doesn't.",
    "The gap between 'works on my machine' and 'works everywhere' is almost always browser quirks and screen sizes, not logic errors. Test on real devices early, not the week before launch.",
    "Animating opacity and transform feels dramatically more polished than people expect -- and it's far cheaper than animating layout properties. Smooth doesn't have to mean expensive.",
    "Asking 'what problem does this actually solve for the user' before writing a line of code saves more time than any framework, library, or build tool ever will.",
    "A component with one clear job is easier to test, easier to reuse, and easier to delete later. Scope creep in a component is technical debt with a UI on top.",
    "Proper `label`, `required`, and `type` attributes handle a surprising amount of form validation before a single line of JavaScript gets written. Native HTML is underrated.",
    "Write setup notes the moment you finish configuring something new -- not later. Later never comes, and the details you'd swear you'd remember are the first ones you forget.",
    "The best code reviews aren't about catching syntax issues -- a linter does that. They're about asking 'will the next person understand why this exists,' which no tool can check for you.",
    "Shipping fast matters, but shipping a page that stays fast matters more. A performance budget set before the first component is built is worth more than any optimization pass after the fact.",
    "Most state bugs aren't state management bugs -- they're a sign that two unrelated pieces of UI are sharing state that should've been separate from the start.",
    "Leaving a clear PR description and a short 'why' comment on a tricky piece of logic is a small investment that pays the next engineer -- and often future you -- back tenfold.",
]

FOLLOW_CTA = "Follow Saad Ali"

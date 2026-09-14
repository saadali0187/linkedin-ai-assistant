"""Pool of pre-written LinkedIn posts for a frontend developer (JS/HTML/CSS, 2 yrs experience).

Posts rotate in order (see post_to_linkedin.py). Add more entries any time --
the index just keeps advancing and wraps around when it runs out.
"""

POSTS = [
    "One thing I wish I knew earlier as a frontend dev: CSS specificity fights are almost always a sign the selector structure needs rethinking, not a reason to reach for !important.",
    "Two years into frontend work and the skill that's paid off the most isn't a framework -- it's reading the browser console properly before guessing at fixes.",
    "Flexbox vs Grid isn't really a debate once you frame it right: Grid for the page layout, Flexbox for the components inside it. Stop fighting one to do the other's job.",
    "Small habit that's saved me hours: committing in small, working chunks instead of one giant 'finished feature' commit. Debugging a regression is so much easier with a clean history.",
    "Semantic HTML is underrated. A page built with <button>, <nav>, and <main> instead of div-soup is easier to style, easier to make accessible, and easier for the next dev to read.",
    "JavaScript tip: array methods like .map, .filter, and .reduce read cleaner than for-loops once they click, but don't force them everywhere -- sometimes a plain loop is the most readable option.",
    "Excel skills quietly make you a better frontend dev than people expect -- reading a messy spreadsheet of product data and turning it into clean UI logic is a real skill, not a side one.",
    "Best debugging advice I've gotten: before touching the code, write one sentence describing exactly what you expected to happen and what actually happened. Half the bugs reveal themselves right there.",
    "CSS custom properties (variables) are one of the most practical upgrades to plain CSS -- theme switching, consistent spacing, and fewer magic numbers scattered across stylesheets.",
    "Two years in, my biggest lesson about learning frontend dev: build real small projects instead of collecting tutorials. Nothing teaches you like being stuck on your own bug at 11pm.",
    "A clean, well-organized MS Word document and a clean HTML document have more in common than people think -- structure first, styling second, both make the content easier to maintain.",
    "Accessibility isn't a 'nice to have' add-on at the end of a project -- alt text, proper labels, and keyboard navigation are much easier to bake in from the start than retrofit later.",
    "If your JavaScript function needs a comment to explain what it does, it usually needs a better name instead. Comments should explain *why*, not *what*.",
    "Responsive design tip: design mobile-first. It forces you to prioritize content, and scaling up to desktop is almost always easier than cramming a desktop layout down to mobile.",
    "The most underrated frontend skill isn't a JS framework -- it's being comfortable enough with plain HTML/CSS/JS that you can debug what the framework is actually doing under the hood.",
    "Version control tip: branch names and commit messages are documentation too. 'fix stuff' tells the next person (often future you) nothing.",
    "Working with real client data in Excel before it ever hits a webpage taught me more about handling edge cases -- empty cells, weird formats, duplicates -- than any course did.",
    "CSS Grid's `fr` unit is one of those small things that once it clicks, you can't imagine building layouts without it.",
    "Two years of frontend work later, the projects I'm proudest of aren't the flashiest ones -- they're the ones where the UI just quietly worked, fast and bug-free, for real users.",
    "A good README is an underrated frontend skill. If a teammate can't get your project running in five minutes, that's a UX problem too -- just for developers instead of users.",
    "JavaScript's `const` and `let` over `var` isn't just a style preference -- block scoping avoids a whole category of bugs that used to be common with `var`.",
    "One practical habit: keep a personal doc (even just in Word) of every weird bug you've solved and how. Six months later that's your own personal Stack Overflow.",
    "Frontend tip: test your layouts with real, messy content -- long names, missing images, empty states -- not just the clean placeholder text from the design file.",
    "Learning to write efficient Excel formulas (VLOOKUP, pivot tables) has made me faster at spotting patterns in data before I even start building the UI for it.",
    "The gap between 'it works on my machine' and 'it works everywhere' is usually browser differences and screen sizes. Testing early on real devices saves a lot of late fixes.",
    "CSS transitions on just 2-3 properties (opacity, transform) feel more polished than people expect, and they're cheap performance-wise compared to animating layout properties.",
    "Two years in, I've learned that asking 'what problem does this solve for the user' before writing a single line of code saves more time than any framework or tool.",
    "Keeping components small and focused on one job makes JavaScript so much easier to test and reuse later -- it's the same logic as keeping an Excel sheet to one clear purpose.",
    "HTML forms with proper `label`, `required`, and `type` attributes do a lot of validation work for free, before a single line of JavaScript is even written.",
    "Documentation habit that's helped me a lot: writing setup notes the moment I finish configuring something new, not 'later' -- later never comes and I forget the details.",
]

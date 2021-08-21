document.addEventListener('DOMContentLoaded', function () {
    const dashAppContent = document.querySelector('body');

    // Create an observer instance
    const observer = new MutationObserver(function (mutations) {
        mutations.forEach(function (mutation) {
            domRefreshed();
        });
    });
    // Configuration of the observer
    const config = {
        childList: true,
        characterData: true,
        subtree: true
    };

    // Start observation to the target
    observer.observe(dashAppContent, config);
});

/**
 * Executes every React changes the DOM.
 * All elements on window are available.
 */
function domRefreshed() {
    // Top companies modal button
    const topCompaniesBtn = document.querySelector('#top-companies');

    if (topCompaniesBtn !== null && !topCompaniesBtn.classList.contains('loaded-element')) {
        // Add loaded-element class to prevent multiples instances
        topCompaniesBtn.classList.add('loaded-element')

        // Init modals
        const modals = M.Modal.init(document.querySelectorAll('.modal'));

        // Init tabs
        const tabs = M.Tabs.init(document.querySelectorAll('.tabs'));

        // Listen when modal is open
        topCompaniesBtn.addEventListener('click', () => {
            window.setTimeout(() => {
                tabs.forEach((tab) => {
                    tab.updateTabIndicator();
                })
            }, 500);
        });
    }

    // Get iframes reference
    const iframes = document.querySelectorAll('iframe');

    iframes.forEach((iframe) => {
        if (!iframe.classList.contains('loaded-element')) {
            // Add loaded-element class to prevent multiples instances
            iframe.classList.add('loaded-element');

            /**
             * Triggers when an iframe is loaded
             */
            const iframeLoaded = (event) => {
                if (event.target.contentWindow.window.length === 0
                    || event.target.contentWindow.window.document.body.children.length === 0) {
                    // Set fallback URL
                    iframe.src = iframe.dataset.fallback;

                    // Unbind load listener
                    iframe.removeEventListener('load', iframeLoaded)
                }
            }

            iframe.addEventListener('load', iframeLoaded);
        }
    });
}
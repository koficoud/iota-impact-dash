/**
 * Init app
 */
document.addEventListener('DOMContentLoaded', function () {
    const bodyElement = document.querySelector('body');

    // Create an observer instance
    const observer = new MutationObserver(function (mutations) {
        mutations.forEach(function () {
            domRefreshed();
        });
    });

    // Start observation to the target
    observer.observe(bodyElement, {
        childList: true,
        characterData: true,
        subtree: true
    });
});

/**
 * Executes every that React changes the DOM
 * All elements on the window are available
 */
function domRefreshed() {
    // Top companies modal button
    const topCompaniesBtn = document.querySelector('#top-companies');


    if (topCompaniesBtn !== null && !topCompaniesBtn.classList.contains('loaded-element')) {
        // Add loaded-element class to prevent multiples instances
        topCompaniesBtn.classList.add('loaded-element')

        // Init modals
        M.Modal.init(document.querySelectorAll('.modal'));

        // Listen when the modal is open
        topCompaniesBtn.addEventListener('click', () => {
            // All iframes that actually are used on top 10 companies modal
            const iframes = document.querySelectorAll('iframe');

            iframes.forEach((iframe) => {
                // Set fallback URL
                iframe.src = iframe.dataset.fallback;
            });

            // Update tab indicator
            window.setTimeout(() => {
                // Init tabs every the modal opens
                const tabs = M.Tabs.init(document.querySelectorAll('.tabs'));

                tabs.forEach((tab) => {
                    tab.updateTabIndicator();
                })
            }, 500);
        });
    }
}
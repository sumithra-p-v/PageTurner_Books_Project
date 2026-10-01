// Live search for title and author.
const searchBox = document.getElementById("searchBox");

if (searchBox) {
    searchBox.addEventListener("input", function () {
        const searchText = this.value.toLowerCase().trim();
        const cards = document.querySelectorAll(".book-card");
        let visibleCount = 0;

        cards.forEach(function (card) {
            const title = card.dataset.title;
            const author = card.dataset.author;

            if (title.includes(searchText) || author.includes(searchText)) {
                card.style.display = "";
                visibleCount++;
            } else {
                card.style.display = "none";
            }
        });

        const noResults = document.getElementById("noSearchResults");

        if (noResults) {
            noResults.classList.toggle("hidden", visibleCount !== 0);
        }
    });
}


// Ask before removing a book.
function confirmRemove() {
    return confirm("Remove this book?");
}


// Check the phone number before checkout.
const checkoutForm = document.getElementById("checkoutForm");

if (checkoutForm) {
    checkoutForm.addEventListener("submit", function (event) {
        const phone = document.getElementById("phone").value.trim();

        if (!/^\d{10}$/.test(phone)) {
            event.preventDefault();
            alert("Phone number must be exactly 10 digits.");
        }
    });
}


// Hide flash messages after 3 seconds.
setTimeout(function () {
    const messages = document.querySelectorAll(".flash");

    messages.forEach(function (message) {
        message.style.opacity = "0";

        setTimeout(function () {
            message.remove();
        }, 500);
    });
}, 3000);

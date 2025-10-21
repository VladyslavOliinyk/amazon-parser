// Ждем полной загрузки DOM, чтобы все элементы были доступны
document.addEventListener("DOMContentLoaded", () => {

    // ========================================================
    // === ЛОГИКА ДЛЯ ЗАДАНИЙ 1 & 2 (старый функционал) =======
    // ========================================================
    function initStaticProductsSection() {
        const productsContainer = document.getElementById("productsContainer");
        const sortSelect = document.getElementById("sortSelect");
        const sortOrderSelect = document.getElementById("sortOrderSelect");
        const minRatingSelect = document.getElementById("minRatingSelect");
        const refreshBtn = document.getElementById("refreshBtn");

        if (!productsContainer) return;

        async function fetchProducts() {
            const minRating = minRatingSelect.value;
            const url = `/items?min_rating=${minRating}`;
            const res = await fetch(url);
            const data = await res.json();
            return data.items;
        }

        function renderProducts(items) {
            productsContainer.innerHTML = "";
            items.forEach(item => {
                const card = document.createElement("div");
                card.className = "product-card";
                card.innerHTML = `
                    <div class="image-box">
                        <img src="${item.main_image_url}" alt="${item.title}">
                    </div>
                    <h3>${item.title}</h3>
                    <div class="row">
                        <span class="price">${item.price || "N/A"}</span>
                        <span class="rating">${item.rating || "N/A"}</span>
                    </div>
                    <p class="meta">Rank: ${item.rank}</p>
                    <a href="${item.url}" target="_blank" class="btn">View on Amazon</a>
                `;
                productsContainer.appendChild(card);
            });
        }

        function sortItems(items) {
            const sortBy = sortSelect.value;
            const order = sortOrderSelect.value;
            return items.sort((a, b) => {
                let valA, valB;
                if (sortBy === "price") {
                    valA = parseFloat(a.price?.replace(/[\$,]/g, '') || 0);
                    valB = parseFloat(b.price?.replace(/[\$,]/g, '') || 0);
                } else if (sortBy === "rating") {
                    valA = parseFloat(a.rating?.split(" ")[0] || 0);
                    valB = parseFloat(b.rating?.split(" ")[0] || 0);
                } else {
                    valA = a.rank;
                    valB = b.rank;
                }
                return order === "asc" ? valA - valB : valB - valA;
            });
        }

        async function refresh() {
            let items = await fetchProducts();
            items = sortItems(items);
            renderProducts(items);
        }

        if(refreshBtn) refreshBtn.addEventListener("click", refresh);
        if(sortSelect) sortSelect.addEventListener("change", refresh);
        if(sortOrderSelect) sortOrderSelect.addEventListener("change", refresh);
        if(minRatingSelect) minRatingSelect.addEventListener("change", refresh);

        refresh();
    }


    // ========================================================
    // === ЛОГИКА ДЛЯ ЗАДАНИЯ 3 (новый интерактивный функционал) =
    // ========================================================
    function initBestsellersSection() {
        console.log("Инициализация секции Daily Bestsellers...");

        // Элементы управления
        const categorySelect = document.getElementById("categorySelect");
        const bestsellersContainer = document.getElementById("bestsellersContainer");
        const manualRefreshBtn = document.getElementById("manualRefreshBtn");
        const lastUpdatedText = document.getElementById("lastUpdatedText");

        // Элементы модальных окон
        const confirmationModal = document.getElementById("confirmationModal");
        const loaderOverlay = document.getElementById("loaderOverlay");
        const confirmRefreshBtn = document.getElementById("confirmRefreshBtn");
        const cancelRefreshBtn = document.getElementById("cancelRefreshBtn");

        // Улучшенная проверка на наличие ВСЕХ необходимых элементов
        if (!categorySelect || !manualRefreshBtn || !confirmationModal || !loaderOverlay) {
            console.error("ОШИБКА: Один или несколько ключевых элементов для секции бестселлеров не найдены на странице!");
            return;
        }
        console.log("Все элементы для секции бестселлеров успешно найдены.");

        let allBestsellersData = {};

        // --- Функции для управления UI ---
        const showModal = () => {
            console.log("Вызов showModal(), меняю display на 'flex'");
            confirmationModal.style.display = 'flex';
        }
        const hideModal = () => {
            confirmationModal.style.display = 'none';
        }
        const showLoader = () => {
            loaderOverlay.style.display = 'flex';
        }
        const hideLoader = () => {
            loaderOverlay.style.display = 'none';
        }

        // --- Основные функции ---

        async function updateParserStatus() {
            try {
                const response = await fetch('/api/parser-status');
                const data = await response.json();
                if (data.last_updated) {
                    lastUpdatedText.textContent = `Last updated: ${data.last_updated}`;
                } else {
                    lastUpdatedText.textContent = 'Data has not been generated yet. Please refresh.';
                }
            } catch (error) {
                lastUpdatedText.textContent = 'Could not get update status.';
                console.error("Ошибка при получении статуса парсера:", error);
            }
        }

        async function fetchAndDisplayData() {
            try {
                const response = await fetch('/api/bestsellers');
                allBestsellersData = await response.json();

                if (Object.keys(allBestsellersData).length > 0) {
                    populateCategorySelect(Object.keys(allBestsellersData));
                } else {
                    categorySelect.innerHTML = `<option value="">No categories found. Run parser.</option>`;
                }
            } catch (error) {
                console.error("Ошибка при загрузке данных о бестселлерах:", error);
                categorySelect.innerHTML = `<option value="">Error loading categories.</option>`;
            }
        }

        function populateCategorySelect(categories) {
            const currentSelection = categorySelect.value;
            categorySelect.innerHTML = `<option value="">-- Please choose a category --</option>`;
            categories.forEach(category => {
                const option = document.createElement('option');
                option.value = category;
                option.textContent = category;
                categorySelect.appendChild(option);
            });
            if(categories.includes(currentSelection)){
                categorySelect.value = currentSelection;
            }
        }

        function renderBestsellers(products) {
            bestsellersContainer.innerHTML = "";
            if (!products || products.length === 0) return;

            products.forEach(item => {
                const card = document.createElement("div");
                card.className = "bestseller-card";
                card.innerHTML = `
                    <div class="rank-badge">${item.rank || '#?'}</div>
                    <div class="image-box">
                        <img src="${item.image_url}" alt="${item.title}">
                    </div>
                    <h3>${item.title || "No title"}</h3>
                    <div class="row">
                        <span class="price">${item.price || "N/A"}</span>
                        <span class="rating">${item.rating || "N/A"}</span>
                    </div>
                    <p class="meta">Reviews: ${item.reviews_count || "0"}</p>
                    <a href="${item.url}" target="_blank" class="btn">View on Amazon</a>
                `;
                bestsellersContainer.appendChild(card);
            });
        }

        async function handleManualRefresh() {
            hideModal();
            showLoader();
            try {
                const response = await fetch('/api/trigger-parser', { method: 'POST' });
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || 'Parser failed to start.');
                }
                const result = await response.json();
                alert(result.message); // Показываем сообщение от сервера

                // Сразу же обновляем данные на странице
                await updateParserStatus();
                await fetchAndDisplayData();

            } catch (error) {
                alert(`Error starting parser: ${error.message}`);
            } finally {
                hideLoader();
            }
        }

        // --- Привязка событий ---
        console.log("Привязка событий к кнопкам...");
        manualRefreshBtn.addEventListener('click', showModal);
        cancelRefreshBtn.addEventListener('click', hideModal);
        confirmRefreshBtn.addEventListener('click', handleManualRefresh);

        categorySelect.addEventListener('change', () => {
            const selectedCategory = categorySelect.value;
            if (selectedCategory && allBestsellersData[selectedCategory]) {
                renderBestsellers(allBestsellersData[selectedCategory]);
            } else {
                bestsellersContainer.innerHTML = "";
            }
        });

        // --- Первоначальная загрузка данных ---
        updateParserStatus();
        fetchAndDisplayData();
    }

    // ========================================================
    // === ЗАПУСК ОБЕИХ ЧАСТЕЙ ПРИ ЗАГРУЗКЕ СТРАНИЦЫ =========
    // ========================================================
    initStaticProductsSection();
    initBestsellersSection();
});


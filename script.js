const gridData = [['А','Б','В','Г','Ґ','Д'],['Е','Є','Ж','З','И','І'],['Ї','Й','К','Л','М','Н'],['О','П','Р','С','Т','У'],['Ф','Х','Ц','Ч','Ш','Щ'],['Ь','Ю','Я','.',',',' ']];
let diaryData = null;

// Змінні для відстеження активної анімації осередку сітки
let activeAnimatingCell = null;
let activeAnimationInterval = null;

// Функція автоматичного регулювання висоти для textarea
function autoResize(el) {
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = el.scrollHeight + 'px';
}

// Функція преміального привид-введення (ghost animation) з рандомізацією років
function setupGhostPlaceholder(input, type) {
    if (!input) return;
    let timeoutId = null;
    let index = 0;
    let typing = true;
    let text = "";
    
    function getNewText() {
        if (type === 'year') {
            return String(Math.floor(Math.random() * (2026 - 1900 + 1)) + 1900);
        }
        return "Твоя чернетка...";
    }
    
    text = getNewText();
    
    function step() {
        if (input.dataset.errorActive === 'true') {
            timeoutId = setTimeout(step, 1000);
            return;
        }
        if (document.activeElement === input || input.value) {
            input.placeholder = '';
            index = 0;
            typing = true;
            return;
        }
        
        if (typing) {
            input.placeholder = text.substring(0, index);
            index++;
            if (index > text.length) {
                typing = false;
                timeoutId = setTimeout(step, 3000); // пауза 3 сек
                return;
            }
            timeoutId = setTimeout(step, 150 + Math.random() * 150);
        } else {
            input.placeholder = text.substring(0, index);
            index--;
            if (index < 0) {
                typing = true;
                index = 0;
                text = getNewText(); // Отримуємо новий випадковий рік для наступного циклу
                timeoutId = setTimeout(step, 1000); // пауза 1 сек перед повтором
                return;
            }
            timeoutId = setTimeout(step, 80);
        }
    }
    
    input.addEventListener('focus', () => {
        clearTimeout(timeoutId);
        input.placeholder = '';
        index = 0;
    });
    
    input.addEventListener('blur', () => {
        if (!input.value && input.dataset.errorActive !== 'true') {
            index = 0;
            typing = true;
            text = getNewText(); // Скидаємо на новий рандомний текст при втраті фокусу
            step();
        }
    });
    
    step();
}

// Керування аудіоплеєром
const audio = document.getElementById('giftAudio');
const playPauseBtn = document.getElementById('playPauseBtn');
const stopBtn = document.getElementById('stopBtn');
const loopBtn = document.getElementById('loopBtn');
const progress = document.getElementById('progress');
const progressContainer = document.querySelector('.progress-container');

const playIcon = document.getElementById('playIcon');
const pauseIcon = document.getElementById('pauseIcon');

if (audio) {
    if (playPauseBtn) {
        playPauseBtn.addEventListener('click', () => {
            if (audio.paused) {
                audio.play();
            } else {
                audio.pause();
            }
        });
    }

    if (stopBtn) {
        stopBtn.addEventListener('click', () => {
            audio.pause();
            audio.currentTime = 0;
            if (progress) progress.style.width = '0%';
            // Явне скидання іконки плей/пауза на Play
            if (playIcon) playIcon.classList.remove('hidden');
            if (pauseIcon) pauseIcon.classList.add('hidden');
            if (playPauseBtn) playPauseBtn.classList.remove('active');
        });
    }

    if (loopBtn) {
        loopBtn.addEventListener('click', () => {
            audio.loop = !audio.loop;
            const loopInactiveIcon = document.getElementById('loopInactiveIcon');
            const loopActiveIcon = document.getElementById('loopActiveIcon');
            if (audio.loop) {
                if (loopInactiveIcon) loopInactiveIcon.classList.add('hidden');
                if (loopActiveIcon) loopActiveIcon.classList.remove('hidden');
                loopBtn.classList.add('active');
            } else {
                if (loopInactiveIcon) loopInactiveIcon.classList.remove('hidden');
                if (loopActiveIcon) loopActiveIcon.classList.add('hidden');
                loopBtn.classList.remove('active');
            }
        });
    }

    audio.addEventListener('play', () => {
        if (playIcon) playIcon.classList.add('hidden');
        if (pauseIcon) pauseIcon.classList.remove('hidden');
        if (playPauseBtn) playPauseBtn.classList.add('active');
    });

    audio.addEventListener('pause', () => {
        if (playIcon) playIcon.classList.remove('hidden');
        if (pauseIcon) pauseIcon.classList.add('hidden');
        if (playPauseBtn) playPauseBtn.classList.remove('active');
    });

    // Оновлення прогресбару
    audio.addEventListener('timeupdate', () => {
        const pct = (audio.currentTime / audio.duration) * 100 || 0;
        if (progress) progress.style.width = pct + '%';
    });

    // Перемотування при кліку на прогресбар
    if (progressContainer) {
        progressContainer.addEventListener('click', (e) => {
            const rect = progressContainer.getBoundingClientRect();
            const clickX = e.clientX - rect.left;
            const width = rect.width;
            if (audio.duration) {
                audio.currentTime = (clickX / width) * audio.duration;
            }
        });
    }
}

function toggleAccordion(sectionToOpen) {
    if (sectionToOpen === birthdaySection) {
        birthdaySection.classList.add('open');
        diarySection.classList.remove('open');
        // Прокрутка до початку секції
        birthdaySection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } else if (sectionToOpen === diarySection) {
        diarySection.classList.add('open');
        birthdaySection.classList.remove('open');
        // Прокрутка до початку секції
        diarySection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

if (birthdayHeader && birthdaySection) {
    birthdayHeader.addEventListener('click', () => toggleAccordion(birthdaySection));
}

if (diaryHeader && diarySection) {
    diaryHeader.addEventListener('click', () => toggleAccordion(diarySection));
}

async function initDiary() {
    // --- birthday.json: статичний, завантажуємо першим і незалежно ---
    try {
        const b = await fetch('./birthday.json?v=' + Date.now());
        if (!b.ok) throw new Error(`HTTP ${b.status}`);
        const bText = await b.text();
        if (!bText || !bText.trim()) throw new Error('birthday.json порожній');
        const birthdayData = JSON.parse(bText);
        const birthdayContent = document.getElementById('birthdayContent');
        if (birthdayContent) {
            birthdayContent.innerHTML = `
                <div class="confession-text">
                    <p>${birthdayData.intro}</p>
                    <blockquote class="blockquote-6">
                        "${birthdayData.quote.text}"
                        <cite>— ${birthdayData.quote.author}</cite>
                    </blockquote>
                    <p>${birthdayData.main_text}</p>
                    <span class="final-wish">${birthdayData.final_wish}</span>
                </div>
            `;
        }
        if (birthdaySection) birthdaySection.classList.add('open');
    } catch (e) {
        // Помилка завантаження статичного привітання
    }

    // --- content.json: динамічний, падіння не зачіпає birthday ---
    try {
        const r = await fetch('./content.json?v=' + Date.now());
        if (!r.ok) throw new Error(`HTTP error! status: ${r.status}`);
        const rawText = await r.text();
        if (!rawText || !rawText.trim()) throw new Error('content.json порожній');
        diaryData = JSON.parse(rawText);

        const now = new Date();
        const today = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;

        if (localStorage.getItem('diary_date') !== today) {
            localStorage.removeItem('diary_unlocked');
            localStorage.removeItem('confession_read');
            localStorage.removeItem('confession_reply');
            localStorage.setItem('diary_date', today);
        }

        if (!diaryData.coding_date || diaryData.coding_date !== today) {
            showTemplate('expiredTemplate');
        } else if (localStorage.getItem('diary_unlocked') === 'true') {
            showUnlocked();
        } else {
            showLocked();
        }
    } catch (e) {
        const content = document.getElementById('diaryContent');
        if (content) content.innerHTML = `<div class="expired-view"><p class="expired-text">Щоденник зараз не на зв’язку. Спробуймо трішки пізніше...</p></div>`;
    }
}

function showTemplate(id) {
    const temp = document.getElementById(id), container = document.getElementById('diaryContent');
    if (container && temp) {
        container.innerHTML = ''; 
        container.appendChild(temp.content.cloneNode(true));
    }
}

function showLocked() {
    showTemplate('lockedTemplate');
    
    // Ініціалізація інструментів шифрування всередині модалки
    const encQuestion = document.getElementById('encodedQuestion');
    const grid = document.getElementById('polybiusGrid');
    const scratch = document.getElementById('scratchpadInput');
    const modal = document.getElementById('cipherModal');
    const closeBtn = document.getElementById('closeModal');

    // Рендер encodedQuestion як пар-токенів <span> для закреслення без розриву
    if (encQuestion) {
        const tokens = diaryData.encoded_question.trim().split(' ');
        encQuestion.innerHTML = tokens.map((token, i) =>
            `<span style="white-space:nowrap;display:inline-block;margin-right:0.35em">${token}</span>`
        ).join('');
        encQuestion.style.textAlign = 'left';
    }

    // Закреслення токенів за кількістю токенів у чернетці (символ за символом)
    function updateStrikethrough() {
        if (!encQuestion || !scratch) return;
        
        // Кількість закреслених токенів тепер дорівнює загальній кількості символів у чернетці
        const count = scratch.value.length;
        
        encQuestion.querySelectorAll('span').forEach((span, i) => {
            if (i < count) {
                span.style.textDecoration = 'line-through';
                span.style.opacity = '0.35';
            } else {
                span.style.textDecoration = '';
                span.style.opacity = '';
            }
        });
    }

    if (grid) {
        // Будуємо сітку одним проходом без += в циклі
        let gridHTML = '<div class="grid-cell label"></div>' +
            [1,2,3,4,5,6].map(n => `<div class="grid-cell label">${n}</div>`).join('');
        gridData.forEach((row, i) => {
            gridHTML += `<div class="grid-cell label">${i+1}</div>`;
            row.forEach((char, j) => {
                gridHTML += `<div class="grid-cell" data-char="${char}" data-code="${i+1}${j+1}">${char === ' ' ? '␣' : char}</div>`;
            });
        });
        grid.innerHTML = gridHTML;

        // Інтерактивна анімація сітки Полібія при натисканні
        grid.addEventListener('click', (e) => {
            const cell = e.target;
            if (!cell.classList.contains('grid-cell') || cell.classList.contains('label')) return;

            const char = cell.getAttribute('data-char');
            const code = cell.getAttribute('data-code');

            // Скидаємо попередню анімовану клітинку
            if (activeAnimatingCell && activeAnimatingCell !== cell) {
                clearInterval(activeAnimationInterval);
                const prevChar = activeAnimatingCell.getAttribute('data-char');
                activeAnimatingCell.textContent = prevChar === ' ' ? '␣' : prevChar;
                activeAnimatingCell.classList.remove('active-highlight');
                // Скидаємо inline-стиль щоб hover не прилипав на мобільному
                activeAnimatingCell.style.background = '';
                activeAnimatingCell.style.color = '';
                delete activeAnimatingCell.dataset.animating;
            }

            if (cell.dataset.animating === 'true') return;
            cell.dataset.animating = 'true';
            cell.classList.add('active-highlight');
            activeAnimatingCell = cell;

            let secondsPassed = 0;
            const displayChar = char === ' ' ? '␣' : char;

            activeAnimationInterval = setInterval(() => {
                secondsPassed += 2;
                if (secondsPassed >= 10) {
                    clearInterval(activeAnimationInterval);
                    cell.textContent = displayChar;
                    cell.classList.remove('active-highlight');
                    // Явно скидаємо inline-стиль — фікс для мобільного hover-прилипання
                    cell.style.background = '';
                    cell.style.color = '';
                    cell.style.borderColor = '';
                    cell.style.transform = '';
                    delete cell.dataset.animating;
                    if (activeAnimatingCell === cell) activeAnimatingCell = null;
                } else {
                    cell.textContent = cell.textContent === displayChar ? code : displayChar;
                }
            }, 2000);
        });
    }

    if (scratch) {
        scratch.addEventListener('input', () => {
            autoResize(scratch);
            updateStrikethrough();
        });
    }

    const clearScratchBtn = document.getElementById('clearScratch');
    if (clearScratchBtn) {
        clearScratchBtn.addEventListener('click', () => {
            if (scratch) {
                scratch.value = '';
                autoResize(scratch);
                updateStrikethrough();
                scratch.focus();
            }
        });
    }

    if (scratch) setupGhostPlaceholder(scratch, 'text');
    
    // Керування модалкою
    if (closeBtn && modal) {
        closeBtn.onclick = () => {
            modal.classList.add('hidden');
            document.body.classList.remove('no-scroll');
        };
    }

    const passInput = document.getElementById('diaryPassword');
    if (passInput) setupGhostPlaceholder(passInput, 'year');

    const unlockBtn = document.getElementById('unlockBtn');
    if (unlockBtn && passInput) {
        unlockBtn.onclick = () => {
            if (passInput.value.trim() === '') {
                // Якщо порожньо - відкриваємо модалку
                if (modal) {
                    modal.classList.remove('hidden');
                    document.body.classList.add('no-scroll');
                }
            } else if (passInput.value.trim() === diaryData.enigma_data.answer) { 
                localStorage.setItem('diary_unlocked', 'true'); 
                showUnlocked(); 
            } else {
                passInput.classList.add('shake-error');
                passInput.value = '';
                passInput.placeholder = 'Невірний пароль! Спробуй ще...';
                passInput.dataset.errorActive = 'true';
                
                setTimeout(() => {
                    passInput.classList.remove('shake-error');
                }, 500);
                
                setTimeout(() => {
                    delete passInput.dataset.errorActive;
                    passInput.value = '';
                    setupGhostPlaceholder(passInput, 'year');
                }, 3000);
            }
        };
    }
}

function showUnlocked() {
    showTemplate('unlockedTemplate');
    const container = document.getElementById('confessionText'), status = document.querySelector('.chat-status');
    const replyArea = document.getElementById('replyArea');
    const fullText = diaryData.confession_text;
    
    // Перевірка стану чату
    const isRead = localStorage.getItem('confession_read') === 'true';
    const savedReply = localStorage.getItem('confession_reply');

    if (container) container.textContent = isRead ? fullText : '';
    if (status) {
        status.textContent = 'не в мережі';
        status.className = 'chat-status';
    }
    
    // Відновлення чату, якщо вже була відповідь
    if (isRead && replyArea) {
        if (savedReply) {
            const messagesList = document.getElementById('messagesList');
            if (messagesList) {
                messagesList.innerHTML += `<div class="vika-message"><div class="chat-header"><div class="avatar"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg></div><div><span class="chat-name">Віка</span><br><span class="chat-status online">в мережі</span></div></div><div class="vika-text">${savedReply}</div></div>`;
            }
            const shareSection = document.getElementById('shareSection');
            if (shareSection) shareSection.classList.remove('hidden');
            replyArea.classList.add('hidden');
        } else {
            replyArea.classList.remove('hidden');
        }
    }
    
    const wait = (ms) => new Promise(r => setTimeout(r, ms));
    
    async function runChatFlow() {
        // ... (код без змін)
        await wait(2000);
        
        if (status) {
            status.textContent = 'в мережі';
            status.className = 'chat-status online';
        }
        await wait(3500);
        
        if (status) {
            status.textContent = 'пише...';
            status.className = 'chat-status typing';
        }
        
        let i = 0;
        if (container) container.classList.add('typing');
        
        function typeWriter() {
            if (i < fullText.length) {
                if (container) container.textContent += fullText.charAt(i); 
                i++;
                setTimeout(typeWriter, 150 + Math.random() * 170);
            } else { 
                if (container) container.classList.remove('typing'); 
                localStorage.setItem('confession_read', 'true');
                if (status) {
                    status.textContent = 'щойно';
                    status.className = 'chat-status online';
                }
                if (replyArea) replyArea.classList.remove('hidden');
                setTimeout(() => {
                    if (status) {
                        status.textContent = 'не в мережі';
                        status.className = 'chat-status';
                    }
                }, 5000);
            }
        }
        typeWriter();
    }
    
    if (!isRead) {
        runChatFlow();
    }
    
    function startCountdown() {
        const h = document.getElementById('t-h'), m = document.getElementById('t-m'), s = document.getElementById('t-s');
        if (!h || !m || !s) return;
        
        function update() {
            const now = new Date();
            const midnight = new Date();
            midnight.setHours(24, 0, 0, 0);
            
            const diff = midnight - now;
            if (diff <= 0) {
                window.location.reload();
                return;
            }
            
            const hours = Math.floor(diff / 3600000);
            const mins = Math.floor((diff % 3600000) / 60000);
            const secs = Math.floor((diff % 60000) / 1000);
            
            h.textContent = String(hours).padStart(2, '0');
            m.textContent = String(mins).padStart(2, '0');
            s.textContent = String(secs).padStart(2, '0');
        }
        
        update();
        setInterval(update, 1000);
    }
    startCountdown();

    const sendReplyBtn = document.getElementById('sendReplyBtn');
    if (sendReplyBtn) {
        sendReplyBtn.onclick = () => {
            const replyInput = document.getElementById('replyInput');
            const text = replyInput ? replyInput.value.trim() : '';
            if (text) {
                // Зберігаємо відповідь у пам'ять браузера
                localStorage.setItem('confession_reply', text);
                
                const messagesList = document.getElementById('messagesList');
                if (messagesList) {
                    messagesList.innerHTML += `<div class="vika-message"><div class="chat-header"><div class="avatar"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg></div><div><span class="chat-name">Віка</span><br><span class="chat-status online">в мережі</span></div></div><div class="vika-text">${text}</div></div>`;
                }
                const replyArea = document.getElementById('replyArea');
                const shareSection = document.getElementById('shareSection');
                if (replyArea) replyArea.classList.add('hidden');
                if (shareSection) shareSection.classList.remove('hidden');
            }
        };
    }

// Повністю робоча кнопка "Поділитися" з копіюванням у буфер обміну
    const shareBtn = document.getElementById('shareBtn');
    if (shareBtn) {
        shareBtn.onclick = async () => {
            const confession = diaryData.confession_text;
            
            // Беремо текст безпосередньо з DOM-елемента повідомлення Віки
            const vikaMessageEl = document.querySelector('.vika-text:last-of-type');
            const reply = vikaMessageEl ? vikaMessageEl.textContent.trim() : "";
            
            let textToShare = `Михайло: "${confession}"`;
            if (reply) {
                textToShare += `\n\nВіка: "${reply}"`;
            }

            if (navigator.share) {
                try {
                    await navigator.share({
                        title: 'Щоденник',
                        text: textToShare
                    });
                } catch (err) {
                    copyToClipboard(textToShare);
                }
            } else {
                copyToClipboard(textToShare);
            }
        };
    }
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        const shareBtn = document.getElementById('shareBtn');
        if (shareBtn) {
            const originalText = shareBtn.textContent;
            shareBtn.textContent = "Скопійовано! 💕";
            setTimeout(() => {
                shareBtn.textContent = originalText;
            }, 2500);
        }
    });
}

const yearSpan = document.getElementById('year');
if (yearSpan) yearSpan.textContent = new Date().getFullYear();

initDiary();

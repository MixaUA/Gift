const audio = document.getElementById('giftAudio');
const playPauseBtn = document.getElementById('playPauseBtn');
const progress = document.getElementById('progress');

let isPlaying = false;

function togglePlay() {
    if (isPlaying) {
        audio.pause();
        showPlayState();
    } else {
        audio.play();
        showPauseState();
    }
    isPlaying = !isPlaying;
}

function showPlayState() {
    playPauseBtn.textContent = 'НАТИСНИ';
    playPauseBtn.classList.remove('playing');
}

function showPauseState() {
    playPauseBtn.textContent = 'ПАУЗА';
    playPauseBtn.classList.add('playing');
}

playPauseBtn.addEventListener('click', togglePlay);

audio.addEventListener('timeupdate', () => {
    const percent = (audio.currentTime / audio.duration) * 100;
    progress.style.width = percent + '%';
});

audio.addEventListener('ended', () => {
    isPlaying = false;
    audio.currentTime = 0;
    progress.style.width = '0%';
    showPlayState();
});

document.querySelector('.progress-container').addEventListener('click', (e) => {
    const width = e.target.clientWidth;
    const clickX = e.offsetX;
    const duration = audio.duration;
    if (duration) {
        audio.currentTime = (clickX / width) * duration;
    }
});

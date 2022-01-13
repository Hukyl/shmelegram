export function getGlobalState() {
    return JSON.parse(localStorage.getItem(STORAGE_GLOBAL_STATE_NAME));
}

export function setGlobalState(state) {
    localStorage.setItem(STORAGE_GLOBAL_STATE_NAME, JSON.stringify(state));
}

export function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}
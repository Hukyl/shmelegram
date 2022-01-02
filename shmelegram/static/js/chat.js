const GLOBAL = {
    invisibleClassName: 'invisible', activeChatClassName: 'active-chat',
    middleSectionInsvisibleSelector: 'div#middle-section > div',
    chatIdAttribute: 'data-id', chatSelector: '.chat',
    activeChatDisplay: null,
    __state: JSON.parse(localStorage.getItem('global-state')),
    get state() { return this.__state },
    set state(data) {
        this.__state = data;
        localStorage.setItem('global-state', JSON.stringify(data));
    }
}


const messageObserver = new IntersectionObserver(function(entries, observer) {
    const state = GLOBAL.state;
    const chatId = parseInt($(`.${GLOBAL.activeChatClassName}`)[0].getAttribute('data-id'));
    for (let entry of entries) {
        let messageId = parseInt(entry.target.getAttribute('data-message-id'));
        socket.emit('add_view', {
            message_id: messageId, user_id: state.currentUserId
        });
        observer.unobserve(entry.target);
        let message = state.messages[chatId].find(message => message.id === messageId);
        message.seen_by.push(state.currentUserId);
        state.chats.byId[chatId].unreadMessagesCount--;
        $(`#chat-list > .chat[data-id=${chatId}] .unread-messages-count`)[0].innerText = (
            state.chats.byId[chatId].unreadMessagesCount
        );            
    }
    GLOBAL.state = state;
}, {threshold: 1, root: $('div#chat-messages')[0]})


class DateMessageGroup {
    #isGroup;
    #html;
    date;

    constructor(date, isGroup) {
        this.#isGroup = isGroup;
        this.date = date;
        this.#html = document.createElement('div');
        this.#html.classList.add('message-date-group');
        let stickyDate = document.createElement('div');
        stickyDate.classList.add('sticky-date');
        let span = document.createElement('span');
        span.classList.add('text-white');
        span.innerText = getDateGroupTime(Date.parse(date));
        stickyDate.appendChild(span);
        this.#html.appendChild(stickyDate);
    }

    get node() { return this.#html; }

    isEmpty() { return this.#html.children.length <= 1}

    createMessage(message) {
        let messageNode = document.createElement('div');
        messageNode.id = `message${message.id}`;
        messageNode.setAttribute('data-message-id', message.id);
        messageNode.classList.add('message');
        let contentWrapper = document.createElement('div');
        contentWrapper.classList.add('message-content-wrapper');
        let content = document.createElement('div');
        content.classList.add('message-content');
        let textContent = document.createElement('p');
        textContent.className = 'text-content text-white';
        textContent.innerText = message.text;
        let messageMeta = document.createElement('span');
        messageMeta.className = 'message-meta';
        let messageTime = document.createElement('span');
        messageTime.className = 'message-time';
        messageTime.innerText = strftime('%H:%M', fromUTCString(message.created_at));
        messageMeta.appendChild(messageTime);
        textContent.appendChild(messageMeta);        
        if (message.from_user === GLOBAL.state.currentUserId) {
            messageNode.classList.add('own');
            let messageOutgoingStatus = document.createElement('div');
            messageOutgoingStatus.className = 'message-outgoing-status';
            let messageDelivery = document.createElement('i');
            messageDelivery.className = 'bi bi-check';
            if (message.seen_by.length > 1) 
                messageDelivery.className += '-all';
            messageOutgoingStatus.appendChild(messageDelivery);
            messageMeta.appendChild(messageOutgoingStatus);
        } else if (this.#isGroup) {
            const user = GLOBAL.state.users[message.from_user];
            let avatarDiv = document.createElement('div');
            avatarDiv.className = `avatar size-small no-photo color-bg-${ordinalLast(user.username)}`;
            avatarDiv.innerText = user.username.charAt(0);
            let titleDiv = document.createElement('div');
            titleDiv.className = `message-title color-${ordinalLast(user.username)}`;
            titleDiv.innerText = user.username;
            content.appendChild(titleDiv);
            messageNode.appendChild(avatarDiv);
        }
        if (!message.seen_by.includes(GLOBAL.state.currentUserId)) 
            messageObserver.observe(messageNode);
        content.appendChild(textContent);
        contentWrapper.append(content);
        messageNode.appendChild(contentWrapper);
        return messageNode;
    }

    insertMessage(message) {
        this.#html.appendChild(this.createMessage(message));
    }

    insertMessageDiv(messageDiv) {
        this.#html.appendChild(messageDiv);
    }

    isMessageDisplayed(messageId) {
        if (this.isEmpty()) return false;
        for (let messageDiv of this.#html.querySelectorAll('.message')) {
            if (messageDiv.getAttribute('data-message-id') === messageId)
                return true;
        }
        return false;
    }

    compareDate(date) {
        let date1 = strftime('%Y-%m-%d', new Date(Date.parse(date)));
        let date2 = strftime('%Y-%m-%d', new Date(Date.parse(this.date)));
        return date1 === date2;
    };
}


class ChatDisplay {
    #statusIntervalId;

    constructor(chat) { 
        this.chat = chat;
        this.messageGroups = [];
        this.#statusIntervalId = null;
    }

    updateStatus() {
        if (this.chat.type === 'group') {
            let [totalMembers, commaSpan, onlineMembers] = $(
                '#middle-header > .info > .status > span'
            );
            totalMembers.innerText = `${this.chat.members.length} member`;
            if (this.chat.members.length > 1)
                totalMembers.innerText += 's';
            let onlineMemberCount = getChatOnlineMembers(this.chat);
            if (onlineMemberCount) {
                commaSpan.classList.remove(GLOBAL.invisibleClassName);
                onlineMembers.innerText = `${onlineMemberCount} online`;
            } else {
                commaSpan.classList.add(GLOBAL.invisibleClassName);
                onlineMembers.innerText = '';
            }
        } else if (this.chat.type === 'private') {
            let [totalMembers, commaSpan, onlineMembers] = $('#middle-header > .info > .status > span');
            commaSpan.classList.add(GLOBAL.invisibleClassName);
            onlineMembers.innerText = '';
            let chatMembers = GLOBAL.state.chats.byId[this.chat.id].members.slice();
            delete chatMembers[chatMembers.indexOf(GLOBAL.state.currentUserId)];
            const companionUser = GLOBAL.state.users[chatMembers.find(el => el !== undefined)];
            if (companionUser.last_online === null)
                totalMembers.innerText = "online";
            else
                totalMembers.innerText = `last seen ${timeSince(fromUTCString(companionUser.last_online))}`;
        }
    }

    #intervalStatus() {
        let totalMembers = $('#middle-header > .info > .status > span')[0];
        let chatMembers = GLOBAL.state.chats.byId[this.chat.id].members.slice();
        delete chatMembers[chatMembers.indexOf(GLOBAL.state.currentUserId)];
        const companionUser = GLOBAL.state.users[chatMembers.find(el => el !== undefined)];
        totalMembers.innerText = (
            `last seen ${timeSince(fromUTCString(companionUser.last_online))}`
        );
    }

    #displayHeader() {
        // display chat in middle header
        $("#middle-title")[0].innerText = this.chat.title;
        let chatAvatar = $("#middle-header > div.avatar")[0];
        if (chatAvatar.className.match(/color-bg-\d/))
            chatAvatar.className = chatAvatar.className.replace(
                /color-bg-\d/, `color-bg-${ordinalLast(this.chat.title)}`
            );
        else
            chatAvatar.classList.add(`color-bg-${ordinalLast(this.chat.title)}`)
        chatAvatar.innerText = this.chat.title.charAt(0).toUpperCase();
        this.updateStatus();
        if (this.chat.type === 'private')
            this.#statusIntervalId = setInterval(
                this.#intervalStatus.bind(this), 60 * 1000
            );
    }

    #displayMessages() {
        // display chat messages in middle section
        const isGroup = this.chat.type === 'group';
        const state = GLOBAL.state;
        const layout = $('#message-layout')[0];
        let messages = state.messages[this.chat.id];
        let dateMessageGroup = new DateMessageGroup(
            messages[0].created_at, isGroup
        );
        this.messageGroups.push(dateMessageGroup);
        for (let i = 0; i < Math.min(messages.length, 50); i++) {
            let message = messages[i];
            if (!dateMessageGroup.compareDate(message.created_at)) {
                if (!dateMessageGroup.isEmpty()) {
                    layout.appendChild(dateMessageGroup.node);
                    dateMessageGroup = new DateMessageGroup(message.created_at, isGroup);
                    this.messageGroups.push(dateMessageGroup);
                }
            }
            dateMessageGroup.insertMessage(message);
        }
        if (!dateMessageGroup.isEmpty())
            layout.appendChild(dateMessageGroup.node);
    }

    isMessageDisplayed(messageId) {
        return this.messageGroups.some(group => group.isMessageDisplayed(messageId));
    }

    addMessage(message) {
        let lastMessageGroup = this.messageGroups[this.messageGroups.length - 1];
        if (lastMessageGroup.compareDate(message.created_at)) {
            lastMessageGroup = new DateMessageGroup(
                message.created_at, this.chat.type === 'group'
            );
            this.messageGroups.push(lastMessageGroup);
        }
        let messageDiv = lastMessageGroup.createMessage(message);
        lastMessageGroup.insertMessageDiv(messageDiv);
    }

    static scrollMessagesToBotton() {
        let chatMessages = $('#chat-messages')[0];
        chatMessages.scrollTop = chatMessages.scrollHeight;    
    }

    display() { 
        this.#displayHeader(); this.#displayMessages();
        ChatDisplay.scrollMessagesToBotton()
    }

    hide() {
        $('#message-layout')[0].innerHTML = '';
        clearInterval(this.#statusIntervalId);
    }
}


function hideActiveChat() {
    GLOBAL.activeChatDisplay?.hide();
    GLOBAL.activeChatDisplay = null;
    $(`.${GLOBAL.activeChatClassName}`)[0]?.classList.remove(GLOBAL.activeChatClassName);
}

function getChatOnlineMembers(chat) {
    const state = GLOBAL.state;
    let count = 0;
    for (let memberId of chat.members) {
        if (state.users[memberId].last_online === null)
            count++;
    }
    return count;
}

function displayChats(chats) {
    // display chats in left section
}


$('input#search').change(function() {
    // display chats found by certain query
});


$('div#middle-header').click(function() {
    // display detailed info about chat
});

const socket = io.connect(
    'http://' + document.domain + ':' + location.port, 
    {query: {
        user_id: parseInt(getCookie('userID'))
    }}
);


$(document).ready(async function() {
    let data = {
        currentUserId: parseInt(getCookie('userID')),
        chats: {byId: {}, listIds: []},
        users: {}, messages: {}
    };
    for (let chat of $(GLOBAL.chatSelector)) {
        let chatId = parseInt(chat.getAttribute(GLOBAL.chatIdAttribute));
        data.chats.byId[chatId] = {id: chatId};
        data.chats.byId[chatId].type = chat.classList[1];
        data.chats.byId[chatId].title = chat.querySelector(
            '.info > .title > h3'
        ).textContent.trim()
        await $.get(`api/messages/chat/${chatId}`)
        .then(function(response) {
            data.messages[chatId] = response.messages.reverse();
        });
        await $.get(`api/users/${data.currentUserId}/chats/${chatId}/unread`)
        .then(function(response) {
            data.chats.byId[chatId].unreadMessagesCount = response.messages.length;
        });
        if (data.chats.byId[chatId].unreadMessagesCount.length !== 0) {
            let unreadDiv = chat.querySelector('.info > .subtitle > div');
            unreadDiv.classList.remove(GLOBAL.invisibleClassName);
            unreadDiv.innerText = data.chats.byId[chatId].unreadMessagesCount;
        }
        await $.get(`api/chats/${chatId}`).then(function(response) {
            data.chats.byId[chatId].members = response.members;
        });
        for (let memberId of data.chats.byId[chatId].members) {
            await $.get(`api/users/${memberId}`).then(function(response) {
                data.users[memberId] = {
                    id: response.id, username: response.username, 
                    last_online: response.last_online
                };
            });
        }
        data.chats.listIds.push(chatId);
    }
    GLOBAL.state = {...GLOBAL.state, ...data};
});


$('.chat').click(function() {
    hideActiveChat();
    this.classList.add(GLOBAL.activeChatClassName);
    $(GLOBAL.middleSectionInsvisibleSelector)[0].classList.remove(GLOBAL.invisibleClassName);
    let chatId = parseInt(this.getAttribute(GLOBAL.chatIdAttribute));
    GLOBAL.activeChatDisplay = new ChatDisplay(GLOBAL.state.chats.byId[chatId]);
    GLOBAL.activeChatDisplay.display();
});

$(window).blur(function() {
    // send request to update last_online
    let userId = parseInt(GLOBAL.state.currentUserId);
    socket.emit('is_offline', {user_id: userId});
});
$(window).focus(function() {
    // send request to set online status
    let userId = parseInt(GLOBAL.state.currentUserId);
    socket.emit('is_online', {user_id: userId}); 
});

$(document).on('keydown', function(e) {
    if (e.key == "Escape") {
        hideActiveChat();
        $(GLOBAL.middleSectionInsvisibleSelector)[0].classList.add(GLOBAL.invisibleClassName);
    }
});


$('button#send-button').click(function() {
    const text = $('#message-input > input')[0].value.trim();
    if (!text)
        return;
    const state = GLOBAL.state;
    const message = {
        chat_id: $(`.${GLOBAL.activeChatClassName}`)[0].getAttribute('data-id'),
        user_id: GLOBAL.state.currentUserId, is_service: false,
        text: text, reply_to: null, 
        created_at: strftime("%Y-%m-%dT%H:%M:%S", toUTC(new Date()))
    };
    socket.emit('message', message);
    state.messages[message.chat_id].push(message);
    GLOBAL.activeChatDisplay.addMessage(message);
});

socket.on('update_user_status', function(data) {
    const state = GLOBAL.state;
    if (state.users.hasOwnProperty(data.user_id)) {
        state.users[data.user_id].last_online = data.last_online;
        GLOBAL.state = state;
    }
    if (GLOBAL.activeChatDisplay?.chat.members.includes(data.user_id))
        GLOBAL.activeChatDisplay.updateStatus();
});


socket.on('update_view', function(data) {
    const state = GLOBAL.state;
    const messageArrId = state.messages[data.chat_id].findIndex(
        message => message.id === data.message_id
    );
    if (messageArrId === -1) return;
    state.messages[data.chat_id][messageArrId].seen_by.push(data.user_id);
    GLOBAL.state = state;
    let fromUser = state.messages[data.chat_id][messageArrId].from_user;
    if (GLOBAL.activeChatDisplay.isMessageDisplayed(data.message_id) && 
            fromUser === state.currentUserId && data.user_id !== state.currentUserId)
        $(
            `.message[data-message-id=${data.message_id}] .message-outgoing-status > i.bi`
        )[0].className += '-all';
});
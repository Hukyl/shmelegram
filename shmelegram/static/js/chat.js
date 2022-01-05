const GLOBAL = {
    invisibleClassName: 'invisible', activeChatClassName: 'active-chat',
    middleSectionInsvisibleSelector: 'div#middle-section > div',
    chatIdAttribute: 'data-id', chatSelector: '.chat',
    activeChatDisplay: null, messageAPILength: 50,
    isLoadingMessages: false, __messageAction: null,
    __state: JSON.parse(localStorage.getItem('global-state')),
    get state() { return this.__state },
    set state(data) {
        this.__state = data;
        localStorage.setItem('global-state', JSON.stringify(data));
    }, 
    get messageAction() {return this.__messageAction === null ? new Message() : this.__messageAction},
    set messageAction(data) {this.__messageAction = data},
    socket: io.connect(
        'http://' + document.domain + ':' + location.port, 
        {query: {
            user_id: parseInt(getCookie('userID'))
        }}
    )
}


const messageObserver = new IntersectionObserver(function(entries, observer) {
    const state = GLOBAL.state;
    const chatId = parseInt($(`.${GLOBAL.activeChatClassName}`)[0].getAttribute('data-id'));
    for (let entry of entries) {
        let messageId = parseInt(entry.target.getAttribute('data-message-id'));
        GLOBAL.socket.emit('add_view', {
            message_id: messageId, user_id: state.currentUserId
        });
        entry.target.classList.remove('unread');
        observer.unobserve(entry.target);
        let message = state.messages[chatId].find(message => message.id === messageId);
        message.seen_by.push(state.currentUserId);
        state.chats.byId[chatId].unreadMessagesCount = Math.max(
            1, state.chats.byId[chatId].unreadMessagesCount
        ) - 1;
        GLOBAL.state = state;
        ChatListDisplay.updateChatUnreadCount(chatId);
    }
}, {threshold: 1})


class DateMessageGroup {
    #html;
    date;

    constructor(date,) {
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

    static createMessage(message) {
        const chat = GLOBAL.state.chats.byId[message.chat];
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
        messageTime.innerText = message.edited_at ? 'edited ' : '';
        messageTime.innerText += strftime('%H:%M', fromUTCString(message.created_at));
        messageTime.title = strftime('%b %d, %Y, %I:%M:%S %p', fromUTCString(message.created_at));
        if (message.edited_at)
            messageTime.title += (
                '\nedited: ' + 
                strftime('%b %d, %Y, %I:%M:%S %p', fromUTCString(message.edited_at))
            )
        messageMeta.appendChild(messageTime);
        textContent.appendChild(messageMeta);
        if (message.from_user === GLOBAL.state.currentUserId) {
            messageNode.classList.add('own');
            let messageOutgoingStatus = document.createElement('div');
            messageOutgoingStatus.className = 'message-outgoing-status';
            let messageDelivery = document.createElement('i');
            messageDelivery.className = 'bi bi-check';
            if (message.seen_by.length > Math.min(chat.members.length - 1, 1)) 
                messageDelivery.className += '-all';
            messageOutgoingStatus.appendChild(messageDelivery);
            messageMeta.appendChild(messageOutgoingStatus);
        } else if (chat.type === 'group') {
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
            messageNode.classList.add('unread');
        content.appendChild(textContent);
        contentWrapper.append(content);
        messageNode.appendChild(contentWrapper);
        return messageNode;
    }

    appendMessage(message) {
        this.#html.appendChild(DateMessageGroup.createMessage(message));
    }

    appendMessageDiv(messageDiv) {
        this.#html.appendChild(messageDiv);
    }

    insertMessage(message) {
        this.#html.insertBefore(DateMessageGroup.createMessage(message), this.#html.children[1]);
    } 

    insertMessageDiv(messageDiv) {
        this.#html.insertBefore(messageDiv, this.#html.children[1]);
    }

    isMessageDisplayed(messageId) {
        if (this.isEmpty()) return false;
        for (let messageDiv of this.#html.querySelectorAll('.message')) {
            if (messageDiv.getAttribute('data-message-id') == messageId)
                return true;
        }
        return false;
    }

    compareDate(date) {
        let date1 = strftime('%Y-%m-%d', new Date(Date.parse(date)));
        let date2 = strftime('%Y-%m-%d', new Date(Date.parse(this.date)));
        return date1 === date2;
    };

    get length() {
        return this.#html.querySelectorAll('div.message').length;
    }
}



class ChatDisplay {
    #statusIntervalId;

    constructor(chatId) { 
        this.chatId = chatId;
        this.messageGroups = [];
        this.#statusIntervalId = null;
    }

    get chat() {
        return GLOBAL.state.chats.byId[this.chatId];
    }

    get onlineMembers() {
        const state = GLOBAL.state;
        let count = 0;
        for (let memberId of this.chat.members) {
            if (state.users[memberId].last_online === null)
                count++;
        }
        return count;
    }

    updateStatus() {
        if (this.chat.type === 'group') {
            let [totalMembers, commaSpan, onlineMembers] = $(
                '#middle-header > .info > .status > span'
            );
            totalMembers.innerText = `${this.chat.members.length} member`;
            if (this.chat.members.length > 1)
                totalMembers.innerText += 's';
            let onlineMemberCount = this.onlineMembers;
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
            this.#intervalStatus();
        }
    }

    #intervalStatus() {
        let totalMembers = $('#middle-header > .info > .status > span')[0];
        let chatMembers = this.chat.members.slice();
        delete chatMembers[chatMembers.indexOf(GLOBAL.state.currentUserId)];
        const companionUser = GLOBAL.state.users[chatMembers.find(el => el !== undefined)];
        if (companionUser.last_online === null)
            totalMembers.innerText = "online";
        else
            totalMembers.innerText = `last seen ${timeSince(fromUTCString(companionUser.last_online))}`;
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
        const layout = $('#message-layout')[0];
        let messages = GLOBAL.state.messages[this.chatId];
        for (
                let i = messages.length - 1; 
                i >= Math.max(0, messages.length - GLOBAL.messageAPILength); 
                i--
            ) {
            let message = messages[i];
            this.insertMessage(message);
        }
        for (let messageGroup of this.messageGroups)
            layout.appendChild(messageGroup.node);
    }

    isMessageDisplayed(messageId) {
        return this.messageGroups.some(group => group.isMessageDisplayed(messageId));
    }

    insertMessage(message) {
        let firstMessageGroup = this.messageGroups[0];
        if (firstMessageGroup === undefined || !firstMessageGroup.compareDate(message.created_at)) {
            firstMessageGroup = new DateMessageGroup(message.created_at);
            this.messageGroups.unshift(firstMessageGroup);
        }
        const messageDiv = DateMessageGroup.createMessage(message);
        firstMessageGroup.insertMessageDiv(messageDiv);
        if (messageDiv.classList.contains('unread')) 
            messageObserver.observe(messageDiv);
    }

    addMessage(message) {
        let lastMessageGroup = this.messageGroups[this.messageGroups.length - 1];
        if (lastMessageGroup === undefined || !lastMessageGroup.compareDate(message.created_at)) {
            lastMessageGroup = new DateMessageGroup(message.created_at);
            this.messageGroups.push(lastMessageGroup);
        }
        const messageDiv = DateMessageGroup.createMessage(message);
        lastMessageGroup.appendMessageDiv(messageDiv);
        if (messageDiv.classList.contains('unread')) 
            messageObserver.observe(messageDiv);
    }

    updateMessage(message) {
        let messageDiv = $(`div.message[data-message-id=${message.id}]`)[0];
        const messageGroup = messageDiv.parentNode;
        const nextSibling = messageDiv.nextElementSibling;
        if (messageDiv.classList.contains('unread'))
            messageObserver.unobserve(messageDiv);
        this.deleteMessage(message.id);
        messageDiv = DateMessageGroup.createMessage(message);
        if (messageDiv.classList.contains('unread'))
            messageObserver.observe(messageDiv);        
        messageGroup.insertBefore(messageDiv, nextSibling);
    }

    static scrollMessagesToBottom() {
        let chatMessages = $('#chat-messages')[0];
        chatMessages.scrollTop = chatMessages.scrollHeight;    
    }

    setReplyTo(messageId) {}

    #createEditDiv(messageId) {
        const message = GLOBAL.state.messages[this.chatId].find(
            msg => msg.id === messageId
        );
        const messageActionDiv = document.createElement('div');
        messageActionDiv.className = 'message-action'
        const cancelButton = document.createElement('button');
        cancelButton.type = 'button';
        cancelButton.className = 'button translucent faded round';
        cancelButton.onclick = cancelMessageAction;
        const cancelIcon = document.createElement('i');
        cancelIcon.className = 'bi bi-x-lg';
        const embedDiv = document.createElement('div');
        embedDiv.className = 'embedded-message inside-input';
        const textDiv = document.createElement('div');
        textDiv.className = 'message-text';
        const p = document.createElement('p');
        p.innerText = message.text;
        const messageTitle = document.createElement('div');
        messageTitle.className = 'message-title';
        messageTitle.innerText = 'Edit Message';
        textDiv.appendChild(p);
        textDiv.appendChild(messageTitle);
        cancelButton.appendChild(cancelIcon);
        embedDiv.appendChild(textDiv);
        messageActionDiv.appendChild(cancelButton);
        messageActionDiv.appendChild(embedDiv);
        return messageActionDiv;
    }

    setEdit(messageId) {
        ChatDisplay.clearMessageAction();
        $('button#send-button > i')[0].className = 'bi bi-check-lg';
        $('#middle-section > div')[0].insertBefore(
            this.#createEditDiv(messageId), $('#message-input')[0]
        );
    }

    static clearMessageAction() {
        const middleSection = $('#middle-section > div')[0];
        $('button#send-button > i')[0].className = 'bi bi-send';
        for (let action of $('.message-action'))
            middleSection.removeChild(action);
        $('#editable-message-text')[0].innerHTML = '';
    }

    display() { 
        this.#displayHeader(); this.#displayMessages();
        ChatDisplay.scrollMessagesToBottom();
    }

    hide() {
        $('#message-layout')[0].innerHTML = '';
        clearInterval(this.#statusIntervalId);
        messageObserver.disconnect();
        ChatDisplay.clearMessageAction();
    }

    get length() {
        return this.messageGroups.reduce((prev, curr) => prev + curr.length, 0)
    }

    get firstMessage() {
        return document.querySelector('div.message');
    }

    deleteMessage(messageId) {
        const messageDiv = $(`div.message[data-message-id=${messageId}]`)[0];
        messageObserver.unobserve(messageDiv);
        messageDiv.parentNode.removeChild(messageDiv);
    }

    setMessageAsViewed(messageId) {
        $(
            `.message[data-message-id=${messageId}] .message-outgoing-status > i.bi`
        )[0].className = 'bi bi-check-all';
    }
}



class ChatListDisplay {
    static addChat(chatId) {}

    static removeChat(chatId) {}

    static selectChat(chatId) {}

    static unselectActiveChat() {
        $(`.${GLOBAL.activeChatClassName}`)[0]?.classList.remove(
            GLOBAL.activeChatClassName
        );
    }

    static updateChat(chatId) {
        const chat = GLOBAL.state.chats.byId[chatId];
        if (!chat) return;
        const chatDiv = $(`#chat-list > .chat[data-id=${chatId}]`)[0];
        if (!chatDiv) return;
        ChatListDisplay.updateChatName(chatId);
        ChatListDisplay.updateChatLastMessage(chatId);
        ChatListDisplay.updateChatUnreadCount(chatId);
    }

    static updateChatName(chatId) {
        const chat = GLOBAL.state.chats.byId[chatId];
        const chatDiv = $(`#chat-list > .chat[data-id=${chatId}]`)[0];        
        const chatAvatar = chatDiv.querySelector('.status > .avatar');
        chatAvatar.className = chatAvatar.className.replace(
            /color-bg-\d/, `color-bg-${ordinalLast(chat.title)}`
        );
        chatAvatar.innerText = chat.title.charAt(0).toUpperCase();
        const chatTitle = chatDiv.querySelector('.info > .title > h3');
        chatTitle.innerHTML = chat.title;
        if (chat.type === 'group')
            chatTitle.innerHTML = `<i class="bi bi-people-fill"></i>  ${chatTitle.innerHTML}`;        
    }

    static updateChatLastMessage(chatId) {
        const chat = GLOBAL.state.chats.byId[chatId];
        const lastMessage = GLOBAL.state.messages[chatId][GLOBAL.state.messages[chatId].length - 1];
        $(`#chat-list > .chat[data-id=${chatId}] .title span`)[0].innerText = diffNow(
            lastMessage.created_at
        );
        const subtitle = $(`#chat-list > .chat[data-id=${chatId}] .info > .subtitle`)[0];
        const lastMessageText = subtitle.querySelector('p');
        lastMessageText.innerText = lastMessage.text;
        if (chat.type === 'group') {
            const fromUser = GLOBAL.state.users[lastMessage.from_user];
            const senderName = fromUser.id === GLOBAL.state.currentUserId ? 'You' : fromUser.username;
            lastMessageText.innerHTML = (
                `<span class="sender-name">${senderName}</span>` +
                lastMessageText.innerHTML
            )                
        }     
    }

    static updateChatUnreadCount(chatId) {
        const chat = GLOBAL.state.chats.byId[chatId];
        const unreadMessagesCount = $(
            `#chat-list > .chat[data-id=${chatId}] div.unread-messages-count`
        )[0];
        unreadMessagesCount.innerText = chat.unreadMessagesCount;
        if (chat.unreadMessagesCount > 0)
            unreadMessagesCount.classList.remove('invisible');
        else
            unreadMessagesCount.classList.add('invisible');               
    }

    static moveToTop(chatId) {
        const chat = GLOBAL.state.chats.byId[chatId];
        if (!chat) return;
        const chatDiv = $(`#chat-list > .chat[data-id=${chatId}]`)[0];
        if (!chatDiv) return;
        const chatList = $('#chat-list')[0];
        chatList.insertBefore(chatDiv, chatList.children[0]);
    }

    static displayChats() {

    }

    static displaySearch(searchQuery) {}

    static hideSearch() {}
}



class Message {
    _createData(text) {
        const state = GLOBAL.state;
        return {
            chat_id: GLOBAL.activeChatDisplay.chatId,
            user_id: state.currentUserId, is_service: false,
            text: text, reply_to: null, seen_by: [state.currentUserId],
            created_at: strftime("%Y-%m-%dT%H:%M:%S", toUTC(new Date()))
        };
    }

    _getEvent() {
        return 'message';
    }

    send(text) {
        GLOBAL.socket.emit(this._getEvent(), this._createData(text));        
    }
}


class ReplyMessage extends Message {
    constructor(toMessageId) {
        super();
        this.toMessageId = toMessageId;
    }

    _createData(...data) {
        const message = super._createData(...data);
        message.reply_to = this.toMessageId;
        return message;
    }
}

class EditMessage extends Message {
    constructor(messageId) {
        super();
        this.messageId = messageId;
    }

    _createData(text) {
        return {
            message_id: this.messageId, text: text, 
            edited_at: strftime("%Y-%m-%dT%H:%M:%S", toUTC(new Date()))
        };
    }

    _getEvent() {
        return 'edit_message';
    }
}



class Dialog {
    createNode() {
        const modalContainer = document.createElement('div');
        modalContainer.className = 'modal fade';
        modalContainer.tabIndex = -1;
        const modalDialog = document.createElement('div');
        modalDialog.className = 'modal-dialog modal-dialog-centered';
        const modalContent = document.createElement('div');
        modalContent.className = 'modal-content';        
        const modalHeader = document.createElement('div');
        modalHeader.className = 'modal-header';
        const modalTitle = document.createElement('h5');
        modalTitle.className = 'modal-title';
        const modalBody = document.createElement('div');
        modalBody.className = 'modal-body';
        const modalFooter = document.createElement('div');
        modalFooter.className = 'modal-footer';
        modalHeader.appendChild(modalTitle);
        modalContent.appendChild(modalHeader);
        modalContent.appendChild(modalBody);
        modalContent.appendChild(modalFooter);
        modalDialog.appendChild(modalContent);
        modalContainer.appendChild(modalDialog);
        return modalContainer;
    }

    display() {
        const node = this.createNode();
        $('div#portals')[0].appendChild(node);
        new bootstrap.Modal(node).show();
        node.addEventListener('hidden.bs.modal', this.hide);
    }

    hide() {
        for (let modal of $('#portals .modal')) {
            bootstrap.Modal.getOrCreateInstance(modal).hide();
        }
        setTimeout(function() {
            $('div#portals')[0].innerHTML = '';
        }, 150);
    }
}

class DeleteMessageDialog extends Dialog {
    createNode() {
        const node = super.createNode();
        const title = node.querySelector('.modal-title');
        title.innerText = 'Delete message';
        const body = node.querySelector('.modal-body');
        const footer = node.querySelector('.modal-footer');
        const p = document.createElement('p');
        p.innerText = 'Are you sure you want to delete this message?';
        const buttonConfirm = document.createElement('button');
        buttonConfirm.className = 'btn btn-danger';
        buttonConfirm.innerText = 'Delete';
        buttonConfirm.onclick = function(event) {
            GLOBAL.socket.emit('delete_message', {message_id: this.messageId});
            this.hide();
        }.bind(this);
        const buttonCancel = document.createElement('button');
        buttonCancel.className = 'btn btn-secondary';
        buttonCancel.innerText = 'Cancel';
        buttonCancel.setAttribute('data-bs-dismiss', 'modal');
        buttonCancel.onclick = this.hide;
        body.appendChild(p); 
        footer.appendChild(buttonConfirm); 
        footer.appendChild(buttonCancel);
        return node;
    }

    constructor(messageId) {
        super();
        this.messageId = messageId;
    }
}



function hideActiveChat() {
    GLOBAL.activeChatDisplay?.hide();
    ChatListDisplay.unselectActiveChat();
    GLOBAL.activeChatDisplay = null;
    $('#editable-message-text')[0].innerHTML = '';
}

function cancelMessageAction() {
    GLOBAL.messageAction = null;
    ChatDisplay.clearMessageAction();
}


$('input#search').change(function() {
    // display chats found by certain query
});


$('div#middle-header').click(function() {
    // display detailed info about chat
});


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
        GLOBAL.state = {...GLOBAL.state, ...data};
        ChatListDisplay.updateChatUnreadCount(chatId);
    }
});


$('.chat').click(function() {
    hideActiveChat();
    this.classList.add(GLOBAL.activeChatClassName);
    $(GLOBAL.middleSectionInsvisibleSelector)[0].classList.remove(GLOBAL.invisibleClassName);
    let chatId = parseInt(this.getAttribute(GLOBAL.chatIdAttribute));
    GLOBAL.activeChatDisplay = new ChatDisplay(chatId);
    GLOBAL.activeChatDisplay.display();
    $('#editable-message-text').focus();
});


$(window).blur(function() {
    // send request to update last_online
    let userId = parseInt(GLOBAL.state.currentUserId);
    GLOBAL.socket.emit('is_offline', {user_id: userId});
});
$(window).focus(function() {
    // send request to set online status
    let userId = parseInt(GLOBAL.state.currentUserId);
    GLOBAL.socket.emit('is_online', {user_id: userId}); 
});


$('#chat-messages').scroll(async function() {
    const chatId = GLOBAL.activeChatDisplay?.chatId;
    if (!chatId) return;
    if ($('#chat-messages')[0].scrollTop > 500) return;
    if (GLOBAL.isLoadingMessages) return;
    GLOBAL.isLoadingMessages = true;
    const totalMessageCount = GLOBAL.state.messages[chatId].length;
    const displayedMessageCount = GLOBAL.activeChatDisplay.length;
    if (displayedMessageCount === totalMessageCount) {
        const messagePage = Math.ceil(totalMessageCount / GLOBAL.messageAPILength) + 1;
        let messages = null;
        await $.get(`api/messages/chat/${chatId}?page=${messagePage}`).then(function(response) {
            messages = response.messages;
        });
        if (messages.length === 0) {
            GLOBAL.isLoadingMessages = false;
            return;
        }
        const state = GLOBAL.state;
        state.messages[chatId].unshift(...messages.reverse());
        GLOBAL.state = state;
    }
    const firstMessageId = parseInt(
        GLOBAL.activeChatDisplay.firstMessage.getAttribute('data-message-id')
    );
    const firstMessageIndex = GLOBAL.state.messages[chatId].findIndex(
        element => element.id === firstMessageId
    );
    for (let i = firstMessageIndex - 1; i >= Math.max(0, firstMessageIndex - GLOBAL.messageAPILength); i--) {
        GLOBAL.activeChatDisplay.insertMessage(GLOBAL.state.messages[chatId][i]);
    }
    GLOBAL.isLoadingMessages = false;
});


$('#editable-message-text').on('input', function() {
    ChatDisplay.scrollMessagesToBottom();
})


$(document).on('keydown', function(e) {
    if (e.key == "Escape") {
        hideActiveChat();
        $(GLOBAL.middleSectionInsvisibleSelector)[0].classList.add(GLOBAL.invisibleClassName);
    } else if (e.key == "Enter") {
        e.preventDefault(); e.stopPropagation();
        $('button#send-button').click();
    }
});


$.contextMenu({
    selector: 'div.message', 
    build: function($trigger, event) {
        const messageDiv = $trigger[0];
        const chat = GLOBAL.activeChatDisplay.chat;
        const message = GLOBAL.state.messages[chat.id].find(
            msg => msg.id === parseInt(messageDiv.getAttribute('data-message-id'))
        );
        const isOwnMessage = message.from_user === GLOBAL.state.currentUserId;
        const items = {};
        items.copy = {
            name: "Copy", icon: 'copy', 
            callback: function (itemKey, opt, rootMenu, originalEvent) {
                const messageId = parseInt(opt.$trigger[0].getAttribute('data-message-id'));
                const chatId = GLOBAL.activeChatDisplay.chatId;
                const messageText = GLOBAL.state.messages[chatId].find(
                    msg => msg.id === messageId
                ).text;
                if (!navigator.clipboard) {
                    console.error('Copy: can not copy text to clipboard');
                    return false;
                }
                navigator.clipboard.writeText(messageText)
                .then(function() {}, function(err) {
                    console.error('Async: Could not copy text: ', err);
                });
                return true;
            }
        };
        if (isOwnMessage) 
            items.edit = {
                name: "Edit", icon: "edit",
                callback: function(itemKey, opt, rootMenu, originalEvent) {
                    const messageId = parseInt(opt.$trigger[0].getAttribute('data-message-id'));
                    const chatId = GLOBAL.activeChatDisplay.chatId;
                    const messageText = GLOBAL.state.messages[chatId].find(
                        msg => msg.id === messageId
                    ).text;
                    GLOBAL.activeChatDisplay.setEdit(messageId);
                    $('#editable-message-text')[0].innerHTML = messageText;
                    GLOBAL.messageAction = new EditMessage(messageId);
                    ChatDisplay.scrollMessagesToBottom();
                    $('#editable-message-text').focus();
                }
            }
        if (chat.type === 'private' || chat.type === 'group' && isOwnMessage)
            items.delete = {
                name: "Delete", icon: "delete", 
                callback: function() {
                    new DeleteMessageDialog(message.id).display();
                    return true;
                }
            }
        return {items: items};
    }
});


$('button#send-button').click(function() {
    const input = $('#editable-message-text')[0];
    const text = input.innerText.trim();
    if (!text)
        return;
    GLOBAL.messageAction.send(text);
    ChatDisplay.clearMessageAction();
    GLOBAL.messageAction = null;
    input.innerHTML = '';
});


GLOBAL.socket.on('message', function(message) {
    const state = GLOBAL.state;
    state.messages[message.chat].push(message);
    GLOBAL.state = state;
    if (message.chat === GLOBAL.activeChatDisplay?.chatId) {
        GLOBAL.activeChatDisplay.addMessage(message);
        ChatDisplay.scrollMessagesToBottom();
        ChatListDisplay.updateChatLastMessage(message.chat);
    } else {
        const state = GLOBAL.state;
        state.chats.byId[message.chat].unreadMessagesCount = Math.max(
            0, state.chats.byId[message.chat].unreadMessagesCount
        ) + 1;
        GLOBAL.state = state;
        ChatListDisplay.updateChat(message.chat);
    }
    ChatListDisplay.moveToTop(message.chat);
});


GLOBAL.socket.on('update_user_status', function(data) {
    const state = GLOBAL.state;
    if (state.users.hasOwnProperty(data.user_id)) {
        state.users[data.user_id].last_online = data.last_online;
        GLOBAL.state = state;
    }
    if (GLOBAL.activeChatDisplay?.chat.members.includes(data.user_id))
        GLOBAL.activeChatDisplay.updateStatus();
});


GLOBAL.socket.on('update_view', function(data) {
    const state = GLOBAL.state;
    const messageArrId = state.messages[data.chat_id].findIndex(
        message => message.id === data.message_id
    );
    if (messageArrId === -1) return;
    state.messages[data.chat_id][messageArrId].seen_by.push(data.user_id);
    GLOBAL.state = state;
    if (GLOBAL.activeChatDisplay?.chatId !== data.chat_id) return;
    let fromUser = state.messages[data.chat_id][messageArrId].from_user;
    if (GLOBAL.activeChatDisplay.isMessageDisplayed(data.message_id) && 
            fromUser === state.currentUserId)
        GLOBAL.activeChatDisplay.setMessageAsViewed(data.message_id);
});

GLOBAL.socket.on('delete_message', function(data) {
    const state = GLOBAL.state;
    const messageArrayIndex = state.messages[data.chat_id].findIndex(
        msg => msg.id === data.message_id
    );
    if (messageArrayIndex === -1) return;
    const message = state.messages[data.chat_id][messageArrayIndex];
    const chat = state.chats.byId[data.chat_id];
    if (!message.seen_by.includes(state.currentUserId))
        chat.unreadMessagesCount = Math.max(1, chat.unreadMessagesCount) - 1;
    state.messages[chat.id].splice(messageArrayIndex, 1);
    GLOBAL.state = state;
    ChatListDisplay.updateChat(message.chat);
    if (GLOBAL.activeChatDisplay?.chatId !== data.chat_id) return;
    if (GLOBAL.activeChatDisplay.isMessageDisplayed(data.message_id))
        GLOBAL.activeChatDisplay.deleteMessage(data.message_id);
});

GLOBAL.socket.on('edit_message', function(data) {
    const state = GLOBAL.state;
    const message = state.messages[data.chat_id].find(
        msg => msg.id === data.message_id
    );
    if (message === -1) return;
    message.edited_at = data.edited_at; message.text = data.text;
    GLOBAL.state = state;
    ChatListDisplay.updateChat(message.chat);
    if (GLOBAL.activeChatDisplay?.chatId !== data.chat_id) return;
    if (GLOBAL.activeChatDisplay.isMessageDisplayed(data.message_id))
        GLOBAL.activeChatDisplay.updateMessage(message);
});
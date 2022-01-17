import { fromUTCString, getDateGroupTime, timeSince, diffNow } from '../utils/date.js';
import * as Api from './api.js';
import GLOBAL from './main.js';
import { messageObserver } from './main.js';
import ordinalLast from '../utils/main.js';


export function cancelMessageAction() {
    GLOBAL.messageAction = null;
    ChatMessagesDisplay.clearMessageAction();
}


class DateMessageGroup {
    #html;
    date;

    constructor(date) {
        this.date = date;
        this.#html = document.createElement('div');
        this.#html.classList.add('message-date-group');
        const stickyDate = DateMessageGroup.createServiceMessage(
            getDateGroupTime(Date.parse(date))
        );
        stickyDate.classList.add('sticky-date');
        stickyDate.classList.remove('message');
        this.#html.appendChild(stickyDate);
    }

    get node() { return this.#html; }

    isEmpty() { return this.#html.children.length <= 1}

    static createServiceMessage(text) {
        const serviceMessage = document.createElement('div');
        serviceMessage.className = 'message service';
        const span = document.createElement('span');
        span.classList.add('text-white');
        span.innerText = text;
        serviceMessage.appendChild(span);
        return serviceMessage;
    }

    static async createMessage(message) {
        if (message.is_service) {
            const messageNode = DateMessageGroup.createServiceMessage(message.text);
            messageNode.setAttribute('data-message-id', message.id);
            if (!message.seen_by.includes(GLOBAL.state.currentUserId)) 
                messageNode.classList.add('unread');
            return messageNode;
        }
        const chat = GLOBAL.state.getChat(message.chat);
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
        if (chat.type === 'group' && message.from_user !== GLOBAL.state.currentUserId) {
            const user = GLOBAL.state.getUser(message.from_user);
            let avatarDiv = document.createElement('div');
            avatarDiv.className = `avatar size-small no-photo color-bg-${ordinalLast(user.id)}`;
            avatarDiv.innerText = user.username.charAt(0);
            let titleDiv = document.createElement('div');
            titleDiv.className = `message-title color-${ordinalLast(user.id)}`;
            titleDiv.innerText = user.username;
            content.appendChild(titleDiv);
            messageNode.appendChild(avatarDiv);
        }
        if (message.reply_to) {
            let replyToMessage = GLOBAL.state.getMessage(chat.id, message.reply_to);
            if (!replyToMessage)
                replyToMessage = await Api.getMessage(chat.id, message.reply_to);
            const embeddedMessage = document.createElement('div');
            embeddedMessage.className = 'embedded-message';
            const embeddedText = document.createElement('div');
            embeddedText.className = 'message-text';
            const embeddedP = document.createElement('p');
            embeddedP.innerText = replyToMessage.text;
            const embeddedTitle = document.createElement('div');
            embeddedTitle.className = 'message-title';
            let user = GLOBAL.state.getUser(replyToMessage.from_user);
            if (!user)
                user = await Api.getUser(replyToMessage.from_user);
            embeddedTitle.innerText = user.username;
            embeddedText.appendChild(embeddedP);
            embeddedText.appendChild(embeddedTitle);
            embeddedMessage.appendChild(embeddedText);
            content.appendChild(embeddedMessage);
        }
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
        }
        if (!message.seen_by.includes(GLOBAL.state.currentUserId)) 
            messageNode.classList.add('unread');
        content.appendChild(textContent);
        contentWrapper.append(content);
        messageNode.appendChild(contentWrapper);
        return messageNode;
    }

    async appendMessage(message) {
        this.#html.appendChild(await DateMessageGroup.createMessage(message));
    }

    appendMessageDiv(messageDiv) {
        this.#html.appendChild(messageDiv);
    }

    async insertMessage(message) {
        this.#html.insertBefore(await DateMessageGroup.createMessage(message), this.#html.children[1]);
    }

    insertMessageDiv(messageDiv) {
        this.#html.insertBefore(messageDiv, this.#html.children[1]);
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


export class ChatMessagesDisplay {
    #statusIntervalId;

    constructor(chatId) { 
        this.chatId = chatId;
        this.messageGroups = [];
        this.#statusIntervalId = null;
    }

    get chat() {
        return GLOBAL.state.getChat(this.chatId);
    }

    get onlineMembers() {
        return GLOBAL.state.getOnlineMembers(this.chatId);
    }

    updateStatus() {
        if (this.chat.type === 'group') {
            let [totalMembers, onlineMembers] = $(
                '#middle-header > .info > .status > span'
            );
            totalMembers.innerText = `${this.chat.members.length} member`;
            if (this.chat.members.length !== 1)
                totalMembers.innerText += 's';
            let onlineMemberCount = this.onlineMembers;
            if (onlineMemberCount) {
                onlineMembers.innerText = `${onlineMemberCount} online`;
            } else {
                onlineMembers.innerText = '';
            }
        } else if (this.chat.type === 'private') {
            let [totalMembers, onlineMembers] = $('#middle-header > .info > .status > span');
            onlineMembers.innerText = '';
            this.#intervalStatus();
        }
    }

    #intervalStatus() {
        let totalMembers = $('#middle-header > .info > .status > span')[0];
        const companionUser = GLOBAL.state.getUser(
            this.chat.members.find(el => el !== GLOBAL.state.currentUserId)
        );
        if (companionUser.last_online === null)
            totalMembers.innerText = "online";
        else
            totalMembers.innerText = `last seen ${timeSince(fromUTCString(companionUser.last_online))}`;
    }

    #displayHeader() {
        // display chat in middle header
        const chat = this.chat;
        $("#middle-title").text(chat.title);
        let chatAvatar = $("#middle-header > div.avatar");
        chatAvatar.removeClass(function (index, className) {
            return (className.match (/(^|\s)color-bg-\d/g) || []).join(' ');
        });
        chatAvatar.addClass(`color-bg-${ordinalLast(chat.id)}`);
        chatAvatar.text(chat.title.charAt(0));
        this.updateStatus();
        if (chat.type === 'private')
            this.#statusIntervalId = setInterval(
                this.#intervalStatus.bind(this), 60 * 1000
            );
    }

    async #displayMessages() {
        // display chat messages in middle section
        const messages = GLOBAL.state.getChatMessages(this.chatId);
        for (
                let i = messages.length - 1; 
                i >= Math.max(0, messages.length - GLOBAL.messageAPILength); 
                i--
            ) {
            let message = messages[i];
            await this.insertMessage(message);
        }
        for (let msgDiv of $('div.message.unread'))
            messageObserver.observe(msgDiv);
    }

    isMessageDisplayed(messageId) {
        return $(`.message[data-message-id=${messageId}]`).length > 0;
    }

    async insertMessage(message) {
        let firstMessageGroup = this.messageGroups[0];
        if (firstMessageGroup === undefined || !firstMessageGroup.compareDate(message.created_at)) {
            firstMessageGroup = new DateMessageGroup(message.created_at);
            this.messageGroups.unshift(firstMessageGroup);
            $('#message-layout')[0].insertBefore(
                firstMessageGroup.node, this.messageGroups[1]?.node
            );
        }
        const messageDiv = await DateMessageGroup.createMessage(message);
        firstMessageGroup.insertMessageDiv(messageDiv);
        if (messageDiv.classList.contains('unread')) 
            messageObserver.observe(messageDiv);
    }

    async addMessage(message) {
        let lastMessageGroup = this.messageGroups[this.messageGroups.length - 1];
        if (lastMessageGroup === undefined || !lastMessageGroup.compareDate(message.created_at)) {
            lastMessageGroup = new DateMessageGroup(message.created_at);
            this.messageGroups.push(lastMessageGroup);
            $('#message-layout')[0].appendChild(lastMessageGroup.node);
        }
        const messageDiv = await DateMessageGroup.createMessage(message);
        lastMessageGroup.appendMessageDiv(messageDiv);
        if (messageDiv.classList.contains('unread')) 
            messageObserver.observe(messageDiv);
    }

    async updateMessage(message) {
        let messageDiv = $(`div.message[data-message-id=${message.id}]`)[0];
        const messageGroup = messageDiv.parentNode;
        const nextSibling = messageDiv.nextElementSibling;
        if (messageDiv.classList.contains('unread'))
            messageObserver.unobserve(messageDiv);
        this.deleteMessage(message);
        messageDiv = await DateMessageGroup.createMessage(message);
        if (messageDiv.classList.contains('unread'))
            messageObserver.observe(messageDiv);
        messageGroup.insertBefore(messageDiv, nextSibling);
    }

    deleteMessage(message) {
        const messageDiv = $(`div.message[data-message-id=${message.id}]`)[0];
        const parentGroupDiv = messageDiv.parentNode;
        messageObserver.unobserve(messageDiv);
        parentGroupDiv.removeChild(messageDiv);
        if (parentGroupDiv.children.length <= 1) {
            this.messageGroups.splice(this.messageGroups.findIndex(
                group => group.compareDate(message.created_at)
            ), 1);
            parentGroupDiv.parentNode.removeChild(parentGroupDiv);
        }
    }    

    static scrollMessagesToBottom() {
        let chatMessages = $('#chat-messages')[0];
        chatMessages.scrollTop = chatMessages.scrollHeight;    
    }

    #createActionDiv() {
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
        const messageTitle = document.createElement('div');
        messageTitle.className = 'message-title';
        textDiv.appendChild(p);
        textDiv.appendChild(messageTitle);
        cancelButton.appendChild(cancelIcon);
        embedDiv.appendChild(textDiv);
        messageActionDiv.appendChild(cancelButton);
        messageActionDiv.appendChild(embedDiv);
        return messageActionDiv;
    }

    #createReplyDiv(messageId) {
        const message = GLOBAL.state.getMessage(this.chatId, messageId);
        const user = GLOBAL.state.getUser(message.from_user);
        const actionDiv = this.#createActionDiv();
        actionDiv.querySelector('p').innerText = message.text;
        actionDiv.querySelector('.message-title').innerText = user.username;
        return actionDiv;
    }

    setReplyTo(messageId) {
        ChatMessagesDisplay.clearMessageAction();
        $('#middle-section > div')[0].insertBefore(
            this.#createReplyDiv(messageId), $('#message-input')[0]
        );
    }

    #createEditDiv(messageId) {
        const message = GLOBAL.state.getMessage(this.chatId, messageId);
        const actionDiv = this.#createActionDiv();
        actionDiv.querySelector('p').innerText = message.text;
        actionDiv.querySelector('.message-title').innerText = 'Edit Message';
        return actionDiv;
    }

    setEdit(messageId) {
        ChatMessagesDisplay.clearMessageAction();
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

    async display() { 
        const chatMessagesDiv = $('#chat-messages');
        chatMessagesDiv.addClass(GLOBAL.invisibleClassName);
        this.#displayHeader(); 
        await this.#displayMessages();
        ChatMessagesDisplay.scrollMessagesToBottom();
        chatMessagesDiv.removeClass(GLOBAL.invisibleClassName);        
    }

    hide() {
        $(GLOBAL.middleSectionInsvisibleSelector).addClass(
            GLOBAL.invisibleClassName
        );
        $('#message-layout')[0].innerHTML = '';
        clearInterval(this.#statusIntervalId);
        messageObserver.disconnect();
        ChatMessagesDisplay.clearMessageAction();
    }

    get length() {
        return this.messageGroups.reduce((prev, curr) => prev + curr.length, 0)
    }

    get firstMessage() {
        return document.querySelector('div.message');
    }

    setMessageAsViewed(messageId) {
        $(
            `.message[data-message-id=${messageId}] .message-outgoing-status > i.bi`
        )[0].className = 'bi bi-check-all';
    }
}



export class ChatListDisplay {
    static createChatBase() {
        const chatDiv = document.createElement('div');
        chatDiv.className = `chat`;
        const status = document.createElement('div');
        status.className = 'status';
        const avatar = document.createElement('div');
        avatar.className = `avatar no-photo size-large`;
        const info = document.createElement('div');
        info.className = 'info';
        const titleDiv = document.createElement('div');
        titleDiv.className = 'title';
        const title = document.createElement('h3');
        title.className = 'text-white list-chat-title';
        const lastMessageMeta = document.createElement('div');
        lastMessageMeta.className = 'last-message-meta';
        const messageStatus = document.createElement('div');
        messageStatus.className = 'message-outgoing-status text-white-50';
        const statusIcon = document.createElement('i');
        statusIcon.className = 'bi';
        const lastMessageSendTime = document.createElement('span');
        lastMessageSendTime.className = 'time text-secondary';
        const subtitle = document.createElement('div');
        subtitle.className = 'subtitle';
        const lastMessageText = document.createElement('p');
        lastMessageText.className = 'last-message text-white-50';
        const senderName = document.createElement('span');
        senderName.className = 'sender-name';
        const unreadMessagesCount = document.createElement('div');
        unreadMessagesCount.className = 'unread-messages-count';
        lastMessageText.appendChild(senderName);        
        messageStatus.appendChild(statusIcon);
        lastMessageMeta.appendChild(messageStatus);
        lastMessageMeta.appendChild(lastMessageSendTime);
        status.appendChild(avatar);
        titleDiv.appendChild(title);
        titleDiv.appendChild(lastMessageMeta);
        subtitle.appendChild(lastMessageText);
        subtitle.appendChild(unreadMessagesCount);
        info.appendChild(titleDiv);
        info.appendChild(subtitle);
        chatDiv.appendChild(status);
        chatDiv.appendChild(info);
        return chatDiv;
    }

    static createChat(chatId) {
        const chat = GLOBAL.state.getChat(chatId);
        const lastMessage = GLOBAL.state.getLastMessage(chatId);
        const chatDiv = this.createChatBase();
        chatDiv.classList.add(chat.type);
        chatDiv.setAttribute('data-id', chat.id);
        const avatar = chatDiv.querySelector('div.avatar');
        avatar.classList.add(`color-bg-${ordinalLast(chat.id)}`);
        avatar.innerText = chat.title.charAt(0);
        chatDiv.querySelector('h3.list-chat-title').innerText = chat.title;
        if (lastMessage?.from_user === GLOBAL.state.currentUserId)
            chatDiv.querySelector('.message-outgoing-status i').classList.add(
                lastMessage?.seen_by.length > Math.min(
                    chat.members.length - 1, 1
                ) ? 'bi-check-all' : 'bi-check'
            );
        chatDiv.querySelector(
            'div.last-message-meta span.time'
        ).innerText = lastMessage ? diffNow(
            fromUTCString(lastMessage.created_at)
        ) : '';
        if (chat.type === 'group' && lastMessage && !lastMessage.is_service)
            chatDiv.querySelector('span.sender-name').innerText = (
                lastMessage?.from_user === GLOBAL.state.currentUserId ? 
                'You' : GLOBAL.state.getUser(lastMessage.from_user).username
            );
        chatDiv.querySelector('p.last-message').innerHTML += lastMessage?.text || '';
        const unreadMessagesCount = chatDiv.querySelector(
            'div.unread-messages-count'
        );
        unreadMessagesCount.innerText = chat.unreadMessagesCount;
        if (chat.unreadMessagesCount <= 0)
            unreadMessagesCount.classList.add(
                GLOBAL.invisibleClassName
            );
        return chatDiv;
    }

    static createQueryChat(chat) {
        const chatDiv = this.createChatBase();
        chatDiv.classList.add(chat.type);
        chatDiv.classList.add('search-result');
        chatDiv.setAttribute('data-id', chat.id);
        const avatar = chatDiv.querySelector('div.avatar');
        avatar.classList.add(`color-bg-${ordinalLast(chat.id)}`);
        avatar.innerText = chat.title.charAt(0);
        chatDiv.querySelector('h3.list-chat-title').innerText = chat.title;
        const lastMessageText = chatDiv.querySelector('p.last-message');
        lastMessageText.innerHTML += `${chat.members.length} member`;
        if (chat.members.length !== 1)
            lastMessageText.innerHTML += 's';
        chatDiv.querySelector('div.unread-messages-count').classList.add(
            GLOBAL.invisibleClassName
        );      
        return chatDiv;
    }

    static insertChat(chatId) {
        const chatList = $('#chat-list')[0];
        chatList.insertBefore(
            this.createChat(chatId), 
            chatList.children[0]
        );
    }

    static addChat(chatId) {
        const chatList = $('#chat-list')[0];
        chatList.appendChild(this.createChat(chatId));
    }

    static removeChat(chatId) {
        $('#chat-list')[0].removeChild(
            $(`.chat[data-id=${chatId}]`)[0]
        );
    }

    static selectChat(chatId) {}

    static unselectActiveChat() {
        $(`.${GLOBAL.activeChatClassName}`)[0]?.classList.remove(
            GLOBAL.activeChatClassName
        );
    }

    static updateChat(chatId) {
        const chatList = $('#chat-list')[0];
        const chatDiv = $(`#chat-list > .chat[data-id=${chatId}]`)[0];
        const nextChat = chatDiv.nextElementSibling;
        chatList.removeChild(chatDiv);
        const newChatDiv = this.createChat(chatId);
        if (chatDiv.classList.contains(GLOBAL.activeChatClassName))
            newChatDiv.classList.add(GLOBAL.activeChatClassName);
        chatList.insertBefore(newChatDiv, nextChat);
    }

    static moveToTop(chatId) {
        const chat = GLOBAL.state.getChat(chatId);
        if (!chat) return;
        const chatDiv = $(`#chat-list > .chat[data-id=${chatId}]`)[0];
        if (!chatDiv) return;
        const chatList = $('#chat-list')[0];
        chatList.insertBefore(chatDiv, chatList.children[0]);
    }

    static displaySearch(chats) {
        const chatList = $('#chat-list');
        const searchResultList = $('#search-result-list');
        searchResultList.empty();
        chatList.addClass(GLOBAL.invisibleClassName);
        searchResultList.removeClass(GLOBAL.invisibleClassName);
        let anyChatDisplayed = false;
        for (let chat of chats) {
            if (!chat.members.includes(GLOBAL.state.currentUserId)) {
                searchResultList.append(this.createQueryChat(chat));
                anyChatDisplayed = true;
            }
        }
        if (!anyChatDisplayed) {
            const msg = document.createElement('h6');
            msg.innerText = 'No chats found';
            msg.style.color = 'lightgray';
            msg.style.textAlign = 'center';
            searchResultList.append(msg);
        }
    }

    static hideSearch() {
        $('#search-result-list').empty();
        $('#search').val('');
        $('#search-result-list').addClass(GLOBAL.invisibleClassName);
        $('#chat-list').removeClass(GLOBAL.invisibleClassName);        
    }

    static isSearchDisplayed() {
        return !$('#search-result-list').hasClass(GLOBAL.invisibleClassName);
    }

    static display() {
        $('#left-section').removeClass(
            GLOBAL.invisibleClassName
        );
    }
    
    static hide() {
        $('#left-section').addClass(
            GLOBAL.invisibleClassName
        );
    }
}


export class ChatInfoDisplay {
    #intervalIds;

    constructor(chatId) {
        this.chatId = chatId;
        this.#intervalIds = {};
    }

    get chat() {
        return GLOBAL.state.getChat(this.chatId);
    }

    get isDisplayed() {
        return !$('#right-section').hasClass(GLOBAL.invisibleClassName);
    }

    isUserDisplayed(userId) {
        return $(
            `#right-section div.members div.member[data-user-id=${userId}]`
        ).length > 0
    }

    #createUser(user) {
        const memberDiv = document.createElement('div');
        memberDiv.className = 'member';
        memberDiv.setAttribute('data-user-id', user.id);
        const avatar = document.createElement('div');
        avatar.className = (
            `avatar no-photo size-large color-bg-${ordinalLast(user.id)}`
        );
        avatar.innerText = user.username.charAt(0);
        const info = document.createElement('info');
        info.className = 'info';
        const titleDiv = document.createElement('div');
        titleDiv.className = 'title';
        const username = document.createElement('h6');
        username.className = 'user-username';
        username.innerText = user.username;
        const statusDiv = document.createElement('div');
        statusDiv.className = 'status text-white-50';
        const status = document.createElement('span');
        status.className = 'online-status';
        titleDiv.appendChild(username);
        statusDiv.appendChild(status);
        info.appendChild(titleDiv);
        info.appendChild(statusDiv);
        memberDiv.appendChild(avatar);
        memberDiv.appendChild(info);
        return memberDiv;
    }

    addUser(user) {
        $('#right-section div.members').append(this.#createUser(user));
        this.updateUserStatus(user.id, true);
        this.#intervalIds[user.id] = setInterval(this.updateUserStatus.bind(
            this, user.id
        ), 1000 * 60);
    }

    removeUser(userId) {
        clearInterval(this.#intervalIds[userId]);
        delete this.#intervalIds[userId];
        $(
            `#right-section div.members div.member[data-user-id=${userId}]`
        ).remove()
    }

    updateUserStatus(userId, moveToTop = false) {
        const user = GLOBAL.state.getUser(userId);
        if (!user || !this.isUserDisplayed(userId)) return;
        const onlineStatus = $(
            `#right-section div.members div.member[data-user-id=${userId}] .online-status`
        );
        if (user.last_online === null) {
            onlineStatus.text("online");
            if (moveToTop)
                $('#right-section div.members').prepend($(
                    `#right-section div.members div.member[data-user-id=${userId}]`
                ));
        } else
            onlineStatus.text(`last seen ${timeSince(fromUTCString(user.last_online))}`);
    }

    updateTitle() {
        const chat = this.chat;
        const avatar = $('#right-section .chat-info .avatar');
        avatar.removeClass(function (index, className) {
            return (className.match (/(^|\s)color-bg-\d/g) || []).join(' ');
        });
        avatar.addClass(`color-bg-${ordinalLast(chat.id)}`);
        avatar.text(chat.title.charAt(0));
        $('#right-title').text(chat.title);
    }

    updateStatus() {
        const chat = this.chat;
        const totalMembers = $('#right-member-count');
        let text = `${chat.members.length} member`;
        if (chat.members.length !== 1)
            text += 's';
        totalMembers.text(text);
        $('#right-section .members-header .member-count').text(text);
        this.updateOnlineCount();
    }

    updateOnlineCount() {
        const onlineMembers = $('#right-online-count');
        let onlineMemberCount = GLOBAL.state.getOnlineMembers(this.chatId);
        if (onlineMemberCount) 
            onlineMembers.text(`${onlineMemberCount} online`);
         else 
            onlineMembers.text('');
    }

    updateMembers() {
        $('#right-section div.members').empty();
        for (let memberId of GLOBAL.state.getUserOrdering(this.chatId))
            this.addUser(GLOBAL.state.getUser(memberId));
    }

    display() {
        this.updateTitle();
        this.updateStatus();
        this.updateMembers();
        $('#right-section').removeClass(GLOBAL.invisibleClassName);
    }

    hide() {
        for (let intervalId of Object.values(this.#intervalIds))
            clearInterval(intervalId);
        $('#right-section').addClass(GLOBAL.invisibleClassName);
    }

    toggle() {
        if (this.isDisplayed)
            this.hide();
        else
            this.display();
    }    
}
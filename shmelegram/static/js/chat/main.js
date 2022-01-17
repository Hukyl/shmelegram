import State from './state.js';
import * as Api from './api.js';
import { 
    DeleteMessageDialog, CreateGroupNameDialog, LeaveChatDialog,
    AddChatMembersDialog, CreatePrivateChatDialog
} from './dialog.js';
import { Message, EditMessage, ReplyMessage } from './message.js';
import { ChatMessagesDisplay, ChatListDisplay, ChatInfoDisplay, cancelMessageAction } from './display.js';
import { getCookie } from '../utils/storage.js';



const GLOBAL = {
    invisibleClassName: 'invisible', activeChatClassName: 'active-chat',
    middleSectionInsvisibleSelector: 'div#middle-section > div',
    chatIdAttribute: 'data-id', chatSelector: '.chat',
    activeChatDisplay: null, messageAPILength: 50,
    infoDisplay: null, maxGroupMemberCount: 50,
    isLoadingMessages: false, __messageAction: null,
    state: new State(), __previousScrollPosition: null,
    get messageAction() {
        return this.__messageAction === null ? new Message(
            this.activeChatDisplay?.chatId
        ) : this.__messageAction
    },
    set messageAction(data) {this.__messageAction = data},
    get previousScrollPosition() {
        if (!this.__previousScrollPosition)
            this.__previousScrollPosition = $('#chat-messages')[0].scrollTop;
        return this.__previousScrollPosition
    },
    set previousScrollPosition(data) {this.__previousScrollPosition = data},    
    socket: io.connect(
        'http://' + document.domain + ':' + location.port, 
        {query: {
            user_id: parseInt(getCookie('userID'))
        }}
    )
}

export const messageObserver = new IntersectionObserver(function(entries, observer) {
    const chatId = GLOBAL.activeChatDisplay.chatId;
    for (let entry of entries) {
        if (!entry.isIntersecting) continue;
        let messageId = parseInt(entry.target.getAttribute('data-message-id'));
        GLOBAL.socket.emit('add_view', {message_id: messageId});
        entry.target.classList.remove('unread');
        observer.unobserve(entry.target);
        let message = GLOBAL.state.getMessage(chatId, messageId);
        message.seen_by.push(GLOBAL.state.currentUserId);
        const chat = GLOBAL.state.getChat(chatId);
        chat.unreadMessagesCount = Math.max(1, chat.unreadMessagesCount) - 1;
        GLOBAL.state.save();
        ChatListDisplay.updateChat(chatId);
    }
}, {threshold: 1});


export default GLOBAL;


function hideActiveChat() {
    GLOBAL.activeChatDisplay?.hide();
    GLOBAL.previousScrollPosition = null;
    ChatListDisplay.unselectActiveChat();
    GLOBAL.activeChatDisplay = null;
    $('#editable-message-text')[0].innerHTML = '';
}


$(document).ready(async function() {
    GLOBAL.state.empty();
    for (let chatData of await Api.getUserChats(GLOBAL.state.currentUserId)) {
        chatData.unreadMessagesCount = await Api.getUnreadMessagesCount(
            chatData.id, GLOBAL.state.currentUserId
        );
        if (chatData.type === 'private') {
            const companionUserId = chatData.members.find(
                el => el !== GLOBAL.state.currentUserId
            );
            let companionUser = GLOBAL.state.getUser(companionUserId);
            if (!companionUser) {
                companionUser = await Api.getUser(companionUserId);
                GLOBAL.state.appendUser(companionUser);
            }
            chatData.title = companionUser.username;
        }
        GLOBAL.state.appendChat(chatData);
        GLOBAL.state.pushMessages(await Api.getChatMessages(chatData.id));
        for (let memberId of chatData.members) {
            if (!GLOBAL.state.userExists(memberId))
                GLOBAL.state.appendUser(await Api.getUser(memberId));
        }
        GLOBAL.state.save();
    }
    for (let chatId of GLOBAL.state.getChatOrdering())
        ChatListDisplay.addChat(chatId);
    ChatListDisplay.display();
});


$(document).on('keydown', function(e) {
    if (e.key == "Escape") {
        if (GLOBAL.__messageAction) {
            cancelMessageAction();
            GLOBAL.messageAction = null;
        } else {
            hideActiveChat();
        }
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
        const message = GLOBAL.state.getMessage(
            chat.id, parseInt(messageDiv.getAttribute('data-message-id'))
        );
        const isOwnMessage = message.from_user === GLOBAL.state.currentUserId;
        const items = {};
        items.reply = {
            name: "Reply", icon: 'reply', 
            callback: function(itemKey, opt, rootMenu, originalEvent) {
                const messageId = parseInt(opt.$trigger[0].getAttribute('data-message-id'));
                GLOBAL.activeChatDisplay.setReplyTo(messageId);
                GLOBAL.messageAction = new ReplyMessage(
                    GLOBAL.activeChatDisplay?.chatId, messageId
                );
                ChatMessagesDisplay.scrollMessagesToBottom();
                $('#editable-message-text').focus();
            }
        }
        items.copy = {
            name: "Copy", icon: 'copy', 
            callback: function (itemKey, opt, rootMenu, originalEvent) {
                const messageId = parseInt(opt.$trigger[0].getAttribute('data-message-id'));
                const chatId = GLOBAL.activeChatDisplay.chatId;
                const messageText = GLOBAL.state.getMessage(chatId, messageId).text;
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
                    const messageText = GLOBAL.state.getMessage(chatId, messageId).text;
                    GLOBAL.activeChatDisplay.setEdit(messageId);
                    $('#editable-message-text')[0].innerHTML = messageText;
                    GLOBAL.messageAction = new EditMessage(
                        GLOBAL.activeChatDisplay.chatId, messageId
                    );
                    ChatMessagesDisplay.scrollMessagesToBottom();
                    $('#editable-message-text').focus();
                }
            }
        if (chat.type === 'private' || chat.type === 'group' && isOwnMessage)
            items.delete = {
                name: "Delete", icon: "delete color-red", 
                callback: function() {
                    new DeleteMessageDialog().success(function() {
                        GLOBAL.socket.emit('delete_message', {message_id: message.id});
                    }).display();
                    return true;
                }
            }
        return {items: items};
    }
});

$.contextMenu({
    selector: '#chat-list div.chat', 
    build: function($trigger, event) {
        const chatDiv = $trigger[0];
        const chat = GLOBAL.state.getChat(parseInt(chatDiv.getAttribute('data-id')));
        return {items: {leave: {
            name: chat.type === 'private' ? 'Delete' : `Leave ${chat.type}`, 
            icon: 'exit color-red', 
            callback: function(itemKey, opt, rootMenu, originalEvent) {
                new LeaveChatDialog(chat.type === 'private').success(function(event) {
                    GLOBAL.socket.emit('leave_chat', {chat_id: chat.id});
                }).display();
                return true;
            }
        }}}
    }
});

$.contextMenu({
    selector: '#search-result-list div.chat', 
    trigger: 'left',
    build: function($trigger, event) {
        const chatDiv = $trigger[0];
        const chatId = parseInt(chatDiv.getAttribute('data-id'));
        return {items: {join: {
            name: 'Join', icon: 'join', 
            callback: () => {
                GLOBAL.socket.emit('join_chat', {chat_id: chatId});
                ChatListDisplay.hideSearch();
                return true;
            }
        }}}
    }
});


$('#chat-list').on('click', '.chat:not(.search-result)', function() {
    const chatId = parseInt(this.getAttribute(GLOBAL.chatIdAttribute));
    if (chatId === GLOBAL.activeChatDisplay?.chatId) return;
    const chat = GLOBAL.state.getChat(chatId);
    hideActiveChat();
    const prevInfoShown = GLOBAL.infoDisplay?.isDisplayed;
    if (chat.type === 'group') {
        GLOBAL.infoDisplay = new ChatInfoDisplay(chatId);
        if (prevInfoShown)
            GLOBAL.infoDisplay.display();
    } else {
        GLOBAL.infoDisplay?.hide();
        GLOBAL.infoDisplay = null;
    }
    this.classList.add(GLOBAL.activeChatClassName);
    $(GLOBAL.middleSectionInsvisibleSelector).removeClass(GLOBAL.invisibleClassName);
    GLOBAL.activeChatDisplay = new ChatMessagesDisplay(chatId);
    GLOBAL.activeChatDisplay.display();
    $('#editable-message-text').focus();
});

$('input#search').on('input', async function() {
    // display chats found by certain query
    const text = this.value.trim();
    if (!text) {
        if (ChatListDisplay.isSearchDisplayed())
            ChatListDisplay.hideSearch();
    } else 
        ChatListDisplay.displaySearch(
            await Api.getChats(text, -1)
        );
});

$('div#middle-header').click(function() {
    GLOBAL.infoDisplay?.toggle();
});

$('button#hide-right').click(function() {
    GLOBAL.infoDisplay?.hide();
});

$('#add-member').click(function() {
    const dialog = new AddChatMembersDialog(
        GLOBAL.activeChatDisplay.chat
    )
    dialog.success(function (event, userId) {
        GLOBAL.socket.emit('join_chat', {
            user_id: userId, chat_id: dialog.chat.id
        });
    }).oninput(async function(event, title) {
        let users;
        if (title === '')
            users = GLOBAL.state.getUsers();
        else
            users = await Api.getUsers(title, -1)
        dialog.setUsers(users);
    }).display();
    dialog.setUsers(GLOBAL.state.getUsers());
});

$('#create-private').click(function() {
    const dialog = new CreatePrivateChatDialog();
    dialog.checkUser = function(user) {
        return GLOBAL.state.getPrivateChatByUser(user.id) === undefined
    };
    dialog.success(function (event, userId) {
        GLOBAL.socket.emit('create_private', {
            user_id: userId
        });
    }).oninput(async function(event, title) {
        let users;
        if (title === '')
            users = GLOBAL.state.getUsers();
        else
            users = await Api.getUsers(title, -1)
        dialog.setUsers(users);
    }).display();
    dialog.setUsers(GLOBAL.state.getUsers());    
});

$('button#create-group').click(function() {
    new CreateGroupNameDialog().success(function(event, title) {
        GLOBAL.socket.emit('create_group', {title: title});
    }).display() 
});

$(window).blur(function() {
    // send request to update last_online
    GLOBAL.socket.emit('is_offline');
});
$(window).focus(function() {
    // send request to set online status
    GLOBAL.socket.emit('is_online'); 
});

$('#editable-message-text').on('input', function() {
    ChatMessagesDisplay.scrollMessagesToBottom();
})

$('button#send-button').click(function() {
    const input = $('#editable-message-text')[0];
    const text = input.innerText.trim();
    if (!text)
        return;
    GLOBAL.messageAction.send(text);
    ChatMessagesDisplay.clearMessageAction();
    GLOBAL.messageAction = null;
    input.innerHTML = '';
});


$('#chat-messages').scroll(async function() {
    const chatId = GLOBAL.activeChatDisplay?.chatId;
    if (!chatId) return;
    const chatMessagesScrollTop = $('#chat-messages')[0].scrollTop;
    if (chatMessagesScrollTop > 500 || GLOBAL.previousScrollPosition < chatMessagesScrollTop) return;
    if (GLOBAL.isLoadingMessages) return;
    GLOBAL.previousScrollPosition = chatMessagesScrollTop;
    GLOBAL.isLoadingMessages = true;
    const totalMessageCount = GLOBAL.state.getChatMessages(chatId).length;
    const displayedMessageCount = GLOBAL.activeChatDisplay.length;
    if (displayedMessageCount === totalMessageCount) {
        const messagePage = Math.ceil(totalMessageCount / GLOBAL.messageAPILength) + 1;
        let messages = await Api.getChatMessages(chatId, messagePage);
        if (messages.length === 0) {
            GLOBAL.isLoadingMessages = false;
            return;
        }
        GLOBAL.state.unshiftMessages(messages);
        GLOBAL.state.save();
    }
    const firstMessageId = parseInt(
        GLOBAL.activeChatDisplay.firstMessage.getAttribute('data-message-id')
    );
    const messages = GLOBAL.state.getChatMessages(chatId);
    const firstMessageIndex = messages.findIndex(
        element => element.id === firstMessageId
    );
    for (let i = firstMessageIndex - 1; i >= Math.max(0, firstMessageIndex - GLOBAL.messageAPILength); i--) {
        GLOBAL.activeChatDisplay.insertMessage(messages[i]);
    }
    GLOBAL.isLoadingMessages = false;
});


GLOBAL.socket.on('message', async function(message) {
    GLOBAL.state.appendMessage(message);
    GLOBAL.state.save();
    if (message.chat === GLOBAL.activeChatDisplay?.chatId) {
        await GLOBAL.activeChatDisplay.addMessage(message);
        ChatMessagesDisplay.scrollMessagesToBottom();
    } else {
        const chat = GLOBAL.state.getChat(message.chat);
        chat.unreadMessagesCount = Math.max(0, chat.unreadMessagesCount) + 1;
        GLOBAL.state.save();
    }
    ChatListDisplay.updateChat(message.chat);
    ChatListDisplay.moveToTop(message.chat);
});

GLOBAL.socket.on('update_user_status', function(data) {
    if (!GLOBAL.state.userExists(data.user_id)) return;
    GLOBAL.state.getUser(data.user_id).last_online = data.last_online;
    GLOBAL.state.save();
    if (GLOBAL.activeChatDisplay?.chat.members.includes(data.user_id))
        GLOBAL.activeChatDisplay.updateStatus();
        GLOBAL.infoDisplay?.updateOnlineCount();
        GLOBAL.infoDisplay?.updateUserStatus(
            data.user_id, data.last_online === null
        );
});

GLOBAL.socket.on('update_view', function(data) {
    const message = GLOBAL.state.getMessage(data.chat_id, data.message_id);
    if (!message) return;
    message.seen_by.push(data.user_id);
    GLOBAL.state.save();
    ChatListDisplay.updateChat(message.chat);
    if (GLOBAL.activeChatDisplay?.chatId !== data.chat_id) return;
    if (GLOBAL.activeChatDisplay.isMessageDisplayed(data.message_id) && 
        message.from_user === GLOBAL.state.currentUserId && !message.is_service)
        GLOBAL.activeChatDisplay.setMessageAsViewed(data.message_id);
});

GLOBAL.socket.on('delete_message', function(data) {
    const message = GLOBAL.state.getMessage(data.chat_id, data.message_id);
    if (!message) return;
    const chat = GLOBAL.state.getChat(data.chat_id);
    if (!message.seen_by.includes(GLOBAL.state.currentUserId))
        chat.unreadMessagesCount = Math.max(1, chat.unreadMessagesCount) - 1;
    GLOBAL.state.removeMessage(chat.id, message.id);
    GLOBAL.state.save();
    ChatListDisplay.updateChat(chat.id);
    if (GLOBAL.activeChatDisplay?.chatId !== data.chat_id) return;
    if (GLOBAL.activeChatDisplay.isMessageDisplayed(data.message_id))
        GLOBAL.activeChatDisplay.deleteMessage(message);
});

GLOBAL.socket.on('edit_message', function(data) {
    const message = GLOBAL.state.getMessage(data.chat_id, data.message_id);
    if (!message) return;
    message.edited_at = data.edited_at; message.text = data.text;
    GLOBAL.state.save();
    ChatListDisplay.updateChat(message.chat);
    if (GLOBAL.activeChatDisplay?.chatId !== data.chat_id) return;
    if (GLOBAL.activeChatDisplay.isMessageDisplayed(data.message_id))
        GLOBAL.activeChatDisplay.updateMessage(message);
});

GLOBAL.socket.on('add_chat', async function(data) {
    data.unreadMessagesCount = await Api.getUnreadMessagesCount(
        data.id, GLOBAL.state.currentUserId
    );
    const messages = await Api.getChatMessages(data.id);
    if (data.type === 'private') {
        const companionUserId = data.members.find(
            el => el !== GLOBAL.state.currentUserId
        );
        let companionUser = GLOBAL.state.getUser(companionUserId);
        if (!companionUser) {
            companionUser = await Api.getUser(companionUserId);
            GLOBAL.state.appendUser(companionUser);
        }
        data.title = companionUser.username;
    }
    GLOBAL.state.appendChat(data);
    GLOBAL.state.pushMessages(messages);
    GLOBAL.state.save();
    ChatListDisplay.insertChat(data.id);
});

GLOBAL.socket.on('add_member', function(data) {
    if (!GLOBAL.state.userExists(data.user.id)) 
        GLOBAL.state.appendUser(data.user);
    GLOBAL.state.appendMember(data.chat_id, data.user.id);
    GLOBAL.state.save();
    GLOBAL.activeChatDisplay.updateStatus();
    GLOBAL.infoDisplay?.addUser(data.user);
    GLOBAL.infoDisplay?.updateStatus();
});

GLOBAL.socket.on('remove_chat', function(data) {
    GLOBAL.state.removeChat(data.chat_id);
    GLOBAL.state.save()
    if (GLOBAL.activeChatDisplay?.chatId === data.chat_id) {
        GLOBAL.infoDisplay?.hide();
        GLOBAL.infoDisplay = null;
        hideActiveChat();
    }
    ChatListDisplay.removeChat(data.chat_id);
});

GLOBAL.socket.on('remove_member', function(data) {
    GLOBAL.state.removeMember(data.chat_id, data.user_id);
    GLOBAL.activeChatDisplay.updateStatus();
    if (GLOBAL.infoDisplay?.isUserDisplayed(data.user_id)) 
        GLOBAL.infoDisplay?.removeUser(data.user_id);
});
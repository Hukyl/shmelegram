import ordinalLast from '../utils/main.js'


class Dialog {
    _cancelFunc = function() {};
    _successFunc = function() {};

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
        node.addEventListener('hidden.bs.modal', Dialog.hide);
    }

    success(func) {
        this._successFunc = func;
        return this;
    }

    cancel(func) {
        this._cancelFunc = func;
        return this;
    }

    static hide() {
        for (let modal of $('#portals .modal')) {
            bootstrap.Modal.getOrCreateInstance(modal).hide();
        }
        setTimeout(function() {
            $('div#portals')[0].innerHTML = '';
        }, 100);
    }
}

export class DeleteMessageDialog extends Dialog {
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
            this._successFunc(event); Dialog.hide();
        }.bind(this);
        const buttonCancel = document.createElement('button');
        buttonCancel.className = 'btn btn-secondary';
        buttonCancel.innerText = 'Cancel';
        buttonCancel.setAttribute('data-bs-dismiss', 'modal');
        buttonCancel.onclick = function(event) {
            this._cancelFunc(event); Dialog.hide();
        }.bind(this);
        body.appendChild(p); 
        footer.appendChild(buttonConfirm);
        footer.appendChild(buttonCancel);
        return node;
    }
}

export class LeaveChatDialog extends Dialog {
    constructor(isPrivate) {
        super();
        this.isPrivate = isPrivate;
    }

    createNode() {
        const node = super.createNode();
        const body = node.querySelector('.modal-body');
        const footer = node.querySelector('.modal-footer');
        const title = document.createElement('h5');
        title.innerText = (
            this.isPrivate ? `Are you sure you want to delete chat?`
            : 'Are you sure you want to leave the group?'
        );
        const buttonConfirm = document.createElement('button');
        buttonConfirm.className = 'btn btn-danger';
        buttonConfirm.innerText = 'Delete';
        buttonConfirm.onclick = function(event) {
            this._successFunc(event); Dialog.hide();
        }.bind(this);
        const buttonCancel = document.createElement('button');
        buttonCancel.className = 'btn btn-secondary';
        buttonCancel.innerText = 'Cancel';
        buttonCancel.setAttribute('data-bs-dismiss', 'modal');
        buttonCancel.onclick = function(event) {
            this._cancelFunc(event); Dialog.hide();
        }.bind(this);
        body.appendChild(title);
        footer.appendChild(buttonConfirm);
        footer.appendChild(buttonCancel);
        return node;
    }
}

export class CreateGroupNameDialog extends Dialog {
    createNode() {
        const node = super.createNode();
        const title = node.querySelector('.modal-title');
        title.innerText = 'New group title';
        const body = node.querySelector('.modal-body');
        const footer = node.querySelector('.modal-footer');
        const titleInput = document.createElement('input');
        titleInput.className = 'form-control';
        titleInput.onchange = function(event) {
            event.target.classList.remove('validation-error');
        }
        const buttonConfirm = document.createElement('button');
        buttonConfirm.className = 'btn btn-primary';
        buttonConfirm.innerText = 'Create';
        buttonConfirm.onclick = function(event) {
            const title = titleInput.value.trim();
            if (title) {
                this._successFunc(event, title); Dialog.hide();
            } else {
                titleInput.classList.add('validation-error');
            }
        }.bind(this);
        const buttonCancel = document.createElement('button');
        buttonCancel.className = 'btn btn-secondary';
        buttonCancel.innerText = 'Cancel';
        buttonCancel.setAttribute('data-bs-dismiss', 'modal');
        buttonCancel.onclick = function(event) {
            this._cancelFunc(event); Dialog.hide();
        }.bind(this);
        body.appendChild(titleInput);
        footer.appendChild(buttonConfirm);
        footer.appendChild(buttonCancel);
        return node;
    }
}

class GetUserIdDialog extends Dialog {
    _node = null;
    _inputFunc = function() {};

    oninput(func) {
        this._inputFunc = func;
        return this;
    }

    _createUser(user) {
        const memberDiv = document.createElement('div');
        memberDiv.className = 'user';
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
        titleDiv.appendChild(username);
        info.appendChild(titleDiv);
        memberDiv.appendChild(avatar);
        memberDiv.appendChild(info);
        return memberDiv;
    }    

    createNode() {
        const node = super.createNode();
        node.querySelector('.modal-dialog').classList.add(
            'modal-sm', 'modal-add-members'
        );
        const header = node.querySelector('.modal-header');
        const body = node.querySelector('.modal-body');
        const footer = node.querySelector('.modal-footer');
        const headerName = document.createElement('h4');
        headerName.innerText = 'Get user';
        const search = document.createElement('input');
        search.placeholder = 'Query'
        search.className = 'form-control';
        search.oninput = function(event) {
            this._inputFunc(event, search.value.trim());
        }.bind(this);
        const userList = document.createElement('div');
        userList.className = 'list user-list custom-scroll';
        const buttonConfirm = document.createElement('button');
        buttonConfirm.className = 'btn btn-primary';
        buttonConfirm.innerText = 'Add';
        buttonConfirm.onclick = function(event) {
            const userId = parseInt(
                node.querySelector('.selected').getAttribute('data-user-id')
            );
            if (userId)
                this._successFunc(event, userId);
            else 
                this._cancelFunc(event)
            Dialog.hide();
        }.bind(this);
        const buttonCancel = document.createElement('button');
        buttonCancel.className = 'btn btn-secondary';
        buttonCancel.innerText = 'Cancel';
        buttonCancel.setAttribute('data-bs-dismiss', 'modal');
        buttonCancel.onclick = function(event) {
            this._cancelFunc(event); Dialog.hide();
        }.bind(this);
        header.appendChild(headerName);
        body.appendChild(search);
        body.appendChild(userList);
        footer.appendChild(buttonConfirm);
        footer.appendChild(buttonCancel);
        this._node = node;
        return node;
    }

    setUsers(users) {
        const userList = $(this._node.querySelector('.user-list'));
        const clickEvent = function(event) {
            this._node.querySelector(
                '.selected'
            )?.classList.remove('selected');
            event.target.classList.add('selected');
        }.bind(this)
        userList.empty();
        let userDiv;
        for (let user of users) {
            if (!this.checkUser(user)) continue;
            userDiv = this._createUser(user);
            userDiv.onclick = clickEvent;
            userList.append(userDiv);
        }
    }

    checkUser(user) { return true; }
}

export class AddChatMembersDialog extends GetUserIdDialog {
    constructor(chat) {
        super();
        this.chat = chat;
    }

    createNode() {
        const node = super.createNode();
        node.querySelector('h4').innerText = 'Add members';
        return node;
    }

    checkUser(user) { return !this.chat.members.includes(user.id); }
}

export class CreatePrivateChatDialog extends GetUserIdDialog {
    createNode() {
        const node = super.createNode();
        node.querySelector('h4').innerText = 'Create private';
        return node;
    }
}
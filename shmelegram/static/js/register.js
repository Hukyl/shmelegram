let form = $('form#main')[0];

$('input#username').on('input', function() {
    let self = $(this)[0];
    self.classList.remove('is-invalid');
    self.classList.remove('is-valid');
});
$('input#username').blur(function() {
    let self = $(this)[0];
    let isValid = validateUsername(self.value);
    let className = (isValid ? 'is-valid' : 'is-invalid');
    self.classList.add(className);
});

$('input#password').on('input', function() {
    let self = $(this)[0];
    self.classList.remove('is-invalid');
    self.classList.remove('is-valid');        
    // form.classList.remove('was-validated');
});
$('input#password').blur(function() {
    let self = $(this)[0];
    let isValid = validatePassword(self.value);
    let className = (isValid ? 'is-valid' : 'is-invalid');
    self.classList.add(className);
});

function validateUsername(username) {
    return /^[\x00-\xFF]{5,29}$/.test(username);
}

function validatePassword(password) {
    let only_ascii = /^[\x00-\xFF]{7,14}$/.test(password);
    let least_one_lower = password.toUpperCase() !== password;
    let least_one_upper = password.toLowerCase() !== password;
    let least_one_digit = /\d+/.exec(password) !== null;
    let least_one_punctuation = /[!"#$%&\'()*+,-./:;<=>?@[\\\]\^\_\`\{\|\}\~]+/.exec(password) !== null;
    return Boolean(
        only_ascii && least_one_digit && least_one_lower 
        && least_one_upper && least_one_punctuation
    );
}

$(document).ready(function() {
    $('input#submit').click(function() {
        let usernameField = form[0], passwordField = form[1];
        if (!username.value || !password.value) {
            username.classList.add('is-invalid');
            form.classList.add('was-validated');
            event.preventDefault();
            event.stopPropagation();                 
        } else {
            form.submit();
        }                   
    });
});
document.addEventListener('DOMContentLoaded', () => {
  const passwordField = document.querySelector('input[name="password"]');
  
  passwordField.addEventListener('focus', () => {
    console.log('Password field focused'); // Example behavior
  });
});

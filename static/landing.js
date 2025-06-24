const text = "HawkEye: AI That Never Blinks";
const speed = 100; // typing speed in ms
let index = 0;
let isDeleting = false;
let typed = "";
const typedTextElement = document.getElementById("typed-text");

function typeEffect() {
  if (!isDeleting) {
    typed += text.charAt(index);
    index++;
    if (index >= text.length) {
      isDeleting = true;
      setTimeout(typeEffect, 1500); // pause at full text
      return;
    }
  } else {
    typed = typed.slice(0, -1);
    index--;
    if (index <= 0) {
      isDeleting = false;
    }
  }

  typedTextElement.textContent = typed;
  setTimeout(typeEffect, isDeleting ? speed / 2 : speed);
}

typeEffect();

// Add click event for 'See It in Action' button
document.getElementById('see-action-btn').addEventListener('click', function() {
  window.location.href = '/app';
});


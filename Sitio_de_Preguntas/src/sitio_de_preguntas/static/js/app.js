document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-password-toggle]").forEach((button) => {
    const input = document.getElementById(button.dataset.passwordToggle);
    if (!input) return;

    button.addEventListener("click", () => {
      const eraVisible = input.type === "text";
      input.type = eraVisible ? "password" : "text";
      button.setAttribute("aria-pressed", String(!eraVisible));
      button.setAttribute(
        "aria-label",
        eraVisible ? "Mostrar contraseña" : "Ocultar contraseña"
      );
    });
  });
});

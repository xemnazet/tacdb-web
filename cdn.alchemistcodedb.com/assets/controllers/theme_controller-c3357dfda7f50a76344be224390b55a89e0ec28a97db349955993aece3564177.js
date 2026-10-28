import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
  connect() {
    setTheme(getPreferredTheme());
    const theme = document.body.getAttribute("data-bs-theme");
    showActiveTheme(theme, false);
    this.colorScheme = window.matchMedia("(prefers-color-scheme: dark)");
    this.colorScheme.addEventListener("change", updatePreferredTheme);
  }

  disconnect() {
    this.colorScheme?.removeEventListener("change", updatePreferredTheme);
  }

  updateTheme(e) {
    e.preventDefault();
    const theme = e.currentTarget.getAttribute("data-bs-theme-value");
    setStoredTheme(theme);
    setTheme(theme);
    showActiveTheme(theme, true);
  }
}

const getStoredTheme = () => {
  const theme = localStorage.getItem("theme");
  return ["light", "dark", "auto"].includes(theme) ? theme : null;
};
const setStoredTheme = theme => localStorage.setItem("theme", theme);

const setTheme = theme => {
  document.body.className = "";
  if (theme == "auto") {
    document.body.classList.add((window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"));
    document.body.setAttribute("data-bs-theme", (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"));
  }
  else {
    document.body.classList.add(theme);
    document.body.setAttribute("data-bs-theme", theme);
  }
}

const getPreferredTheme = () => {
  const storedTheme = getStoredTheme();
  if (storedTheme) {
    return storedTheme;
  }

  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

const updatePreferredTheme = () => {
  const storedTheme = getStoredTheme()
  if (storedTheme != "light" && storedTheme != "dark") {
    setTheme(getPreferredTheme());
  }
}

const showActiveTheme = (theme, focus = false) => {
  const themeSwitcher = document.querySelector("#themeDropDown");

  if (!themeSwitcher) {
    return;
  }

  const activeThemeIcon = document.querySelector("#themeDropDown i");
  const btnToActive = Array.from(document.querySelectorAll("[data-bs-theme-value]"))
    .find((button) => button.getAttribute("data-bs-theme-value") === theme);
  if (!activeThemeIcon || !btnToActive) {
    return;
  }

  document.querySelectorAll("a[data-bs-theme-value] .fa-check").forEach(iconEl => {
    iconEl.classList.add("d-none");
  });

  btnToActive.querySelector(".fa-check")?.classList.remove("d-none");
  const themeIcon = btnToActive.querySelector("i");
  if (themeIcon) {
    activeThemeIcon.className = themeIcon.classList.toString();
  }
  activeThemeIcon.classList.remove("fa-fw", "me-2");

  if (focus) {
    themeSwitcher.focus();
  }
};

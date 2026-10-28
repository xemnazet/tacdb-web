import { Controller } from "@hotwired/stimulus"
import "tippy"

export default class extends Controller {
  connect() {
    this.tippyElements.forEach(element => {
      if (element._tippy) {
        return;
      }
      tippy(element, {
        theme: "info",
      });
    });
  }

  get tippyElements() {
    return this.element.matches("[data-tippy-content]")
      ? [this.element, ...this.element.querySelectorAll("[data-tippy-content]")]
      : this.element.querySelectorAll("[data-tippy-content]");
  }
};

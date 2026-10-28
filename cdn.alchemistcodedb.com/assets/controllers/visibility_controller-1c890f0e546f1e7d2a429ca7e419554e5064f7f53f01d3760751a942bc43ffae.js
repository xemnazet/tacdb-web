import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
  static targets = ["hideable"]

  toggleTargets(e) {
    e.preventDefault();
    this.hideableTargets.forEach((el) => {
      el.hidden = !el.hidden;
    });
    const trigger = e.currentTarget;
    if(trigger.textContent.trim() == "[+]") {
      trigger.textContent = "[-]";
    }
    else {
      trigger.textContent = "[+]"
    }
  }

  toggleRows(e) {
    e.preventDefault();
    this.hideableTargets.forEach((el) => {
      el.hidden = !el.hidden;
    });
    const trigger = e.currentTarget;
    if(trigger.textContent.trim() == "Show More") {
      trigger.textContent = "Show Less";
    }
    else {
      trigger.textContent = "Show More";
    }
  }

  toggleText(e) {
    const trigger = e.currentTarget;
    const collapseText = trigger.getAttribute("data-text");
    if(!collapseText) {
      return;
    }
    if(trigger.textContent.trim().startsWith("Show")) {
      trigger.textContent = "Hide " + collapseText;
    }
    else {
      trigger.textContent = "Show " + collapseText;
    }
  }

  toggleTabs(e) {
    const mainList = document.querySelectorAll(".main-collapse");
    mainList.forEach(mainEl => {
      if(!mainEl.classList.contains("show")) {
        const childList = mainEl.querySelectorAll("a[aria-expanded='true']");
        childList.forEach(childEl => {
          childEl.click();
        });
      }
    });
    const skillId = e.currentTarget.getAttribute("data-insp-skill");
    const triggerTab = document.getElementById("it" + skillId);
    const skillTab = document.getElementById("is" + skillId);
    if(!triggerTab || !skillTab) {
      return;
    }
    if(!triggerTab.classList.contains("active")) {
      const triggerTabList = document.querySelectorAll("#triggerTabsContent .tab-pane");
      triggerTabList.forEach(triggerEl => {
        triggerEl.classList.remove("show", "active");
      });
      triggerTab.classList.add("show", "active");
    }
    if(!skillTab.classList.contains("active")) {
      const skillTabList = document.querySelectorAll("#inspTabsContent .tab-pane");
      skillTabList.forEach(skillEl => {
        skillEl.classList.remove("show", "active");
      });
      skillTab.classList.add("show", "active");
    }
  }
};

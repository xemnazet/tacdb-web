import { Controller } from "@hotwired/stimulus"
import { Tab } from "bootstrap"

export default class extends Controller {
  connect() {
    this.tabTriggers = Array.from(
      document.querySelectorAll("a[data-bs-toggle='list'], a[data-bs-toggle='tab']")
    );
    this.tabClickHandlers = new Map();
    this.tabTriggers.forEach((trigger) => {
      const handler = (event) => this.clickTab(event, trigger);
      this.tabClickHandlers.set(trigger, handler);
      trigger.addEventListener("click", handler);
    });

    this.jobIcons = Array.from(document.querySelectorAll(".job-tab"));
    this.jobIconClickHandlers = new Map();
    this.jobIcons.forEach((icon) => {
      const handler = (event) => this.clickIcon(event, icon);
      this.jobIconClickHandlers.set(icon, handler);
      icon.addEventListener("click", handler);
    });

    this.hashChangeHandler = () => this.showHash(location.hash || "#stats");
    window.addEventListener("hashchange", this.hashChangeHandler);
    this.showHash(location.hash);
  }

  disconnect() {
    this.tabClickHandlers.forEach((handler, trigger) => {
      trigger.removeEventListener("click", handler);
    });
    this.jobIconClickHandlers.forEach((handler, icon) => {
      icon.removeEventListener("click", handler);
    });
    window.removeEventListener("hashchange", this.hashChangeHandler);
  }

  clickTab(event, trigger) {
    event.preventDefault();
    const target = this.targetFor(trigger);
    if (!target) {
      return;
    }

    let currentTarget = target;
    const targetId = target.slice(1);
    if (["jobs", "equipment", "enlightenment"].includes(targetId)) {
      this.show(trigger);
      const tabListIds = {
        jobs: "jobTabs",
        equipment: "equipmentTabs",
        enlightenment: "enlightenmentTabs",
      };
      const firstTab = document.querySelector(`#${tabListIds[targetId]} li:first-child a`);
      if (firstTab) {
        this.show(firstTab);
        currentTarget = this.targetFor(firstTab) || currentTarget;
      }
    } else {
      this.show(trigger);
    }

    if (trigger.getAttribute("data-bs-toggle") === "list") {
      document.getElementById(targetId)?.scrollIntoView({ block: "start" });
    }
    this.updateHash(currentTarget);
  }

  clickIcon(event, icon) {
    event.preventDefault();
    const jobTarget = icon.getAttribute("href");
    const mainTab = this.findTrigger("#jobs");
    const jobTab = this.findTrigger(jobTarget);
    if (!mainTab || !jobTab) {
      return;
    }

    this.show(mainTab);
    this.show(jobTab);
    document.getElementById("jobs")?.scrollIntoView({ block: "start" });
    this.updateHash(jobTarget);
  }

  showHash(hash) {
    if (!hash) {
      return;
    }
    if (hash.includes("equipment")) {
      this.show(this.findTrigger("#equipment"));
    } else if (hash.includes("gate")) {
      this.show(this.findTrigger("#enlightenment"));
    } else if (hash.startsWith("#j")) {
      this.show(this.findTrigger("#jobs"));
    }
    this.show(this.findTrigger(hash));
  }

  findTrigger(target) {
    return this.tabTriggers.find((trigger) => this.targetFor(trigger) === target);
  }

  targetFor(trigger) {
    return trigger?.getAttribute("data-bs-target") || trigger?.getAttribute("href");
  }

  show(trigger) {
    if (trigger) {
      Tab.getOrCreateInstance(trigger).show();
    }
  }

  updateHash(target) {
    if (target && history.replaceState) {
      history.replaceState(history.state, "", target);
    } else if (target) {
      location.hash = target;
    }
  }
}

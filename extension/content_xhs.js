// Force-enable right-click on Xiaohongshu and surface background-image
// elements as a synthetic <img> so Chrome's contextMenus image context fires.

(() => {
  // 1. Stop the page from swallowing contextmenu / selectstart / copy.
  ["contextmenu", "selectstart", "copy", "dragstart"].forEach((evt) => {
    window.addEventListener(
      evt,
      (e) => e.stopImmediatePropagation(),
      { capture: true }
    );
  });

  // 2. Walk up from the right-clicked element. If the visible image is a
  //    CSS background-image (div), inject a transparent overlay <img> so
  //    Chrome treats the click as an image-context click.
  document.addEventListener(
    "contextmenu",
    (e) => {
      const target = e.target;
      if (!target || target.tagName === "IMG") return;
      let node = target;
      let depth = 0;
      while (node && depth < 6) {
        const bg = getComputedStyle(node).backgroundImage;
        const m = bg && bg.match(/url\(["']?(https?:[^"')]+)["']?\)/);
        if (m) {
          const url = m[1];
          const r = node.getBoundingClientRect();
          let overlay = node.querySelector(":scope > .__xphoto_overlay");
          if (!overlay) {
            overlay = document.createElement("img");
            overlay.className = "__xphoto_overlay";
            overlay.src = url;
            overlay.style.cssText = `
              position: absolute;
              left: 0; top: 0;
              width: 100%; height: 100%;
              opacity: 0.001;
              pointer-events: auto;
              z-index: 999999;
            `;
            const cs = getComputedStyle(node);
            if (cs.position === "static") node.style.position = "relative";
            node.appendChild(overlay);
          } else {
            overlay.src = url;
          }
          // Don't preventDefault — let the native right-click menu fire on the overlay.
          return;
        }
        node = node.parentElement;
        depth++;
      }
    },
    { capture: true }
  );
})();

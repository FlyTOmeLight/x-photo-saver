const HOST_NAME = "com.x.photosaver";
const MENU_SAVE = "save-x-image-to-photos";
const MENU_DEBUG = "save-x-image-to-photos-debug";

chrome.runtime.onInstalled.addListener(() => {
  const docs = [
    "https://x.com/*",
    "https://twitter.com/*",
    "https://*.xiaohongshu.com/*",
    "https://xiaohongshu.com/*"
  ];
  chrome.contextMenus.create({
    id: MENU_SAVE,
    title: "Save image to Photos",
    contexts: ["image"],
    documentUrlPatterns: docs
  });
  chrome.contextMenus.create({
    id: MENU_DEBUG,
    title: "Save (debug info)",
    contexts: ["image"],
    documentUrlPatterns: docs
  });
});

function fmtBytes(n) {
  if (!n) return "?";
  if (n < 1024) return `${n}B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)}KB`;
  return `${(n / 1024 / 1024).toFixed(2)}MB`;
}

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId !== MENU_SAVE && info.menuItemId !== MENU_DEBUG) return;
  const debug = info.menuItemId === MENU_DEBUG;
  const payload = {
    srcUrl: info.srcUrl,
    pageUrl: info.pageUrl || (tab && tab.url) || ""
  };
  chrome.runtime.sendNativeMessage(HOST_NAME, payload, (response) => {
    const err = chrome.runtime.lastError;
    const title = "X Photo Saver";
    let message;
    if (err) {
      message = `Error: ${err.message}`;
    } else if (response && response.ok) {
      if (debug) {
        message = `OK ${response.format || "?"} ${fmtBytes(response.bytes)}\n${response.url || ""}`;
      } else {
        message = `Saved (${response.format || "?"} ${fmtBytes(response.bytes)})`;
      }
    } else {
      message = `Failed: ${(response && response.error) || "unknown"}`;
    }
    if (debug) console.log("[X Photo Saver]", { payload, response, err });
    chrome.notifications.create({
      type: "basic",
      iconUrl: "icon.png",
      title,
      message
    });
  });
});

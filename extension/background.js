// Context-menu entry: right-click selected text, a link, or an image's page.
// The text is held in session storage only until the popup reads and clears it.
const MENU = "rakshalens-check";

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: MENU,
    title: "Check with RakshaLens",
    contexts: ["selection", "link"],
  });
});

chrome.contextMenus.onClicked.addListener(async (info) => {
  if (info.menuItemId !== MENU) return;
  const text = info.selectionText || info.linkUrl || "";
  if (!text) return;
  await chrome.storage.session.set({ pending: text.slice(0, 8000) });
  chrome.windows.create({ url: chrome.runtime.getURL("popup.html?pending=1"), type: "popup", width: 420, height: 640 });
});

// This file can be imported inside the service worker,
// which means all of its functions and variables will be accessible
// inside the service worker.
// The importation is done in the file `service-worker.js`.

console.log("External file is also loaded!")

chrome.runtime.onInstalled.addListener(async () => {
    chrome.contextMenus.create({
        id: 'label-data',
        title: 'label',
        type: 'normal',
        contexts: ['selection'],
    });
});

chrome.contextMenus.onClicked.addListener(async (info, tab)=>{
    if (info.menuItemId == 'label-data'){
        // pass selection text to the message listener on the source page
        console.log('right click: label-data')
        chrome.tabs.sendMessage(tab.id, {'type': 'label-data', 'text': info.selectionText}, (rsp)=>{
            console.log('right click: label-data --', rsp)
        })
    }
})
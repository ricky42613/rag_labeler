// This is the service worker script, which executes in its own context
// when the extension is installed or refreshed (or when you access its console).
// It would correspond to the background script in chrome extensions v2.

console.log("This prints to the console of the service worker (background script)")

// Importing and using functionality from external files is also possible.
importScripts('service-worker-login.js')
importScripts('service-worker-contextmenu.js')

// If you want to import a file that is deeper in the file hierarchy of your
// extension, simply do `importScripts('path/to/file.js')`.
// The path should be relative to the file `manifest.json`.

function update_tags(){
    return new Promise(function(resolve, reject){
        chrome.storage.sync.get(["ragTags"]).then((result) => {
            let ragTags = []
            if(result.hasOwnProperty("ragTags") == true) {
                ragTags = result.ragTags
            }
            let headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
            let data = {'tags': ragTags}
            fetch('http://127.0.0.1:8888/api/tags', {
                method: 'POST',
                headers: headers,
                body: JSON.stringify(data)
            }).then(r=>r.json()).then(rsp=>{
                resolve(rsp)
            }).catch(e=>{
                resolve({'status': 500, 'msg': e})
            })
        });
    })
}

chrome.runtime.onInstalled.addListener(async function(details){
    console.log('Installed rag-labeler!')
    rsp = await update_tags()
    console.log('update tags info: ', rsp)
})

chrome.runtime.onMessage.addListener(function(msg, sender, sendResponse){
    if (msg.type == 'save-label-data'){
        msg.data.user = USER
        let headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        fetch('http://127.0.0.1:8888/api/data', {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(msg.data)
        }).then(r=>r.json()).then(rsp=>{
            if (rsp.status == 200){
                sendResponse({'status': 200})
            }else{
                sendResponse({'status': 500})
            }
        }).catch(async e=>{
            console.log(e)
            sendResponse({'status': 500})
        })
    }
    else if (msg.type == 'add-tag'){
        chrome.storage.sync.get(["ragTags"]).then((result) => {
            let ragTags = []
            if(result.hasOwnProperty("ragTags") == true) {
                ragTags = result.ragTags
            }
            if (ragTags.indexOf(msg.tag) == -1){
                ragTags.push(msg.tag)
            }
            chrome.storage.sync.set({ 'ragTags': ragTags }).then(async() => {
                rsp = await update_tags()
                console.log('update tags info: ', rsp)
                sendResponse({'status': 200, 'tags': ragTags})
            });
        });
    }
    else if (msg.type == 'get-tags'){
        chrome.storage.sync.get(["ragTags"]).then((result) => {
            let ragTags = []
            if(result.hasOwnProperty("ragTags") == true) {
                ragTags = result.ragTags
            }
            console.log(ragTags)
            sendResponse({'status': 200, 'tags': ragTags})
        });
    }
    else if (msg.type == 'del-tags'){
        chrome.storage.sync.get(["ragTags"]).then((result) => {
            let ragTags = []
            if(result.hasOwnProperty("ragTags") == true) {
                ragTags = result.ragTags
            }
            let delIdx = ragTags.indexOf(msg.tag)
            if (delIdx != -1){
                ragTags.splice(delIdx, 1)
            }
            chrome.storage.sync.set({ 'ragTags': ragTags }).then(async() => {
                rsp = await update_tags()
                console.log('update tags info: ', rsp)
                sendResponse({'status': 200, 'tags': ragTags})
            });
        });
    }
    return true
})
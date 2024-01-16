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

chrome.runtime.onMessage.addListener(function(msg, sender, sendResponse){
    if (msg.type == 'save-label-data'){
        msg.data.user = USER
        let headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        fetch('http://127.0.0.1:8000/api/data', {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(msg.data)
        }).then(r=>r.json()).then(rsp=>{
            if (rsp.status == 200){
                sendResponse({'status': 200})
            }else{
                sendResponse({'status': 500})
            }
        }).catch(e=>{
            console.log(e)
            sendResponse({'status': 500})
        })
    }
    return true
})
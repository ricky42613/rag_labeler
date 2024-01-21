// This script gets injected into any opened page
// whose URL matches the pattern defined in the manifest
// (see "content_script" key).
// Several foreground scripts can be declared
// and injected into the same or different pages.


(function () {
    console.log("This prints to the console of the page (injected only if the page url matched)")
    chrome.runtime.onMessage.addListener(async (msg, sender, sendResponse)=>{
        if(msg.type == 'label-data') {
            sendResponse({'status': 200})
            $('.ui.modal').modal('show')
            document.querySelector('.rag-context').value = msg.text
        }
    })
    window.onload = async function() {
        function get_tags(){
            return new Promise(function(resolve, reject){
                chrome.runtime.sendMessage({'type': 'get-tags'}, function(rsp){
                    if (rsp.status == 200){
                        resolve(rsp.tags)
                    }else{
                        resolve([])
                    }
                })
            })
        }
        let tags = await get_tags()
        let tags_dropdown = tags.map(item=>{
            return `<option value="${item}">${item}</option>`
        })
        modal = `
        <div class="ui modal">
            <div class="header">Knowledge Editor</div>
            <div class="content">
                <div class="ui form">
                    <div class="field">
                        <label>Tags</label>
                        <select multiple="" name="tags" class="tags ui search fluid normal dropdown">
                            ${tags_dropdown.join('')}
                        </select>
                    </div>
                    <div class="field">
                        <label>Context</label>
                        <textarea class="rag-context" spellcheck="false"></textarea>
                    </div>
                    <div class="field">
                        <label>Question</label>
                        <textarea class="rag-question" rows="2"></textarea>
                    </div>
                    <div class="field">
                        <label>Answer</label>
                        <textarea class="rag-answer" rows="2"></textarea>
                    </div>
                </div>
            </div>
            <div class="actions">
                <div class="ui cancel button">Cancel</div>
                <div class="ui rag-save button">Save</div>
            </div>
        </div>`
        document.querySelector('body').insertAdjacentHTML('afterend', modal)
        console.log($('.ui.dropdown'))
        $('.ui.dropdown').dropdown();
        $(document).on("click",".rag-save",function() {
            let tags = $('.ui.dropdown').dropdown('get value')
            msg = {'type': 'save-label-data', 'data': {}}
            msg.data.context = document.querySelector('.rag-context').value
            msg.data.question = document.querySelector('.rag-question').value
            msg.data.answer = document.querySelector('.rag-answer').value
            msg.data.content = document.querySelector('body').outerHTML
            msg.data.url = window.location.href
            msg.data.tags = tags
            chrome.runtime.sendMessage(msg, (response) => {
                console.log('save-label-data: ', response);
                if (response.status == 200){
                    alert('Data Saved Successfully!')
                    $('.ui.modal').modal('hide')
                    document.querySelector('.rag-question').value = ''
                    document.querySelector('.rag-answer').value = ''
                }else{
                    alert('Something wrong, try again!')
                }
            });
        });
    }
})()
(function () {
    function add_search_btn(){
        let form = document.querySelector('#prompt-textarea').parentNode;
        let search_btn = `<button class="ui button search-ctx" style="margin: 5px">🔍</button>`
        form.insertAdjacentHTML('afterend', search_btn)
    }
    window.onload = function(){
        console.log('add script: search-ctx')
        add_search_btn()
        $(document).on("click",".search-ctx",function(e) {
            e.preventDefault()
            let prompt = document.querySelector('#prompt-textarea').textContent
            if (prompt.length > 0){
                msg = {'type': 'search-context', 'data': {}}
                msg.data.question = prompt
                chrome.runtime.sendMessage(msg, (response) => {
                    if (response.status == 200){
                        let data = JSON.parse(response.data)
                        console.log('search-context: ', data);
                        if (data.length > 0){
                            let context = ''
                            if (data[0]._distance < 0.4){
                                context += `${data[0].context}\n${data[0].question}\n${data[0].answer}\n`
                            }
                            document.querySelector('#prompt-textarea').value = context + '\n' + prompt
                        }
                    }
                });
            }
        })
        window.navigation.addEventListener("navigate", () => {
            setTimeout(function(){
                if(document.querySelectorAll('.search-ctx').length == 0){
                   add_search_btn()
                }
            },3000)
        }, false);
    }
})()
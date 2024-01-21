(function(){
    function get_tags(cb){
        chrome.runtime.sendMessage({'type': 'get-tags'}, function(rsp){
            if (rsp.status == 200){
                cb(rsp.tags)
            }else{
                cb([])
            }
        })
    }
    function render_tags(tags){
        let listHtml = ''
        tags.forEach(item => {
            listHtml += `
            <div class="item">
                <div class="right floated content">
                    <div class="header">
                    <div class="ui button mini del-tag" data-id="${item}">✖️</div>
                    </div>
                </div>
                <div class="content">
                    <div class="header">${item}</div>
                </div>
            </div>
            `
        });
        document.querySelector('.tag-list').innerHTML = listHtml
    }
    window.onload = function(){
        get_tags(tags=>{
            render_tags(tags)
        })
        $(document).on('click','.add-tag',function(e){
            tag = $('.new-tag').val()
            chrome.runtime.sendMessage({'type': 'add-tag', 'tag': tag}, function(rsp){
                render_tags(rsp.tags)
            })
        })
        $(document).on('click','.del-tag',function(e){
            let tag = e.currentTarget.dataset['id']
            chrome.runtime.sendMessage({'type': 'del-tags', 'tag': tag}, function(rsp){
                render_tags(rsp.tags)
            })
        })
    }
})()
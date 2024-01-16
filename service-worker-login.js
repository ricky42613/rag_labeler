var USER = ''
chrome.identity.getProfileUserInfo(function(userInfo){
    USER = userInfo.email
    console.log(USER)
});
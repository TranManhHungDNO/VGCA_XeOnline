chrome.action.onClicked.addListener(() => {

    chrome.runtime.sendNativeMessage(
        "vn.hung.vgca",
        {
            action: "OPEN"
        },
        (response) => {

            console.log(response);

            if (chrome.runtime.lastError) {
                console.error(chrome.runtime.lastError);
            }

        }
    );

});